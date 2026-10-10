"""Unit test for steam_service.py"""
from pathlib import Path
from steam_rater.steam_service import (
    find_steam_path,
    get_steam_users,
    get_owned_app_ids,
    is_steam_running,
    read_cloudstorage_json,
    get_cloudstorage_paths,
)


def test_steam_detection():
    path = find_steam_path()
    assert path is not None
    assert path.is_dir()
    print("Detected Steam Path:", path)

    running = is_steam_running()
    print("Is Steam running:", running)

    users = get_steam_users(path)
    assert len(users) > 0
    print("Detected users:", users)

    user = users[0]
    apps = get_owned_app_ids(path, user["account_id"])
    assert len(apps) > 0
    print(f"User {user['persona_name']} ({user['account_id']}) has {len(apps)} apps. First 5: {apps[:5]}")

    ns1, namespaces = get_cloudstorage_paths(path, user["account_id"])
    assert ns1.exists()
    items = read_cloudstorage_json(ns1)
    print(f"Cloudstorage entries count: {len(items)}")


if __name__ == "__main__":
    test_steam_detection()
    print("Steam service test passed successfully!")
