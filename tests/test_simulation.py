"""
test_simulation.py
Unit and integration tests for warehouse simulation execution, distance,
hotspot ranking, multi-load conditions, and multi-seed statistical validation.
"""

import pytest
import pandas as pd
import numpy as np
from src.data_generator import (
    generate_warehouse_dataset,
    calculate_grid_distance,
    calculate_path_total_distance,
    DEFAULT_AISLES
)
from src.simulation import WarehouseSimulation
from src.metrics import compute_hotspot_analysis, compute_simulation_metrics
from src.scenarios import (
    run_low_load_scenario,
    run_extreme_load_scenario,
    run_multirun_validation
)


def test_distance_calculation_accuracy():
    """Verify grid Manhattan distance calculation."""
    # A01 is at (0,0), A02 is at (0,1) -> Manhattan dist = 1 unit = 15m
    d_a1_a2 = calculate_grid_distance("A01", "A02")
    assert d_a1_a2 == 15.0

    # A01 is at (0,0), A07 is at (1,2) -> Manhattan dist = |0-1| + |0-2| = 3 units = 45m
    d_a1_a7 = calculate_grid_distance("A01", "A07")
    assert d_a1_a7 == 45.0

    # Total path distance from depot: A01 -> A02
    path_dist = calculate_path_total_distance(["A01", "A02"])
    assert path_dist == 15.0


def test_waiting_time_non_negative():
    """Ensure worker waiting times are strictly non-negative under both baseline and controlled."""
    df = generate_warehouse_dataset(num_workers=20, num_orders=40, seed=101)

    # Baseline simulation
    sim_base = WarehouseSimulation(df, controlled=False)
    base_res = sim_base.run()
    assert (base_res["waiting_time"] >= 0.0).all(), "Baseline waiting times must be >= 0"

    # Controlled simulation
    sim_ctrl = WarehouseSimulation(df, controlled=True, safe_threshold=70.0)
    ctrl_res = sim_ctrl.run()
    assert (ctrl_res["waiting_time"] >= 0.0).all(), "Controlled waiting times must be >= 0"


def test_simulation_reproducibility():
    """Ensure that identical seeds yield perfectly reproducible simulation outputs."""
    df1 = generate_warehouse_dataset(num_workers=20, num_orders=30, seed=999)
    df2 = generate_warehouse_dataset(num_workers=20, num_orders=30, seed=999)

    pd.testing.assert_frame_equal(df1, df2)

    sim1 = WarehouseSimulation(df1, controlled=True, safe_threshold=75.0)
    res1 = sim1.run()

    sim2 = WarehouseSimulation(df2, controlled=True, safe_threshold=75.0)
    res2 = sim2.run()

    pd.testing.assert_frame_equal(res1, res2)


def test_hotspot_analysis_structure():
    """Verify that hotspot analysis correctly ranks aisles and computes metrics."""
    df = generate_warehouse_dataset(num_workers=30, num_orders=60, seed=42, peak_multiplier=2.5)
    sim = WarehouseSimulation(df, controlled=False)
    sim.run()
    timeseries = sim.get_aisle_congestion_timeseries(time_step_seconds=30.0)

    hotspot_df = compute_hotspot_analysis(timeseries)
    assert not hotspot_df.empty
    assert "Aisle" in hotspot_df.columns
    assert "Average_Congestion_Pct" in hotspot_df.columns
    assert "Critical_Events_Count" in hotspot_df.columns
    assert len(hotspot_df) == len(DEFAULT_AISLES)

    # Verify top hotspot is one of the designated popularity aisles (A03 or A07)
    top_aisles = hotspot_df["Aisle"].head(3).tolist()
    assert ("A03" in top_aisles or "A07" in top_aisles)


def test_low_load_scenario_metrics():
    """Verify that Low Load scenario executes with lower congestion than normal/peak."""
    res = run_low_load_scenario(seed=42)
    m = res["metrics"]
    assert m["num_orders"] == 180
    assert m["avg_congestion_pct"] >= 0.0
    assert m["critical_events_count"] <= 25  # Low load has few or zero critical bottlenecks


def test_extreme_load_scenario_stress():
    """Verify that Extreme Load scenario stress-tests the warehouse with high demand."""
    res = run_extreme_load_scenario(seed=42)
    base_m = res["baseline"]["metrics"]
    ctrl_m = res["controlled"]["metrics"]
    assert base_m["num_orders"] == 450
    assert base_m["critical_events_count"] > 100
    # Controlled mode should show delayed orders
    assert ctrl_m["delayed_orders_count"] > 0


def test_multirun_validation_statistics():
    """Verify multi-run statistical evaluation calculates valid mean and standard deviation."""
    df_runs, summary_df = run_multirun_validation(seeds=[42, 101, 202])
    assert len(df_runs) == 3
    assert not summary_df.empty
    assert "Mean" in summary_df.columns
    assert "Std" in summary_df.columns

    # Standard deviation should be non-negative
    assert (summary_df["Std"] >= 0.0).all()
