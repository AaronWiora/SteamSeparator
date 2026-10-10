"""
Catalog of Steam AppIDs and names, and game filtering logic.
"""
import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional
import httpx
from .config import WORKSPACE_ROOT

logger = logging.getLogger(__name__)

CACHE_FILE = WORKSPACE_ROOT / "app_names_cache.json"
APP_LIST_URL = "https://raw.githubusercontent.com/dgibbs64/SteamCMD-AppID-List/master/steamcmd_appid.json"

# Generic patterns of non-game technical items, test servers, branches, demos, and media
NON_GAME_PATTERNS = [
    r"\b(demo|beta|alpha|playtest|play test|staging|server|dedicated server|sdk|benchmark)\b",
    r"[-–—:]\s*(single player|multiplayer|tech(nical)? test|public test(ing)?|client|depot|experimental)\b",
    r"\b(dedicated server|test server|public test(ing)?|tech(nical)? test|multiplayer test|playtest|staging branch|experimental branch|experimental|public beta client)\b",
    r"\b(video player|soundtrack|ost|season pass|expansion pack|dlc|content pack|trailer|teaser|benchmark)\b",
    r"\b(steam client|winui2|steam input|input configs?|screenshots?|steam screenshots|steamvr|steam linux runtime|spacewar|redistributables?|steamworks)\b",
]

NON_GAME_REGEX = re.compile("|".join(NON_GAME_PATTERNS), re.IGNORECASE)

_name_cache: Optional[Dict[int, str]] = None


def load_app_catalog() -> Dict[int, str]:
    """Load cached app names or download if not present."""
    global _name_cache
    if _name_cache is not None:
        return _name_cache

    if CACHE_FILE.is_file():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                _name_cache = {int(k): v for k, v in raw.items()}
                return _name_cache
        except Exception as e:
            logger.warning(f"Error reading app cache file: {e}")

    try:
        logger.info("Downloading official Steam AppID names list...")
        headers = {"User-Agent": "Steam Rating Collections Manager"}
        res = httpx.get(APP_LIST_URL, headers=headers, timeout=15.0)
        if res.status_code == 200:
            data = res.json()
            apps = data.get("applist", {}).get("apps", [])
            _name_cache = {}
            for item in apps:
                aid = item.get("appid")
                nm = item.get("name")
                if aid and nm:
                    _name_cache[int(aid)] = nm.strip()

            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(_name_cache, f, ensure_ascii=False)
            return _name_cache
    except Exception as e:
        logger.warning(f"Failed to download app names list: {e}")

    _name_cache = {}
    return _name_cache


def get_cached_name(appid: int) -> Optional[str]:
    """Get the official game name for an app ID."""
    catalog = load_app_catalog()
    return catalog.get(appid)


def is_valid_game(appid: int, name: Optional[str] = None) -> bool:
    """Filter out tools, DLCs, servers, redistributables, and non-games."""
    app_name = name or get_cached_name(appid)
    if not app_name:
        return False

    if NON_GAME_REGEX.search(app_name):
        return False

    return True
