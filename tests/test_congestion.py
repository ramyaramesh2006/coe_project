"""
test_congestion.py
Unit tests for congestion calculation and classification logic.
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


def test_congestion_classification_boundaries():
    """Validate 0-<50% LOW, 50-<75% MEDIUM, 75-<100% HIGH, >=100% CRITICAL."""
    assert classify_congestion(0.0) == "LOW"
    assert classify_congestion(49.9) == "LOW"
    assert classify_congestion(50.0) == "MEDIUM"
    assert classify_congestion(74.9) == "MEDIUM"
    assert classify_congestion(75.0) == "HIGH"
    assert classify_congestion(99.9) == "HIGH"
    assert classify_congestion(100.0) == "CRITICAL"
    assert classify_congestion(150.0) == "CRITICAL"


def test_congestion_classification_custom_thresholds():
    """Validate configurable thresholds."""
    custom_thresh = {"LOW_MAX": 40.0, "MEDIUM_MAX": 70.0, "HIGH_MAX": 90.0}
    assert classify_congestion(45.0, thresholds=custom_thresh) == "MEDIUM"
    assert classify_congestion(72.0, thresholds=custom_thresh) == "HIGH"
    assert classify_congestion(95.0, thresholds=custom_thresh) == "CRITICAL"
