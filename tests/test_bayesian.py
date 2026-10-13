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
    # Raw is 100%, and Bayesian is 80.8% >= 80% gate -> qualifies for Overwhelmingly Positive!
    res = evaluate_game(80, 80, c=50.0, m=0.5, active_tiers={"Overwhelmingly Positive", "Very Positive"})
    assert res["raw_percent"] == 100.0
    assert res["status"] == "assigned"
    assert res["assigned_tier"] == "Overwhelmingly Positive"


def test_evaluate_game_major_hit():
    # Major hit with 10,000 positive out of 10,200 (98%)
    res = evaluate_game(10000, 10200, c=50.0, m=0.5, active_tiers={"Overwhelmingly Positive", "Very Positive"})
    assert res["status"] == "assigned"
    assert res["assigned_tier"] == "Overwhelmingly Positive"


def test_positive_tier_multipliers():
    # Level 5: C = 700
    c_val = 700.0
    active = {"Overwhelmingly Positive", "Very Positive", "Mostly Positive"}
    
    # Overwhelmingly Positive: 1.25 * 700 = 875 reviews required
    res_op_low = evaluate_game(870, 874, c=c_val, active_tiers=active) # ~99.5%
    assert res_op_low["status"] == "low_confidence", "874 reviews should be low_confidence for OP at C=700"
    res_op_ok = evaluate_game(871, 875, c=c_val, active_tiers=active)
    assert res_op_ok["status"] == "assigned" and res_op_ok["assigned_tier"] == "Overwhelmingly Positive"

    # Very Positive: 3.57 * 700 = 2499 reviews required
    res_vp_low = evaluate_game(2200, 2498, c=c_val, active_tiers=active) # ~88%
    assert res_vp_low["status"] == "low_confidence", "2498 reviews should be low_confidence for VP at C=700"
    res_vp_ok = evaluate_game(2200, 2500, c=c_val, active_tiers=active)
    assert res_vp_ok["status"] == "assigned" and res_vp_ok["assigned_tier"] == "Very Positive"

    # Mostly Positive: 5.7 * 700 = 3990 reviews required
    res_mp_low = evaluate_game(2990, 3989, c=c_val, active_tiers=active) # ~75%
    assert res_mp_low["status"] == "low_confidence", "3989 reviews should be low_confidence for MP at C=700"
    res_mp_ok = evaluate_game(2995, 3990, c=c_val, active_tiers=active)
    assert res_mp_ok["status"] == "assigned" and res_mp_ok["assigned_tier"] == "Mostly Positive"


def test_neutral_negative_tier_baselines():
    # Mixed and Negative tiers must use Steam baselines (50 / 500) regardless of high C values!
    high_c = 3500.0 # Level 10
    active = {"Mixed", "Mostly Negative", "Overwhelmingly Negative"}

    # Mixed: raw 40-69%, baseline 50 reviews
    res_mixed_under = evaluate_game(25, 49, c=high_c, active_tiers=active) # 51%
    assert res_mixed_under["status"] == "low_confidence", "<50 reviews should be low_confidence"
    res_mixed_ok = evaluate_game(25, 50, c=high_c, active_tiers=active) # 50%
    assert res_mixed_ok["status"] == "assigned" and res_mixed_ok["assigned_tier"] == "Mixed"

    # Mostly Negative: raw 20-39%, baseline 50 reviews
    res_mn_under = evaluate_game(10, 40, c=high_c, active_tiers=active) # 25%
    assert res_mn_under["status"] == "low_confidence", "<50 reviews should be low_confidence"
    res_mn_ok = evaluate_game(15, 50, c=high_c, active_tiers=active) # 30%
    assert res_mn_ok["status"] == "assigned" and res_mn_ok["assigned_tier"] == "Mostly Negative"

    # Overwhelmingly Negative: raw <20%, baseline 500 reviews
    res_on_under = evaluate_game(40, 499, c=high_c, active_tiers=active) # 8%
    assert res_on_under["status"] == "low_confidence", "<500 reviews should be low_confidence"
    res_on_ok = evaluate_game(40, 500, c=high_c, active_tiers=active) # 8%
    assert res_on_ok["status"] == "assigned" and res_on_ok["assigned_tier"] == "Overwhelmingly Negative"


if __name__ == "__main__":
    test_calculate_bayesian_score()
    test_evaluate_game_niche_game_disqualified()
    test_evaluate_game_exceptional_indie_qualifies()
    test_evaluate_game_major_hit()
    test_positive_tier_multipliers()
    test_neutral_negative_tier_baselines()
    print("All tests passed!")

