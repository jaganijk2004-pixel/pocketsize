"""
product_service.py
------------------
Product/service data access layer.

This module is the ONLY layer that knows about the data source.
All three planner prompt builders call this module to get filtered catalog data.

To integrate real APIs in the future, replace the body of each function below
with API calls. The function signatures, return types, and callers do not change.
"""

import json
import os
from typing import Optional

# ── Data file paths ────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HOME_DATA_PATH = os.path.join(_BASE_DIR, "data", "home_products.json")
_PARTY_DATA_PATH = os.path.join(_BASE_DIR, "data", "party_services.json")
_JEWELRY_DATA_PATH = os.path.join(_BASE_DIR, "data", "jewelry_products.json")

# ── Lazy-loaded caches (loaded once on first access) ───────────────────────
_home_catalog_cache: Optional[dict] = None
_party_catalog_cache: Optional[dict] = None
_jewelry_catalog_cache: Optional[list] = None


def _load_home_catalog() -> dict:
    global _home_catalog_cache
    if _home_catalog_cache is None:
        with open(_HOME_DATA_PATH, "r", encoding="utf-8") as f:
            _home_catalog_cache = json.load(f)
    return _home_catalog_cache


def _load_party_catalog() -> dict:
    global _party_catalog_cache
    if _party_catalog_cache is None:
        with open(_PARTY_DATA_PATH, "r", encoding="utf-8") as f:
            _party_catalog_cache = json.load(f)
    return _party_catalog_cache


def _load_jewelry_catalog() -> list:
    global _jewelry_catalog_cache
    if _jewelry_catalog_cache is None:
        with open(_JEWELRY_DATA_PATH, "r", encoding="utf-8") as f:
            _jewelry_catalog_cache = json.load(f)
    return _jewelry_catalog_cache


# ── Public API ─────────────────────────────────────────────────────────────

def get_home_catalog(room_types: list[str]) -> dict:
    """
    Return the home products catalog filtered to the requested room types.

    Parameters
    ----------
    room_types : list[str]
        List of room type keys as stored in home_products.json
        e.g. ["living_room", "bedroom", "kitchen"]

    Returns
    -------
    dict
        Keys are the requested room type strings; values are lists of product dicts.
        Example: {"living_room": [...], "bedroom": [...]}
    """
    full_catalog = _load_home_catalog()

    # Normalise keys: lowercase, replace spaces/hyphens with underscores
    normalised_rooms = [r.lower().replace(" ", "_").replace("-", "_") for r in room_types]

    filtered: dict = {}
    for room in normalised_rooms:
        if room in full_catalog:
            filtered[room] = full_catalog[room]

    # Fallback: if no rooms matched, return the entire catalog
    if not filtered:
        filtered = full_catalog

    return filtered


def get_party_catalog(event_type: str) -> dict:
    """
    Return the party services catalog filtered by event type compatibility.

    Parameters
    ----------
    event_type : str
        One of: Birthday, Wedding, Corporate, Anniversary, Casual Gathering

    Returns
    -------
    dict
        Keys are category names (catering, decoration, entertainment, venue).
        Each value is a list of service dicts compatible with the given event type.
    """
    full_catalog = _load_party_catalog()

    filtered: dict = {}

    for category, items in full_catalog.items():
        compatible = []
        for item in items:
            # Items with an event_types list: filter by compatibility
            if "event_types" in item:
                if event_type in item["event_types"]:
                    compatible.append(item)
            else:
                # Items without event_types filter are universally compatible
                compatible.append(item)

        # Fallback: if fewer than 2 items matched, include all items in the category
        if len(compatible) < 2:
            compatible = items

        if compatible:
            filtered[category] = compatible

    return filtered


def get_jewelry_catalog(occasion: str, style: str, metal: str) -> list:
    """
    Return jewelry items filtered by occasion, style, and metal preference.

    At least ONE of the three criteria must match for an item to be included.
    If fewer than 3 items match, the full unfiltered catalog is returned.

    Parameters
    ----------
    occasion : str
        e.g. "Wedding", "Festival", "Birthday", "Casual", "Office", "Party"
    style : str
        e.g. "Traditional", "Modern", "Minimalist", "Statement", "Bohemian"
    metal : str
        e.g. "Gold", "Silver", "Rose Gold", "Platinum", "No Preference"

    Returns
    -------
    list
        List of jewelry product dicts matching the criteria.
    """
    full_catalog = _load_jewelry_catalog()

    # "No Preference" for metal means all metals are acceptable
    metal_filter_active = metal.lower() not in ("no preference", "no_preference", "")

    matched = []
    for item in full_catalog:
        occasion_match = occasion in item.get("occasions", [])
        style_match = style in item.get("styles", [])
        metal_match = (not metal_filter_active) or (item.get("metal", "") == metal)

        if occasion_match or style_match or metal_match:
            matched.append(item)

    # Fallback: return full catalog if fewer than 3 items matched
    if len(matched) < 3:
        return full_catalog

    return matched
