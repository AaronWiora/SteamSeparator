"""
Steam filesystem, registry detection, and cloud-storage collection management.
"""
import json
import os
import re
import shutil
import subprocess
import time
import winreg
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from .app_catalog import is_valid_game, get_cached_name


def find_steam_path() -> Optional[Path]:
    """Find the Steam installation path via Windows Registry."""
    reg_locations = [
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
    ]
    for hkey, subkey, val_name in reg_locations:
        try:
            with winreg.OpenKey(hkey, subkey) as key:
                val, _ = winreg.QueryValueEx(key, val_name)
                p = Path(val)
                if p.is_dir() and (p / "steam.exe").exists():
                    return p
        except OSError:
            continue

    # Fallbacks
    for fallback in [
        Path(r"C:\Program Files (x86)\Steam"),
        Path(r"C:\Program Files\Steam"),
    ]:
        if fallback.is_dir() and (fallback / "steam.exe").exists():
            return fallback

    return None


def is_steam_running() -> bool:
    """Check if the Steam process is currently running on Windows."""
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq steam.exe", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
        )
        return "steam.exe" in output.lower()
    except Exception:
        return False


def parse_vdf_simple(text: str) -> Dict[str, Any]:
    """Basic VDF parser for loginusers.vdf."""
    result = {}
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        m = re.match(r'^"([^"]+)"\s+"([^"]+)"', line)
        if m:
            k, v = m.group(1), m.group(2)
            result[k] = v
    return result


def get_steam_users(steam_path: Path) -> List[Dict[str, Any]]:
    """Discover all user accounts in Steam/userdata."""
    userdata_dir = steam_path / "userdata"
    if not userdata_dir.is_dir():
        return []

    loginusers_file = steam_path / "config" / "loginusers.vdf"
    user_metadata = {}
    if loginusers_file.is_file():
        try:
            content = loginusers_file.read_text(encoding="utf-8", errors="ignore")
            blocks = re.findall(r'"(\d{17})"\s*\{([^}]+)\}', content)
            for steam_id64, inner in blocks:
                steam_id3 = str(int(steam_id64) - 76561197960265728)
                meta = parse_vdf_simple(inner)
                user_metadata[steam_id3] = {
                    "steam_id64": steam_id64,
                    "persona_name": meta.get("PersonaName", ""),
                    "account_name": meta.get("AccountName", ""),
                    "most_recent": meta.get("MostRecent") == "1",
                    "timestamp": int(meta.get("Timestamp", 0)),
                }
        except Exception:
            pass

    users = []
    for entry in userdata_dir.iterdir():
        if entry.is_dir() and entry.name.isdigit() and entry.name != "0":
            account_id = entry.name
            meta = user_metadata.get(account_id, {})
            persona_name = meta.get("persona_name") or f"Account {account_id}"
            users.append({
                "account_id": account_id,
                "persona_name": persona_name,
                "account_name": meta.get("account_name", ""),
                "steam_id64": meta.get("steam_id64", ""),
                "userdata_path": str(entry),
                "is_recent": meta.get("most_recent", False),
            })

    users.sort(key=lambda u: u["is_recent"], reverse=True)
    return users


