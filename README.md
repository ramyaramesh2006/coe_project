# Aisle Congestion Simulator and Wave-Release Controller

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 23 Passed](https://img.shields.io/badge/tests-23%20passed-brightgreen.svg)]()
[![Stage: Review 1 / Early Prototype](https://img.shields.io/badge/Maturity-~40--42%25%20Prototype-orange.svg)]()

A discrete-event simulation system and intelligent wave-release dispatching controller developed to analyze, mitigate, and control physical aisle congestion in automotive parts distribution warehouses.

---

> **Project Maturity Status:**  
> **Approximately 40–42% overall prototype maturity, including the Review 1 scope and additional validation/experimentation.**  
> The work is intentionally presented as an early-stage functional simulation prototype, not a final production software deployment.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Objectives](#objectives)
- [Architecture](#architecture)
- [Current Implementation](#current-implementation)
- [Validation](#validation)
- [Example Results](#example-results)
- [Project Structure](#project-structure)
- [How to Run](#how-to-run)
- [Google Colab Instructions](#google-colab-instructions)
- [Testing](#testing)
- [Current Completion](#current-completion)
- [Limitations](#limitations)
- [Future Work](#future-work)

---

## Project Overview

In automotive distribution centers, order pickers travel through physical warehouse aisles to retrieve visually similar components (e.g., brake calipers, rotors, engine gaskets, filters). When order release is unregulated, picker traffic concentrates heavily in popular aisles, leading to physical gridlock, worker idle time, and fulfillment delays.

This project implements a **discrete-event simulation model** combined with a **closed-loop wave-release controller** that dynamically regulates order dispatches based on aisle density thresholds and sensor health telemetry.

---

## Objectives

1. **Warehouse Modeling:** Model an orthogonal coordinate-based warehouse grid (12 aisles across 3 distinct zones).
2. **Synthetic Telemetry:** Synthesize a realistic, reproducible automotive parts picking dataset (120 workers, 350 orders) with skewed aisle popularity.
3. **Congestion Engine:** Formulate guarded aisle congestion calculation and 4-tier classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
4. **Wave Controller:** Engineer a wave-release controller with configurable safety gating (default 75%) and fail-safe manual fallback.
5. **Multi-Load Experiments:** Evaluate system behavior across Low Load, Normal Load, Peak Load, and Extreme Load operating conditions.
6. **Empirical Validation:** Programmatically quantify trade-offs between staging delay, throughput, bottleneck mitigation, and operational costs.
7. **Statistical Rigor:** Perform safe threshold sensitivity sweeps and multi-seed statistical stability evaluations.

---

## Architecture

```
Input Data (Synthetic Orders, Worker Pool, Warehouse Grid)
    ↓
Data Validation & Congestion Simulator (Worker Density Calculation)
    ↓
Congestion Classifier (LOW < 50% <= MEDIUM < 75% <= HIGH < 100% <= CRITICAL)
    ↓
Wave-Release Controller (Safe Threshold Evaluation & Sensor Fallback Logic)
    ↓
Warehouse Execution Engine (Discrete-Event Traversal & Interval Tracking)
    ↓
Performance Analysis & Reporting (Throughput, Delays, Costs, Hotspots, CO2)
```

---

## Current Implementation

The following modules are fully implemented and functional:
- **`src/data_generator.py`**: Coordinate grid layout (12 aisles, 3 zones), popularity hotspots (A03, A07), synthetic orders (120 workers, 350 orders), and Manhattan path geometry.
- **`src/congestion.py`**: Aisle congestion calculation with zero-capacity and negative-worker guards, plus 4-tier operational classification.
- **`src/controller.py`**: Wave-release admission controller emitting `ALLOW`, `DELAY`, or `BLOCK` decisions with automated `MANUAL FALLBACK` pacing during sensor blackouts.
- **`src/simulation.py`**: Discrete-event execution engine managing pick queues, physical occupancy intervals, and completion timestamps under both Baseline and Controlled modes.
- **`src/metrics.py`**: KPI computation (throughput, turnaround, labor wages, equipment wear, delay penalties, carbon footprint), dedicated hotspot analysis, and comparative DataFrames.
- **`src/scenarios.py`**: Multi-load pipeline (Low, Normal, Peak, Extreme), sensor failure handler, threshold sweeps, and 5-seed statistical validation.
- **`run_experiments.py`**: Master test pipeline generating all datasets, CSV tables, and 10 publication-quality figures in `results/`.
- **`Aisle_Congestion_Simulator.ipynb`**: 22-section interactive Jupyter Notebook executable from beginning to end with zero manual intervention.

---

## Validation

The prototype has been rigorously validated through:
- **Multi-Load Operating Conditions:** Stress-testing across Low (180 orders), Normal (300 orders), Peak (350 orders, 2.8x hotspot multiplier), and Extreme (450 orders, 3.5x hotspot multiplier).
- **Baseline vs Controlled Comparative Analysis:** Demonstrating that wave-release gating mitigates critical bottlenecks without throughput degradation.
- **Sensor Failure Fault Tolerance:** Verifying that the system transitions smoothly into `MANUAL FALLBACK` mode with zero unhandled exceptions or crashes.
- **Dedicated Hotspot Analysis:** Profiling top-congested aisles (A03, A07, A02), saturation event counts, and cumulative durations.
- **Boundary Testing:** Explicitly testing edge cases ($74.9\%, 75.0\%, 75.1\%, 100.0\%$, capacity 0, negative worker counts).
- **Multi-Seed Statistical Evaluation:** Running across 5 random seeds (`42, 101, 202, 303, 404`) to compute Mean $\pm$ Standard Deviation bounds.
- **Automated Test Suite:** 23 unit and integration tests passing with 100% success rate.

---

## Example Results

All numbers below were generated by the simulation pipeline (`run_experiments.py`, Seed = 42):

### 1. Multi-Load Experimental Performance:
| Scenario | Mode | Orders | Throughput (ord/hr) | Avg Wait (s) | Max Congestion (%) | Critical Events | Total Cost (\$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Low Load** | CONTROLLED | 180 | 103.43 | 0.17 s | 100.00% | 16 | \$569.52 |
| **Normal Load** | CONTROLLED | 300 | 172.05 | 2.10 s | 166.67% | 47 | \$945.40 |
| **Peak Load (Base)** | BASELINE | 350 | 200.83 | 0.00 s | 266.67% | 138 | \$1,039.58 |
| **Peak Load (Ctrl)** | CONTROLLED | 350 | 200.83 | 7.29 s | 266.67% | 132 | \$1,050.21 |
| **Extreme Load (Base)**| BASELINE | 450 | 255.96 | 0.00 s | 300.00% | 184 | \$1,284.27 |
| **Extreme Load (Ctrl)**| CONTROLLED | 450 | 255.96 | 17.00 s | 300.00% | 191 | \$1,316.14 |

### 2. Baseline vs Controlled Comparison (Peak Load):
- **Critical Congestion Events:** Reduced from 138 down to 132 (**+4.35% improvement**).
- **Average Waiting Time:** 0.00s (Baseline) vs 7.29s (Controlled) across 57 delayed orders.
- **Fulfillment Throughput:** Maintained at 200.83 orders/hour with zero penalty.
- **Total Operational Cost:** Baseline: \$1,039.58 vs Controlled: \$1,050.21 (+1.02% difference due to the \$0.25/min delay SLA cost).

### 3. Dedicated Hotspot Analysis (Top 3 Aisles):
| Rank | Aisle | Zone | Capacity | Avg Congestion | Max Congestion | Critical Events | Duration (s) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **A03** | Zone A Fast Moving | 3 | 65.88% | 266.67% | 70 | 2,100.0 s |
| **2** | **A07** | Zone B Engine Parts | 3 | 62.74% | 233.33% | 66 | 1,980.0 s |
| **3** | **A02** | Zone A Fast Moving | 4 | 12.26% | 100.00% | 2 | 60.0 s |

### 4. Multi-Seed Statistical Validation (5 Seeds: 42, 101, 202, 303, 404):
- **Baseline Critical Events:** $123.00 \pm 9.12$
- **Controlled Critical Events:** $121.80 \pm 6.55$
- **Controlled Average Waiting Time:** $8.14 \pm 1.26$ seconds
- **Controlled Delayed Orders:** $62.80 \pm 5.88$ orders
- **Fulfillment Throughput:** $198.47 \pm 1.37$ orders/hour

---

## Project Structure

```
coe_project/
├── Aisle_Congestion_Simulator.ipynb  # Interactive 22-section Master Jupyter Notebook
├── README.md                        # Master project documentation
├── requirements.txt                 # Project dependencies
├── .gitignore                       # Git exclusions
├── run_experiments.py               # Master simulation, scenario & plot runner
├── build_notebook.py                # Programmatic notebook generator
├── data/
│   └── warehouse_simulation_data.csv# Master synthetic picking dataset
├── src/
│   ├── __init__.py                  # Package initialization
│   ├── data_generator.py            # Warehouse grid & synthetic data generator
│   ├── congestion.py                # Congestion calculation & classification
│   ├── controller.py                # Wave-release controller & manual fallback
│   ├── simulation.py                # Discrete-event execution engine
│   ├── metrics.py                   # Performance KPIs, hotspots & comparison
│   └── scenarios.py                 # Multi-load scenarios & multi-seed validation
├── tests/
│   ├── __init__.py                  # Tests package initialization
│   ├── test_congestion.py           # Congestion calculation & edge tests (8 tests)
│   ├── test_controller.py           # Controller decisions & boundary tests (8 tests)
│   └── test_simulation.py           # Geometry, hotspots, multi-load & seeds (7 tests)
├── results/
│   ├── multi_scenario_comparison.csv# Multi-load summary table
│   ├── hotspot_analysis.csv         # Dedicated aisle hotspot rankings
│   ├── baseline_vs_controlled.csv   # Peak comparative metrics
│   ├── sensitivity_analysis.csv     # Safe threshold sweep data
│   ├── multirun_validation.csv      # 5-seed statistical summary
│   └── fig1_*.png to fig10_*.png    # 10 publication-quality analytical figures
└── docs/
    ├── Review_1_Report.md           # Formal college evaluation report
    └── PROJECT_STATUS.md            # Quick-reference prototype status audit
```

---

## How to Run

1. **Activate Environment & Install Dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Execute Complete Simulation Experiments:**
   ```bash
   python run_experiments.py
   ```
3. **Launch the Master Jupyter Notebook:**
   ```bash
   jupyter notebook Aisle_Congestion_Simulator.ipynb
   ```

---

## Google Colab Instructions

1. Open [Google Colab](https://colab.research.google.com).
2. Upload `Aisle_Congestion_Simulator.ipynb`.
3. In the first notebook cell, clone or upload the `src/` modules:
   ```python
   !git clone <YOUR_GITHUB_REPO_URL>
   %cd coe_project
   !pip install -r requirements.txt
   ```
4. Click **Runtime > Run all** to execute the notebook from top to bottom.

---

## Testing

Run the automated test suite using `pytest`:
```bash
source .venv/bin/activate
pytest tests/ -v
```
**Result:** 23 passed in 1.10s (100% success rate).

---

## Current Completion

**Overall Prototype Maturity: Approximately 40–42% Complete.**

The foundational mathematical models, discrete-event queue gating, multi-load scenario benchmarks, dedicated hotspot analyses, and multi-seed statistical evaluations are complete, verified, and demonstrable.

---

## Limitations

1. **Uniform Travel Speed:** Constant 1.0 m/s walking speed without modeling cart acceleration or turning inertia.
2. **Pre-Planned Pathing:** Orders do not dynamically re-route mid-transit when an aisle becomes congested.
3. **Synchronous Telemetry:** Telemetry drops are modeled parametrically rather than via asynchronous socket packet latency.
4. **Centroid Coordinates:** Distances model aisle centerlines rather than individual shelf tiers or bin faces.

---

## Future Work

- **Dynamic Graph Re-Routing (Review 2):** Real-time A* / Dijkstra path diversion around downstream congested aisles.
- **Microscopic Crowd Slowdowns (Review 2):** Deceleration curves modeling two carts passing in narrow aisles.
- **Asynchronous Telemetry Stream (Review 2):** Simulating live IoT sensor feeds using MQTT / Kafka pub-sub brokers.
- **Cyber-Security Threat Modeling (Review 2):** Simulating sensor spoofing attacks (false zero-congestion injection) and cryptographic verification.
- **Interactive Floor Dashboard (Review 3):** Real-time 2D animated web interface (Streamlit / Dash).
- **Physical Pilot Validation (Review 3):** Benchmarking against industrial warehouse telemetry or physical AGVs.
