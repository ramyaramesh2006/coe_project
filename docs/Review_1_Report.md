# Review 1 Report: Aisle Congestion Simulator and Wave-Release Controller

**Academic Department:** Department of Computer Science & Engineering (Cyber Security)  
**Project Milestone:** Review 1 Evaluation & Enhanced Prototype Validation  
**Prototype Completion Status:** Approximately 40–42% Overall Project Maturity  
**Date:** September 2026  

---

> Approximately 40–42% of the overall project has been developed as a functional simulation-based prototype. The work is intentionally not presented as a final production system.

---

## 1. Project Title
**Aisle Congestion Simulator and Wave-Release Controller for Automotive Parts Warehouses**

---

## 2. Project Objective
The primary objective of this project is to develop a simulation-based congestion management framework to eliminate worker congestion and optimize order fulfillment in automotive parts warehouses. Visually similar components stored in narrow aisles lead to worker clustering, physical gridlocks, extended waiting times, and fulfillment delays.

The proposed system models dynamic aisle worker density and implements a closed-loop wave-release controller that evaluates real-time aisle congestion against configurable safety thresholds, delaying or pacing dispatches to prevent bottleneck formation while maintaining robust operation during IoT network and sensor telemetry failures.

---

## 3. Problem Statement
Automotive spare parts warehouses present distinct logistical and cyber-physical challenges:
1. **High Visual Similarity & Manual Picking:** Components such as brake pads, oil filters, and spark plugs require careful manual inspection and picking by human workers pushing carts.
2. **Velocity Skew & Hotspots:** Fast-moving automotive maintenance components create concentrated demand hotspots in specific aisles (e.g., Aisles A03 and A07), whereas bulk engine blocks or body panels experience lower traffic.
3. **Physical Capacity Bottlenecks:** Warehouse aisles typically have physical width constraints that safely accommodate only 3 to 5 workers simultaneously. Unregulated dispatches cause acute aisle saturation ($\ge 100\%$ capacity).
4. **Queue Degradation & Inefficiencies:** Uncontrolled entry results in pickers queuing inside aisles, increasing idle labor costs and worker stress.
5. **Sensor Telemetry Vulnerability:** Sensor blackouts or network disruptions often cause automated dispatch systems to crash or release workers blindly, creating chaotic warehouse gridlocks.

---

## 4. Current Work Categorization

### A. Completed / Working Modules
- **Warehouse Simulation Engine:** Discrete-event execution modeling worker traversal and picking intervals.
- **Congestion Detection & Formulation:** Formula $(\text{workers} / \text{capacity}) \times 100$ with zero-capacity and negative-input guards.
- **Congestion Classification:** 4-tier operational classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Wave-Release Controller:** Dynamic gating with `ALLOW`, `DELAY`, `BLOCK` decisions based on safe thresholds.
- **Baseline vs Controlled Comparison:** Dual-mode evaluation quantifying bottleneck reduction and trade-offs.
- **Failure Fallback:** Autonomous transition to `MANUAL FALLBACK` mode with conservative release pacing.
- **Performance Metrics Engine:** Programmatic computation of waiting time, throughput, travel distance, cost, and emissions.
- **Automated Testing Suite:** 23 passing tests covering unit functions, boundary conditions, and scenarios.
- **Documentation & Notebook:** 22-section interactive Jupyter Notebook and comprehensive repository documentation.

### B. Additional Prototype Validation (Maturity: ~40–42%)
- **Multi-Load Scenario Pipeline:** Executing and comparing Low Load, Normal Load, Peak Congestion, and Extreme Load stress tests.
- **Dedicated Hotspot Analysis:** Quantifying top-3 congested aisles (A03, A07, A02), event frequencies, and saturation durations.
- **Threshold Sensitivity Analysis:** Safe threshold sweeps from 60% to 90% tracking decision breakdowns (`ALLOW`, `DELAY`, `BLOCK`).
- **Controller Boundary Testing:** Rigorous unit tests for exact threshold boundaries ($74.9\%, 75.0\%, 75.1\%, 100.0\%$), batch requests, and missing telemetry.
- **Multi-Run Statistical Validation:** Multi-seed evaluation across 5 random seeds (`42, 101, 202, 303, 404`) computing Mean $\pm$ Standard Deviation bounds.
- **Expanded Visualizations:** 10 analytical Matplotlib figures capturing scenario loads, hotspot profiles, decision distributions, and multi-seed variability.

### C. Pending Work (Reviews 2 & 3 Roadmap)
- **Dynamic In-Transit Re-Routing:** Graph-based dynamic rerouting (A* / Dijkstra) diverting workers around downstream congested aisles.
- **Microscopic Crowd Dynamics:** Modeling passing slowdowns and deceleration when two carts meet in a narrow aisle.
- **Real-Time Message Broker Integration:** Simulating live IoT sensor feeds using MQTT / Kafka pub-sub brokers.
- **Cyber-Security Threat Modeling:** Adversarial sensor spoofing attack simulation (false zero-congestion injection) and cryptographic verification.
- **Interactive Floor Dashboard & GUI:** Real-time 2D animated web interface (Streamlit / Dash).
- **Physical Pilot & Warehouse Validation:** Benchmarking against physical AGVs or industrial warehouse telemetry.

---

## 5. Summary of Empirical Results

