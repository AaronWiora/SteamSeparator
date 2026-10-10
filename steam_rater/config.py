"""
Configuration constants and defaults for Steam Rating Collections Manager.
"""
from pathlib import Path

# Mathematical defaults
DEFAULT_C = 350.0      # Bayesian damping / confidence weight (balanced ~1,900 reviews baseline)
DEFAULT_M = 0.50       # Neutral prior mean (50/50 without evidence)

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
