"""
Bayesian Confidence Filter and Rating Categorization Logic.
"""
from typing import Dict, Any, Optional, Set
from .config import DEFAULT_C, DEFAULT_M, TIERS, POSITIVE_TIER_MULTIPLIERS, BASELINE_TIER_REVIEWS



def calculate_bayesian_score(
    positive: int,
    total: int,
    c: float = DEFAULT_C,
    m: float = DEFAULT_M
) -> float:
    """Calculate the Bayesian confidence score."""
    if total <= 0:
        return 0.0
    return (c * m + positive) / (c + total)


def get_base_tier(raw_percent: float) -> str:
    """Determine base Steam tier from raw positive ratio."""
    if raw_percent >= 0.95:
        return "Overwhelmingly Positive"
    elif raw_percent >= 0.80:
        return "Very Positive"
    elif raw_percent >= 0.70:
        return "Mostly Positive"
    elif raw_percent >= 0.40:
        return "Mixed"
    elif raw_percent >= 0.20:
        return "Mostly Negative"
    else:
        return "Overwhelmingly Negative"


def evaluate_game(
    positive: int,
    total: int,
    c: float = DEFAULT_C,
    m: float = DEFAULT_M,
    active_tiers: Optional[Set[str]] = None,
    is_scanned: bool = True,
    is_delisted: bool = False,
    is_unavailable: bool = False,
) -> Dict[str, Any]:
    """
    Evaluates a game using the Bayesian confidence score.
    Returns concise, clean status labels without confusing terms.
    """
    if is_unavailable:
        raw_pct = round((positive / total) * 100, 1) if total > 0 else 0.0
        b_score = round(calculate_bayesian_score(positive, total, c=c, m=m) * 100, 1) if total > 0 else 0.0
        b_tier = get_base_tier(positive / total) if total > 0 else "Unrated"
        return {
            "raw_percent": raw_pct,
            "bayesian_score": b_score,
            "base_tier": b_tier,
            "assigned_tier": None,
            "status": "unavailable",
            "status_label_de": "Nicht verfügbar",
            "status_label_en": "Unavailable",
        }

    if is_delisted:
        raw_pct = round((positive / total) * 100, 1) if total > 0 else 0.0
        b_score = round(calculate_bayesian_score(positive, total, c=c, m=m) * 100, 1) if total > 0 else 0.0
        b_tier = get_base_tier(positive / total) if total > 0 else "Unrated"
        return {
            "raw_percent": raw_pct,
            "bayesian_score": b_score,
            "base_tier": b_tier,
            "assigned_tier": None,
            "status": "delisted",
            "status_label_de": "Delistet",
            "status_label_en": "Delisted",
        }

    if not is_scanned:
        return {
            "raw_percent": 0.0,
            "bayesian_score": 0.0,
            "base_tier": "Unrated",
            "assigned_tier": None,
            "status": "unscanned",
            "status_label_de": "Noch nicht gescannt",
            "status_label_en": "Not scanned yet",
        }

    if total <= 0:
        return {
            "raw_percent": 0.0,
            "bayesian_score": 0.0,
            "base_tier": "Unrated",
            "assigned_tier": None,
            "status": "no_reviews",
            "status_label_de": "Keine Reviews",
            "status_label_en": "No reviews",
        }

    raw_percent = positive / total
    b_score = calculate_bayesian_score(positive, total, c=c, m=m)
    base_tier = get_base_tier(raw_percent)

    # 1. If the user hasn't selected this tier's collection to be created, mark unassigned
    if active_tiers is not None and base_tier not in active_tiers:
        return {
            "raw_percent": round(raw_percent * 100, 1),
            "bayesian_score": round(b_score * 100, 1),
            "base_tier": base_tier,
            "assigned_tier": None,
            "status": "unassigned",
            "status_label_de": "Nicht ausgewählt",
            "status_label_en": "Not selected",
        }

    # 2. Base tier is in active collections! Quality Gate check:
    # - Positive tiers scale with the confidence slider C to filter out niche echo chambers.
    # - Neutral / Negative tiers require standard Steam baselines (50 reviews, 500 for Overwhelmingly Negative)
    #   because low ratings do not represent quality that needs proving.
    if base_tier in POSITIVE_TIER_MULTIPLIERS:
        required_reviews = POSITIVE_TIER_MULTIPLIERS[base_tier] * c
    else:
        required_reviews = BASELINE_TIER_REVIEWS.get(base_tier, 50)

    if total < required_reviews:
        return {
            "raw_percent": round(raw_percent * 100, 1),
            "bayesian_score": round(b_score * 100, 1),
            "base_tier": base_tier,
            "assigned_tier": None,
            "status": "low_confidence",
            "status_label_de": "Zu wenige Reviews",
            "status_label_en": "Few reviews",
        }

    return {
        "raw_percent": round(raw_percent * 100, 1),
        "bayesian_score": round(b_score * 100, 1),
        "base_tier": base_tier,
        "assigned_tier": base_tier,
        "status": "assigned",
        "status_label_de": base_tier,
        "status_label_en": base_tier,
    }
