"""
run_experiments.py
Master execution pipeline for Aisle Congestion Simulator and Wave-Release Controller.
Generates multi-load datasets (Low, Normal, Peak, Extreme), executes baseline vs controlled runs,
runs hotspot analytics, multi-seed statistical validation (5 seeds), and threshold sensitivity sweeps.
Exports consolidated CSV reports and 10 publication-quality analytical figures to results/.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

# Ensure local package import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_generator import generate_warehouse_dataset, DEFAULT_AISLES
from src.metrics import compute_hotspot_analysis
from src.scenarios import (
    run_low_load_scenario,
    run_normal_operation_scenario,
    run_peak_congestion_scenario,
    run_extreme_load_scenario,
    run_sensor_failure_scenario,
    run_multi_load_experiments,
    run_sensitivity_analysis,
    run_multirun_validation
)


def main():
    print("================================================================================")
    print(" AISLE CONGESTION SIMULATOR & WAVE-RELEASE CONTROLLER (MATURITY: ~40-42%)       ")
    print("================================================================================")

    os.makedirs("data", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    # 1. Generate & Save Master Dataset
    print("\n[Step 1/7] Generating synthetic warehouse dataset (120 workers, 350 orders)...")
    master_df = generate_warehouse_dataset(num_workers=120, num_orders=350, seed=42)
    master_path = os.path.join("data", "warehouse_simulation_data.csv")
    master_df.to_csv(master_path, index=False)
    print(f" -> Saved master dataset to {master_path} ({len(master_df)} pick item records)")

    # 2. Multi-Load Scenario Experiments (Low, Normal, Peak, Extreme)
    print("\n[Step 2/7] Executing Multi-Load Scenarios (Low, Normal, Peak, Extreme)...")
    multi_load_df = run_multi_load_experiments(seed=42)
    multi_path = os.path.join("results", "multi_scenario_comparison.csv")
    multi_load_df.to_csv(multi_path, index=False)
    print(" -> Multi-Load Comparison Summary:")
    print(multi_load_df[["Scenario", "Mode", "Throughput_ord_hr", "Avg_Waiting_Sec", "Critical_Events", "Total_Cost_USD"]].to_string(index=False))
    print(f" -> Saved multi-load comparison to {multi_path}")

    # 3. Peak Congestion Scenario & Hotspot Analysis
    print("\n[Step 3/7] Executing Peak Congestion Scenario & Dedicated Hotspot Analysis...")
    res_peak = run_peak_congestion_scenario(seed=42, safe_threshold=75.0)
    comp_df = res_peak["comparison_table"]
    comp_path = os.path.join("results", "baseline_vs_controlled.csv")
    comp_df.to_csv(comp_path, index=False)
    print(f" -> Saved Baseline vs Controlled comparison to {comp_path}")

    hotspot_df = res_peak["hotspot_table"]
    hotspot_path = os.path.join("results", "hotspot_analysis.csv")
    hotspot_df.to_csv(hotspot_path, index=False)
    print("\n -> Dedicated Hotspot Analysis (Top Congested Aisles):")
    print(hotspot_df[["Aisle", "Zone", "Capacity", "Average_Congestion_Pct", "Max_Congestion_Pct", "Critical_Events_Count"]].head(5).to_string(index=False))
    print(f" -> Saved hotspot analysis to {hotspot_path}")

    # 4. Sensor Failure & Fallback Mode
    print("\n[Step 4/7] Executing Sensor / Network Failure Scenario (Manual Fallback)...")
    res_fail = run_sensor_failure_scenario(seed=42, fallback_congestion=65.0)
    print(f" -> Status: {res_fail['system_status']} | Mode: {res_fail['mode']}")
    print(f" -> Handled {len(res_fail['controller_logs'])} dispatches safely with conservative fallback rules.")

    # 5. Safe Threshold Sensitivity Sweep
    print("\n[Step 5/7] Executing Threshold Sensitivity Sweep [60% - 90%]...")
    sens_df = run_sensitivity_analysis(thresholds=[60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0], seed=42)
    sens_path = os.path.join("results", "sensitivity_analysis.csv")
    sens_df.to_csv(sens_path, index=False)
    print(sens_df[["safe_threshold_pct", "allow_decisions", "delay_decisions", "block_decisions", "avg_waiting_time_sec", "critical_events_count"]].to_string(index=False))
    print(f" -> Saved sensitivity analysis to {sens_path}")

    # 6. Multi-Seed Statistical Validation (5 Seeds)
    print("\n[Step 6/7] Executing Multi-Run Statistical Validation across 5 seeds...")
    seeds = [42, 101, 202, 303, 404]
    runs_df, multirun_summary_df = run_multirun_validation(seeds=seeds, safe_threshold=75.0)
    multirun_path = os.path.join("results", "multirun_validation.csv")
    multirun_summary_df.to_csv(multirun_path, index=False)
    print(" -> Multi-Seed Statistical Summary (Mean ± Std):")
    print(multirun_summary_df.to_string(index=False))
    print(f" -> Saved multi-run validation to {multirun_path}")

    # 7. Generate All 10 Analytical Visualizations
    print("\n[Step 7/7] Generating all 10 analytical visualization figures in results/...")
    generate_all_plots(multi_load_df, res_peak, hotspot_df, sens_df, runs_df, multirun_summary_df)
    print(" -> All 10 analytical plots successfully created.")

    print("\n================================================================================")
    print("                PROTOTYPE EXPERIMENTS COMPLETED SUCCESSFULLY                    ")
    print("================================================================================")


def generate_all_plots(multi_load_df, res_peak, hotspot_df, sens_df, runs_df, multirun_summary_df):
    """Renders 10 purposeful analytical plots using Matplotlib."""

    # 1. Congestion by Scenario
    plt.figure(figsize=(9, 5))
    scenarios = multi_load_df["Scenario"].tolist()
    max_congs = multi_load_df["Max_Congestion_Pct"].tolist()
    colors = ["#5bc0de", "#337ab7", "#f0ad4e", "#5cb85c", "#d9534f", "#993333"]
    bars = plt.bar(scenarios, max_congs, color=colors[:len(scenarios)], width=0.55)
    plt.axhline(100.0, color="red", linestyle="--", label="Critical Saturation Limit (100%)")
    plt.ylabel("Maximum Aisle Congestion (%)")
    plt.title("Figure 1: Maximum Congestion by Operating Load Scenario")
    plt.xticks(rotation=20, ha="right")
    plt.legend()
    for b in bars:
        y = b.get_height()
        plt.text(b.get_x() + b.get_width()/2.0, y + 3, f"{y:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=9)
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig1_congestion_by_scenario.png", dpi=300)
    plt.close()

    # 2. Critical Events by Scenario
    plt.figure(figsize=(9, 5))
    crit_events = multi_load_df["Critical_Events"].tolist()
    bars = plt.bar(scenarios, crit_events, color=colors[:len(scenarios)], width=0.55)
    plt.ylabel("Critical Congestion Events Count")
    plt.title("Figure 2: Critical Congestion Bottleneck Events by Scenario")
    plt.xticks(rotation=20, ha="right")
    for b in bars:
        y = b.get_height()
        plt.text(b.get_x() + b.get_width()/2.0, y + 2, f"{int(y)}", ha="center", va="bottom", fontweight="bold")
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig2_critical_events_by_scenario.png", dpi=300)
    plt.close()

    # 3. Throughput Comparison
    plt.figure(figsize=(9, 5))
    throughputs = multi_load_df["Throughput_ord_hr"].tolist()
    bars = plt.bar(scenarios, throughputs, color=colors[:len(scenarios)], width=0.55)
    plt.ylabel("Throughput (orders / hour)")
    plt.title("Figure 3: Warehouse Order Fulfillment Throughput across Scenarios")
    plt.xticks(rotation=20, ha="right")
    for b in bars:
        y = b.get_height()
        plt.text(b.get_x() + b.get_width()/2.0, y + 2, f"{y:.1f}", ha="center", va="bottom", fontweight="bold")
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig3_throughput_comparison.png", dpi=300)
    plt.close()

    # 4. Waiting-Time Comparison
    plt.figure(figsize=(9, 5))
    waits = multi_load_df["Avg_Waiting_Sec"].tolist()
    bars = plt.bar(scenarios, waits, color=colors[:len(scenarios)], width=0.55)
    plt.ylabel("Average Dispatch Waiting Time (seconds)")
    plt.title("Figure 4: Average Worker Staging Delay Across Operating Scenarios")
    plt.xticks(rotation=20, ha="right")
    for b in bars:
        y = b.get_height()
        plt.text(b.get_x() + b.get_width()/2.0, y + 0.3, f"{y:.2f}s", ha="center", va="bottom", fontweight="bold")
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig4_waiting_time_comparison.png", dpi=300)
    plt.close()

    # 5. Baseline vs Controlled (Key Metrics in Peak)
    base_m = res_peak["baseline"]["metrics"]
    ctrl_m = res_peak["controlled"]["metrics"]
    labels = ["Critical Events", "Avg Wait (s)", "Throughput (ord/hr)", "Cost ($/10)"]
    base_vals = [base_m["critical_events_count"], base_m["avg_waiting_time_sec"], base_m["throughput_orders_per_hr"], base_m["total_estimated_cost_usd"]/10.0]
    ctrl_vals = [ctrl_m["critical_events_count"], ctrl_m["avg_waiting_time_sec"], ctrl_m["throughput_orders_per_hr"], ctrl_m["total_estimated_cost_usd"]/10.0]
    x = np.arange(len(labels))
    width = 0.35
    plt.figure(figsize=(9, 5))
    plt.bar(x - width/2, base_vals, width, label="Baseline (Unregulated)", color="#d9534f")
    plt.bar(x + width/2, ctrl_vals, width, label="Controlled (Wave-Release)", color="#5cb85c")
    plt.xticks(x, labels)
    plt.ylabel("Metric Values (Normalized)")
    plt.title("Figure 5: Baseline vs. Controlled Performance Comparison (Peak Scenario)")
    plt.legend()
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig5_baseline_vs_controlled.png", dpi=300)
    plt.close()

    # 6. Hotspot Aisle Analysis
    top_aisles = hotspot_df.head(6)
    plt.figure(figsize=(9, 5))
    x = np.arange(len(top_aisles))
    plt.bar(x - width/2, top_aisles["Average_Congestion_Pct"], width, label="Mean Congestion (%)", color="#337ab7")
    plt.bar(x + width/2, top_aisles["Max_Congestion_Pct"], width, label="Max Congestion (%)", color="#d9534f")
    plt.axhline(100.0, color="red", linestyle="--", label="Critical 100%")
    plt.xticks(x, [f"{r['Aisle']} (Cap:{r['Capacity']})" for _, r in top_aisles.iterrows()])
    plt.ylabel("Congestion Percentage (%)")
    plt.title("Figure 6: Dedicated Hotspot Analysis - Top Congested Aisles")
    plt.legend()
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig6_hotspot_aisle_analysis.png", dpi=300)
    plt.close()

    # 7. Threshold Sensitivity
    plt.figure(figsize=(9, 5))
    plt.plot(sens_df["safe_threshold_pct"], sens_df["avg_waiting_time_sec"], marker="o", color="#d9534f", label="Avg Waiting Time (s)", linewidth=2)
    plt.plot(sens_df["safe_threshold_pct"], sens_df["critical_events_count"], marker="s", color="#337ab7", label="Critical Events Count", linewidth=2)
    plt.xlabel("Safe Congestion Threshold (%)")
    plt.ylabel("Value (Seconds / Events)")
    plt.title("Figure 7: Safe Threshold Sensitivity Analysis (Trade-off Curve)")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig7_threshold_sensitivity.png", dpi=300)
    plt.close()

    # 8. ALLOW/DELAY/BLOCK Distribution across Thresholds
    plt.figure(figsize=(9, 5))
    thresh_labels = [f"{t}%" for t in sens_df["safe_threshold_pct"]]
    x = np.arange(len(thresh_labels))
    plt.bar(x, sens_df["allow_decisions"], label="ALLOW", color="#5cb85c")
    plt.bar(x, sens_df["delay_decisions"], bottom=sens_df["allow_decisions"], label="DELAY", color="#f0ad4e")
    plt.bar(x, sens_df["block_decisions"], bottom=sens_df["allow_decisions"] + sens_df["delay_decisions"], label="BLOCK", color="#d9534f")
    plt.xlabel("Safe Congestion Threshold")
    plt.ylabel("Dispatch Decision Counts")
    plt.title("Figure 8: Wave Controller Decision Breakdown (ALLOW vs DELAY vs BLOCK)")
    plt.xticks(x, thresh_labels)
    plt.legend()
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig8_controller_decisions_distribution.png", dpi=300)
    plt.close()

    # 9. Worker Load vs Congestion Time-Series (Peak Hotspot A03)
    base_ts = res_peak["baseline"]["timeseries"]
    ctrl_ts = res_peak["controlled"]["timeseries"]
    plt.figure(figsize=(10, 5))
    plt.plot(base_ts["timestamp_sec"]/60.0, base_ts["A03_congestion"], label="Baseline Congestion", color="#d9534f", alpha=0.8)
    plt.plot(ctrl_ts["timestamp_sec"]/60.0, ctrl_ts["A03_congestion"], label="Controlled Congestion", color="#5cb85c", alpha=0.8)
    plt.axhline(100.0, color="red", linestyle="--", label="Critical Saturation")
    plt.xlabel("Simulation Elapsed Time (minutes)")
    plt.ylabel("Aisle A03 Congestion (%)")
    plt.title("Figure 9: Dynamic Congestion Profile over Time (Hotspot Aisle A03)")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig9_worker_load_vs_congestion.png", dpi=300)
    plt.close()

    # 10. Multi-Run Statistical Variability (5 Seeds)
    plt.figure(figsize=(9, 5))
    seeds_x = [f"Seed {s}" for s in runs_df["seed"]]
    x = np.arange(len(seeds_x))
    plt.bar(x - width/2, runs_df["base_critical_events"], width, label="Baseline Critical Events", color="#d9534f")
    plt.bar(x + width/2, runs_df["ctrl_critical_events"], width, label="Controlled Critical Events", color="#5cb85c")
    plt.xticks(x, seeds_x)
    plt.ylabel("Critical Events Count")
    mean_b = multirun_summary_df.loc[multirun_summary_df["Metric"] == "base_critical_events", "Mean"].values[0]
    mean_c = multirun_summary_df.loc[multirun_summary_df["Metric"] == "ctrl_critical_events", "Mean"].values[0]
    plt.axhline(mean_b, color="#d9534f", linestyle=":", label=f"Baseline Mean ({mean_b:.1f})")
    plt.axhline(mean_c, color="#5cb85c", linestyle=":", label=f"Controlled Mean ({mean_c:.1f})")
    plt.title("Figure 10: Multi-Seed Statistical Stability (Seeds: 42, 101, 202, 303, 404)")
    plt.legend()
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig("results/fig10_multirun_variability.png", dpi=300)
    plt.close()


if __name__ == "__main__":
    main()
