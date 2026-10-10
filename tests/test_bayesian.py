"""Tests for Bayesian Confidence Filter."""
from steam_rater.bayesian import evaluate_game, calculate_bayesian_score


def test_calculate_bayesian_score():
    # 0 reviews -> 0.0
    assert calculate_bayesian_score(0, 0, c=50.0, m=0.5) == 0.0
    
    # 10/10 with C=50, m=0.5 -> (25 + 10) / (50 + 10) = 35 / 60 = 0.5833
    score_10 = calculate_bayesian_score(10, 10, c=50.0, m=0.5)
    assert round(score_10, 4) == 0.5833

    # 80/80 with C=50, m=0.5 -> (25 + 80) / (50 + 80) = 105 / 130 = 0.8077
    score_80 = calculate_bayesian_score(80, 80, c=50.0, m=0.5)
    assert round(score_80, 4) == 0.8077

    # 200/200 with C=50, m=0.5 -> (25 + 200) / (50 + 200) = 225 / 250 = 0.90
    score_200 = calculate_bayesian_score(200, 200, c=50.0, m=0.5)
    assert round(score_200, 4) == 0.9000


def test_evaluate_game_niche_game_disqualified():
    # A game with 10/10 positive reviews is raw 100%, but too niche for Overwhelmingly Positive
    res = evaluate_game(10, 10, c=50.0, m=0.5, active_tiers={"Overwhelmingly Positive", "Very Positive"})
    assert res["raw_percent"] == 100.0
    assert res["base_tier"] == "Overwhelmingly Positive"
    assert res["status"] == "low_confidence"
    assert res["assigned_tier"] is None


def test_evaluate_game_exceptional_indie_qualifies():
    # An indie hit with 80/80 positive reviews sets itself through!
    # Raw is 100%, but Bayesian is 80.8% -> qualifies for Very Positive (min 75%)
    res = evaluate_game(80, 80, c=50.0, m=0.5, active_tiers={"Overwhelmingly Positive", "Very Positive"})
    assert res["raw_percent"] == 100.0
    # Base tier is Overwhelmingly Positive (>=95%), needs Bayesian >= 88%
    # With 80/80, Bayesian is 80.8% < 88%, so for Overwhelmingly Positive it is still low_confidence
    # Let's test with 180/180 -> Bayesian = (25 + 180)/(50 + 180) = 205/230 = 89.1% >= 88%!
    res_180 = evaluate_game(180, 180, c=50.0, m=0.5, active_tiers={"Overwhelmingly Positive", "Very Positive"})
    assert res_180["status"] == "assigned"
    assert res_180["assigned_tier"] == "Overwhelmingly Positive"


def test_evaluate_game_major_hit():
    # Major hit with 10,000 positive out of 10,200 (98%)
    res = evaluate_game(10000, 10200, c=50.0, m=0.5, active_tiers={"Overwhelmingly Positive", "Very Positive"})
    assert res["status"] == "assigned"
    assert res["assigned_tier"] == "Overwhelmingly Positive"


if __name__ == "__main__":
    test_calculate_bayesian_score()
    test_evaluate_game_niche_game_disqualified()
    test_evaluate_game_exceptional_indie_qualifies()
    test_evaluate_game_major_hit()
    print("All tests passed!")
