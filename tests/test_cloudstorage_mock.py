"""Unit test for cloudstorage writing and backup in a mock directory."""
import json
import shutil
import tempfile
from pathlib import Path
from steam_rater.steam_service import (
    get_cloudstorage_paths,
    read_cloudstorage_json,
    read_namespaces_json,
    write_rating_collections,
)


def test_mock_cloudstorage_write(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    try:
        steam_mock = temp_dir / "Steam"
        user_id = "12345678"
        cs_dir = steam_mock / "userdata" / user_id / "config" / "cloudstorage"
        cs_dir.mkdir(parents=True, exist_ok=True)

        ns1_file = cs_dir / "cloud-storage-namespace-1.json"
        ns_meta = cs_dir / "cloud-storage-namespaces.json"

        # Mock existing collections
        initial_data = [
            [
                "user-collections.favorite",
                {
                    "key": "user-collections.favorite",
                    "timestamp": 1000,
                    "value": json.dumps({"id": "favorite", "name": "Favorites", "added": [10, 20], "removed": []}),
                    "version": "100"
                }
            ]
        ]
        ns1_file.write_text(json.dumps(initial_data), encoding="utf-8")
        ns_meta.write_text(json.dumps([[1, "100"]]), encoding="utf-8")

        # Monkeypatch is_steam_running to False for the test
        import steam_rater.steam_service as ss
        original_is_running = ss.is_steam_running
        ss.is_steam_running = lambda: False

        try:
            # Call write_rating_collections
            tier_app_map = {
                "Overwhelmingly Positive": [10, 30],
                "Very Positive": [40, 50],
            }
            res = ss.write_rating_collections(steam_mock, user_id, tier_app_map, prefix="★ ")
            assert res["success"] is True
            assert res["backup_path"] is not None
            assert Path(res["backup_path"]).exists()

            # Verify backup content
            backup_data = json.loads(Path(res["backup_path"]).read_text(encoding="utf-8"))
            assert len(backup_data) == 1
            assert backup_data[0][0] == "user-collections.favorite"

            # Verify new file content
            new_data = json.loads(ns1_file.read_text(encoding="utf-8"))
            keys = [entry[0] for entry in new_data]
            assert "user-collections.favorite" in keys
            assert "user-collections.rating-overwhelmingly-positive" in keys
            assert "user-collections.rating-very-positive" in keys

            # Check that Favorites was preserved
            fav_entry = next(e for e in new_data if e[0] == "user-collections.favorite")
            assert json.loads(fav_entry[1]["value"])["name"] == "Favorites"

            # Check new rating collection
            op_entry = next(e for e in new_data if e[0] == "user-collections.rating-overwhelmingly-positive")
            val = json.loads(op_entry[1]["value"])
            assert val["name"] == "★ Overwhelmingly Positive"
            assert val["added"] == [10, 30]

            print("Mock cloudstorage write and backup test passed!")
        finally:
            ss.is_steam_running = original_is_running
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_mock_cloudstorage_write(None)
