"""
scenarios.py
Defines the three mandatory operating scenarios:
- Scenario A: Normal Operation
- Scenario B: Peak Congestion (Baseline vs Controlled)
- Scenario C: Sensor/Network Failure (Manual Fallback Mode)
Also includes sensitivity analysis for safe threshold optimization.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
from src.data_generator import generate_warehouse_dataset, DEFAULT_AISLES
from src.simulation import WarehouseSimulation
from src.metrics import compute_simulation_metrics, generate_comparison_table


def run_normal_operation_scenario(seed: int = 42) -> Dict[str, Any]:
    """
    Executes Scenario A: Normal Operation.
    Simulates standard daily warehouse picking flow with typical item distribution.
    """
    print("\n--- Running Scenario A: Normal Operation ---")
    data_df = generate_warehouse_dataset(
        num_workers=100,
        num_orders=300,
        seed=seed,
        scenario_name="Normal Operation",
        peak_multiplier=1.0
    )

    sim = WarehouseSimulation(
        orders_df=data_df,
        controlled=True,
        safe_threshold=75.0,
        sensor_available=True
    )
    orders_result = sim.run()
    timeseries = sim.get_aisle_congestion_timeseries(time_step_seconds=30.0)
    metrics = compute_simulation_metrics(orders_result, timeseries)

    return {
        "scenario": "Normal Operation",
        "system_status": "NORMAL",
        "mode": "AUTOMATIC",
        "dataset": data_df,
        "orders_result": orders_result,
        "timeseries": timeseries,
        "metrics": metrics
    }


def run_peak_congestion_scenario(seed: int = 42, safe_threshold: float = 75.0) -> Dict[str, Any]:
    """
    Executes Scenario B: Peak Congestion.
    Concentrates order demand heavily into fast-moving aisles (A03, A07) to generate
    congestive bottlenecks, running both Baseline (uncontrolled) and Controlled waves.
    """
    print("\n--- Running Scenario B: Peak Congestion (Baseline vs Controlled) ---")
    data_df = generate_warehouse_dataset(
        num_workers=120,
        num_orders=350,
        seed=seed,
        scenario_name="Peak Congestion",
        peak_multiplier=2.8
    )

    # 1. Baseline Execution (Unregulated)
    sim_base = WarehouseSimulation(
        orders_df=data_df,
        controlled=False,
        safe_threshold=safe_threshold,
        sensor_available=True
    )
    base_orders = sim_base.run()
    base_timeseries = sim_base.get_aisle_congestion_timeseries(time_step_seconds=30.0)
    base_metrics = compute_simulation_metrics(base_orders, base_timeseries)

    # 2. Controlled Execution (Wave-Release Managed)
    sim_ctrl = WarehouseSimulation(
        orders_df=data_df,
        controlled=True,
        safe_threshold=safe_threshold,
        sensor_available=True
    )
    ctrl_orders = sim_ctrl.run()
    ctrl_timeseries = sim_ctrl.get_aisle_congestion_timeseries(time_step_seconds=30.0)
    ctrl_metrics = compute_simulation_metrics(ctrl_orders, ctrl_timeseries)

    # 3. Comparative Analysis
    comparison_df = generate_comparison_table(base_metrics, ctrl_metrics)

    return {
        "scenario": "Peak Congestion",
        "dataset": data_df,
        "baseline": {
            "orders": base_orders,
            "timeseries": base_timeseries,
            "metrics": base_metrics
        },
        "controlled": {
            "orders": ctrl_orders,
            "timeseries": ctrl_timeseries,
            "metrics": ctrl_metrics
        },
        "comparison_table": comparison_df
    }


def run_sensor_failure_scenario(seed: int = 42, fallback_congestion: float = 65.0) -> Dict[str, Any]:
    """
    Executes Scenario C: Sensor / Network Failure.
    Simulates total telemetry blackout (sensor_available = False).
    Proves system fails gracefully into MANUAL FALLBACK mode without crashing.
    """
    print("\n--- Running Scenario C: Sensor / Network Failure (Manual Fallback) ---")
    data_df = generate_warehouse_dataset(
        num_workers=100,
        num_orders=300,
        seed=seed,
        scenario_name="Sensor Failure",
        peak_multiplier=1.5
    )

    sim_failure = WarehouseSimulation(
        orders_df=data_df,
        controlled=True,
        safe_threshold=75.0,
        sensor_available=False,
        fallback_congestion=fallback_congestion
    )
    orders_result = sim_failure.run()
    timeseries = sim_failure.get_aisle_congestion_timeseries(time_step_seconds=30.0)
    metrics = compute_simulation_metrics(orders_result, timeseries)

    return {
        "scenario": "Sensor/Network Failure",
        "system_status": "SENSOR FAILURE",
        "mode": "MANUAL FALLBACK",
        "dataset": data_df,
        "orders_result": orders_result,
        "timeseries": timeseries,
        "metrics": metrics,
        "controller_logs": sim_failure.controller_logs
    }


def run_sensitivity_analysis(
    thresholds: List[float] = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Sweeps safe congestion threshold values [60%, 65%, 70%, 75%, 80%, 85%, 90%]
    to evaluate operational trade-offs between worker delays and aisle congestion.
    """
    if thresholds is None:
        thresholds = [60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0]

    print("\n--- Running Sensitivity Analysis on Safe Thresholds ---")
    data_df = generate_warehouse_dataset(
        num_workers=120,
        num_orders=350,
        seed=seed,
        scenario_name="Sensitivity Analysis",
        peak_multiplier=2.5
    )

    records = []
    for thresh in thresholds:
        sim = WarehouseSimulation(
            orders_df=data_df,
            controlled=True,
            safe_threshold=thresh,
            sensor_available=True
        )
        res_orders = sim.run()
        res_ts = sim.get_aisle_congestion_timeseries(time_step_seconds=30.0)
        metrics = compute_simulation_metrics(res_orders, res_ts)

        records.append({
            "safe_threshold_pct": thresh,
            "avg_waiting_time_sec": metrics["avg_waiting_time_sec"],
            "total_waiting_time_sec": metrics["total_waiting_time_sec"],
            "throughput_orders_per_hr": metrics["throughput_orders_per_hr"],
            "avg_congestion_pct": metrics["avg_congestion_pct"],
            "max_congestion_pct": metrics["max_congestion_pct"],
            "critical_events_count": metrics["critical_events_count"],
            "delayed_orders_count": metrics["delayed_orders_count"],
            "total_estimated_cost_usd": metrics["total_estimated_cost_usd"],
            "estimated_emissions_kg": metrics["estimated_emissions_kg"]
        })

    return pd.DataFrame(records)
