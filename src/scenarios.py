"""
scenarios.py
Multi-load experimental framework and validation engine:
- Scenario A: Low Load
- Scenario B: Normal Load
- Scenario C: Peak Congestion (Baseline vs Controlled)
- Scenario D: Extreme Load (Stress-testing saturation)
- Scenario E: Sensor/Network Failure (Manual Fallback Mode)
- Multi-run statistical stability across multiple random seeds (42, 101, 202, 303, 404)
- Configurable threshold sensitivity sweeps with full ALLOW/DELAY/BLOCK accounting
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from src.data_generator import generate_warehouse_dataset, DEFAULT_AISLES
from src.simulation import WarehouseSimulation
from src.metrics import compute_simulation_metrics, generate_comparison_table, compute_hotspot_analysis


def run_low_load_scenario(seed: int = 42) -> Dict[str, Any]:
    """
    Executes Scenario A: Low Load.
    Simulates off-peak warehouse operation with sparse picking traffic.
    """
    print("\n--- Running Scenario A: Low Load ---")
    data_df = generate_warehouse_dataset(
        num_workers=60,
        num_orders=180,
        seed=seed,
        scenario_name="Low Load",
        peak_multiplier=0.7
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
        "scenario": "Low Load",
        "system_status": "NORMAL",
        "mode": "AUTOMATIC",
        "dataset": data_df,
        "orders_result": orders_result,
        "timeseries": timeseries,
        "metrics": metrics
    }


def run_normal_operation_scenario(seed: int = 42) -> Dict[str, Any]:
    """
    Executes Scenario B: Normal Load.
    Simulates standard daily warehouse picking flow with typical item distribution.
    """
    print("\n--- Running Scenario B: Normal Operation ---")
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
    Executes Scenario C: Peak Congestion.
    Concentrates order demand into fast-moving aisles (A03, A07),
    running both Baseline (uncontrolled) and Controlled wave-release.
    """
    print("\n--- Running Scenario C: Peak Congestion (Baseline vs Controlled) ---")
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

    # 3. Hotspot Analysis
    hotspot_df = compute_hotspot_analysis(base_timeseries)

    # 4. Comparative Analysis
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
        "hotspot_table": hotspot_df,
        "comparison_table": comparison_df
    }


def run_extreme_load_scenario(seed: int = 42, safe_threshold: float = 75.0) -> Dict[str, Any]:
    """
    Executes Scenario D: Extreme Load.
    Stress-tests the warehouse under extreme shift demands (150 workers, 450 orders, 3.5x multiplier).
    """
    print("\n--- Running Scenario D: Extreme Load (Stress Test) ---")
    data_df = generate_warehouse_dataset(
        num_workers=150,
        num_orders=450,
        seed=seed,
        scenario_name="Extreme Load",
        peak_multiplier=3.5
    )

    sim_base = WarehouseSimulation(
        orders_df=data_df,
        controlled=False,
        safe_threshold=safe_threshold,
        sensor_available=True
    )
    base_orders = sim_base.run()
    base_timeseries = sim_base.get_aisle_congestion_timeseries(time_step_seconds=30.0)
    base_metrics = compute_simulation_metrics(base_orders, base_timeseries)

    sim_ctrl = WarehouseSimulation(
        orders_df=data_df,
        controlled=True,
        safe_threshold=safe_threshold,
        sensor_available=True
    )
    ctrl_orders = sim_ctrl.run()
    ctrl_timeseries = sim_ctrl.get_aisle_congestion_timeseries(time_step_seconds=30.0)
    ctrl_metrics = compute_simulation_metrics(ctrl_orders, ctrl_timeseries)

    comparison_df = generate_comparison_table(base_metrics, ctrl_metrics)

    return {
        "scenario": "Extreme Load",
        "dataset": data_df,
        "baseline": {"orders": base_orders, "timeseries": base_timeseries, "metrics": base_metrics},
        "controlled": {"orders": ctrl_orders, "timeseries": ctrl_timeseries, "metrics": ctrl_metrics},
        "comparison_table": comparison_df
    }


def run_sensor_failure_scenario(seed: int = 42, fallback_congestion: float = 65.0) -> Dict[str, Any]:
    """
    Executes Scenario E: Sensor / Network Failure.
    Simulates total telemetry blackout (sensor_available = False).
    Proves system fails gracefully into MANUAL FALLBACK mode with conservative release pacing.
    """
    print("\n--- Running Scenario: Sensor / Network Failure (Manual Fallback) ---")
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


