"""
test_simulation.py
Unit and integration tests for warehouse simulation execution, distance, and waiting times.
"""

import pytest
import pandas as pd
from src.data_generator import (
    generate_warehouse_dataset,
    calculate_grid_distance,
    calculate_path_total_distance,
    DEFAULT_AISLES
)
from src.simulation import WarehouseSimulation


def test_distance_calculation_accuracy():
    """Verify grid Manhattan distance calculation."""
    # A01 is at (0,0), A02 is at (0,1) -> Manhattan dist = 1 unit = 15m
    d_a1_a2 = calculate_grid_distance("A01", "A02")
    assert d_a1_a2 == 15.0

    # A01 is at (0,0), A07 is at (1,2) -> Manhattan dist = |0-1| + |0-2| = 3 units = 45m
    d_a1_a7 = calculate_grid_distance("A01", "A07")
    assert d_a1_a7 == 45.0

    # Total path distance from depot: A01 -> A02
    # Depot (0,0) to A01 (0,0) = 0m, A01 to A02 = 15m -> Total = 15m
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
