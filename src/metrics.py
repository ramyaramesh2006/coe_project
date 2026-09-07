"""
metrics.py
Warehouse Performance Evaluation and Comparative Analysis Engine.
Calculates congestion, waiting time, throughput, travel distance, operational costs,
and carbon emissions programmatically.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


# Configurable Cost Model Assumptions (Review 1 Prototype)
DEFAULT_COST_CONFIG = {
    "worker_cost_per_minute": 0.35,      # $21.00 / hr standard warehouse picker wage
    "cost_per_meter": 0.02,              # Wear/tear & cart equipment maintenance per meter
    "delay_cost_per_minute": 0.25,       # Idle worker & order fulfillment SLA penalty per minute
}

# Configurable Emission Model Assumptions (Review 1 Prototype)
DEFAULT_EMISSION_CONFIG = {
    "emission_factor_per_meter": 0.00015  # kg CO2e per meter (battery-electric cart energy share)
}


def compute_simulation_metrics(
    orders_result_df: pd.DataFrame,
    timeseries_df: pd.DataFrame,
    cost_config: Dict[str, float] = None,
    emission_config: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Computes all standard performance KPIs from simulation execution data.
    """
    if cost_config is None:
        cost_config = DEFAULT_COST_CONFIG
    if emission_config is None:
        emission_config = DEFAULT_EMISSION_CONFIG

    if orders_result_df.empty:
        return {}

    num_orders = len(orders_result_df)
    sim_start_time = orders_result_df["requested_release_time"].min()
    sim_end_time = orders_result_df["completion_time"].max()
    sim_duration_sec = max(1.0, sim_end_time - sim_start_time)
    sim_duration_hrs = sim_duration_sec / 3600.0

    # Waiting Time
    waiting_times = orders_result_df["waiting_time"]
    total_waiting_sec = float(waiting_times.sum())
    avg_waiting_sec = float(waiting_times.mean())
    max_waiting_sec = float(waiting_times.max())
    delayed_orders_count = int((orders_result_df["delay_count"] > 0).sum())

    # Throughput (orders per hour)
    throughput_per_hr = float(round(num_orders / sim_duration_hrs, 2))

    # Travel Distance
    total_distance_m = float(orders_result_df["total_distance_m"].sum())
    avg_distance_m = float(orders_result_df["total_distance_m"].mean())

    # Congestion Metrics from Timeseries
    cong_cols = [c for c in timeseries_df.columns if c.endswith("_congestion")]
    if cong_cols and not timeseries_df.empty:
        all_congs = timeseries_df[cong_cols].values.flatten()
        avg_congestion = float(np.mean(all_congs))
        max_congestion = float(np.max(all_congs))

        # Count of time-steps where any aisle was CRITICAL (>= 100%) or HIGH (>= 75%)
        critical_events = int((timeseries_df[cong_cols] >= 100.0).sum().sum())
        high_events = int(((timeseries_df[cong_cols] >= 75.0) & (timeseries_df[cong_cols] < 100.0)).sum().sum())
    else:
        avg_congestion = 0.0
        max_congestion = 0.0
        critical_events = 0
        high_events = 0

    # Operational Cost Estimation ($)
    # Total active order fulfillment time (excluding idle waiting)
    total_active_minutes = float((orders_result_df["turnaround_time"] - orders_result_df["waiting_time"]).sum() / 60.0)
    total_waiting_minutes = total_waiting_sec / 60.0

    labor_cost = total_active_minutes * cost_config["worker_cost_per_minute"]
    travel_cost = total_distance_m * cost_config["cost_per_meter"]
    delay_cost = total_waiting_minutes * cost_config["delay_cost_per_minute"]
    total_cost = labor_cost + travel_cost + delay_cost

    # Carbon Emissions Estimation (kg CO2e)
    estimated_emissions_kg = total_distance_m * emission_config["emission_factor_per_meter"]

    return {
        "num_orders": num_orders,
        "sim_duration_sec": sim_duration_sec,
        "sim_duration_hrs": sim_duration_hrs,
        "throughput_orders_per_hr": throughput_per_hr,
        "avg_congestion_pct": round(avg_congestion, 2),
        "max_congestion_pct": round(max_congestion, 2),
        "critical_events_count": critical_events,
        "high_events_count": high_events,
        "total_waiting_time_sec": round(total_waiting_sec, 2),
        "avg_waiting_time_sec": round(avg_waiting_sec, 2),
        "max_waiting_time_sec": round(max_waiting_sec, 2),
        "delayed_orders_count": delayed_orders_count,
        "total_distance_m": round(total_distance_m, 2),
        "avg_distance_m": round(avg_distance_m, 2),
        "labor_cost_usd": round(labor_cost, 2),
        "travel_cost_usd": round(travel_cost, 2),
        "delay_cost_usd": round(delay_cost, 2),
        "total_estimated_cost_usd": round(total_cost, 2),
        "estimated_emissions_kg": round(estimated_emissions_kg, 4)
    }


def generate_comparison_table(
    baseline_metrics: Dict[str, Any],
    controlled_metrics: Dict[str, Any]
) -> pd.DataFrame:
    """
    Constructs an honest, programmatically calculated comparison table.
    Shows Baseline, Controlled, Absolute Difference, and Percentage Improvement.
    """
    kpis = [
        ("Average Congestion (%)", "avg_congestion_pct", "lower"),
        ("Maximum Congestion (%)", "max_congestion_pct", "lower"),
        ("Critical Congestion Events", "critical_events_count", "lower"),
        ("High Congestion Events", "high_events_count", "lower"),
        ("Average Waiting Time (s)", "avg_waiting_time_sec", "lower"),
        ("Maximum Waiting Time (s)", "max_waiting_time_sec", "lower"),
        ("Total Waiting Time (s)", "total_waiting_time_sec", "lower"),
        ("Delayed Orders Count", "delayed_orders_count", "lower"),
        ("Throughput (orders/hr)", "throughput_orders_per_hr", "higher"),
        ("Total Distance (m)", "total_distance_m", "lower"),
        ("Average Distance (m)", "avg_distance_m", "lower"),
        ("Total Estimated Cost ($)", "total_estimated_cost_usd", "lower"),
        ("Estimated Emissions (kg CO2e)", "estimated_emissions_kg", "lower"),
    ]

    rows = []
    for label, key, preference in kpis:
        base_val = baseline_metrics.get(key, 0.0)
        ctrl_val = controlled_metrics.get(key, 0.0)
        diff = ctrl_val - base_val

        # Calculate improvement percentage honestly
        if base_val == 0:
            if ctrl_val == 0:
                imp_pct = 0.0
            else:
                imp_pct = -100.0 if preference == "lower" else 100.0
        else:
            if preference == "lower":
                # For things like congestion, cost, events: lower is better
                imp_pct = ((base_val - ctrl_val) / base_val) * 100.0
            else:
                # For throughput: higher is better
                imp_pct = ((ctrl_val - base_val) / base_val) * 100.0

        rows.append({
            "Metric": label,
            "Baseline": base_val,
            "Controlled": ctrl_val,
            "Difference": round(diff, 2) if isinstance(diff, float) else diff,
            "Improvement_Percentage": round(imp_pct, 2)
        })

    return pd.DataFrame(rows)
