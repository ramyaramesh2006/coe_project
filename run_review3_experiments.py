"""Reproducible Review 3 experiment runner.

Run from repository root:
    python run_review3_experiments.py

All result CSVs are generated from the simulation at execution time. No result values
are hard-coded into this script.
"""
from pathlib import Path
import json
import pandas as pd

from src.scenarios import (
    run_normal_operation_scenario,
    run_peak_congestion_scenario,
    run_extreme_load_scenario,
    run_sensor_failure_scenario,
    run_telemetry_tamper_scenario,
    run_sensitivity_analysis,
    run_multirun_validation,
)

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
SEED = 42


def add_record(rows, scenario_name, mode, metrics, expected_orders=None, **extra):
    completed = int(metrics.get("num_orders", 0))
    requested = int(expected_orders if expected_orders is not None else completed)
    row = {
        "scenario": scenario_name,
        "mode": mode,
        "requested_orders": requested,
        "completed_orders": completed,
        "completion_reliability_pct": round(100.0 * completed / requested, 2) if requested else 0.0,
        "throughput_orders_per_hr": metrics.get("throughput_orders_per_hr"),
        "avg_waiting_time_sec": metrics.get("avg_waiting_time_sec"),
        "max_congestion_pct": metrics.get("max_congestion_pct"),
        "critical_events_count": metrics.get("critical_events_count"),
        "total_distance_m": metrics.get("total_distance_m"),
        "total_estimated_cost_usd": metrics.get("total_estimated_cost_usd"),
        "estimated_emissions_kg": metrics.get("estimated_emissions_kg"),
        "total_verification_overhead_sec": metrics.get("total_verification_overhead_sec"),
        "total_mispick_count": metrics.get("total_mispick_count"),
        "rerouted_orders_count": metrics.get("rerouted_orders_count"),
    }
    row.update(extra)
    rows.append(row)


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []

    normal = run_normal_operation_scenario(seed=SEED)
    add_record(rows, "Normal Operation", "CONTROLLED", normal["metrics"], 300)

    peak = run_peak_congestion_scenario(seed=SEED, safe_threshold=75.0)
    add_record(rows, "Peak Congestion", "BASELINE", peak["baseline"]["metrics"], 350)
    add_record(rows, "Peak Congestion", "CONTROLLED", peak["controlled"]["metrics"], 350)

    extreme = run_extreme_load_scenario(seed=SEED, safe_threshold=75.0)
    add_record(rows, "Extreme Load", "BASELINE", extreme["baseline"]["metrics"], 450)
    add_record(rows, "Extreme Load", "CONTROLLED", extreme["controlled"]["metrics"], 450)

    sensor_failure = run_sensor_failure_scenario(seed=SEED, fallback_congestion=65.0)
    add_record(rows, "Sensor / Network Failure", "MANUAL FALLBACK",
               sensor_failure["metrics"], 300,
               fallback_dispatches=len(sensor_failure["controller_logs"]))

    tamper = run_telemetry_tamper_scenario(seed=SEED, num_orders=300, tamper_fraction=0.10)
    add_record(rows, "Telemetry Tamper", "HMAC + FALLBACK + S&F",
               tamper["metrics"], 300,
               packets_checked=tamper["telemetry_summary"]["packets_checked"],
               packets_accepted=tamper["telemetry_summary"]["packets_accepted"],
               packets_rejected=tamper["telemetry_summary"]["packets_rejected"],
               queued_events=(tamper["store_and_forward_summary"] or {}).get("total_events_queued", 0),
               replayed_events=(tamper["store_and_forward_summary"] or {}).get("total_events_replayed", 0))

    summary = pd.DataFrame(rows)
    summary.to_csv(RESULTS / "review3_experiment_summary.csv", index=False)
    pd.DataFrame(tamper["telemetry_logs"]).to_csv(
        RESULTS / "review3_telemetry_audit.csv", index=False
    )
    pd.DataFrame(tamper["controller_logs"]).to_csv(
        RESULTS / "review3_tamper_controller_log.csv", index=False
    )

    sensitivity = run_sensitivity_analysis(
        thresholds=[60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0], seed=SEED
    )
    sensitivity.to_csv(RESULTS / "review3_sensitivity_analysis.csv", index=False)

    run_rows, multi_seed_summary = run_multirun_validation(
        seeds=[42, 101, 202, 303, 404], safe_threshold=75.0
    )
    run_rows.to_csv(RESULTS / "review3_multiseed_runs.csv", index=False)
    multi_seed_summary.to_csv(RESULTS / "review3_multiseed_summary.csv", index=False)

    metadata = {
        "seed": SEED,
        "multi_seed_validation": [42, 101, 202, 303, 404],
        "peak_safe_threshold_pct": 75.0,
        "telemetry_tamper_fraction": 0.10,
        "telemetry_hmac_key": "ephemeral simulation-only test key; not a production secret",
        "generated_files": [
            "review3_experiment_summary.csv",
            "review3_telemetry_audit.csv",
            "review3_tamper_controller_log.csv",
            "review3_sensitivity_analysis.csv",
            "review3_multiseed_runs.csv",
            "review3_multiseed_summary.csv",
        ],
    }
    (RESULTS / "review3_run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(summary.to_string(index=False))
    print(f"Review 3 experiment artifacts written to: {RESULTS}")


if __name__ == "__main__":
    main()
