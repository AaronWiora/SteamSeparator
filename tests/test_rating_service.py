"""Unit test for rating_service.py SQLite and basic fetch."""
import tempfile
from pathlib import Path
from steam_rater.rating_service import RatingDatabase


def test_rating_database():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        db_path = temp_dir / "test_ratings.db"
        db = RatingDatabase(db_path)

        # Upsert a game
        db.upsert_game(
            appid=400,
            name="Portal",
            total_positive=197000,
            total_negative=2900,
            total_reviews=199900,
            review_score_desc="Overwhelmingly Positive",
        )

        game = db.get_game(400)
        assert game is not None
        assert game["name"] == "Portal"
        assert game["total_positive"] == 197000
        assert game["total_reviews"] == 199900

        # Test Adaptive Interval Backoff
        # 1. Initial insert -> 14 days
        assert game["scan_interval_days"] == 14

        # 2. Re-scan with identical tier -> doubles to 28 days
        db.upsert_game(400, "Portal", 198000, 2900, 200900, "Overwhelmingly Positive")
        g2 = db.get_game(400)
        assert g2["scan_interval_days"] == 28

        # 3. Re-scan with identical tier -> doubles to 56 days
        db.upsert_game(400, "Portal", 199000, 2900, 201900, "Overwhelmingly Positive")
        g3 = db.get_game(400)
        assert g3["scan_interval_days"] == 56

        # 4. Re-scan with identical tier -> caps at 90 days
        db.upsert_game(400, "Portal", 200000, 2900, 202900, "Overwhelmingly Positive")
        g4 = db.get_game(400)
        assert g4["scan_interval_days"] == 90

        # 5. Rating changes to 'Very Positive' -> resets to 14 days
        db.upsert_game(400, "Portal", 200000, 40000, 240000, "Very Positive")
        g5 = db.get_game(400)
        assert g5["scan_interval_days"] == 14

        all_games = db.get_all_games()
        assert 400 in all_games
        print("RatingDatabase and Adaptive Interval tests passed successfully!")
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_rating_database()
