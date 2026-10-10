"""Test live fetching of real games into ratings.db."""
import asyncio
from steam_rater.rating_service import RatingDatabase, RatingFetcher


async def test_live_fetch():
    db = RatingDatabase()
    fetcher = RatingFetcher(db)

    # Test with 3 well-known games: 400 (Portal), 620 (Portal 2), 70 (Half-Life)
    test_app_ids = [400, 620, 70]
    print(f"Fetching review stats for apps: {test_app_ids}...")
    await fetcher.scan_apps(test_app_ids, force_refresh=True)

    games = db.get_all_games()
    for aid in test_app_ids:
        g = games.get(aid)
        assert g is not None
        assert g["total_reviews"] > 0
        print(f"App {aid} ({g['name']}): Pos={g['total_positive']}, Total={g['total_reviews']}, ScoreDesc={g['review_score_desc']}")

    print("Live fetch test passed successfully!")


if __name__ == "__main__":
    asyncio.run(test_live_fetch())
