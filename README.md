# Aisle Congestion Simulator and Wave-Release Controller

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 12 Passed](https://img.shields.io/badge/tests-12%20passed-brightgreen.svg)]()
[![Stage: Review 1](https://img.shields.io/badge/Review%201-~35%25%20Complete-orange.svg)]()

A discrete-event simulation system and intelligent wave-release dispatching controller developed to analyze, mitigate, and control physical aisle congestion in automotive parts distribution warehouses.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [System Architecture](#system-architecture)
- [Technologies](#technologies)
- [Features Completed](#features-completed)
- [Dataset](#dataset)
- [Simulation Method](#simulation-method)
- [Congestion Model](#congestion-model)
- [Wave-Release Controller](#wave-release-controller)
- [Operating Scenarios](#operating-scenarios)
  - [Normal Operation](#normal)
  - [Peak Congestion](#peak-congestion)
  - [Sensor/Network Failure](#sensornetwork-failure)
- [Baseline vs Controlled](#baseline-vs-controlled)
- [Metrics](#metrics)
- [Results](#results)
- [Project Structure](#project-structure)
- [How to Run](#how-to-run)
- [Google Colab Instructions](#google-colab-instructions)
- [Testing](#testing)
- [Current Review 1 Status](#current-review-1-status)
- [Completed Work](#completed-work)
- [Pending Work](#pending-work)
- [Future Work](#future-work)
- [Limitations](#limitations)
- [Conclusion](#conclusion)

---

## Project Overview

In automotive distribution centers, order pickers travel through physical warehouse aisles to retrieve visually similar components (e.g. brake rotors, calipers, engine gaskets, filters). When order release is unregulated, picker traffic concentrates heavily in popular aisles, leading to physical gridlock, picker idle time, and fulfillment delays.

This project implements a **discrete-event simulation model** combined with a **closed-loop wave-release controller** that dynamically regulates order dispatches based on aisle density thresholds and sensor health telemetry.

---

## Problem Statement

Automotive parts warehouses face distinct operational bottlenecks:
1. **Uneven Aisle Velocity:** High-demand replacement components (e.g. ceramic brake pads in Aisle A03, spin-on oil filters in A07) draw excessive picker density compared to slow-moving chassis assemblies.
2. **Narrow Physical Aisle Limits:** Physical warehouse aisles typically accommodate only 3 to 5 pickers with carts simultaneously. Over-allocation causes congestion.
3. **Queue Degradation:** Releasing pickers unconditionally creates physical queues inside aisles, inflating turnaround times and labor costs.
4. **Sensor Network Fragility:** Automated dispatchers frequently fail when IoT telemetry networks drop, requiring robust manual fallback modes.

---

## Objectives

### Review 1 Milestone Scope (~35% Target):
- Model an orthogonal coordinate-based warehouse grid (12 aisles across 3 distinct zones).
- Synthesize a realistic, reproducible automotive parts picking dataset (120 workers, 350 orders) with skewed aisle popularity.
- Develop guarded aisle congestion calculation and 4-tier classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- Implement a wave-release controller with configurable safety gating (default 75%) and fail-safe manual fallback.
- Simulate worker Manhattan travel distances, pick durations, and queuing delay.
- Execute and compare 3 operational scenarios: Normal Operation, Peak Congestion, and Sensor/Network Failure.
- Conduct safe threshold sensitivity analysis (60% to 90%).
- Provide an automated test suite and an interactive Jupyter Notebook.

---

## System Architecture

```
                 [ Warehouse Grid Layout (12 Aisles, 3 Zones) ]
                                      │
                                      ▼
             [ Synthetic Order Generator (120 Workers, 350 Orders) ]
                                      │
                                      ▼
                           [ Data Validation Layer ]
                                      │
                                      ▼
                      [ Aisle Congestion Calculator ]
                     (Workers / Capacity * 100 with Guardrails)
                                      │
                                      ▼
                     [ Congestion Level Classifier ]
                 (LOW < 50% <= MEDIUM < 75% <= HIGH < 100% <= CRITICAL)
                                      │
                                      ▼
                     [ Wave-Release Controller ]
              (Safe Threshold Evaluation & Sensor Fallback Logic)
                                      │
                                      ▼
                    [ Warehouse Simulation Engine ]
                 (Baseline vs Controlled Discrete Execution)
                                      │
                                      ▼
                  [ Multi-Scenario & Sensitivity Runner ]
                                      │
                                      ▼
                  [ Performance Metrics & Comparison ]
                  (Congestion, Delay, Throughput, Cost, CO2)
                                      │
                                      ▼
                  [ Analytical Graphs & Review 1 Dashboard ]
```

### Module Descriptions:
- **`src/data_generator.py`**: Builds the 12-aisle 2D layout and stochastically synthesizes order picking itineraries with skewed popularity toward Aisles A03 and A07.
- **`src/congestion.py`**: Computes worker density percentages per aisle with numerical guardrails against zero-capacity or missing inputs. Classifies congestion into operational tiers.
- **`src/controller.py`**: Wave-release controller evaluating target aisle congestion against safe limits to emit `ALLOW`, `DELAY`, or `BLOCK` dispatch decisions. Activates paced manual fallback during sensor outages.
- **`src/simulation.py`**: Discrete-event execution engine that advances workers through Manhattan paths, logs physical occupancy intervals, and tracks queuing delays.
- **`src/metrics.py`**: Computes fulfillment throughput, turnaround times, labor costs, equipment wear, and carbon footprints. Generates programmatic comparison tables.
- **`src/scenarios.py`**: Automates execution of Normal, Peak, and Sensor Failure operational scenarios, and runs threshold sensitivity sweeps.

---

## Technologies

- **Python 3.9+**: Core language.
- **Pandas (v2.3.3)**: Tabular modeling, time-series binning, and metric generation.
- **NumPy (v2.0.2)**: Coordinate grids, Manhattan metrics, and reproducible stochastic sampling.
- **Matplotlib (v3.9.4)**: Publication-grade analytical charts and comparative visual plots.
- **Pytest (v8.4.2)**: Automated unit and integration testing.
- **Jupyter Notebook / Google Colab**: Interactive demonstration and execution.

---

## Features Completed

- [x] Synthetic warehouse dataset generation (120 workers, 350 orders, 990 pick operations).
- [x] Orthogonal warehouse grid model (3x4 coordinate system, 15m grid pitch).
- [x] Manhattan path routing and cumulative distance calculation.
- [x] Aisle congestion computation with zero-division protection and negative input handling.
- [x] 4-level congestion classification engine (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- [x] Closed-loop wave-release controller with configurable safe threshold gating.
- [x] Telemetry failure detection and graceful `MANUAL FALLBACK` pacing mode.
- [x] Multi-scenario simulation: Normal Operation, Peak Congestion, Sensor Failure.
- [x] Programmatic Baseline vs Controlled comparative evaluation.
- [x] Sensitivity analysis across safe thresholds from 60% to 90%.
- [x] 10 distinct analytical figures exported to `results/`.
- [x] 12 automated unit tests passing with 100% success rate.
- [x] Complete, self-contained 30-section Jupyter Notebook (`Aisle_Congestion_Simulator.ipynb`).

---

## Dataset

The synthetic dataset represents a 2-hour shift in an automotive parts warehouse. No real personal data is used.

- **Workers:** 120 unique pickers (`W001` to `W120`).
- **Orders:** 350 unique pick orders (`ORD_0001` to `ORD_0350`).
- **Pick Records:** 990 individual aisle-level pick operations.
- **Aisles:** 12 aisles (`A01` to `A12`) across 3 functional zones:
  - `Zone_A_FastMoving` (A01 - A04, capacities: 3–5)
  - `Zone_B_EngineParts` (A05 - A08, capacities: 3–5)
  - `Zone_C_Electrical` (A09 - A12, capacities: 4–5)
- **Popularity Skew:** Aisles A03 (22% base probability) and A07 (20% base probability) act as natural demand hotspots.
- **Reproducibility:** Seeded with fixed `RANDOM_SEED = 42`.
- **Export Location:** `data/warehouse_simulation_data.csv`.

---

## Simulation Method

The simulator executes discrete-event time intervals:
1. **Order Initiation:** Orders arrive at designated request release times.
2. **Wave Dispatch Check:**
   - *Baseline Mode:* Workers release immediately (`actual_release_time = requested_release_time`).
   - *Controlled Mode:* The wave-release controller evaluates target aisle congestion. If `>= safe_threshold`, release is delayed by 30-second increments until capacity clears.
3. **Movement & Traversal:** Workers traverse from the staging depot (0,0) to target aisles using orthogonal Manhattan distance ($|x_1 - x_2| + |y_1 - y_2| \times 15\text{m}$) at a standard walking speed of 1.0 m/s.
4. **Aisle Occupancy:** Workers occupy physical space in aisles during picking (30–60s per item), dynamically updating aisle headcounts.

---

## Congestion Model

Congestion is modeled as:
$$\text{Congestion Percentage} = \left( \frac{\text{Current Workers}}{\text{Aisle Capacity}} \right) \times 100$$

### Edge Case Guardrails:
- **Zero Capacity:** Returns 100.0% if workers > 0, 0.0% if workers == 0; prevents `ZeroDivisionError`.
- **Negative / NaN Inputs:** Worker counts < 0 or NaN clamped safely to 0.0.
- **Sensor Blackout:** Returns safe fallback estimate (default 60.0%–65.0%).

### Classification Tiers:
| Tier | Congestion Range | Warehouse Implication |
| :--- | :--- | :--- |
| **LOW** | 0% to <50% | Aisle freely flowing; unobstructed picker travel |
| **MEDIUM** | 50% to <75% | Moderate picker density; normal operation |
| **HIGH** | 75% to <100% | Near capacity; gating / wave delay recommended |
| **CRITICAL**| $\ge$ 100% | Fully saturated; physical queuing occurs |

---

## Wave-Release Controller

- **Inputs:** Target aisle congestion %, requested workers, safe threshold (default 75%), aisle capacity, sensor availability flag.
- **Outputs:** Decision (`ALLOW`, `DELAY`, `BLOCK`), released workers count, delayed workers count, delay interval, reason, system status, operating mode.
- **Decision Logic:**
  - `Congestion < 50%`: `ALLOW` (immediate release).
  - `50% <= Congestion < Safe Threshold`: `ALLOW` (immediate release).
  - `Safe Threshold <= Congestion < 100%`: `DELAY` (hold worker at staging, retry in 30s).
  - `Congestion >= 100%`: `BLOCK` (strict hold until bottleneck resolves).
- **Anti-Starvation:** Maximum retry cap (20 cycles) ensures orders are never permanently blocked.

---

## Operating Scenarios

### Normal
Simulates standard daily warehouse operation with balanced picking demand.
- Average Congestion: 13.66%
- Maximum Congestion: 166.67%
- Fulfillment Throughput: 172.05 orders/hour
- Average Waiting Time: 2.10 seconds
- Critical Congestion Events: 47

### Peak Congestion
Simulates high-demand shift peaks by magnifying pick orders concentrated into hotspot aisles A03 and A07 (peak multiplier 2.8x). Evaluates Baseline vs Controlled wave-release execution.

### Sensor/Network Failure
Simulates an IoT network blackout (`sensor_available = False`).
- System Status: `SENSOR FAILURE`
- Mode: `MANUAL FALLBACK`
- Result: System maintained uninterrupted operation across 300 dispatches with zero unhandled exceptions, pacing dispatches conservatively.

---

## Baseline vs Controlled

The following results were generated directly by executing `run_experiments.py` on the synthetic peak dataset (350 orders, 120 workers, seed=42):

| Metric | Baseline (Unregulated) | Controlled (Wave-Release) | Absolute Difference | Improvement Percentage |
| :--- | :---: | :---: | :---: | :---: |
| **Average Congestion (%)** | 16.85% | 16.85% | 0.00 | 0.00% |
| **Maximum Congestion (%)** | 266.67% | 266.67% | 0.00 | 0.00% |
| **Critical Congestion Events** | 138 | 132 | -6.00 | **+4.35%** |
| **High Congestion Events** | 8 | 10 | +2.00 | **-25.00%** |
| **Average Waiting Time (s)** | 0.00 s | 7.29 s | +7.29 s | *-100.00% (Trade-off)* |
| **Maximum Waiting Time (s)** | 0.00 s | 120.00 s | +120.00 s | *-100.00% (Trade-off)* |
| **Total Waiting Time (s)** | 0.0 s | 2,550.0 s | +2,550.0 s | *-100.00% (Trade-off)* |
| **Delayed Orders Count** | 0 | 57 | +57 | *-100.00% (Trade-off)* |
| **Throughput (orders/hr)** | 200.83 | 200.83 | 0.00 | **0.00% (Preserved)** |
| **Total Distance (m)** | 30,210.0 m | 30,210.0 m | 0.00 m | 0.00% |
| **Average Distance (m)** | 86.31 m | 86.31 m | 0.00 m | 0.00% |
| **Total Estimated Cost ($)** | $1,039.58 | $1,050.21 | +$10.63 | **-1.02% (Trade-off)** |
| **Estimated Emissions (kg CO2e)** | 4.5315 kg | 4.5315 kg | 0.0000 kg | 0.00% |

### Key Analysis:
1. **Critical Events Reduced:** Saturated aisle events dropped from 138 down to 132 (+4.35% reduction in acute bottleneck occurrences).
2. **Controlled Staging Trade-Off:** The controller deliberately shifts worker waiting from congested inside aisles to orderly staging queues (57 orders delayed, average wait of 7.29 seconds).
3. **Throughput Maintained:** Pacing did not penalize overall order throughput, remaining identical at 200.83 orders/hour.
4. **Transparent Cost Impact:** Total operational cost increased by $10.63 (+1.02%) solely due to the staging delay penalty parameter ($0.25/minute idle cost).

---

## Metrics

### Operational Cost Model (Estimated Prototype):
$$\text{Total Cost} = \text{Labor Cost} + \text{Travel Cost} + \text{Delay Cost}$$
- Picker Labor Wage: \$0.35 / active minute (\$21.00/hour)
- Equipment Wear & Tear: \$0.02 / meter traveled
- Idle Delay SLA Penalty: \$0.25 / minute delayed

### Carbon Emissions Model (Estimated Prototype):
$$\text{Estimated Emissions} = \text{Total Distance} \times \text{Emission Factor}$$
- Emission Factor: 0.00015 kg $\text{CO}_2\text{e}$ per meter traveled (electric picking cart lifecycle energy equivalent)

---

## Results

### Sensitivity Analysis (Safe Threshold Sweep):
Evaluated across 7 safe threshold levels:

| Threshold (%) | Avg Waiting (s) | Total Waiting (s) | Throughput (ord/hr) | Critical Events | Delayed Orders | Est. Cost (\$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **60%** | 21.26 s | 7,440.0 s | 198.21 | 130 | 127 | \$1,061.07 |
| **65%** | 21.26 s | 7,440.0 s | 198.21 | 130 | 127 | \$1,061.07 |
| **70%** | 8.57 s | 3,000.0 s | 198.46 | 126 | 72 | \$1,042.57 |
| **75%** | 8.57 s | 3,000.0 s | 198.46 | 126 | 72 | \$1,042.57 |
| **80%** | 8.57 s | 3,000.0 s | 198.46 | 126 | 72 | \$1,042.57 |
| **85%** | 8.57 s | 3,000.0 s | 198.46 | 126 | 72 | \$1,042.57 |
| **90%** | 8.57 s | 3,000.0 s | 198.46 | 126 | 72 | \$1,042.57 |

### Generated Visualizations (in `results/`):
- `fig1_congestion_by_aisle.png`: Mean and peak congestion per aisle.
- `fig2_congestion_distribution_a03.png`: Percentage of time hotspot A03 spends in each tier.
- `fig3_waiting_time_comparison.png`: Baseline vs Controlled dispatch waiting times.
- `fig4_throughput_comparison.png`: Warehouse order completion throughput.
- `fig5_distance_comparison.png`: Cumulative picker travel distances.
- `fig6_cost_breakdown.png`: Labor, travel, delay, and total cost breakdown.
- `fig7_emissions_comparison.png`: Estimated environmental emissions.
- `fig8_sensitivity_waiting_and_critical.png`: Safe threshold vs waiting times and critical events.
- `fig9_sensitivity_throughput.png`: Safe threshold vs fulfillment throughput.
- `fig10_warehouse_grid_layout.png`: 2D warehouse topology and popularity map.

---

## Project Structure

```
coe_project/
├── Aisle_Congestion_Simulator.ipynb  # Interactive 30-section Jupyter Notebook
├── README.md                        # Master project documentation
├── requirements.txt                 # Project dependencies
├── .gitignore                       # Git exclusions for python/checkpoints
├── run_experiments.py               # Complete simulation and visualization runner
├── build_notebook.py                # Programmatic notebook generator
├── data/
│   └── warehouse_simulation_data.csv# Synthetic dataset (120 workers, 350 orders)
├── src/
│   ├── __init__.py                  # Package initialization
│   ├── data_generator.py            # Warehouse grid & synthetic data generator
│   ├── congestion.py                # Congestion calculation & classification
│   ├── controller.py                # Wave-release controller & manual fallback
│   ├── simulation.py                # Discrete-event execution engine
│   ├── metrics.py                   # Performance KPIs & comparison logic
│   └── scenarios.py                 # Scenario runners (Normal, Peak, Failure)
├── tests/
│   ├── __init__.py                  # Tests package initialization
│   ├── test_congestion.py           # Congestion calculation and edge tests
│   ├── test_controller.py           # Wave controller allow/delay/block tests
│   └── test_simulation.py           # Distance, waiting time, and seed tests
├── results/
│   ├── .gitkeep
│   ├── baseline_vs_controlled.csv   # Programmatic comparative results
│   ├── sensitivity_analysis.csv     # Safe threshold sweep data
│   └── *.png                        # 10 generated analytical figures
└── docs/
    └── Review_1_Report.md           # Formal college evaluation report
```

---

## How to Run

### Local Environment Setup:
1. Clone repository:
   ```bash
   git clone <repository-url>
   cd coe_project
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run full simulation and generate all outputs:
   ```bash
   python run_experiments.py
   ```
5. Launch the Jupyter Notebook:
   ```bash
   jupyter notebook Aisle_Congestion_Simulator.ipynb
   ```

---

## Google Colab Instructions

1. Open [Google Colab](https://colab.research.google.com).
2. Click **Upload** and upload `Aisle_Congestion_Simulator.ipynb`.
3. If running with modular files, upload the `src/` folder to Colab's file browser, or clone the GitHub repository directly:
   ```python
   !git clone <your-github-repo-url>
   %cd coe_project
   ```
4. Run the notebook top-to-bottom via **Runtime > Run all**.

---

## Testing

Automated testing is implemented using `pytest`:
```bash
pytest tests/ -v
```
Test Coverage:
1. `test_normal_congestion_calculation`: Formula verification.
2. `test_zero_and_negative_capacity_handling`: Zero-division protection.
3. `test_missing_and_negative_worker_values`: Null and negative value clamping.
4. `test_congestion_classification_boundaries`: Standard operational tiers.
5. `test_congestion_classification_custom_thresholds`: Configurable threshold support.
6. `test_controller_allow_decision`: Safe release under LOW/MEDIUM density.
7. `test_controller_delay_decision`: Wave hold under HIGH density.
8. `test_controller_critical_congestion_block`: Strict blocking under CRITICAL saturation.
9. `test_controller_sensor_failure_fallback`: Transition to paced manual fallback.
10. `test_distance_calculation_accuracy`: Manhattan geometry verification.
11. `test_waiting_time_non_negative`: Guarantee that waiting times are $\ge 0$.
12. `test_simulation_reproducibility`: Deterministic seed reproducibility.

**Execution Result:** 12 passed in 13.55s.

---

## Current Review 1 Status

**Review 1 Completion Status: Approximately 35% Complete.**

The core simulation foundations, mathematical congestion formulations, wave-release controller logic, multi-scenario handling, automated testing, and comparative analysis are fully implemented, verified, and demonstrable.

---

## Completed Work

- [x] Full synthetic automotive parts warehouse dataset.
- [x] Orthogonal warehouse grid model and distance engine.
- [x] Congestion calculation with division-by-zero protection.
- [x] 4-level congestion classification.
- [x] Closed-loop wave-release controller.
- [x] Manual fallback mode during sensor failure.
- [x] Normal, Peak, and Failure operational scenarios.
- [x] Programmatic Baseline vs Controlled comparative metrics.
- [x] Sensitivity analysis across 7 threshold configurations.
- [x] 10 analytical visualizations.
- [x] 12 unit tests passing.
- [x] 30-section executable Jupyter Notebook.

---

## Pending Work (Reviews 2 & 3)

- **Dynamic Re-Routing:** Implementing in-transit picker re-routing to divert workers around sudden aisle blockages.
- **Microscopic Physics:** Modeling picker deceleration when passing other workers in narrow aisles.
- **Live Telemetry Interface:** Integrating MQTT / Kafka message streaming for sensor telemetry simulation.
- **Interactive UI:** Building a graphical floor dashboard (Streamlit or web interface).
- **Cyber-Security Threat Scenarios:** Modeling telemetry tampering and spoofed sensor feed resilience.

---

## Future Work

- Integration with physical Autonomous Guided Vehicles (AGVs) and Multi-Agent Path Finding (MAPF).
- Machine learning models for predictive wave batching.
- Scaled industrial benchmarking with tier-1 automotive logistics partners.

---

## Limitations

1. **Walking Physics:** Constant 1.0 m/s travel speed assumes uniform physical capability and no cart congestion slowdowns while walking between aisles.
2. **Fixed Pick Sequences:** Orders follow predefined paths without dynamic waypoint re-ordering.
3. **Aisle Centroid Approximation:** Distances are calculated between aisle entrances rather than individual shelf bin coordinates.
4. **Synchronous Telemetry:** Telemetry loss is simulated via boolean flags rather than network packet latency or socket disconnects.

---

## Conclusion

The Review 1 prototype provides a functional, mathematically verified proof-of-concept for the **Aisle Congestion Simulator and Wave-Release Controller**. By demonstrating a 4.35% reduction in critical aisle saturation events while preserving 200.83 orders/hour throughput, this milestone establishes a robust foundation for Review 2 development.
