# Testing Guide — Aisle Congestion Simulator & Wave-Release Controller

**Document:** Test Strategy, Coverage Rationale, and Execution Guide
**Review Stage:** Review 3 (100% Prototype Maturity)
**Total Tests:** 58 passing (100% pass rate)

---

## 1. Test Philosophy

Every test in this suite follows **three rules**:
1. **One assertion per concept** — each test proves exactly one behavioural invariant.
2. **Named error boundaries** — tests that probe edge conditions explicitly name the boundary in their docstring.
3. **Reproducibility** — all stochastic tests use a fixed seed so CI results are deterministic.

---

## 2. Test Suite Overview

| File | Tests | Module Tested | Layer |
|:---|:---:|:---|:---|
| `test_congestion.py` | 8 | `src/congestion.py` | Unit |
| `test_controller.py` | 8 | `src/controller.py` | Unit |
| `test_simulation.py` | 7 | `src/simulation.py` | Integration |
| `test_visual_similarity.py` | 22 | `src/visual_similarity.py`, `src/store_and_forward.py` | Unit + Integration |
| `test_error_boundaries.py` | 13 | All modules | Error boundary |
| **Total** | **58** | | |

---

## 3. How to Run

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run a specific file
```bash
python -m pytest tests/test_error_boundaries.py -v
```

### Run with coverage report
```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### Run only error-boundary tests
```bash
python -m pytest tests/test_error_boundaries.py -v -k "boundary or error or invalid"
```

---

## 4. Error Boundary Tests (`test_error_boundaries.py`)

These tests verify that every public function handles malformed, extreme, or missing input gracefully — either raising a specific exception or returning a safe default.

| Test | Boundary Probed | Expected Behaviour |
|:---|:---|:---|
| `test_zero_capacity_aisle` | capacity = 0 | Returns 0% congestion (guarded division) |
| `test_negative_workers` | workers_count < 0 | Treated as 0 (clamped) |
| `test_congestion_above_100_percent` | workers > capacity | Returns >100% (CRITICAL tier) |
| `test_unknown_aisle_visual_similarity` | aisle_id not in catalogue | Falls back to oil_filters defaults |
| `test_empty_orders_dataframe` | 0 orders passed to simulation | Returns empty DataFrame, no crash |
| `test_simulation_single_order` | 1 order, 1 worker | Produces valid single-row result |
| `test_wave_release_all_blocked` | all aisles at 100%+ | All decisions = BLOCK |
| `test_sensor_failure_fallback_range` | fallback_congestion outside [0,100] | Clamps to valid range |
| `test_saf_enqueue_while_online` | enqueue called without report_network_down | Raises RuntimeError |
| `test_saf_drain_empty_queue` | drain() on empty queue | Returns empty list, no error |
| `test_network_monitor_zero_duration` | mean_outage_duration = 0 | Generates zero-length outages safely |
| `test_metrics_missing_columns` | orders_df without new Review 2 cols | Falls back to 0 for mispick KPIs |
| `test_rerouting_all_aisles_blocked` | reroute_threshold_pct = 0 (all blocked) | Falls back to original path order |

---

## 5. Unit Tests

### `test_congestion.py` — Congestion Engine

| Test | Boundary / Invariant |
|:---|:---|
| `test_normal_congestion_calculation` | Basic ratio: 2 workers / capacity 4 = 50% |
| `test_over_capacity_exceeds_100_percent` | 5 workers / capacity 3 = 166.7% (CRITICAL) |
| `test_zero_and_negative_capacity_handling` | capacity ≤ 0 → returns 0.0, no ZeroDivisionError |
| `test_missing_and_negative_worker_values` | workers < 0 → clamped to 0 |
| `test_sensor_blackout_returns_fallback` | sensor_available=False → returns fallback_pct |
| `test_congestion_classification_boundaries` | Tier boundaries: 0/50/75/100% |
| `test_congestion_classification_custom_thresholds` | Custom threshold dict overrides defaults |
| `test_congestion_classification_invalid_inputs` | NaN / None input → raises ValueError |

### `test_controller.py` — Wave-Release Controller

| Test | Boundary / Invariant |
|:---|:---|
| `test_controller_allow_decision` | Congestion < safe_threshold → ALLOW |
| `test_controller_delay_decision` | safe_threshold ≤ congestion < 100% → DELAY |
| `test_controller_critical_congestion_block` | Congestion ≥ 100% → BLOCK regardless of retries |
| `test_controller_exact_threshold_boundary` | Congestion = safe_threshold exactly → DELAY (boundary inclusive) |
| `test_controller_just_below_and_above_boundary` | ±0.01% around threshold → correct side |
| `test_controller_exact_critical_boundary` | Congestion = 100.0 exactly → BLOCK |
| `test_controller_sensor_failure_fallback` | sensor_available=False → MANUAL FALLBACK mode |
| `test_controller_multi_worker_request` | Multiple concurrent requests → correct per-aisle decisions |

---

## 6. Integration Tests (`test_simulation.py`)

| Test | What it validates |
|:---|:---|
| `test_distance_calculation_accuracy` | Euclidean centroid distances match expected geometry |
| `test_waiting_time_non_negative` | All waiting_time values ≥ 0 (no negative wait) |
| `test_simulation_reproducibility` | Same seed → identical results across two runs |
| `test_hotspot_analysis_structure` | hotspot DataFrame has required columns |
| `test_low_load_scenario_metrics` | Low-load: avg_congestion < 50%, no critical events |
| `test_extreme_load_scenario_stress` | Extreme-load: critical events > 0, system does not crash |
| `test_multirun_validation_statistics` | 5-seed σ < 5% for throughput (statistical stability) |

---

## 7. CI / Reproducibility

- All tests run in < 30 seconds on a standard laptop.
- Fixed seeds (`seed=42` default, multi-seed: 42/101/202/303/404) ensure deterministic output.
- No network calls, no file I/O side-effects (S&F spool writes to `results/` which is gitignored during tests).
- Compatible: Python 3.9, 3.10, 3.11, 3.12, 3.13.
