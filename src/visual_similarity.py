"""
visual_similarity.py
Domain-specific modelling of visually similar automotive components.

Key insight from Review 1 feedback:
    "Explicitly model the impact of 'visually similar components' (e.g., increased pick
     verification duration, error-checking delays, or mispick returns) on aisle dwell time."

This module provides:
- A catalogue of automotive part categories with similarity risk scores.
- A pick-latency model that injects extra verification time based on visual-similarity risk.
- A mispick model that simulates returns causing re-entry into the source aisle.
- Functions consumed by data_generator.py and simulation.py to enrich every pick event.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# 1. Automotive Part Catalogue
#    Each category carries:
#      similarity_risk   : 0.0 (clearly distinct) → 1.0 (near-identical appearance)
#      avg_pick_time_sec : baseline pick time WITHOUT extra verification
#      verification_extra_sec : mean extra seconds added per pick for visual check
#      mispick_probability    : probability worker grabs wrong SKU on first attempt
# ──────────────────────────────────────────────────────────────────────────────
PART_CATALOGUE: Dict[str, Dict] = {
    "brake_pads": {
        "category": "Braking",
        "similarity_risk": 0.90,        # Very high – dozens of SKUs look identical
        "avg_pick_time_sec": 38.0,
        "verification_extra_sec": 18.0, # Barcode scan + tactile check
        "mispick_probability": 0.12,    # 12% first-attempt error rate
    },
    "oil_filters": {
        "category": "Filtration",
        "similarity_risk": 0.85,
        "avg_pick_time_sec": 35.0,
        "verification_extra_sec": 15.0,
        "mispick_probability": 0.10,
    },
    "spark_plugs": {
        "category": "Ignition",
        "similarity_risk": 0.80,
        "avg_pick_time_sec": 30.0,
        "verification_extra_sec": 12.0,
        "mispick_probability": 0.09,
    },
    "air_filters": {
        "category": "Filtration",
        "similarity_risk": 0.75,
        "avg_pick_time_sec": 33.0,
        "verification_extra_sec": 10.0,
        "mispick_probability": 0.07,
    },
    "engine_gaskets": {
        "category": "Engine",
        "similarity_risk": 0.88,
        "avg_pick_time_sec": 45.0,
        "verification_extra_sec": 20.0,
        "mispick_probability": 0.11,
    },
    "fuel_injectors": {
        "category": "Fuel System",
        "similarity_risk": 0.82,
        "avg_pick_time_sec": 42.0,
        "verification_extra_sec": 16.0,
        "mispick_probability": 0.09,
    },
    "serpentine_belts": {
        "category": "Drive",
        "similarity_risk": 0.70,
        "avg_pick_time_sec": 36.0,
        "verification_extra_sec": 8.0,
        "mispick_probability": 0.06,
    },
    "wheel_bearings": {
        "category": "Suspension",
        "similarity_risk": 0.78,
        "avg_pick_time_sec": 50.0,
        "verification_extra_sec": 14.0,
        "mispick_probability": 0.08,
    },
    "alternators": {
        "category": "Electrical",
        "similarity_risk": 0.60,
        "avg_pick_time_sec": 55.0,
        "verification_extra_sec": 6.0,
        "mispick_probability": 0.04,
    },
    "starter_motors": {
        "category": "Electrical",
        "similarity_risk": 0.65,
        "avg_pick_time_sec": 52.0,
        "verification_extra_sec": 7.0,
        "mispick_probability": 0.05,
    },
    "water_pumps": {
        "category": "Cooling",
        "similarity_risk": 0.55,
        "avg_pick_time_sec": 48.0,
        "verification_extra_sec": 5.0,
        "mispick_probability": 0.03,
    },
    "radiator_hoses": {
        "category": "Cooling",
        "similarity_risk": 0.50,
        "avg_pick_time_sec": 28.0,
        "verification_extra_sec": 4.0,
        "mispick_probability": 0.03,
    },
}

# Map aisles to their dominant part category (reflects automotive zone layout)
AISLE_PART_MAP: Dict[str, str] = {
    "A01": "serpentine_belts",
    "A02": "oil_filters",
    "A03": "brake_pads",       # Hotspot – highest similarity risk
    "A04": "air_filters",
    "A05": "engine_gaskets",
    "A06": "fuel_injectors",
    "A07": "spark_plugs",      # Hotspot – high similarity risk
    "A08": "wheel_bearings",
    "A09": "alternators",
    "A10": "starter_motors",
    "A11": "water_pumps",
    "A12": "radiator_hoses",
}

# Return-trip overhead when a mispick is detected and worker must re-pick
MISPICK_RETURN_TIME_SEC: float = 45.0   # Walk back, locate correct item, re-scan


# ──────────────────────────────────────────────────────────────────────────────
# 2. Pick-Time Model
# ──────────────────────────────────────────────────────────────────────────────

def compute_adjusted_pick_time(
    aisle_id: str,
    rng: Optional[np.random.Generator] = None,
    aisle_part_map: Optional[Dict[str, str]] = None,
    include_mispick_returns: bool = True,
) -> Tuple[float, Dict]:
    """
    Returns the total dwell time for one pick event at `aisle_id`, accounting for:
      1. Base pick time (Gaussian around part average)
      2. Visual verification overhead (proportional to similarity_risk)
      3. Mispick return penalty (probabilistic)

    Parameters
    ----------
    aisle_id              : Aisle identifier (e.g., "A03")
    rng                   : Optional numpy random generator for reproducibility
    aisle_part_map        : Override mapping of aisle → part category
    include_mispick_returns : Whether to simulate mispick return delays

    Returns
    -------
    (total_pick_time_sec, detail_dict)
        detail_dict keys: base_time, verification_time, mispick_occurred,
                          return_penalty, total_time, similarity_risk, part_category
    """
    if rng is None:
        rng = np.random.default_rng()
    if aisle_part_map is None:
        aisle_part_map = AISLE_PART_MAP

    part_key = aisle_part_map.get(aisle_id, "oil_filters")
    part = PART_CATALOGUE[part_key]

    # 1. Base pick time: N(avg, 0.15 * avg) – realistic warehouse variability
    base_std = 0.15 * part["avg_pick_time_sec"]
    base_time = float(rng.normal(part["avg_pick_time_sec"], base_std))
    base_time = max(15.0, base_time)   # Minimum 15-second physical pick

    # 2. Verification overhead: scales with similarity_risk
    verif_std = 0.20 * part["verification_extra_sec"]
    verif_time = float(rng.normal(part["verification_extra_sec"], verif_std))
    verif_time = max(0.0, verif_time) * part["similarity_risk"]

    # 3. Mispick return penalty
    mispick_occurred = False
    return_penalty = 0.0
    if include_mispick_returns:
        if rng.random() < part["mispick_probability"]:
            mispick_occurred = True
            return_penalty = MISPICK_RETURN_TIME_SEC + float(rng.uniform(0, 20))

    total_time = base_time + verif_time + return_penalty

    return total_time, {
        "base_time": round(base_time, 2),
        "verification_time": round(verif_time, 2),
        "mispick_occurred": mispick_occurred,
        "return_penalty": round(return_penalty, 2),
        "total_time": round(total_time, 2),
        "similarity_risk": part["similarity_risk"],
        "part_category": part["category"],
        "part_key": part_key,
    }


def get_zone_similarity_risk(aisle_id: str, aisle_part_map: Optional[Dict[str, str]] = None) -> float:
    """Returns the visual similarity risk score (0.0–1.0) for a given aisle."""
    if aisle_part_map is None:
        aisle_part_map = AISLE_PART_MAP
    part_key = aisle_part_map.get(aisle_id, "oil_filters")
    return PART_CATALOGUE[part_key]["similarity_risk"]


def compute_expected_dwell_time(aisle_id: str, aisle_part_map: Optional[Dict[str, str]] = None) -> float:
    """
    Returns the expected (mean) total dwell time in seconds for `aisle_id`,
    accounting for base pick time, verification overhead, and expected mispick penalty.
    """
    if aisle_part_map is None:
        aisle_part_map = AISLE_PART_MAP
    part_key = aisle_part_map.get(aisle_id, "oil_filters")
    part = PART_CATALOGUE[part_key]

    expected_base = part["avg_pick_time_sec"]
    expected_verif = part["verification_extra_sec"] * part["similarity_risk"]
    expected_return = part["mispick_probability"] * MISPICK_RETURN_TIME_SEC

    return round(expected_base + expected_verif + expected_return, 2)
