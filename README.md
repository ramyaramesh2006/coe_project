# Aisle Congestion Simulator and Wave-Release Controller

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-CI%20validation%20pending-lightgrey.svg)]()
[![Stage: Review 3 Implementation](https://img.shields.io/badge/Stage-Review%203%20Implementation-orange.svg)]()

A discrete-event simulation system and intelligent wave-release dispatching controller developed to analyze, mitigate, and control physical aisle congestion in **automotive parts distribution warehouses containing visually similar components**.

---

> **Review 2 baseline:**  
> Three Review 1 mandated improvements fully implemented:  
> (1) Visual-similarity-aware pick model · (2) Store-and-forward offline queue · (3) Formal risk register + stakeholder assumptions.  
> The Review 2 baseline includes scenarios A–H, visual-similarity modelling, store-and-forward queuing, and dynamic rerouting. The test guide records 58 pre-Review-3 tests.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Review 2 Improvements](#review-2-improvements)
- [Review 3 Additions](#review-3-additions)
- [Review 3 Additions](#review-3-additions)
- [Architecture](#architecture)
- [Modules](#modules)
- [Scenarios](#scenarios)
- [Example Results](#example-results)
- [Project Structure](#project-structure)
- [How to Run](#how-to-run)
- [Testing](#testing)
- [Documentation](#documentation)
- [Limitations](#limitations)

---

## Project Overview

In automotive distribution centers, order pickers travel through physical warehouse aisles to retrieve **visually similar components** (e.g., brake calipers, oil filters, engine gaskets). When order release is unregulated, picker traffic concentrates in popular aisles, causing physical gridlock, idle time, mispick errors, and fulfillment delays.

This project implements a **discrete-event simulation model** combined with a **closed-loop wave-release controller** that:
1. Dynamically regulates order dispatches based on real-time aisle density thresholds
2. Models pick verification overhead and mispick returns from visually similar parts
3. Gracefully degrades to store-and-forward offline queuing during sensor/network failures
4. Dynamically reroutes workers around critically congested aisles

---

## Review 2 Improvements

### 1. Visual Similarity Domain Model (`src/visual_similarity.py`)
- **12-part automotive catalogue** with `similarity_risk` (0.50–0.90), `verification_extra_sec`, `mispick_probability`
- **A03 (brake pads):** 0.90 risk · 18 s verification overhead · 12% mispick probability
- **A07 (spark plugs):** 0.80 risk · 12 s verification overhead · 9% mispick probability
- **Pick-time model:** base + Gaussian verification overhead + probabilistic mispick return penalty (avg 45 s)
- **Expected dwell increase:** A03 = +93% longer dwell vs. uniform baseline

### 2. Store-and-Forward Offline Queue (`src/store_and_forward.py`)
- **`StoreAndForwardQueue`:** FIFO in-memory queue + CSV spool (audit trail) for decisions during outages
- **`NetworkStateMonitor`:** Poisson outage schedule simulation; `is_online(sim_time)` for each tick
- **Reconnection Replay:** Reconciles queued decisions against real-time state → CONFIRMED / OVERRIDDEN
- **Result:** S&F reduces network-outage throughput penalty by ~75% vs total-failure mode

### 3. Formal Documentation (`docs/`)
- **`docs/RISK_REGISTER.md`:** 14 risks with L×I scoring, heat map, mitigation strategies
- **`docs/STAKEHOLDER_ASSUMPTIONS.md`:** 22 assumptions across 5 categories, stakeholder map, decision-changing assumption analysis

---

## Review 3 Additions

### Timestamped worker movement
`WarehouseSimulation.get_movement_trace()` exposes travel and pick segments with worker/order IDs, simulation timestamps, and start/end grid coordinates. The trace feeds the 2D floor dashboard.

### Interactive 2D floor dashboard
Install optional dependencies with `pip install -r requirements-dashboard.txt`, then run `streamlit run dashboard/app.py`. Select Normal, Peak, or Extreme load, toggle wave-release control, and scrub simulation time to inspect worker movement and aisle congestion. Run `python run_review3_experiments.py` to generate the baseline/controlled, failure, telemetry-tamper, sensitivity, and multi-seed CSV evidence under `results/`.

### Telemetry integrity component
`src/telemetry_security.py` provides HMAC-SHA256 signing, constant-time signature verification, packet freshness checks, and nonce-based replay detection. This is a simulation-layer security component; it does not replace TLS, device identity, secure key provisioning, or a live MQTT deployment.

## Architecture

```
Input: Synthetic Orders + Worker Pool + Warehouse Grid (12 aisles, 3 zones)
    ↓
Visual Similarity Model ──────────────────────────────────────────────────────┐
  Part Catalogue → similarity_risk, verification_overhead, mispick_prob        │
    ↓                                                                          │
Network State Monitor                                                           │
  Poisson outage schedule → is_online(sim_time) → ONLINE / OFFLINE             │
    ↓                                                                          │
Wave-Release Controller                                                         │
  ONLINE: live occupancy-based ALLOW / DELAY / BLOCK                           │
  OFFLINE: fallback estimate → enqueue to Store-and-Forward queue              │
    ↓                                                                          │
Store-and-Forward Queue                                                         │
  Offline: buffer events → CSV spool (audit trail)                             │
  On reconnect: replay + reconcile (CONFIRMED / OVERRIDDEN)                   │
    ↓                                                                          │
Warehouse Execution Engine ←─────────────────────────────────────────────────┘
  Dynamic A* Rerouting: bypass aisles ≥ 90% congested
  Visual-similarity pick times: base + verification + mispick penalty
  Discrete-event interval occupancy tracking
    ↓
Performance Analysis Engine
  Throughput · Delays · Cost (+ mispick cost) · Emissions · Mispick KPIs
    ↓
Scenarios A–H: 8 operating conditions
```

---

## Modules

| File | Description |
|:---|:---|
| `src/data_generator.py` | 12-aisle grid layout, skewed popularity, synthetic orders (120 workers, 350 orders) |
| `src/congestion.py` | Guarded congestion calculation + 4-tier classification (LOW/MEDIUM/HIGH/CRITICAL) |
| `src/controller.py` | Wave-release controller: ALLOW/DELAY/BLOCK + MANUAL FALLBACK pacing |
| `src/simulation.py` | Discrete-event engine: visual-similarity pick times, S&F integration, A* rerouting, timestamped movement trace |
| `src/visual_similarity.py` | **[NEW Rev 2]** Part catalogue, pick-time model, mispick simulation |
| `src/store_and_forward.py` | **[NEW Rev 2]** S&F queue, replay engine, network outage monitor |
| `src/telemetry_security.py` | **[NEW Rev 3]** HMAC-SHA256 telemetry integrity, freshness, and replay checks |
| `src/telemetry_security.py` | **[NEW Rev 3]** HMAC-SHA256 telemetry integrity, freshness, replay checks |
| `src/metrics.py` | KPIs: throughput, cost, emissions, mispick count, verification overhead |
| `src/scenarios.py` | 8 scenarios: Low Load → Extreme Load + S&F + Visual Similarity + Rerouting |

---

## Scenarios

| ID | Scenario | Description | Mode |
|:---:|:---|:---|:---:|
| A | Low Load | 60 workers, 180 orders, off-peak traffic | CONTROLLED |
| B | Normal Operation | 100 workers, 300 orders, standard flow | CONTROLLED |
| C | Peak Congestion | 120 workers, 350 orders, 2.8× hotspot · Baseline vs Controlled | BOTH |
| D | Extreme Load | 150 workers, 450 orders, stress test | BOTH |
| E | Sensor Failure | Total telemetry blackout · Manual fallback | FALLBACK |
| F | **Store-and-Forward** | Intermittent outages · S&F queue active · 3-way comparison | BOTH |
| G | **Visual Similarity Impact** | Without vs. with domain-accurate pick times | BOTH |
| H | **Dynamic Rerouting** | Fixed path vs. A*-based congestion bypass | BOTH |

---

## Example Results

### Baseline vs Controlled (Peak Load, Seed=42)
- **Critical Congestion Events:** Reduced from 138 → 132 (−4.35%)
- **Throughput:** Maintained at 200.83 orders/hr (0% degradation)
- **Mispick Events:** ~35 per shift · \$133 mispick cost modelled
- **S&F Throughput Penalty:** < 2% vs always-online mode

### Visual Similarity Impact (Scenario G)
- **A03 Expected Dwell:** 73.5 s (vs. 38 s baseline) — +93% dwell increase
- **Verification Overhead:** ~4,280 s total per 350-order shift
- **Mispick Rate:** ~10.9% of orders experience at least one mispick

### Store-and-Forward (Scenario F)
- **Outages Simulated:** ~4 per 2-hour shift (Poisson, λ=900 s)
- **Reconciliation Accuracy:** ~88% CONFIRMED, ~12% OVERRIDDEN
- **Throughput Penalty:** Only −2% vs always-online (vs. −8% for total failure)

---

## Project Structure

```
coe_project/
├── Aisle_Congestion_Simulator.ipynb
├── README.md
├── requirements.txt
├── requirements-dashboard.txt
├── run_experiments.py
├── run_review3_experiments.py
├── dashboard/
│   └── app.py
├── data/
├── src/
│   ├── data_generator.py
│   ├── congestion.py
│   ├── controller.py
│   ├── simulation.py
│   ├── visual_similarity.py
│   ├── store_and_forward.py
│   ├── telemetry_security.py
│   ├── metrics.py
│   └── scenarios.py
├── tests/
│   ├── test_congestion.py
│   ├── test_controller.py
│   ├── test_simulation.py
│   ├── test_visual_similarity.py
│   ├── test_error_boundaries.py
│   ├── test_movement_trace.py
│   ├── test_telemetry_security.py
│   └── test_telemetry_integration.py
├── results/
└── docs/
    ├── Review_1_Report.md
    ├── Review_2_Report.md
    ├── PROJECT_STATUS.md
    ├── RISK_REGISTER.md
    ├── STAKEHOLDER_ASSUMPTIONS.md
    └── STAKEHOLDER_VALIDATION.md
```

---
 
## How to Run

1. **Create Environment & Install Dependencies:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

2. **Run All Experiments:**
   ```bash
   python run_experiments.py
   ```

3. **Run New Review 2 Scenarios:**
   ```python
   from src.scenarios import (
       run_store_and_forward_scenario,
       run_visual_similarity_impact_scenario,
       run_dynamic_rerouting_scenario,
   )
   res_f = run_store_and_forward_scenario(seed=42)
   res_g = run_visual_similarity_impact_scenario(seed=42)
   res_h = run_dynamic_rerouting_scenario(seed=42)
   ```

4. **Launch Jupyter Notebook:**
   ```bash
   jupyter notebook Aisle_Congestion_Simulator.ipynb
   ```

---

## Testing

Run the full suite with:

```bash
python -m pytest tests/ -v
```

The Review 2 source suite contains 62 test functions (8 congestion, 8 controller, 7 simulation, 22 visual-similarity, and 17 error-boundary tests). Review 3 adds 13 tests (2 movement trace, 8 HMAC security, and 3 telemetry integration), for an expected total of 75. GitHub Actions run #31 confirmed **75 passed in 3.19 seconds** on Python 3.11. The expanded experiment and dashboard checks are being added to the next CI run.

| Test File | Count | Description |
|:---|:---:|:---|
| `test_congestion.py` | 8 | Calculation, classification, edge cases |
| `test_controller.py` | 8 | ALLOW/DELAY/BLOCK, boundaries, fallback |
| `test_simulation.py` | 7 | Geometry, multirun, scenario integration |
| `test_visual_similarity.py` | 22 | Part catalogue, pick model, S&F, rerouting |
| `test_error_boundaries.py` | 17 | Defensive and error-boundary tests |
| `test_movement_trace.py` | 2 | Timestamped worker movement segments |
| `test_telemetry_security.py` | 8 | HMAC, tamper, freshness, replay checks |
| `test_telemetry_integration.py` | 3 | Authenticated sensor data, fallback, S&F integration |

## Documentation

| Document | Description |
|:---|:---|
| [`docs/Review_1_Report.md`](docs/Review_1_Report.md) | Review 1 findings and empirical results |
| [`docs/Review_2_Report.md`](docs/Review_2_Report.md) | Review 2 improvements, new scenarios, updated results |
| [`docs/RISK_REGISTER.md`](docs/RISK_REGISTER.md) | 14-entry formal risk register (L×I matrix, mitigations) |
| [`docs/STAKEHOLDER_ASSUMPTIONS.md`](docs/STAKEHOLDER_ASSUMPTIONS.md) | 22 assumptions, stakeholder map, decision-change analysis |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | Quick-reference prototype status |
| [`docs/Review_3_Report.md`](docs/Review_3_Report.md) | Review 3 implementation, evidence, and remaining validation |
| [`docs/STAKEHOLDER_VALIDATION.md`](docs/STAKEHOLDER_VALIDATION.md) | Walkthrough and blank feedback evidence template |

---

## Limitations

1. **Constant Walking Speed:** 1.0 m/s; no cart acceleration or turning inertia modelled.
2. **Static Part-Aisle Mapping:** SKU location reassignments are not dynamically tracked.
3. **No Physical Gating Enforcement:** Worker compliance is assumed; badge-gate hardware is not integrated.
4. **No Live Sensor/MQTT Deployment:** HMAC signing, freshness, and replay checks are implemented as a simulation-layer component; live device provisioning and broker integration remain future work.
5. **No Physical Pilot / AGV Integration:** The dashboard uses synthetic simulation data; warehouse pilot validation and AGV/MAPF integration are not implemented.
6. **No ML Wave Batching:** Current order release remains rule/threshold based; predictive batching remains future work.
7. **Centroid Coordinates:** Distances model aisle centrelines, not individual shelf faces.
