"""
test_congestion.py
Unit tests for congestion calculation, classification boundaries, and edge-case resilience.
"""

import pytest
import numpy as np
from src.congestion import calculate_congestion, classify_congestion, DEFAULT_THRESHOLDS


def test_normal_congestion_calculation():
    """Verify formula: (current_workers / aisle_capacity) * 100"""
    res = calculate_congestion(current_workers=2, aisle_capacity=4)
    assert res == 50.0

    res2 = calculate_congestion(current_workers=3, aisle_capacity=3)
    assert res2 == 100.0


def test_over_capacity_exceeds_100_percent():
    """Verify that congestion percentage legitimately exceeds 100% when workers > capacity."""
    res_over = calculate_congestion(current_workers=5, aisle_capacity=4)
    assert res_over == 125.0
    assert res_over > 100.0

    res_extreme = calculate_congestion(current_workers=7, aisle_capacity=3)
    assert res_extreme == 233.33


def test_zero_and_negative_capacity_handling():
    """Ensure zero or negative capacity does not cause ZeroDivisionError and handles safely."""
    # Capacity = 0 with workers > 0 should return 100.0 (fully blocked)
    res = calculate_congestion(current_workers=2, aisle_capacity=0)
    assert res == 100.0

    # Capacity = 0 with 0 workers
    res_zero = calculate_congestion(current_workers=0, aisle_capacity=0)
    assert res_zero == 0.0

    # Negative capacity
    res_neg = calculate_congestion(current_workers=1, aisle_capacity=-2)
    assert res_neg == 100.0


def test_missing_and_negative_worker_values():
    """Ensure None, NaN, and negative worker inputs are safely clamped."""
    # None workers -> treated as 0
    res_none = calculate_congestion(current_workers=None, aisle_capacity=4)
    assert res_none == 0.0

    # Negative workers -> clamped to 0
    res_neg_workers = calculate_congestion(current_workers=-5, aisle_capacity=4)
    assert res_neg_workers == 0.0

    # NaN workers
    res_nan = calculate_congestion(current_workers=np.nan, aisle_capacity=4)
    assert res_nan == 0.0


def test_sensor_blackout_returns_fallback():
    """Ensure that sensor failure flag returns fallback congestion estimate."""
    res = calculate_congestion(current_workers=2, aisle_capacity=4, sensor_available=False, fallback_congestion=65.0)
    assert res == 65.0


def test_congestion_classification_boundaries():
    """Validate 0-<50% LOW, 50-<75% MEDIUM, 75-<100% HIGH, >=100% CRITICAL."""
    assert classify_congestion(0.0) == "LOW"
    assert classify_congestion(49.99) == "LOW"
    assert classify_congestion(50.0) == "MEDIUM"
    assert classify_congestion(74.99) == "MEDIUM"
    assert classify_congestion(75.0) == "HIGH"
    assert classify_congestion(99.99) == "HIGH"
    assert classify_congestion(100.0) == "CRITICAL"
    assert classify_congestion(150.0) == "CRITICAL"


def test_congestion_classification_custom_thresholds():
    """Validate configurable classification thresholds."""
    custom_thresh = {"LOW_MAX": 40.0, "MEDIUM_MAX": 70.0, "HIGH_MAX": 90.0}
    assert classify_congestion(39.9, thresholds=custom_thresh) == "LOW"
    assert classify_congestion(45.0, thresholds=custom_thresh) == "MEDIUM"
    assert classify_congestion(72.0, thresholds=custom_thresh) == "HIGH"
    assert classify_congestion(95.0, thresholds=custom_thresh) == "CRITICAL"


def test_congestion_classification_invalid_inputs():
    """Ensure None and NaN classifications return UNKNOWN without crashing."""
    assert classify_congestion(None) == "UNKNOWN"
    assert classify_congestion(np.nan) == "UNKNOWN"
