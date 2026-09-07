"""
test_controller.py
Unit tests for wave-release controller decision logic, boundary conditions, and fallback mechanisms.
"""

import pytest
from src.controller import wave_release_controller


def test_controller_allow_decision():
    """Verify ALLOW decision when congestion is below safe threshold."""
    # LOW congestion (25%)
    res_low = wave_release_controller(
        congestion_percentage=25.0,
        requested_workers=1,
        safe_threshold=75.0
    )
    assert res_low["decision"] == "ALLOW"
    assert res_low["released_workers"] == 1
    assert res_low["delayed_workers"] == 0
    assert res_low["system_status"] == "NORMAL"

    # MEDIUM congestion (60%) below 75% threshold
    res_med = wave_release_controller(
        congestion_percentage=60.0,
        requested_workers=1,
        safe_threshold=75.0
    )
    assert res_med["decision"] == "ALLOW"
    assert res_med["released_workers"] == 1


def test_controller_delay_decision():
    """Verify DELAY decision when congestion reaches or exceeds safe threshold."""
    res_high = wave_release_controller(
        congestion_percentage=80.0,
        requested_workers=1,
        safe_threshold=75.0
    )
    assert res_high["decision"] == "DELAY"
    assert res_high["released_workers"] == 0
    assert res_high["delayed_workers"] == 1
    assert "Holding release" in res_high["reason"]


def test_controller_critical_congestion_block():
    """Verify BLOCK decision when congestion is CRITICAL (>= 100%)."""
    res_crit = wave_release_controller(
        congestion_percentage=125.0,
        requested_workers=1,
        safe_threshold=75.0
    )
    assert res_crit["decision"] == "BLOCK"
    assert res_crit["released_workers"] == 0
    assert res_crit["delayed_workers"] == 1
    assert res_crit["congestion_level"] == "CRITICAL"


def test_controller_exact_threshold_boundary():
    """Boundary Test: Exactly at safe threshold (75.0%) -> DELAY."""
    res = wave_release_controller(
        congestion_percentage=75.0,
        requested_workers=1,
        safe_threshold=75.0
    )
    assert res["decision"] == "DELAY", "At exact threshold, release must be delayed"
    assert res["released_workers"] == 0
    assert res["delayed_workers"] == 1


def test_controller_just_below_and_above_boundary():
    """Boundary Test: 74.9% -> ALLOW, 75.1% -> DELAY."""
    res_below = wave_release_controller(congestion_percentage=74.9, safe_threshold=75.0)
    assert res_below["decision"] == "ALLOW"
    assert res_below["released_workers"] == 1

    res_above = wave_release_controller(congestion_percentage=75.1, safe_threshold=75.0)
    assert res_above["decision"] == "DELAY"
    assert res_above["released_workers"] == 0


def test_controller_exact_critical_boundary():
    """Boundary Test: Exactly at 100.0% -> BLOCK."""
    res_crit = wave_release_controller(congestion_percentage=100.0, safe_threshold=75.0)
    assert res_crit["decision"] == "BLOCK"
    assert res_crit["congestion_level"] == "CRITICAL"


def test_controller_sensor_failure_fallback():
    """Verify graceful transition to MANUAL FALLBACK mode when telemetry fails."""
    res_fail = wave_release_controller(
        requested_workers=2,
        safe_threshold=75.0,
        sensor_available=False,
        fallback_congestion=60.0
    )
    assert res_fail["system_status"] == "SENSOR FAILURE"
    assert res_fail["mode"] == "MANUAL FALLBACK"
    assert res_fail["released_workers"] <= 1  # Conservative paced release
    assert "Sensor telemetry offline" in res_fail["reason"]


def test_controller_multi_worker_request():
    """Verify batch request handling (e.g. 4 workers requested)."""
    # When clear (20%), all 4 should be released
    res_allow = wave_release_controller(congestion_percentage=20.0, requested_workers=4, safe_threshold=75.0)
    assert res_allow["released_workers"] == 4
    assert res_allow["delayed_workers"] == 0

    # When high (85%), all 4 should be delayed
    res_delay = wave_release_controller(congestion_percentage=85.0, requested_workers=4, safe_threshold=75.0)
    assert res_delay["released_workers"] == 0
    assert res_delay["delayed_workers"] == 4
