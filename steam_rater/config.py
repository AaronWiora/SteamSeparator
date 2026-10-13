"""
Configuration constants and defaults for Steam Rating Collections Manager.
"""
from pathlib import Path

# Mathematical defaults
DEFAULT_C = 700.0      # Bayesian damping / confidence weight (Level 5 Balanced default: ~875 OP / ~2.5k VP)
DEFAULT_M = 0.50       # Neutral prior mean (50/50 without evidence)

# 10 Stepped Filter Levels for Unified Quality Gate
FILTER_LEVELS = [
    {"level": 1, "c": 150.0, "op_reviews": 180, "vp_reviews": 530, "op_hint": "180", "vp_hint": "530", "label_en": "Very Lenient", "label_de": "Sehr locker"},
    {"level": 2, "c": 250.0, "op_reviews": 300, "vp_reviews": 890, "op_hint": "300", "vp_hint": "890", "label_en": "Lenient", "label_de": "Locker"},
    {"level": 3, "c": 350.0, "op_reviews": 440, "vp_reviews": 1250, "op_hint": "440", "vp_hint": "1.2k", "label_en": "Light", "label_de": "Leicht"},
    {"level": 4, "c": 500.0, "op_reviews": 625, "vp_reviews": 1800, "op_hint": "625", "vp_hint": "1.8k", "label_en": "Moderate", "label_de": "Moderat"},
    {"level": 5, "c": 700.0, "op_reviews": 875, "vp_reviews": 2500, "op_hint": "875", "vp_hint": "2.5k", "label_en": "Balanced", "label_de": "Ausgewogen"},
    {"level": 6, "c": 950.0, "op_reviews": 1200, "vp_reviews": 3400, "op_hint": "1.2k", "vp_hint": "3.4k", "label_en": "Firm", "label_de": "Bestimmt"},
    {"level": 7, "c": 1300.0, "op_reviews": 1600, "vp_reviews": 4600, "op_hint": "1.6k", "vp_hint": "4.6k", "label_en": "Strict", "label_de": "Streng"},
    {"level": 8, "c": 1800.0, "op_reviews": 2250, "vp_reviews": 6400, "op_hint": "2.2k", "vp_hint": "6.4k", "label_en": "Very Strict", "label_de": "Sehr streng"},
    {"level": 9, "c": 2500.0, "op_reviews": 3100, "vp_reviews": 8900, "op_hint": "3.1k", "vp_hint": "8.9k", "label_en": "High Confidence", "label_de": "Hohe Relevanz"},
    {"level": 10, "c": 3500.0, "op_reviews": 4400, "vp_reviews": 12500, "op_hint": "4.4k", "vp_hint": "12.5k", "label_en": "Bestsellers Only", "label_de": "Nur Bestseller"},
]

# Tier Quality Multipliers for Positive Tiers (scaled by slider C factor)
POSITIVE_TIER_MULTIPLIERS = {
    "Overwhelmingly Positive": 1.25,
    "Very Positive": 3.57,
    "Mostly Positive": 5.7,
}

# Baseline Steam review requirements for Neutral / Negative tiers
BASELINE_TIER_REVIEWS = {
    "Mixed": 50,
    "Mostly Negative": 50,
    "Overwhelmingly Negative": 500,
}


# Rating Tier Thresholds
TIERS = {
    "Overwhelmingly Positive": {
        "raw_min": 0.95,
        "bayesian_min": 0.88,
        "badge_color": "#66c0f4",
        "icon": "",
        "default_active": True,
    },
    "Very Positive": {
        "raw_min": 0.80,
        "bayesian_min": 0.75,
        "badge_color": "#a4d007",
        "icon": "",
        "default_active": True,
    },
    "Mostly Positive": {
        "raw_min": 0.70,
        "bayesian_min": 0.65,
        "badge_color": "#8bc34a",
        "icon": "",
        "default_active": False,
    },
    "Mixed": {
        "raw_min": 0.40,
        "bayesian_min": 0.40,
        "badge_color": "#b29400",
        "icon": "",
        "default_active": False,
    },
    "Mostly Negative": {
        "raw_min": 0.20,
        "bayesian_min": 0.20,
        "badge_color": "#cd5c5c",
        "icon": "",
        "default_active": False,
    },
    "Overwhelmingly Negative": {
        "raw_min": 0.00,
        "bayesian_min": 0.00,
        "badge_color": "#d9534f",
        "icon": "",
        "default_active": False,
    },
}

# Local DB path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE_ROOT / "ratings.db"
