"""Persistent player profiles: named saves with cumulative score, per-level
best results, a 24h-refilling lives economy, a premium currency ("Stardust
Shards"), and owned/equipped cosmetics. Replaces the old flat scores.json
with one file (profiles.json) holding every named profile."""

import json
import os
from datetime import datetime, timedelta, timezone

PROFILES_PATH = os.path.join(os.path.dirname(__file__), "profiles.json")
LEGACY_SCORES_PATH = os.path.join(os.path.dirname(__file__), "scores.json")

FREE_LIVES = 3
LIVES_REFILL = timedelta(hours=24)
STARTING_CURRENCY = 10_000          # generous test-environment default, per design brief
LIFE_REFILL_COST = 150              # Shards to instantly refill lives outside the 24h window

DEFAULT_SKIN = "default_skin"
DEFAULT_DEATH_FX = "default_death"

COSMETICS = {
    "default_skin": {"category": "skin", "name": "Standard Issue", "price_shards": 0, "color": None},
    "crimson_skin": {"category": "skin", "name": "Crimson Racer", "price_shards": 800, "color": (235, 90, 90)},
    "gold_skin": {"category": "skin", "name": "Gold Rush", "price_shards": 1500, "color": (240, 200, 80)},
    "void_skin": {"category": "skin", "name": "Void Walker", "price_shards": 1500, "color": (150, 90, 235)},
    "default_death": {"category": "death_fx", "name": "Standard Burst", "price_shards": 0, "color": None},
    "nova_death": {"category": "death_fx", "name": "Nova Burst", "price_shards": 600, "color": (255, 170, 60)},
    "frost_death": {"category": "death_fx", "name": "Frost Shatter", "price_shards": 600, "color": (140, 220, 255)},
    # Real-money entries are architecturally identical to Shard purchases -
    # `price_usd` is what a payment-SDK integration would key off later.
    # No payment processing happens here: `buy_cosmetic(..., pay_with="usd")`
    # just simulates success. See README / GDD for the integration note.
    "nebula_reskin": {"category": "theme", "name": "Nebula Reskin (preview)", "price_shards": None, "price_usd": 4.99, "color": None},
}


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat()


def _parse(iso_str):
    return datetime.fromisoformat(iso_str)


def load_profiles():
    if not os.path.exists(PROFILES_PATH):
        return {"profiles": {}, "last_active": None}
    try:
        with open(PROFILES_PATH, "r") as f:
            data = json.load(f)
            data.setdefault("profiles", {})
            data.setdefault("last_active", None)
            return data
    except (json.JSONDecodeError, OSError):
        return {"profiles": {}, "last_active": None}


def save_profiles(data):
    with open(PROFILES_PATH, "w") as f:
        json.dump(data, f, indent=2)


def list_profile_names(data):
    return sorted(data["profiles"].keys())


def create_profile(data, name):
    name = name.strip()
    profile = {
        "name": name,
        "created_at": _iso(_now()),
        "cumulative_score": 0,
        "levels": {},
        "last_level_key": None,
        "seen_features": [],
        "tutorial_completed": False,
        "currency": STARTING_CURRENCY,
        "lives": FREE_LIVES,
        "lives_reset_at": _iso(_now() + LIVES_REFILL),
        "cosmetics_owned": [DEFAULT_SKIN, DEFAULT_DEATH_FX],
        "cosmetics_equipped": {"skin": DEFAULT_SKIN, "death_fx": DEFAULT_DEATH_FX},
    }
    data["profiles"][name] = profile
    data["last_active"] = name
    save_profiles(data)
    return profile


def get_profile(data, name):
    return data["profiles"].get(name)


