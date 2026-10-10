from steam_rater.rating_service import RatingDatabase
db = RatingDatabase()
games = db.get_all_games()
print("Total games in ratings.db:", len(games))
no_name = [g for g in games.values() if g["name"].startswith("App ")]
print("Games with placeholder App name:", len(no_name))
for g in list(games.values())[:10]:
    print(g["appid"], g["name"], "reviews:", g["total_reviews"])
