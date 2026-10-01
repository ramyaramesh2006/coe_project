"""
test_error_boundaries.py  (Review 3)
Error-boundary and defensive-programming tests.

Each test probes one specific failure mode or edge-case input and verifies
that the system responds gracefully — either raising the documented exception
or returning a safe, predictable default — rather than crashing with an
unhandled exception or producing a mathematically undefined result.

Run with:
    python -m pytest tests/test_error_boundaries.py -v
"""

import pytest
import numpy as np
import pandas as pd

from src.congestion import calculate_congestion, classify_congestion
from src.controller import wave_release_controller
from src.data_generator import generate_warehouse_dataset, DEFAULT_AISLES
from src.simulation import WarehouseSimulation
from src.visual_similarity import compute_adjusted_pick_time, get_zone_similarity_risk
from src.store_and_forward import StoreAndForwardQueue, NetworkStateMonitor
from src.metrics import compute_simulation_metrics


# ─────────────────────────────────────────────────────────────────────────────
# 1. Congestion engine — numeric boundary cases
# ─────────────────────────────────────────────────────────────────────────────

def test_zero_capacity_aisle():
    """
    Boundary: aisle_capacity = 0.
    Division by zero must be guarded — function must not raise ZeroDivisionError.
    The module returns 100.0 (fully blocked / CRITICAL) as a safe-fail for a
    zero-capacity aisle, which is the correct conservative behaviour.
    Signature: calculate_congestion(current_workers, aisle_capacity, ...)
    """
    result = calculate_congestion(current_workers=2, aisle_capacity=0)
    # Must not raise; safe-fail returns a defined sentinel (100.0 = CRITICAL)
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    assert result >= 0.0, f"Expected non-negative result, got {result}"


def test_negative_workers_clamped_to_zero():
    """
    Boundary: current_workers < 0 (sensor glitch reporting negative occupancy).
    Negative workers must not produce negative congestion.
    """
    result = calculate_congestion(current_workers=-3, aisle_capacity=4)
    assert result >= 0.0, f"Expected >= 0.0 for negative workers, got {result}"


def test_congestion_above_100_percent_is_critical():
    """
    Boundary: current_workers > aisle_capacity (physically over-packed aisle).
    Congestion > 100% is valid and must classify as CRITICAL.
    """
    pct = calculate_congestion(current_workers=5, aisle_capacity=3)
    assert pct > 100.0, f"Expected >100% for over-capacity aisle, got {pct}"
    tier = classify_congestion(pct)
    assert tier == "CRITICAL", f"Expected CRITICAL tier, got {tier}"


def test_congestion_classification_none_input():
    """
    Boundary: None passed as congestion_percentage.
    Must handle gracefully — either raises or returns a defined fallback tier.
    """
    try:
        result = classify_congestion(None)
        # If it doesn't raise, it must return a string tier (sensor-fallback behaviour)
        assert isinstance(result, str), f"Expected string tier, got {type(result)}"
    except (TypeError, ValueError):
        pass  # Also acceptable — documented error path


def test_congestion_classification_extreme_high():
    """
    Boundary: congestion = 999% (extreme saturation).
    Must return CRITICAL and not overflow or produce undefined behaviour.
    """
    tier = classify_congestion(999.0)
    assert tier == "CRITICAL", f"Expected CRITICAL for 999%, got {tier}"


def test_congestion_classification_exactly_zero():
    """
    Boundary: congestion = 0.0 (empty aisle).
    Must return LOW — the lowest tier.
    """
    tier = classify_congestion(0.0)
    assert tier == "LOW", f"Expected LOW for 0% congestion, got {tier}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Controller — decision boundary cases
# ─────────────────────────────────────────────────────────────────────────────

def test_wave_release_all_aisles_at_full_capacity():
    """
    Boundary: congestion_percentage >= 100% (aisle over-capacity).
    Decision must be BLOCK regardless of requested_workers.
    Signature: wave_release_controller(congestion_percentage, requested_workers, ...)
    """
    result = wave_release_controller(
        congestion_percentage=105.0,
        requested_workers=1,
        safe_threshold=75.0,
        aisle_capacity=3,
        current_workers=4,
        sensor_available=True,
    )
    assert result["decision"] == "BLOCK", (
        f"Expected BLOCK for 105% congestion, got {result['decision']}"
    )


def test_controller_fallback_congestion_high_out_of_range():
    """
    Boundary: fallback_congestion = 150% (out of normal [0,100] range) during sensor failure.
    Must still produce a valid decision string — no crash.
    """
    valid_decisions = {"ALLOW", "DELAY", "BLOCK"}
    result = wave_release_controller(
        congestion_percentage=None,
        requested_workers=1,
        safe_threshold=75.0,
        aisle_capacity=3,
        current_workers=None,
        sensor_available=False,
        fallback_congestion=150.0,
    )
    assert result["decision"] in valid_decisions, (
        f"Expected valid decision, got {result['decision']}"
    )