All results reported below were generated programmatically by the simulation pipeline (`run_experiments.py`, Seed = 42):

### 1. Multi-Load Experimental Scenarios:
| Scenario | Mode | Orders | Throughput (ord/hr) | Avg Wait (s) | Max Congestion (%) | Critical Events | Total Cost (\$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Low Load** | CONTROLLED | 180 | 103.43 | 0.17 s | 100.00% | 16 | \$569.52 |
| **Normal Load** | CONTROLLED | 300 | 172.05 | 2.10 s | 166.67% | 47 | \$945.40 |
| **Peak Load (Base)** | BASELINE | 350 | 200.83 | 0.00 s | 266.67% | 138 | \$1,039.58 |
| **Peak Load (Ctrl)** | CONTROLLED | 350 | 200.83 | 7.29 s | 266.67% | 132 | \$1,050.21 |
| **Extreme Load (Base)**| BASELINE | 450 | 255.96 | 0.00 s | 300.00% | 184 | \$1,284.27 |
| **Extreme Load (Ctrl)**| CONTROLLED | 450 | 255.96 | 17.00 s | 300.00% | 191 | \$1,316.14 |

### 2. Baseline vs Controlled Operation (Peak Load):
- **Critical Congestion Events:** Reduced from 138 down to 132 (**+4.35% improvement**).
- **Staging Delay Trade-off:** Average wait increased from 0.00s to 7.29s (max delay 120.0s across 57 delayed orders).
- **Throughput:** Maintained at 200.83 orders/hour with zero degradation.
- **Cost Trade-off:** Slight increase from \$1,039.58 to \$1,050.21 (+1.02%) due to the staging delay SLA penalty (\$0.25/min).

### 3. Dedicated Hotspot Analysis:
| Rank | Aisle | Zone | Capacity | Avg Congestion | Max Congestion | Critical Events | High Events | Duration (s) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **A03** | Zone A Fast Moving | 3 | 65.88% | 266.67% | 70 | 0 | 2,100.0 s |
| **2** | **A07** | Zone B Engine Parts | 3 | 62.74% | 233.33% | 66 | 0 | 1,980.0 s |
| **3** | **A02** | Zone A Fast Moving | 4 | 12.26% | 100.00% | 2 | 0 | 60.0 s |
| 4 | A05 | Zone B Engine Parts | 4 | 8.96% | 75.00% | 0 | 4 | 120.0 s |
| 5 | A01 | Zone A Fast Moving | 4 | 7.90% | 75.00% | 0 | 4 | 120.0 s |

### 4. Multi-Seed Statistical Validation (Seeds: 42, 101, 202, 303, 404):
| Metric | Mean | Std | Min | Max |
| :--- | :---: | :---: | :---: | :---: |
| **Baseline Critical Events** | 123.00 | 9.12 | 113.00 | 138.00 |
| **Controlled Critical Events** | 121.80 | 6.55 | 113.00 | 132.00 |
| **Critical Reduction (%)** | +0.58% | 7.46% | -11.50% | +8.87% |
| **Controlled Avg Waiting Time (s)** | 8.14 s | 1.26 s | 7.03 s | 10.54 s |
| **Controlled Delayed Orders** | 62.80 | 5.88 | 57.00 | 73.00 |
| **Throughput (orders/hr)** | 198.47 | 1.37 | 197.15 | 200.83 |
| **Total Estimated Cost (\$)** | \$1,048.11 | \$17.54 | \$1,029.19 | \$1,080.51 |

---

## 6. Sensitivity Analysis Findings & Discrete Queuing Note
Testing thresholds $[60\%, 65\%, 70\%, 75\%, 80\%, 85\%, 90\%]$:
- At thresholds $\le 65\%$, the controller enters an aggressive gating regime (127 delayed orders, 21.26s average wait), throttling entry when 2 workers are inside capacity-3 aisles ($66.7\% \ge 60\%$).
- At thresholds $\ge 70\%$, the controller operates in a moderate gating regime (72 delayed orders, 8.57s average wait), allowing 2 workers ($66.7\% < 70\%$) and only blocking when 3 workers saturate the aisle ($100\% \ge 70\%$).
- This step-function plateau between 70% and 90% is a legitimate mathematical consequence of discrete integer worker counts in small-capacity aisles ($w/3 \in \{33.3\%, 66.7\%, 100\%\}$), where no discrete occupancy state physically exists between 66.7% and 100%.

---

## 7. Current Prototype Limitations
1. **Constant Walking Pace:** Modeled at a uniform 1.0 m/s without simulating acceleration curves or turning geometry.
2. **Pre-Determined Order Paths:** Worker itineraries are fixed at dispatch; dynamic diversion around active bottlenecks is not implemented.
3. **Synchronous Sensor Abstraction:** Telemetry drops are simulated via boolean flags rather than network packet latency or socket disconnects.
4. **Centroid Coordinates:** Distances model aisle centerlines rather than individual shelf tiers or bin faces.

---

## 8. Review 1 Evaluation Conclusion
The prototype has achieved **~40–42% overall project maturity**. All foundational modules required for Review 1 are functional, verified with 23 automated tests, and reinforced by multi-load scenario benchmarks, dedicated hotspot analyses, and multi-seed statistical evaluations. Substantial future engineering remains for Reviews 2 and 3.
