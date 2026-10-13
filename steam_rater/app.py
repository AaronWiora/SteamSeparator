"""
FastAPI application for Steam Rating Collections Manager.
"""
from typing import Dict, List, Optional
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import DEFAULT_C, DEFAULT_M, TIERS, FILTER_LEVELS, WORKSPACE_ROOT
from .bayesian import evaluate_game
from .rating_service import RatingDatabase, RatingFetcher
from .app_catalog import get_cached_name
from .steam_service import (
    find_steam_path,
    is_steam_running,
    get_steam_users,
    get_owned_app_ids,
    write_rating_collections,
    list_backups,
    restore_backup,
)

app = FastAPI(title="SteamSeparator")

db = RatingDatabase()
fetcher = RatingFetcher(db)
static_dir = WORKSPACE_ROOT / "static"


class ScanRequest(BaseModel):
    account_id: Optional[str] = None
    force_refresh: bool = False


class BatchScanRequest(BaseModel):
    appids: List[int]


class PreviewRequest(BaseModel):
    account_id: Optional[str] = None
    c: float = DEFAULT_C
    m: float = DEFAULT_M
    active_tiers: List[str] = ["Overwhelmingly Positive", "Very Positive"]


class SaveRequest(BaseModel):
    account_id: str
    c: float = DEFAULT_C
    m: float = DEFAULT_M
    active_tiers: List[str] = ["Overwhelmingly Positive", "Very Positive"]


class RestoreRequest(BaseModel):
    account_id: str
    backup_filename: str


@app.get("/api/status")
async def get_status():
    steam_path = find_steam_path()
    running = is_steam_running()
    users = get_steam_users(steam_path) if steam_path else []

    selected_account_id = users[0]["account_id"] if users else None
    owned_apps_count = 0
    if steam_path and selected_account_id:
        owned_apps_count = len(get_owned_app_ids(steam_path, selected_account_id))

    cached_games = db.get_all_games()

    return {
        "steam_path": str(steam_path) if steam_path else None,
        "is_steam_running": running,
        "users": users,
        "selected_account_id": selected_account_id,
        "total_owned_apps": owned_apps_count,
        "cached_apps_count": len(cached_games),
        "default_c": DEFAULT_C,
        "default_m": DEFAULT_M,
        "tiers": TIERS,
        "filter_levels": FILTER_LEVELS,
    }


@app.get("/api/scan/progress")
async def get_scan_progress():
    return fetcher.progress


@app.post("/api/scan/start")
async def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    if fetcher.is_scanning:
        return {"status": "already_scanning", "message": "Ein Scan läuft bereits."}

    steam_path = find_steam_path()
    if not steam_path:
        raise HTTPException(status_code=400, detail="Steam installation not found.")

    users = get_steam_users(steam_path)
    account_id = req.account_id or (users[0]["account_id"] if users else None)
    if not account_id:
        raise HTTPException(status_code=400, detail="No Steam user found.")

    app_ids = get_owned_app_ids(steam_path, account_id)
    background_tasks.add_task(fetcher.scan_apps, app_ids, req.force_refresh)

    return {"status": "started", "total_apps": len(app_ids)}


