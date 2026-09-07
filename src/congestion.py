"""
congestion.py
Aisle Congestion Calculation and Classification Engine.
Handles numerical edge cases (zero capacity, negative inputs, missing data) safely.
"""

from typing import Dict, Union, Optional
import numpy as np

# Standard Congestion Level Thresholds
DEFAULT_THRESHOLDS = {
    "LOW_MAX": 50.0,       # 0% to <50% = LOW
    "MEDIUM_MAX": 75.0,    # 50% to <75% = MEDIUM
    "HIGH_MAX": 100.0,     # 75% to <100% = HIGH
                           # >=100% = CRITICAL
}


def calculate_congestion(
    current_workers: Union[int, float, None],
    aisle_capacity: Union[int, float, None],
    sensor_available: bool = True,
    fallback_congestion: float = 60.0
) -> float:
    """
    Calculates the aisle congestion percentage.
    Formula: (current_workers / aisle_capacity) * 100.0

    Handles edge cases:
    - Zero capacity -> returns 100.0% (fully blocked/critical) to avoid ZeroDivisionError.
    - Negative values -> clamped to 0.0.
    - Missing / NaN values -> handled safely.
    - Sensor failure -> returns safe fallback estimate.
    """
    if not sensor_available:
        return float(fallback_congestion)

    # Check for missing/None values
    if current_workers is None or np.isnan(current_workers):
        current_workers = 0.0
    if aisle_capacity is None or np.isnan(aisle_capacity):
        return float(fallback_congestion)

    # Convert to float and clamp negatives
    workers = max(0.0, float(current_workers))
    capacity = float(aisle_capacity)

    # Edge case: zero or negative capacity
    if capacity <= 0.0:
        return 100.0 if workers > 0 else 0.0

    congestion_pct = (workers / capacity) * 100.0
    return float(round(congestion_pct, 2))


def classify_congestion(
    congestion_percentage: Union[int, float, None],
    thresholds: Optional[Dict[str, float]] = None
) -> str:
    """
    Classifies the congestion percentage into standard operational levels:
    - LOW:      0% to <50%
    - MEDIUM:   50% to <75%
    - HIGH:     75% to <100%
    - CRITICAL: >= 100%

    Thresholds can be customized via the 'thresholds' dictionary.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    if congestion_percentage is None or np.isnan(congestion_percentage):
        return "UNKNOWN"

    val = float(congestion_percentage)

    if val < thresholds.get("LOW_MAX", 50.0):
        return "LOW"
    elif val < thresholds.get("MEDIUM_MAX", 75.0):
        return "MEDIUM"
    elif val < thresholds.get("HIGH_MAX", 100.0):
        return "HIGH"
    else:
        return "CRITICAL"
