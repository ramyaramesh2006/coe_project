"""
run_experiments.py
Master execution script for Aisle Congestion Simulator and Wave-Release Controller.
Generates synthetic data, executes all 3 scenarios, performs sensitivity analysis,
saves CSV reports, and generates all 10 analytical plots into the results/ folder.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Headless execution
import matplotlib.pyplot as plt

# Ensure local package import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_generator import generate_warehouse_dataset, DEFAULT_AISLES
from src.scenarios import (
    run_normal_operation_scenario,
    run_peak_congestion_scenario,
    run_sensor_failure_scenario,
    run_sensitivity_analysis
)


def main():
    print("================================================================================")
    print("   AISLE CONGESTION SIMULATOR & WAVE-RELEASE CONTROLLER (REVIEW 1 PROTOTYPE)   ")
    print("================================================================================")

    # 1. Directories Setup
    os.makedirs("data", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    # 2. Generate and Save Baseline Simulation Dataset
    print("\n[Step 1/6] Generating initial synthetic warehouse dataset (120 workers, 350 orders)...")
    dataset_df = generate_warehouse_dataset(
        num_workers=120,
        num_orders=350,
        seed=42,
        scenario_name="Normal Operation"
    )
    data_path = os.path.join("data", "warehouse_simulation_data.csv")
    dataset_df.to_csv(data_path, index=False)
    print(f" -> Saved synthetic dataset to {data_path} ({len(dataset_df)} pick item records)")

    # 3. Scenario A: Normal Operation
    print("\n[Step 2/6] Executing Scenario A: Normal Operation...")
    res_normal = run_normal_operation_scenario(seed=42)
    m_norm = res_normal["metrics"]
    print(f" -> Normal Operation Metrics:")
    print(f"    - Avg Congestion: {m_norm['avg_congestion_pct']}% | Max Congestion: {m_norm['max_congestion_pct']}%")
    print(f"    - Throughput: {m_norm['throughput_orders_per_hr']} orders/hr")
    print(f"    - Avg Waiting Time: {m_norm['avg_waiting_time_sec']}s | Critical Events: {m_norm['critical_events_count']}")

    # 4. Scenario B: Peak Congestion (Baseline vs Controlled)
    print("\n[Step 3/6] Executing Scenario B: Peak Congestion (Baseline vs Controlled)...")
    res_peak = run_peak_congestion_scenario(seed=42, safe_threshold=75.0)
    comparison_df = res_peak["comparison_table"]
    comp_path = os.path.join("results", "baseline_vs_controlled.csv")
    comparison_df.to_csv(comp_path, index=False)
    print(f" -> Comparative Performance Results:")
    print(comparison_df.to_string(index=False))
    print(f" -> Saved comparative results to {comp_path}")

    # 5. Scenario C: Sensor / Network Failure
    print("\n[Step 4/6] Executing Scenario C: Sensor Failure (Manual Fallback Mode)...")
    res_failure = run_sensor_failure_scenario(seed=42, fallback_congestion=65.0)
    m_fail = res_failure["metrics"]
    print(f" -> System Status: {res_failure['system_status']} | Mode: {res_failure['mode']}")
    print(f"    - Simulation completed successfully with zero unhandled exceptions.")
    print(f"    - Handled {len(res_failure['controller_logs'])} wave controller dispatch decisions in fallback mode.")

    # 6. Sensitivity Analysis
    print("\n[Step 5/6] Executing Safe Threshold Sensitivity Analysis [60% to 90%]...")
    sens_df = run_sensitivity_analysis(thresholds=[60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0], seed=42)
    sens_path = os.path.join("results", "sensitivity_analysis.csv")
    sens_df.to_csv(sens_path, index=False)
    print(sens_df.to_string(index=False))
    print(f" -> Saved sensitivity analysis data to {sens_path}")

    # 7. Generate Visualizations
    print("\n[Step 6/6] Generating analytical visualization plots...")
    generate_all_plots(res_peak, sens_df)
    print(" -> All figures saved successfully to results/")

    print("\n================================================================================")
    print("                        SIMULATION EXECUTION COMPLETED                          ")
    print("================================================================================")


def generate_all_plots(res_peak: dict, sens_df: pd.DataFrame):
    """Generates the 10 required figures and saves them in results/."""
    base_ts = res_peak["baseline"]["timeseries"]
    ctrl_ts = res_peak["controlled"]["timeseries"]
    base_m = res_peak["baseline"]["metrics"]
    ctrl_m = res_peak["controlled"]["metrics"]

    aisle_names = list(DEFAULT_AISLES.keys())

    # 1. Congestion by Aisle (Mean & Max during Peak)
    plt.figure(figsize=(10, 5))
    base_means = [base_ts[f"{a}_congestion"].mean() for a in aisle_names]
    ctrl_means = [ctrl_ts[f"{a}_congestion"].mean() for a in aisle_names]
    x = np.arange(len(aisle_names))
    width = 0.35
    plt.bar(x - width/2, base_means, width, label="Baseline (Unregulated)", color="#d9534f")
    plt.bar(x + width/2, ctrl_means, width, label="Controlled (Wave-Release)", color="#5cb85c")
    plt.axhline(75.0, color="#f0ad4e", linestyle="--", label="Safe Threshold (75%)")
    plt.axhline(100.0, color="#d9534f", linestyle=":", label="Critical Threshold (100%)")
    plt.xlabel("Warehouse Aisle")
    plt.ylabel("Mean Congestion (%)")
    plt.title("Figure 1: Mean Congestion Across Warehouse Aisles (Peak Scenario)")
    plt.xticks(x, aisle_names)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/fig1_congestion_by_aisle.png", dpi=300)
    plt.close()

    # 2. Congestion Level Distribution (Time in each level for hotspot A03)
    plt.figure(figsize=(8, 5))
    categories = ["LOW (<50%)", "MEDIUM (50-75%)", "HIGH (75-100%)", "CRITICAL (>=100%)"]
    def get_distribution(ts_series):
        low = (ts_series < 50.0).mean() * 100
        med = ((ts_series >= 50.0) & (ts_series < 75.0)).mean() * 100
        high = ((ts_series >= 75.0) & (ts_series < 100.0)).mean() * 100
        crit = (ts_series >= 100.0).mean() * 100
        return [low, med, high, crit]

    base_dist = get_distribution(base_ts["A03_congestion"])
    ctrl_dist = get_distribution(ctrl_ts["A03_congestion"])
    x = np.arange(len(categories))
    plt.bar(x - width/2, base_dist, width, label="Baseline", color="#d9534f")
    plt.bar(x + width/2, ctrl_dist, width, label="Controlled", color="#5cb85c")
    plt.xlabel("Congestion Classification Level")
    plt.ylabel("Percentage of Operational Time (%)")
    plt.title("Figure 2: Congestion Level Distribution for Hotspot Aisle A03")
    plt.xticks(x, categories, rotation=15)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/fig2_congestion_distribution_a03.png", dpi=300)
    plt.close()

    # 3. Baseline vs Controlled Waiting Time
    plt.figure(figsize=(6, 5))
    bars = plt.bar(["Baseline", "Controlled"], [base_m["avg_waiting_time_sec"], ctrl_m["avg_waiting_time_sec"]],
                   color=["#337ab7", "#5cb85c"], width=0.5)
    plt.ylabel("Average Waiting Time (seconds)")
    plt.title("Figure 3: Worker Dispatch Waiting Time Comparison")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f"{yval:.1f} s", ha="center", va="bottom", fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/fig3_waiting_time_comparison.png", dpi=300)
    plt.close()

    # 4. Baseline vs Controlled Throughput
    plt.figure(figsize=(6, 5))
    bars = plt.bar(["Baseline", "Controlled"], [base_m["throughput_orders_per_hr"], ctrl_m["throughput_orders_per_hr"]],
                   color=["#337ab7", "#5cb85c"], width=0.5)
    plt.ylabel("Fulfillment Throughput (orders / hour)")
    plt.title("Figure 4: Warehouse Throughput Comparison")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.1f}", ha="center", va="bottom", fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/fig4_throughput_comparison.png", dpi=300)
    plt.close()

    # 5. Baseline vs Controlled Travel Distance
    plt.figure(figsize=(6, 5))
    bars = plt.bar(["Baseline", "Controlled"], [base_m["total_distance_m"], ctrl_m["total_distance_m"]],
                   color=["#337ab7", "#5cb85c"], width=0.5)
    plt.ylabel("Total Worker Travel Distance (meters)")
    plt.title("Figure 5: Total Worker Travel Distance Comparison")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 100, f"{yval:,.0f} m", ha="center", va="bottom", fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/fig5_distance_comparison.png", dpi=300)
    plt.close()

    # 6. Baseline vs Controlled Cost Breakdown
    plt.figure(figsize=(7, 5))
    cost_cats = ["Labor Cost", "Travel Cost", "Delay Cost", "Total Cost"]
    b_costs = [base_m["labor_cost_usd"], base_m["travel_cost_usd"], base_m["delay_cost_usd"], base_m["total_estimated_cost_usd"]]
    c_costs = [ctrl_m["labor_cost_usd"], ctrl_m["travel_cost_usd"], ctrl_m["delay_cost_usd"], ctrl_m["total_estimated_cost_usd"]]
    x = np.arange(len(cost_cats))
    plt.bar(x - width/2, b_costs, width, label="Baseline ($)", color="#d9534f")
    plt.bar(x + width/2, c_costs, width, label="Controlled ($)", color="#5cb85c")
    plt.xlabel("Cost Component")
    plt.ylabel("Estimated Cost ($ USD)")
    plt.title("Figure 6: Operational Cost Breakdown Comparison")
    plt.xticks(x, cost_cats)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/fig6_cost_breakdown.png", dpi=300)
    plt.close()

    # 7. Baseline vs Controlled Carbon Emissions
    plt.figure(figsize=(6, 5))
    bars = plt.bar(["Baseline", "Controlled"], [base_m["estimated_emissions_kg"], ctrl_m["estimated_emissions_kg"]],
                   color=["#337ab7", "#5cb85c"], width=0.5)
    plt.ylabel("Estimated Emissions (kg CO2e)")
    plt.title("Figure 7: Estimated Carbon Emissions Comparison")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.05, f"{yval:.3f} kg", ha="center", va="bottom", fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/fig7_emissions_comparison.png", dpi=300)
    plt.close()

    # 8. Sensitivity Analysis: Safe Threshold vs Waiting Time & Critical Events
    plt.figure(figsize=(9, 5))
    plt.plot(sens_df["safe_threshold_pct"], sens_df["avg_waiting_time_sec"], marker="o", color="#d9534f", label="Avg Waiting Time (s)", linewidth=2)
    plt.plot(sens_df["safe_threshold_pct"], sens_df["critical_events_count"], marker="s", color="#337ab7", label="Critical Events Count", linewidth=2)
    plt.xlabel("Safe Congestion Threshold (%)")
    plt.ylabel("Value (Seconds / Event Count)")
    plt.title("Figure 8: Sensitivity Analysis - Threshold vs Waiting Time & Critical Events")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/fig8_sensitivity_waiting_and_critical.png", dpi=300)
    plt.close()

    # 9. Sensitivity Analysis: Safe Threshold vs Throughput
    plt.figure(figsize=(8, 5))
    plt.plot(sens_df["safe_threshold_pct"], sens_df["throughput_orders_per_hr"], marker="^", color="#5cb85c", label="Throughput (orders/hr)", linewidth=2)
    plt.xlabel("Safe Congestion Threshold (%)")
    plt.ylabel("Throughput (orders / hour)")
    plt.title("Figure 9: Sensitivity Analysis - Threshold vs Warehouse Throughput")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/fig9_sensitivity_throughput.png", dpi=300)
    plt.close()

    # 10. Warehouse Aisle Grid Layout Map
    plt.figure(figsize=(8, 6))
    for aisle, info in DEFAULT_AISLES.items():
        gx, gy = info["grid"]
        pop = info["base_prob"]
        # Invert gy for intuitive top-down view
        color = "#d9534f" if pop >= 0.20 else ("#f0ad4e" if pop >= 0.08 else "#5bc0de")
        plt.scatter(gy, -gx, s=1200, c=color, edgecolors="black", linewidths=1.5, zorder=3)
        plt.text(gy, -gx, f"{aisle}\nCap:{info['capacity']}\nP:{pop:.2f}",
                 ha="center", va="center", color="white", fontweight="bold", fontsize=9)
    plt.xlim(-0.8, 3.8)
    plt.ylim(-2.8, 0.8)
    plt.title("Figure 10: Warehouse Aisle Grid Layout & Popularity Topology")
    plt.xlabel("Aisle Column Index (Grid X)")
    plt.ylabel("Aisle Row Index (Grid Y)")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig10_warehouse_grid_layout.png", dpi=300)
    plt.close()


if __name__ == "__main__":
    main()
