"""
Rating fetcher and SQLite persistent cache service.
"""
import asyncio
import html
import json
import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import httpx
from .config import DB_PATH
from .app_catalog import get_cached_name

logger = logging.getLogger(__name__)

STORE_HEADERS = {
    "Cookie": "birthtime=788918401; lastagecheckage=1-0-1995; mature_content=1;",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}

SCORE_MAP = {
    1: "Overwhelmingly Negative",
    2: "Very Negative",
    3: "Negative",
    4: "Mostly Negative",
    5: "Mixed",
    6: "Mostly Positive",
    7: "Positive",
    8: "Very Positive",
    9: "Overwhelmingly Positive",
}


class RatingDatabase:
    """Manages SQLite cache for game ratings and metadata."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    appid INTEGER PRIMARY KEY,
                    name TEXT,
                    total_positive INTEGER DEFAULT 0,
                    total_negative INTEGER DEFAULT 0,
                    total_reviews INTEGER DEFAULT 0,
                    review_score_desc TEXT,
                    scan_interval_days INTEGER DEFAULT 14,
                    is_free INTEGER DEFAULT NULL,
                    updated_at INTEGER
                )
            """)
            # Auto-migrate existing database table if needed
            cursor = conn.cursor()
            cols = [row[1] for row in cursor.execute("PRAGMA table_info(games)").fetchall()]
            if "scan_interval_days" not in cols:
                cursor.execute("ALTER TABLE games ADD COLUMN scan_interval_days INTEGER DEFAULT 14")
            if "is_free" not in cols:
                cursor.execute("ALTER TABLE games ADD COLUMN is_free INTEGER DEFAULT NULL")
            if "is_delisted" not in cols:
                cursor.execute("ALTER TABLE games ADD COLUMN is_delisted INTEGER DEFAULT 0")
            if "is_unavailable" not in cols:
                cursor.execute("ALTER TABLE games ADD COLUMN is_unavailable INTEGER DEFAULT 0")
            conn.commit()

    def get_game(self, appid: int) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM games WHERE appid = ?", (appid,)
            ).fetchone()
            if row:
                return dict(row)
        return None

    def get_all_games(self) -> Dict[int, Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM games").fetchall()
            return {row["appid"]: dict(row) for row in rows}

    def clean_invalid_entries(self, valid_app_ids: List[int]):
        """Remove entries that are not in valid_app_ids."""
        if not valid_app_ids:
            return
        placeholders = ",".join("?" for _ in valid_app_ids)
        with self._get_conn() as conn:
            conn.execute(
                f"DELETE FROM games WHERE appid NOT IN ({placeholders})",
                valid_app_ids
            )
            conn.commit()

    def upsert_game(
        self,
        appid: int,
        name: Optional[str],
        total_positive: int,
        total_negative: int,
        total_reviews: int,
        review_score_desc: str,
        is_free: Optional[int] = None,
        is_delisted: Optional[int] = None,
        is_unavailable: Optional[int] = None,
    ):
        with self._get_conn() as conn:
            catalog_name = get_cached_name(appid)
            final_name = catalog_name or name or f"App {appid}"

            # Calculate adaptive backoff interval (14 -> 28 -> 56 -> max 90 days)
            existing = conn.execute(
                "SELECT review_score_desc, scan_interval_days FROM games WHERE appid = ?", (appid,)
            ).fetchone()

            if existing and existing["review_score_desc"]:
                old_desc = existing["review_score_desc"]
                current_interval = existing["scan_interval_days"] or 14
                if old_desc == review_score_desc:
                    # Rating unchanged: double interval up to 90 days
                    new_interval = min(90, current_interval * 2)
                else:
                    # Official rating tier changed: reset back to 14 days
                    new_interval = 14
            else:
                new_interval = 14

            conn.execute("""
                INSERT INTO games (appid, name, total_positive, total_negative, total_reviews, review_score_desc, scan_interval_days, is_free, is_delisted, is_unavailable, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(appid) DO UPDATE SET
                    name = excluded.name,
                    total_positive = excluded.total_positive,
                    total_negative = excluded.total_negative,
                    total_reviews = excluded.total_reviews,
                    review_score_desc = excluded.review_score_desc,
                    scan_interval_days = excluded.scan_interval_days,
                    is_free = COALESCE(excluded.is_free, games.is_free),
                    is_delisted = COALESCE(excluded.is_delisted, games.is_delisted),
                    is_unavailable = COALESCE(excluded.is_unavailable, games.is_unavailable),
                    updated_at = excluded.updated_at
            """, (
                appid,
                final_name,
                total_positive,
                total_negative,
                total_reviews,
                review_score_desc,
                new_interval,
                is_free,
                is_delisted,
                is_unavailable,
                int(time.time()),
            ))
            conn.commit()


class RatingFetcher:
    """Asynchronously fetches reviews from Steam with fallback and cache."""

    def __init__(self, db: RatingDatabase):
        self.db = db
        self.is_scanning = False
        self.scan_task: Optional[asyncio.Task] = None
        self.progress = {
            "is_scanning": False,
            "total": 0,
            "current": 0,
            "percent": 0,
            "current_name": "",
            "message": "Bereit",
            "last_error": None,
        }

    async def fetch_app_reviews(
        self,
        client: httpx.AsyncClient,
        appid: int
    ) -> Dict[str, Any]:
        """Fetch review statistics for a single app matching official Steam Store page."""
        pos = 0
        neg = 0
        total = 0
        desc = "Unrated"
        fetched_ok = False
        is_free_val: Optional[int] = None
        is_delisted_val: Optional[int] = None
        is_unavailable_val: Optional[int] = None
        store_name: Optional[str] = None

        # Check if is_free is already known in database
        existing = self.db.get_game(appid)
        if existing:
            if existing.get("is_free") is not None:
                is_free_val = existing["is_free"]

        # 1. Attempt to fetch canonical review numbers directly from the Steam store page (data-props)
        try:
            store_url = f"https://store.steampowered.com/app/{appid}/"
            res_store = await client.get(store_url, headers=STORE_HEADERS, timeout=8.0)
            if res_store.status_code == 200:
                if "/app/" not in str(res_store.url):
                    # Redirected to store homepage -> Store page removed by Steam completely
                    is_delisted_val = 1
                    is_unavailable_val = 0
                else:
                    # Store page is live -> not delisted for owners!
                    is_delisted_val = 0
                    text_lower = res_store.text.lower()
                    is_region_locked = (
                        "nicht zur verfügung" in text_lower or
                        "nicht zur verf&uuml;gung" in text_lower or
                        "nicht in ihrem land" in text_lower or
                        "unavailable in your region" in text_lower or
                        "not available in your region" in text_lower or
                        "currently unavailable in your region" in text_lower
                    )
                    if is_region_locked:
                        is_unavailable_val = 1
                    else:
                        is_unavailable_val = 0

                    m_props = re.search(r'data-featuretarget="appreviews"\s*data-props="([^"]+)"', res_store.text)
                    if m_props:
                        props = json.loads(html.unescape(m_props.group(1)))
                        store_name = props.get("appname")
                        filt_opts = props.get("filter_options", {})
                        n_steam = filt_opts.get("nReviewsSteamPurchase", 0)
                        raw_pos = filt_opts.get("nReviewsPositive", 0)
                        raw_neg = filt_opts.get("nReviewsNegative", 0)
                        raw_tot_all = raw_pos + raw_neg

                        has_purchase = "btn_add_to_cart" in res_store.text or "free_btn" in res_store.text
                        is_free_bool = any(k in text_lower for k in ["free to play", "play for free", "kostenlos spielen", "kostenlos"])
                        is_free_val = 1 if (is_free_bool or (n_steam == 0 and raw_tot_all > 0)) else 0

                        # Review counts:
                        # For games with purchase disabled (e.g. remasters replaced originals), F2P, 0 steam checkout, or high key ratios:
                        is_purchase_disabled = not has_purchase and not is_free_bool and any(k in text_lower for k in ["no longer available", "nicht mehr im steam-shop", "nicht mehr zur verfügung"])
                        if is_purchase_disabled or is_free_val == 1 or n_steam == 0 or (n_steam > 0 and raw_tot_all > 1.5 * n_steam and raw_tot_all - n_steam > 1000):
                            total = raw_tot_all
                            pos = raw_pos
                            neg = raw_neg
                        elif n_steam > 0:
                            total = n_steam
                            ratio = (raw_pos / raw_tot_all) if raw_tot_all > 0 else 0.9
                            pos = int(round(total * ratio))
                            neg = total - pos
                        else:
                            summary_disp = props.get("summary_options", {}).get("summaryDisplayed") or props.get("summary_options", {}).get("summaryGlobalNoOutliers") or {}
                            total = summary_disp.get("nReviews", 0)
                            pos = summary_disp.get("nReviewsPositive", 0)
                            neg = max(0, total - pos)

                        summary_disp = props.get("summary_options", {}).get("summaryDisplayed") or props.get("summary_options", {}).get("summaryGlobalNoOutliers") or {}
                        score_id = summary_disp.get("eReviewScore", 0)
                        desc = SCORE_MAP.get(score_id, "Unrated")

                        if total > 0:
                            fetched_ok = True
        except Exception:
            pass

        async def fetch_query(purchase_type: str) -> Optional[Dict[str, Any]]:
            url = f"https://store.steampowered.com/appreviews/{appid}?json=1&num_per_page=0&language=all&purchase_type={purchase_type}&filter_offtopic_activity=0"
            for attempt in range(3):
                try:
                    res = await client.get(url, timeout=10.0)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("success") == 1:
                            return data.get("query_summary", {})
                    elif res.status_code == 429:
                        await asyncio.sleep(2.0 * (attempt + 1))
                except Exception:
                    await asyncio.sleep(0.8)
            return None

        # 2. If store page did not resolve review numbers, fallback to official appreviews API
        if not fetched_ok:
            # If delisted game: Steam Store defaults to purchase_type=all
            if is_delisted_val == 1:
                summary = await fetch_query("all")
                if summary:
                    pos = summary.get("total_positive", 0)
                    neg = summary.get("total_negative", 0)
                    total = summary.get("total_reviews", 0)
                    desc = summary.get("review_score_desc", "Unrated")
                fetched_ok = True
            # If already known whether the game is Free-to-Play or Paid:
            elif is_free_val == 1:
                # Free-to-Play game: Steam Store defaults to purchase_type=all
                summary = await fetch_query("all")
                if summary:
                    pos = summary.get("total_positive", 0)
                    neg = summary.get("total_negative", 0)
                    total = summary.get("total_reviews", 0)
                    desc = summary.get("review_score_desc", "Unrated")
                    fetched_ok = True
            elif is_free_val == 0:
                # Paid game: check steam purchases first, then all if 0
                summary_steam = await fetch_query("steam")
                tot_steam = summary_steam.get("total_reviews", 0) if summary_steam else 0
                if tot_steam == 0:
                    summary_all = await fetch_query("all")
                    if summary_all and summary_all.get("total_reviews", 0) > 0:
                        pos = summary_all.get("total_positive", 0)
                        neg = summary_all.get("total_negative", 0)
                        total = summary_all.get("total_reviews", 0)
                        desc = summary_all.get("review_score_desc", "Unrated")
                        is_free_val = 1
                        fetched_ok = True
                    elif summary_steam:
                        pos = 0
                        neg = 0
                        total = 0
                        desc = summary_steam.get("review_score_desc", "Unrated")
                        fetched_ok = True
                else:
                    pos = summary_steam.get("total_positive", 0)
                    neg = summary_steam.get("total_negative", 0)
                    total = summary_steam.get("total_reviews", 0)
                    desc = summary_steam.get("review_score_desc", "Unrated")
                    fetched_ok = True
            else:
                # Unknown is_free: Query purchase_type=steam first
                summary_steam = await fetch_query("steam")
                tot_steam = summary_steam.get("total_reviews", 0) if summary_steam else 0

                if tot_steam == 0:
                    # 0 Steam checkout purchases -> check purchase_type=all
                    summary_all = await fetch_query("all")
                    if summary_all and summary_all.get("total_reviews", 0) > 0:
                        pos = summary_all.get("total_positive", 0)
                        neg = summary_all.get("total_negative", 0)
                        total = summary_all.get("total_reviews", 0)
                        desc = summary_all.get("review_score_desc", "Unrated")
                        is_free_val = 1
                        fetched_ok = True
                    elif summary_steam:
                        pos = summary_steam.get("total_positive", 0)
                        neg = summary_steam.get("total_negative", 0)
                        total = 0
                        desc = summary_steam.get("review_score_desc", "Unrated")
                        is_free_val = 0
                        fetched_ok = True
                else:
                    # tot_steam > 0: Check purchase_type=all to see if it's Free-to-Play or transitioned
                    summary_all = await fetch_query("all")
                    tot_all = summary_all.get("total_reviews", 0) if summary_all else tot_steam

                    # Determine if Free-to-Play:
                    if (tot_all >= 10 * tot_steam and tot_all >= 500) or (tot_all - tot_steam > 500000):
                        is_free_val = 1
                    elif tot_all < 1.4 * tot_steam:
                        is_free_val = 0
                    else:
                        try:
                            det_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&filters=basic"
                            res_det = await client.get(det_url, timeout=5.0)
                            if res_det.status_code == 200:
                                data_det = res_det.json()
                                if data_det and str(appid) in data_det and data_det[str(appid)].get("success"):
                                    is_free_bool = data_det[str(appid)].get("data", {}).get("is_free", False)
                                    is_free_val = 1 if is_free_bool else 0
                        except Exception:
                            pass
                        if is_free_val is None:
                            is_free_val = 0

                    if is_free_val == 1 and summary_all:
                        pos = summary_all.get("total_positive", 0)
                        neg = summary_all.get("total_negative", 0)
                        total = summary_all.get("total_reviews", 0)
                        desc = summary_all.get("review_score_desc", "Unrated")
                        fetched_ok = True
                    elif summary_steam:
                        pos = summary_steam.get("total_positive", 0)
                        neg = summary_steam.get("total_negative", 0)
                        total = summary_steam.get("total_reviews", 0)
                        desc = summary_steam.get("review_score_desc", "Unrated")
                        fetched_ok = True

        name = store_name or get_cached_name(appid) or f"App {appid}"

        return {
            "appid": appid,
            "name": name,
            "total_positive": pos,
            "total_negative": neg,
            "total_reviews": total,
            "review_score_desc": desc,
            "is_free": is_free_val,
            "is_delisted": is_delisted_val,
            "is_unavailable": is_unavailable_val,
            "fetched_ok": fetched_ok,
        }

    async def scan_apps(self, app_ids: List[int], force_refresh: bool = False):
        """Scan a list of app IDs."""
        if self.is_scanning:
            return

        self.is_scanning = True
        cached_games = self.db.get_all_games()
        now = int(time.time())

        to_fetch = []
        for aid in app_ids:
            cached = cached_games.get(aid)
            if not cached or not cached.get("updated_at"):
                to_fetch.append(aid)
            elif cached.get("total_reviews", 0) == 0:
                to_fetch.append(aid)
            elif cached.get("is_delisted") == 1 or cached.get("is_unavailable") == 1:
                to_fetch.append(aid)
            elif force_refresh:
                to_fetch.append(aid)
            else:
                interval_days = cached.get("scan_interval_days") or 14
                if now - cached.get("updated_at", 0) >= interval_days * 86400:
                    to_fetch.append(aid)

        total_count = len(to_fetch)
        self.progress = {
            "is_scanning": True,
            "total": total_count,
            "current": 0,
            "percent": 0 if total_count > 0 else 100,
            "current_name": "",
            "message": f"{total_count} fällige Spiele werden abgefragt..." if total_count > 0 else "Alle Spiele sind aktuell! Keine fälligen Spiele.",
            "last_error": None,
        }

        if total_count == 0:
            self.is_scanning = False
            self.progress["is_scanning"] = False
            return

        semaphore = asyncio.Semaphore(3)
        completed = 0

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
        }

        async def worker(appid: int, client: httpx.AsyncClient):
            nonlocal completed
            async with semaphore:
                try:
                    info = await self.fetch_app_reviews(client, appid)
                    if info.get("fetched_ok"):
                        self.db.upsert_game(
                            appid=info["appid"],
                            name=info["name"],
                            total_positive=info["total_positive"],
                            total_negative=info["total_negative"],
                            total_reviews=info["total_reviews"],
                            review_score_desc=info["review_score_desc"],
                            is_free=info.get("is_free"),
                            is_delisted=info.get("is_delisted"),
                            is_unavailable=info.get("is_unavailable"),
                        )
                    completed += 1
                    self.progress["current"] = completed
                    self.progress["percent"] = int((completed / total_count) * 100)
                    self.progress["current_name"] = info["name"]
                    self.progress["message"] = f"Scanne {completed}/{total_count}: {info['name']}"
                    await asyncio.sleep(0.12)
                except Exception as e:
                    logger.error(f"Worker error for {appid}: {e}")

        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            tasks = [worker(aid, client) for aid in to_fetch]
            await asyncio.gather(*tasks, return_exceptions=True)

        self.is_scanning = False
        self.progress["is_scanning"] = False
        self.progress["message"] = f"Scan abgeschlossen! {completed} Spiele verarbeitet."