def get_owned_app_ids(steam_path: Path, account_id: str) -> List[int]:
    """
    Extract all real, owned game AppIDs.
    Parses Software/Valve/Steam/apps, existing collections, and installed library folders.
    Strictly filters out non-games, depots, test servers, and tools.
    """
    user_dir = steam_path / "userdata" / account_id
    candidate_ids = set()

    # 1. Parse Software/Valve/Steam/apps from localconfig.vdf
    localconfig_path = user_dir / "config" / "localconfig.vdf"
    if localconfig_path.is_file():
        try:
            content = localconfig_path.read_text(encoding="utf-8", errors="ignore")
            # Locate Software -> Valve -> Steam -> apps block
            idx = content.find('"Software"')
            if idx != -1:
                apps_idx = content.find('"apps"', idx)
                if apps_idx != -1:
                    # Parse block
                    open_brace = content.find('{', apps_idx)
                    if open_brace != -1:
                        depth = 1
                        curr = open_brace + 1
                        while curr < len(content) and depth > 0:
                            if content[curr] == '{':
                                depth += 1
                            elif content[curr] == '}':
                                depth -= 1
                            curr += 1
                        apps_text = content[open_brace:curr]
                        # Only take direct app sub-keys (e.g. \n\t\t\t\t"400"\n\t\t\t\t{)
                        for m in re.finditer(r'^\s*"(\d{2,10})"\s*\{', apps_text, re.MULTILINE):
                            candidate_ids.add(int(m.group(1)))
        except Exception:
            pass

    # 2. Parse libraryfolders.vdf for installed games
    libraryfolders_path = steam_path / "steamapps" / "libraryfolders.vdf"
    if libraryfolders_path.is_file():
        try:
            content = libraryfolders_path.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'"apps"\s*\{([^}]+)\}', content):
                for num in re.findall(r'"(\d{2,10})"', m.group(1)):
                    candidate_ids.add(int(num))
        except Exception:
            pass

    # 3. Parse existing cloud-storage-namespace-1.json (e.g. Hidden, Favorites, NewContentRollup)
    cs_path = user_dir / "config" / "cloudstorage" / "cloud-storage-namespace-1.json"
    if cs_path.is_file():
        try:
            cs_data = json.loads(cs_path.read_text(encoding="utf-8"))
            for entry in cs_data:
                if isinstance(entry, list) and len(entry) == 2:
                    k, v = entry[0], entry[1]
                    if k.startswith("NewContentRollup_"):
                        aid_str = k.replace("NewContentRollup_", "")
                        if aid_str.isdigit():
                            candidate_ids.add(int(aid_str))
                    elif k.startswith("user-collections."):
                        val_str = v.get("value")
                        if val_str and isinstance(val_str, str):
                            try:
                                coll_obj = json.loads(val_str)
                                for aid in coll_obj.get("added", []):
                                    if isinstance(aid, int):
                                        candidate_ids.add(aid)
                            except Exception:
                                pass
        except Exception:
            pass

    # Filter candidates: Must be a valid game in catalog and not a tool/DLC/server
    clean_app_ids = []
    for aid in candidate_ids:
        if is_valid_game(aid):
            clean_app_ids.append(aid)

    clean_app_ids.sort()
    return clean_app_ids


def get_cloudstorage_paths(steam_path: Path, account_id: str) -> Tuple[Path, Path]:
    cs_dir = steam_path / "userdata" / account_id / "config" / "cloudstorage"
    cs_dir.mkdir(parents=True, exist_ok=True)
    ns1_file = cs_dir / "cloud-storage-namespace-1.json"
    namespaces_file = cs_dir / "cloud-storage-namespaces.json"
    return ns1_file, namespaces_file


def create_cloudstorage_backup(steam_path: Path, account_id: str) -> Optional[Path]:
    ns1_file, _ = get_cloudstorage_paths(steam_path, account_id)
    if not ns1_file.is_file():
        return None
    timestamp = int(time.time())
    backup_file = ns1_file.parent / f"cloud-storage-namespace-1.backup-{timestamp}.json"
    shutil.copy2(ns1_file, backup_file)
    return backup_file


def list_backups(steam_path: Path, account_id: str) -> List[Dict[str, Any]]:
    ns1_file, _ = get_cloudstorage_paths(steam_path, account_id)
    backups = []
    for file in ns1_file.parent.glob("cloud-storage-namespace-1.backup-*.json"):
        backups.append({
            "filename": file.name,
            "path": str(file),
            "timestamp": file.stat().st_mtime,
            "size": file.stat().st_size,
        })
    backups.sort(key=lambda b: b["timestamp"], reverse=True)
    return backups


def restore_backup(steam_path: Path, account_id: str, backup_filename: str) -> bool:
    """Restore a backup file."""
    if is_steam_running():
        raise RuntimeError("Steam läuft noch. Bitte beende Steam vollständig vor der Wiederherstellung.")

    ns1_file, _ = get_cloudstorage_paths(steam_path, account_id)
    backup_path = ns1_file.parent / backup_filename
    if not backup_path.is_file():
        raise FileNotFoundError(f"Backup-Datei {backup_filename} nicht gefunden.")

    shutil.copy2(backup_path, ns1_file)
    return True


