"""
test_controller.py
Unit tests for wave-release controller decision logic and fallback mechanisms.
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
    assert res_fail["released_workers"] <= 1  # Paced release
    assert "Sensor telemetry offline" in res_fail["reason"]