@app.api_route("/api/scan/single/{appid}", methods=["GET", "POST"])
@app.api_route("/api/scan/single/{appid}/", methods=["GET", "POST"])
async def scan_single_app(appid: int):
    """Scan or refresh a single game immediately from Steam."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        info = await fetcher.fetch_app_reviews(client, appid)
        if info.get("fetched_ok"):
            db.upsert_game(
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
            return {
                "success": True,
                "game": db.get_game(appid),
                "info": info
            }
        else:
            raise HTTPException(
                status_code=502,
                detail=f"Konnte Review-Daten von Steam für AppID {appid} nicht abrufen."
            )


@app.post("/api/scan/batch")
async def scan_batch_apps(req: BatchScanRequest, background_tasks: BackgroundTasks):
    """Scan a specific batch of apps immediately in the background."""
    if not req.appids:
        return {"status": "empty", "count": 0}
    if fetcher.is_scanning:
        return {"status": "already_scanning", "message": "Ein Scan läuft bereits."}
    background_tasks.add_task(fetcher.scan_apps, req.appids, True)
    return {"status": "started", "count": len(req.appids)}


@app.post("/api/preview")
async def get_preview(req: PreviewRequest):
    steam_path = find_steam_path()
    if not steam_path:
        raise HTTPException(status_code=400, detail="Steam not found.")

    users = get_steam_users(steam_path)
    account_id = req.account_id or (users[0]["account_id"] if users else None)
    if not account_id:
        raise HTTPException(status_code=400, detail="No user selected.")

    app_ids = get_owned_app_ids(steam_path, account_id)
    cached_games = db.get_all_games()
    active_set = set(req.active_tiers)

    stats = {
        "total_owned": len(app_ids),
        "scanned": 0,
        "assigned": 0,
        "low_confidence": 0,
        "unassigned": 0,
        "unscanned": 0,
        "delisted": 0,
        "unavailable": 0,
        "tier_counts": {t: 0 for t in TIERS},
    }

    tier_app_map: Dict[str, List[int]] = {t: [] for t in req.active_tiers}
    games_list = []

    for aid in app_ids:
        cached = cached_games.get(aid)
        is_scanned = bool(cached and cached.get("updated_at"))
        is_delisted = bool(cached and cached.get("is_delisted"))
        is_unavailable = bool(cached and cached.get("is_unavailable"))

        if cached and is_scanned:
            stats["scanned"] += 1
            pos = cached.get("total_positive", 0)
            tot = cached.get("total_reviews", 0)
            neg = cached.get("total_negative", 0)
            name = get_cached_name(aid) or cached.get("name") or f"App {aid}"
        else:
            pos = 0
            tot = 0
            neg = 0
            name = get_cached_name(aid) or f"App {aid}"

        eval_res = evaluate_game(
            pos,
            tot,
            c=req.c,
            m=req.m,
            active_tiers=active_set,
            is_scanned=is_scanned,
            is_delisted=is_delisted,
            is_unavailable=is_unavailable,
        )
        status = eval_res["status"]
        assigned_tier = eval_res["assigned_tier"]

        if status == "assigned" and assigned_tier:
            stats["assigned"] += 1
            stats["tier_counts"][assigned_tier] = stats["tier_counts"].get(assigned_tier, 0) + 1
            if assigned_tier in tier_app_map:
                tier_app_map[assigned_tier].append(aid)
        elif status == "delisted":
            stats["delisted"] += 1
        elif status == "unavailable":
            stats["unavailable"] += 1
        elif status == "low_confidence":
            stats["low_confidence"] += 1
        elif status == "unassigned":
            stats["unassigned"] += 1
        else:
            stats["unscanned"] += 1

        games_list.append({
            "appid": aid,
            "name": name,
            "total_positive": pos,
            "total_negative": neg,
            "total_reviews": tot,
            "raw_percent": eval_res["raw_percent"],
            "bayesian_score": eval_res["bayesian_score"],
            "base_tier": eval_res["base_tier"],
            "assigned_tier": assigned_tier,
            "status": status,
            "status_label_de": eval_res["status_label_de"],
            "status_label_en": eval_res["status_label_en"],
        })

    # Sort games: Assigned first, then by Bayesian Score descending
    games_list.sort(key=lambda g: (1 if g["status"] == "assigned" else 0, g["bayesian_score"]), reverse=True)

    return {
        "stats": stats,
        "tier_app_map": tier_app_map,
        "games": games_list,
        "is_steam_running": is_steam_running(),
    }


@app.post("/api/save")
async def save_collections(req: SaveRequest):
    if is_steam_running():
        raise HTTPException(
            status_code=409,
            detail="Steam läuft aktuell noch! Bitte beende Steam vollständig vor dem Speichern."
        )

    steam_path = find_steam_path()
    if not steam_path:
        raise HTTPException(status_code=400, detail="Steam installation not found.")

    app_ids = get_owned_app_ids(steam_path, req.account_id)
    cached_games = db.get_all_games()
    active_set = set(req.active_tiers)

    tier_app_map: Dict[str, List[int]] = {t: [] for t in req.active_tiers}
    for aid in app_ids:
        cached = cached_games.get(aid)
        # Skip delisted and unavailable games from collections completely
        if cached and (cached.get("is_delisted") or cached.get("is_unavailable")):
            continue
        pos = cached.get("total_positive", 0) if cached else 0
        tot = cached.get("total_reviews", 0) if cached else 0
        eval_res = evaluate_game(pos, tot, c=req.c, m=req.m, active_tiers=active_set)
        assigned = eval_res.get("assigned_tier")
        if assigned and assigned in tier_app_map:
            tier_app_map[assigned].append(aid)

    try:
        result = write_rating_collections(
            steam_path=steam_path,
            account_id=req.account_id,
            tier_app_map=tier_app_map,
            prefix="",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backups")
async def get_backups(account_id: str):
    steam_path = find_steam_path()
    if not steam_path:
        return []
    return list_backups(steam_path, account_id)


@app.post("/api/restore")
async def post_restore(req: RestoreRequest):
    steam_path = find_steam_path()
    if not steam_path:
        raise HTTPException(status_code=400, detail="Steam not found.")
    try:
        restore_backup(steam_path, req.account_id, req.backup_filename)
        return {"success": True, "message": f"Backup {req.backup_filename} wiederhergestellt!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# Static frontend mounting
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(
            static_dir / "index.html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