def run_multi_load_experiments(seed: int = 42) -> pd.DataFrame:
    """
    Executes Low, Normal, Peak, and Extreme operating conditions.
    Returns a consolidated multi-load comparative performance summary table.
    """
    print("\n================================================================================")
    print("           EXECUTING MULTI-LOAD WAREHOUSE EXPERIMENTS (A, B, C, D)             ")
    print("================================================================================")
    res_low = run_low_load_scenario(seed=seed)
    res_norm = run_normal_operation_scenario(seed=seed)
    res_peak = run_peak_congestion_scenario(seed=seed)
    res_extr = run_extreme_load_scenario(seed=seed)

    records = [
        {
            "Scenario": "Low Load",
            "Orders": res_low["metrics"]["num_orders"],
            "Mode": "CONTROLLED",
            "Throughput_ord_hr": res_low["metrics"]["throughput_orders_per_hr"],
            "Avg_Waiting_Sec": res_low["metrics"]["avg_waiting_time_sec"],
            "Max_Congestion_Pct": res_low["metrics"]["max_congestion_pct"],
            "Critical_Events": res_low["metrics"]["critical_events_count"],
            "High_Events": res_low["metrics"]["high_events_count"],
            "Affected_Aisles": res_low["metrics"]["affected_aisles_count"],
            "Total_Cost_USD": res_low["metrics"]["total_estimated_cost_usd"],
            "Emissions_KG": res_low["metrics"]["estimated_emissions_kg"]
        },
        {
            "Scenario": "Normal Load",
            "Orders": res_norm["metrics"]["num_orders"],
            "Mode": "CONTROLLED",
            "Throughput_ord_hr": res_norm["metrics"]["throughput_orders_per_hr"],
            "Avg_Waiting_Sec": res_norm["metrics"]["avg_waiting_time_sec"],
            "Max_Congestion_Pct": res_norm["metrics"]["max_congestion_pct"],
            "Critical_Events": res_norm["metrics"]["critical_events_count"],
            "High_Events": res_norm["metrics"]["high_events_count"],
            "Affected_Aisles": res_norm["metrics"]["affected_aisles_count"],
            "Total_Cost_USD": res_norm["metrics"]["total_estimated_cost_usd"],
            "Emissions_KG": res_norm["metrics"]["estimated_emissions_kg"]
        },
        {
            "Scenario": "Peak Load (Base)",
            "Orders": res_peak["baseline"]["metrics"]["num_orders"],
            "Mode": "BASELINE",
            "Throughput_ord_hr": res_peak["baseline"]["metrics"]["throughput_orders_per_hr"],
            "Avg_Waiting_Sec": res_peak["baseline"]["metrics"]["avg_waiting_time_sec"],
            "Max_Congestion_Pct": res_peak["baseline"]["metrics"]["max_congestion_pct"],
            "Critical_Events": res_peak["baseline"]["metrics"]["critical_events_count"],
            "High_Events": res_peak["baseline"]["metrics"]["high_events_count"],
            "Affected_Aisles": res_peak["baseline"]["metrics"]["affected_aisles_count"],
            "Total_Cost_USD": res_peak["baseline"]["metrics"]["total_estimated_cost_usd"],
            "Emissions_KG": res_peak["baseline"]["metrics"]["estimated_emissions_kg"]
        },
        {
            "Scenario": "Peak Load (Ctrl)",
            "Orders": res_peak["controlled"]["metrics"]["num_orders"],
            "Mode": "CONTROLLED",
            "Throughput_ord_hr": res_peak["controlled"]["metrics"]["throughput_orders_per_hr"],
            "Avg_Waiting_Sec": res_peak["controlled"]["metrics"]["avg_waiting_time_sec"],
            "Max_Congestion_Pct": res_peak["controlled"]["metrics"]["max_congestion_pct"],
            "Critical_Events": res_peak["controlled"]["metrics"]["critical_events_count"],
            "High_Events": res_peak["controlled"]["metrics"]["high_events_count"],
            "Affected_Aisles": res_peak["controlled"]["metrics"]["affected_aisles_count"],
            "Total_Cost_USD": res_peak["controlled"]["metrics"]["total_estimated_cost_usd"],
            "Emissions_KG": res_peak["controlled"]["metrics"]["estimated_emissions_kg"]
        },
        {
            "Scenario": "Extreme Load (Base)",
            "Orders": res_extr["baseline"]["metrics"]["num_orders"],
            "Mode": "BASELINE",
            "Throughput_ord_hr": res_extr["baseline"]["metrics"]["throughput_orders_per_hr"],
            "Avg_Waiting_Sec": res_extr["baseline"]["metrics"]["avg_waiting_time_sec"],
            "Max_Congestion_Pct": res_extr["baseline"]["metrics"]["max_congestion_pct"],
            "Critical_Events": res_extr["baseline"]["metrics"]["critical_events_count"],
            "High_Events": res_extr["baseline"]["metrics"]["high_events_count"],
            "Affected_Aisles": res_extr["baseline"]["metrics"]["affected_aisles_count"],
            "Total_Cost_USD": res_extr["baseline"]["metrics"]["total_estimated_cost_usd"],
            "Emissions_KG": res_extr["baseline"]["metrics"]["estimated_emissions_kg"]
        },
        {
            "Scenario": "Extreme Load (Ctrl)",
            "Orders": res_extr["controlled"]["metrics"]["num_orders"],
            "Mode": "CONTROLLED",
            "Throughput_ord_hr": res_extr["controlled"]["metrics"]["throughput_orders_per_hr"],
            "Avg_Waiting_Sec": res_extr["controlled"]["metrics"]["avg_waiting_time_sec"],
            "Max_Congestion_Pct": res_extr["controlled"]["metrics"]["max_congestion_pct"],
            "Critical_Events": res_extr["controlled"]["metrics"]["critical_events_count"],
            "High_Events": res_extr["controlled"]["metrics"]["high_events_count"],
            "Affected_Aisles": res_extr["controlled"]["metrics"]["affected_aisles_count"],
            "Total_Cost_USD": res_extr["controlled"]["metrics"]["total_estimated_cost_usd"],
            "Emissions_KG": res_extr["controlled"]["metrics"]["estimated_emissions_kg"]
        }
    ]

    return pd.DataFrame(records)