def migrate_legacy_scores_if_needed(data):
    """One-time import of the old flat scores.json (from before named
    profiles existed) into a "Player" profile, so real prior progress
    isn't silently lost. No-op if any profile already exists."""
    if data["profiles"] or not os.path.exists(LEGACY_SCORES_PATH):
        return None
    try:
        with open(LEGACY_SCORES_PATH, "r") as f:
            legacy = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    profile = create_profile(data, "Player")
    for level_key, entry in legacy.items():
        profile["levels"][level_key] = {
            "best_pct": entry.get("best_pct", 0.0),
            "completed": entry.get("completed", False),
            "attempts": entry.get("attempts", 0),
            "best_score": 0,
        }
    save_profiles(data)
    return profile


def delete_profile(data, name):
    data["profiles"].pop(name, None)
    if data.get("last_active") == name:
        data["last_active"] = None
    save_profiles(data)
    save_profiles(data)


# -- lives -------------------------------------------------------------------
def refresh_lives(profile):
    """Refills lives to full if the 24h window has elapsed. Returns True if
    a refill just happened."""
    reset_at = _parse(profile["lives_reset_at"])
    if _now() >= reset_at:
        profile["lives"] = FREE_LIVES
        profile["lives_reset_at"] = _iso(_now() + LIVES_REFILL)
        return True
    return False


def consume_life(profile):
    """Spends one free life. Returns True if a life was available and spent."""
    refresh_lives(profile)
    if profile["lives"] > 0:
        profile["lives"] -= 1
        return True
    return False


def time_until_life_refill(profile):
    reset_at = _parse(profile["lives_reset_at"])
    remaining = reset_at - _now()
    return max(timedelta(0), remaining)


# -- currency ------------------------------------------------------------------
def add_currency(profile, amount):
    profile["currency"] += amount


def spend_currency(profile, amount):
    if profile["currency"] >= amount:
        profile["currency"] -= amount
        return True
    return False


def refill_lives_with_currency(profile):
    if spend_currency(profile, LIFE_REFILL_COST):
        profile["lives"] = FREE_LIVES
        profile["lives_reset_at"] = _iso(_now() + LIVES_REFILL)
        return True
    return False


def reset_currency_debug(profile):
    """Test-environment helper: top back up to the starting balance."""
    profile["currency"] = STARTING_CURRENCY


# -- cosmetics -----------------------------------------------------------------
def buy_cosmetic(profile, cosmetic_id, pay_with="shards"):
    item = COSMETICS.get(cosmetic_id)
    if item is None or cosmetic_id in profile["cosmetics_owned"]:
        return False
    if pay_with == "shards":
        price = item.get("price_shards")
        if price is None or not spend_currency(profile, price):
            return False
    elif pay_with == "usd":
        if item.get("price_usd") is None:
            return False
        # STUB: no real payment processing. A production build would call
        # out to a payment SDK here and only continue on a verified
        # success callback; this test build simulates an instant success.
    else:
        return False
    profile["cosmetics_owned"].append(cosmetic_id)
    return True


def equip_cosmetic(profile, cosmetic_id):
    item = COSMETICS.get(cosmetic_id)
    if item is None or cosmetic_id not in profile["cosmetics_owned"]:
        return False
    profile["cosmetics_equipped"][item["category"]] = cosmetic_id
    return True


# -- levels / scoring ------------------------------------------------------------
def mark_feature_seen(profile, feature_key):
    """Returns True the first time this profile encounters `feature_key`."""
    if feature_key in profile["seen_features"]:
        return False
    profile["seen_features"].append(feature_key)
    return True


def record_attempt(profile, level_key, progress, completed, run_score):
    entry = profile["levels"].setdefault(level_key, {"best_pct": 0.0, "completed": False, "attempts": 0, "best_score": 0})
    entry["attempts"] += 1
    pct = round(progress * 100, 1)
    is_new_best_pct = pct > entry["best_pct"]
    if is_new_best_pct:
        entry["best_pct"] = pct
    if run_score > entry["best_score"]:
        entry["best_score"] = run_score
    if completed:
        entry["completed"] = True
    profile["cumulative_score"] += run_score
    return is_new_best_pct
