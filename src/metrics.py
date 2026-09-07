"""
metrics.py
Warehouse Performance Evaluation and Comparative Analysis Engine.
Calculates congestion, waiting time, throughput, travel distance, operational costs,
carbon emissions, advanced congestion duration, worker exposure, and hotspot rankings.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from src.data_generator import DEFAULT_AISLES


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
    cost_config: Optional[Dict[str, float]] = None,
    emission_config: Optional[Dict[str, float]] = None,
    time_step_seconds: float = 30.0
) -> Dict[str, Any]:
    """
    Computes all standard and advanced performance KPIs from simulation execution data.
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

        # Number of affected aisles experiencing at least one HIGH or CRITICAL event
        affected_aisles_set = set()
        aisle_mean_congs = {}
        for col in cong_cols:
            aisle_name = col.replace("_congestion", "")
            if (timeseries_df[col] >= 75.0).any():
                affected_aisles_set.add(aisle_name)
            aisle_mean_congs[aisle_name] = timeseries_df[col].mean()

        affected_aisles_count = len(affected_aisles_set)
        most_congested_aisle = max(aisle_mean_congs.items(), key=lambda x: x[1])[0] if aisle_mean_congs else "N/A"

        # Congestion duration (seconds where any aisle was >= 75%)
        any_congested_steps = (timeseries_df[cong_cols] >= 75.0).any(axis=1).sum()
        congestion_duration_sec = float(any_congested_steps * time_step_seconds)

        # Worker exposure count (orders that were delayed or traversed during peak intervals)
        worker_exposure_count = delayed_orders_count
    else:
        avg_congestion = 0.0
        max_congestion = 0.0
        critical_events = 0
        high_events = 0
        affected_aisles_count = 0
        most_congested_aisle = "N/A"
        congestion_duration_sec = 0.0
        worker_exposure_count = 0

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
        "affected_aisles_count": affected_aisles_count,
        "most_congested_aisle": most_congested_aisle,
        "congestion_duration_sec": round(congestion_duration_sec, 1),
        "worker_exposure_count": worker_exposure_count,
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


def compute_hotspot_analysis(
    timeseries_df: pd.DataFrame,
    aisles_def: Optional[Dict] = None,
    time_step_seconds: float = 30.0
) -> pd.DataFrame:
    """
    Performs comprehensive hotspot analysis across all warehouse aisles.
    Identifies top congested aisles, frequency of critical/high events, and duration.
    """
    if aisles_def is None:
        aisles_def = DEFAULT_AISLES

    rows = []
    for aisle, info in aisles_def.items():
        cong_col = f"{aisle}_congestion"
        if cong_col in timeseries_df.columns:
            series = timeseries_df[cong_col]
            avg_c = float(series.mean())
            max_c = float(series.max())
            high_ev = int(((series >= 75.0) & (series < 100.0)).sum())
            crit_ev = int((series >= 100.0).sum())
            total_cong_time = float((high_ev + crit_ev) * time_step_seconds)
        else:
            avg_c, max_c, high_ev, crit_ev, total_cong_time = 0.0, 0.0, 0, 0, 0.0

        rows.append({
            "Aisle": aisle,
            "Zone": info["zone"],
            "Capacity": info["capacity"],
            "Average_Congestion_Pct": round(avg_c, 2),
            "Max_Congestion_Pct": round(max_c, 2),
            "High_Events_Count": high_ev,
            "Critical_Events_Count": crit_ev,
            "Total_Congestion_Events": high_ev + crit_ev,
            "Congestion_Duration_Sec": round(total_cong_time, 1)
        })

    df = pd.DataFrame(rows)
    # Sort descending by Critical_Events_Count then Average_Congestion_Pct
    df = df.sort_values(by=["Critical_Events_Count", "Total_Congestion_Events", "Average_Congestion_Pct"], ascending=False).reset_index(drop=True)
    return df


def generate_comparison_table(
    baseline_metrics: Dict[str, Any],
    controlled_metrics: Dict[str, Any]
) -> pd.DataFrame:
    """
    Constructs an honest, programmatically calculated comparison table.
    Shows Baseline, Controlled, Absolute Difference, and Percentage Improvement.
    Formula: ((baseline - controlled) / baseline) * 100 where lower is better.
    """
    kpis = [
        ("Average Congestion (%)", "avg_congestion_pct", "lower"),
        ("Maximum Congestion (%)", "max_congestion_pct", "lower"),
        ("Critical Congestion Events", "critical_events_count", "lower"),
        ("High Congestion Events", "high_events_count", "lower"),
        ("Affected Aisles Count", "affected_aisles_count", "lower"),
        ("Congestion Duration (s)", "congestion_duration_sec", "lower"),
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