def run_sensitivity_analysis(
    thresholds: Optional[List[float]] = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Sweeps safe congestion threshold values [60%, 65%, 70%, 75%, 80%, 85%, 90%].
    Tracks decision breakdowns (ALLOW, DELAY, BLOCK), waiting times, throughput, and costs.
    """
    if thresholds is None:
        thresholds = [60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0]

    print("\n--- Running Safe Threshold Sensitivity Analysis ---")
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

        # Count decisions from controller logs
        decisions = [log["decision"] for log in sim.controller_logs]
        allow_count = decisions.count("ALLOW")
        delay_count = decisions.count("DELAY")
        block_count = decisions.count("BLOCK")
        total_evals = len(decisions)

        records.append({
            "safe_threshold_pct": thresh,
            "total_evaluations": total_evals,
            "allow_decisions": allow_count,
            "delay_decisions": delay_count,
            "block_decisions": block_count,
            "avg_waiting_time_sec": metrics["avg_waiting_time_sec"],
            "total_waiting_time_sec": metrics["total_waiting_time_sec"],
            "throughput_orders_per_hr": metrics["throughput_orders_per_hr"],
            "avg_congestion_pct": metrics["avg_congestion_pct"],
            "max_congestion_pct": metrics["max_congestion_pct"],
            "critical_events_count": metrics["critical_events_count"],
            "delayed_orders_count": metrics["delayed_orders_count"],
            "total_estimated_cost_usd": metrics["total_estimated_cost_usd"]
        })

    return pd.DataFrame(records)


def run_multirun_validation(
    seeds: Optional[List[int]] = None,
    safe_threshold: float = 75.0
) -> pd.DataFrame:
    """
    Executes multiple simulation runs using different random seeds (42, 101, 202, 303, 404).
    Calculates Mean, Min, Max, and Standard Deviation (Std) for key performance indicators.
    Demonstrates that results are statistically robust and not an artifact of a single seed.
    """
    if seeds is None:
        seeds = [42, 101, 202, 303, 404]

    print(f"\n--- Running Multi-Seed Statistical Validation across seeds: {seeds} ---")
    run_records = []

    for seed in seeds:
        data_df = generate_warehouse_dataset(
            num_workers=120,
            num_orders=350,
            seed=seed,
            scenario_name="MultiRun Validation",
            peak_multiplier=2.8
        )

        # Baseline run
        sim_base = WarehouseSimulation(data_df, controlled=False, sensor_available=True)
        base_res = sim_base.run()
        base_ts = sim_base.get_aisle_congestion_timeseries()
        base_m = compute_simulation_metrics(base_res, base_ts)

        # Controlled run
        sim_ctrl = WarehouseSimulation(data_df, controlled=True, safe_threshold=safe_threshold, sensor_available=True)
        ctrl_res = sim_ctrl.run()
        ctrl_ts = sim_ctrl.get_aisle_congestion_timeseries()
        ctrl_m = compute_simulation_metrics(ctrl_res, ctrl_ts)

        run_records.append({
            "seed": seed,
            "base_critical_events": base_m["critical_events_count"],
            "ctrl_critical_events": ctrl_m["critical_events_count"],
            "critical_reduction_pct": ((base_m["critical_events_count"] - ctrl_m["critical_events_count"]) / max(1, base_m["critical_events_count"])) * 100.0,
            "ctrl_avg_waiting_sec": ctrl_m["avg_waiting_time_sec"],
            "ctrl_delayed_orders": ctrl_m["delayed_orders_count"],
            "base_throughput": base_m["throughput_orders_per_hr"],
            "ctrl_throughput": ctrl_m["throughput_orders_per_hr"],
            "base_cost": base_m["total_estimated_cost_usd"],
            "ctrl_cost": ctrl_m["total_estimated_cost_usd"]
        })

    df_runs = pd.DataFrame(run_records)

    # Calculate summary statistics
    metrics_to_summarize = [
        "base_critical_events", "ctrl_critical_events", "critical_reduction_pct",
        "ctrl_avg_waiting_sec", "ctrl_delayed_orders",
        "base_throughput", "ctrl_throughput",
        "base_cost", "ctrl_cost"
    ]

    summary_rows = []
    for col in metrics_to_summarize:
        vals = df_runs[col].values
        summary_rows.append({
            "Metric": col,
            "Mean": round(float(np.mean(vals)), 2),
            "Std": round(float(np.std(vals)), 2),
            "Min": round(float(np.min(vals)), 2),
            "Max": round(float(np.max(vals)), 2)
        })

    summary_df = pd.DataFrame(summary_rows)
    return df_runs, summary_df