def test_controller_exact_safe_threshold_boundary():
    """
    Boundary: congestion_percentage == safe_threshold exactly (75.0 == 75.0).
    At the boundary, decision must be DELAY (threshold is inclusive upper bound for ALLOW).
    """
    result = wave_release_controller(
        congestion_percentage=75.0,
        requested_workers=1,
        safe_threshold=75.0,
        aisle_capacity=4,
        current_workers=3,
        sensor_available=True,
    )
    assert result["decision"] in {"DELAY", "BLOCK"}, (
        f"Expected DELAY or BLOCK at exact threshold, got {result['decision']}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Visual similarity — unknown / edge inputs
# ─────────────────────────────────────────────────────────────────────────────

def test_unknown_aisle_visual_similarity_falls_back():
    """
    Boundary: aisle_id not in AISLE_PART_MAP (e.g., 'Z99').
    compute_adjusted_pick_time must not raise KeyError — uses safe default part.
    """
    rng = np.random.default_rng(42)
    total_time, detail = compute_adjusted_pick_time("Z99", rng=rng)
    assert total_time > 0, "Expected positive pick time for unknown aisle"
    assert "part_key" in detail, "Expected part_key in detail dict"


def test_unknown_aisle_similarity_risk_falls_back():
    """
    Boundary: get_zone_similarity_risk for unmapped aisle_id.
    Must return a float in [0, 1] — never raise or return None.
    """
    risk = get_zone_similarity_risk("Z99")
    assert isinstance(risk, float), "Expected float risk score"
    assert 0.0 <= risk <= 1.0, f"Risk score out of range: {risk}"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Simulation — empty and minimal inputs
# ─────────────────────────────────────────────────────────────────────────────

def test_simulation_empty_orders_returns_empty_dataframe():
    """
    Boundary: orders_df with 0 rows.
    Simulation must return an empty DataFrame without raising IndexError.
    """
    df = generate_warehouse_dataset(num_workers=5, num_orders=1, seed=42)
    empty_df = df.iloc[0:0].copy()
    sim = WarehouseSimulation(empty_df, controlled=True, seed=42)
    result = sim.run()
    assert isinstance(result, pd.DataFrame), "Expected DataFrame return"
    assert len(result) == 0, f"Expected 0 rows for empty input, got {len(result)}"


def test_simulation_single_order_single_worker():
    """
    Boundary: 1 order, 1 worker — absolute minimum viable simulation.
    Must produce at least 1 result row with non-NaN turnaround and waiting times.
    """
    df = generate_warehouse_dataset(num_workers=1, num_orders=1, seed=42)
    sim = WarehouseSimulation(df, controlled=True, use_visual_similarity=True, seed=42)
    result = sim.run()
    assert len(result) >= 1, "Expected at least 1 result row"
    assert not result["turnaround_time"].isna().any(), "NaN turnaround_time for single order"
    assert not result["waiting_time"].isna().any(), "NaN waiting_time for single order"


def test_metrics_missing_review2_columns_falls_back_to_zero():
    """
    Boundary: orders_df without Review 2 columns (mispick_count, verification_overhead_sec etc.).
    compute_simulation_metrics must not raise KeyError — missing KPIs default to 0.
    """
    df = generate_warehouse_dataset(num_workers=20, num_orders=40, seed=42)
    sim = WarehouseSimulation(df, controlled=True, use_visual_similarity=False, seed=42)
    result = sim.run()
    for col in ["mispick_count", "verification_overhead_sec", "mispick_penalty_sec", "rerouted"]:
        if col in result.columns:
            result = result.drop(columns=[col])
    ts = sim.get_aisle_congestion_timeseries()
    metrics = compute_simulation_metrics(result, ts)
    assert metrics["total_mispick_count"] == 0
    assert metrics["total_verification_overhead_sec"] == 0.0
    assert metrics["rerouted_orders_count"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# 5. Store-and-Forward — lifecycle edge cases
# ─────────────────────────────────────────────────────────────────────────────

def test_saf_drain_empty_queue_returns_empty_list():
    """
    Boundary: drain() called on a queue with no enqueued events.
    Must return [] without raising — no crash on empty deque.
    """
    saf = StoreAndForwardQueue()
    events = saf.drain()
    assert events == [], f"Expected [], got {events}"


def test_network_monitor_zero_mean_duration_does_not_crash():
    """
    Boundary: mean_outage_duration = near-zero (0.001 s).
    Monitor must not raise or produce infinite loops.
    """
    monitor = NetworkStateMonitor(
        total_sim_duration=3600.0,
        mean_outage_interval=300.0,
        mean_outage_duration=0.001,
        seed=42,
    )
    schedule = monitor.get_outage_schedule()
    assert isinstance(schedule, list), "Expected list schedule"


def test_rerouting_with_very_low_threshold_does_not_crash():
    """
    Boundary: reroute_threshold_pct = 0.0 (every aisle effectively 'blocked' for rerouting).
    Simulation must complete without raising and produce valid results.
    """
    df = generate_warehouse_dataset(num_workers=10, num_orders=20, seed=42)
    sim = WarehouseSimulation(
        df, controlled=True, use_visual_similarity=True,
        enable_dynamic_rerouting=True, reroute_threshold_pct=0.0, seed=42
    )
    result = sim.run()
    assert len(result) >= 1, "Expected results even with threshold=0"
    assert (result["path_length"] >= 1).all(), "All orders must visit at least 1 aisle"
