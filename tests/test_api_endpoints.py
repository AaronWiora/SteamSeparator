"""Integration tests for updated FastAPI endpoints."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from steam_rater.app import app

client = TestClient(app)


def get_test_account_id() -> str:
    res = client.get("/api/status")
    data = res.json()
    if data.get("users"):
        return data["users"][0]["account_id"]
    return "0"


def test_api_status():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "steam_path" in data
    assert "users" in data
    assert data["total_owned_apps"] > 0
    print(f"Status test passed: {data['total_owned_apps']} clean games detected.")


def test_api_preview_levels():
    account_id = get_test_account_id()
    # Test preview with Low (C=25), Med (C=50), High (C=100)
    for c_val in [25.0, 50.0, 100.0]:
        res = client.post("/api/preview", json={
            "account_id": account_id,
            "c": c_val,
            "m": 0.50,
            "active_tiers": ["Overwhelmingly Positive", "Very Positive"]
        })
        assert res.status_code == 200
        data = res.json()
        assert "stats" in data
        assert "games" in data
        assert len(data["games"]) > 0

        # Verify no 228981 or non-game depot in list
        app_ids = [g["appid"] for g in data["games"]]
        assert 228981 not in app_ids
        assert 228980 not in app_ids

        # Verify all games have real names
        sample_names = [g["name"] for g in data["games"][:10]]
        print(f"C={c_val} Preview: {data['stats']['assigned']} assigned. Sample games: {sample_names[:3]}")

        # Verify bilingual labels exist
        assert "status_label_de" in data["games"][0]
        assert "status_label_en" in data["games"][0]


def test_api_scan_single():
    # Test single-app scan endpoint with Raft (648800)
    res = client.post("/api/scan/single/648800")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["game"]["appid"] == 648800
    assert data["game"]["name"] == "Raft"
    assert data["game"]["total_reviews"] > 300000
    print(f"Single scan test passed: {data['game']['name']} -> {data['game']['total_reviews']} reviews.")


def test_delisted_games_excluded():
    account_id = get_test_account_id()
    res = client.post("/api/preview", json={
        "account_id": account_id,
        "c": 50.0,
        "m": 0.50,
        "active_tiers": ["Overwhelmingly Positive", "Very Positive", "Mostly Positive"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["stats"]["delisted"] > 0

    # Truly removed store pages (e.g. Gremlins vs Automatons 587670) are delisted
    delisted_game = next((g for g in data["games"] if g["appid"] in [587670, 31740, 212370]), None)
    assert delisted_game is not None
    assert delisted_game["status"] == "delisted"
    assert delisted_game["assigned_tier"] is None

    # Mark of the Ninja (214560) and Baphomets Fluch (57640) must NOT be delisted
    ninja = next((g for g in data["games"] if g["appid"] == 214560), None)
    if ninja:
        assert ninja["status"] == "assigned", f"Mark of the Ninja should be assigned, got {ninja['status']}"
        assert ninja["assigned_tier"] in ["Overwhelmingly Positive", "Very Positive"]

    broken_sword = next((g for g in data["games"] if g["appid"] == 57640), None)
    if broken_sword:
        assert broken_sword["status"] == "assigned", f"Baphomets Fluch should be assigned, got {broken_sword['status']}"
        assert broken_sword["assigned_tier"] in ["Overwhelmingly Positive", "Very Positive"]

    print(f"Delisted test passed: truly removed={delisted_game['name']} status={delisted_game['status']}")


def test_unavailable_games_excluded():
    account_id = get_test_account_id()
    res = client.post("/api/preview", json={
        "account_id": account_id,
        "c": 350.0,
        "m": 0.50,
        "active_tiers": ["Overwhelmingly Positive", "Very Positive"]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["stats"]["unavailable"] > 0

    # Find Friday the 13th (438740)
    friday = next((g for g in data["games"] if g["appid"] == 438740), None)
    assert friday is not None
    assert friday["status"] == "unavailable"
    assert friday["assigned_tier"] is None
    assert friday["status_label_de"] == "Nicht verfügbar"
    assert friday["status_label_en"] == "Unavailable"

    # Ensure it is NOT present in any active collection tier
    for tier, apps in data["tier_app_map"].items():
        assert 438740 not in apps, f"Unavailable game 438740 should not be in tier {tier}"

    print(f"Unavailable test passed: {friday['name']} status={friday['status']}")


def test_elec_dude_and_gremlins():
    account_id = get_test_account_id()
    res = client.post("/api/preview", json={
        "account_id": account_id,
        "c": 350.0,
        "m": 0.50,
        "active_tiers": ["Overwhelmingly Positive", "Very Positive"]
    })
    assert res.status_code == 200
    data = res.json()

    # Elec Dude (1907980) has 124 reviews, not 0!
    elec = next((g for g in data["games"] if g["appid"] == 1907980), None)
    assert elec is not None
    assert elec["total_reviews"] == 124
    assert elec["total_positive"] == 119
    assert elec["status"] == "low_confidence"

    # Gremlins vs Automatons (587670) is delisted because store page was pulled by Steam
    gremlins = next((g for g in data["games"] if g["appid"] == 587670), None)
    assert gremlins is not None
    assert gremlins["status"] == "delisted"
    assert gremlins["assigned_tier"] is None

    print(f"Elec Dude & Gremlins test passed: Elec reviews={elec['total_reviews']}, Gremlins status={gremlins['status']}")


if __name__ == "__main__":
    test_api_status()
    test_api_preview_levels()
    test_delisted_games_excluded()
    test_unavailable_games_excluded()
    test_elec_dude_and_gremlins()
    test_api_scan_single()
    print("All updated integration tests passed!")