def read_cloudstorage_json(ns1_file: Path) -> List[Any]:
    if not ns1_file.is_file():
        return []
    try:
        content = ns1_file.read_text(encoding="utf-8")
        return json.loads(content)
    except Exception:
        return []


def read_namespaces_json(namespaces_file: Path) -> Tuple[List[Any], int]:
    if not namespaces_file.is_file():
        return [[1, "1"]], 1
    try:
        data = json.loads(namespaces_file.read_text(encoding="utf-8"))
        max_ver = 1
        for item in data:
            if isinstance(item, list) and len(item) == 2 and item[0] == 1:
                try:
                    max_ver = max(max_ver, int(item[1]))
                except ValueError:
                    pass
        return data, max_ver
    except Exception:
        return [[1, "1"]], 1


def write_rating_collections(
    steam_path: Path,
    account_id: str,
    tier_app_map: Dict[str, List[int]],
    prefix: str = ""
) -> Dict[str, Any]:
    """
    Write rating collections into cloud-storage-namespace-1.json.
    Creates automatic backup silently in the background.
    """
    if is_steam_running():
        raise RuntimeError(
            "Steam läuft aktuell noch! Bitte beende Steam vollständig vor dem Speichern."
        )

    # Silent automatic backup
    backup_file = create_cloudstorage_backup(steam_path, account_id)

    ns1_file, namespaces_file = get_cloudstorage_paths(steam_path, account_id)
    items = read_cloudstorage_json(ns1_file)
    namespaces_data, current_max_version = read_namespaces_json(namespaces_file)

    now_ts = int(time.time())
    next_ver = current_max_version + 1

    active_slugs = {}
    for tier_name, app_ids in tier_app_map.items():
        slug = f"rating-{tier_name.lower().replace(' ', '-')}"
        active_slugs[slug] = {
            "tier_name": tier_name,
            "display_name": f"{prefix}{tier_name}".strip(),
            "app_ids": app_ids,
        }

    existing_items_dict = {}
    other_items = []

    for entry in items:
        if isinstance(entry, list) and len(entry) == 2:
            key = entry[0]
            val_obj = entry[1]
            if key.startswith("user-collections.rating-"):
                existing_items_dict[key] = val_obj
            else:
                other_items.append(entry)
        else:
            other_items.append(entry)

    new_collection_entries = []

    for slug, info in active_slugs.items():
        key = f"user-collections.{slug}"
        display_name = info["display_name"]
        app_ids = info["app_ids"]

        val_payload = json.dumps({
            "id": slug,
            "name": display_name,
            "added": app_ids,
            "removed": [],
        }, separators=(',', ':'))

        entry_obj = {
            "key": key,
            "timestamp": now_ts,
            "value": val_payload,
            "version": str(next_ver),
            "conflictResolutionMethod": "custom",
            "strMethodId": "union-collections",
        }
        next_ver += 1
        new_collection_entries.append([key, entry_obj])

    for old_key in existing_items_dict:
        slug = old_key.replace("user-collections.", "")
        if slug not in active_slugs:
            deleted_obj = {
                "key": old_key,
                "timestamp": now_ts,
                "is_deleted": True,
                "version": str(next_ver),
            }
            next_ver += 1
            new_collection_entries.append([old_key, deleted_obj])

    final_items = other_items + new_collection_entries

    ns1_file.write_text(
        json.dumps(final_items, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    updated_namespaces = []
    found_ns1 = False
    for item in namespaces_data:
        if isinstance(item, list) and len(item) == 2 and item[0] == 1:
            updated_namespaces.append([1, str(next_ver)])
            found_ns1 = True
        else:
            updated_namespaces.append(item)
    if not found_ns1:
        updated_namespaces.append([1, str(next_ver)])

    namespaces_file.write_text(
        json.dumps(updated_namespaces, separators=(',', ':')),
        encoding="utf-8"
    )

    return {
        "success": True,
        "backup_path": str(backup_file) if backup_file else None,
        "written_collections": [
            {"tier": info["tier_name"], "name": info["display_name"], "count": len(info["app_ids"])}
            for info in active_slugs.values()
        ],
    }
