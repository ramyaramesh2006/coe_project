# Project Status: Aisle Congestion Simulator and Wave-Release Controller

**Academic Milestone:** Review 1 Evaluation / Working Simulation Prototype  
**Maturity Status:** Approximately 40–42% Overall Prototype Maturity  
**Target Milestone Date:** September 2026  
**Department:** Computer Science & Engineering (Cyber Security)  

---

## 1. Current Stage
**Review 1 / Early-Stage Working Simulation Prototype**

The project has transitioned beyond initial baseline demonstration (~35%) into a verified, multi-load experimental prototype (~40–42%). It implements core simulation engines, discrete-event queue gating, multi-scenario evaluation, dedicated hotspot analytics, threshold sensitivity analysis, and multi-seed statistical validation.

> [!NOTE]
> This prototype is intentionally positioned as a functional research and evaluation prototype (~40–42% completion), not a final production software deployment.

---

## 2. Estimated Project Maturity Breakdown
- **Mathematical Modeling & Layout:** 100% of Review 1 scope complete.
- **Wave-Release Controller Core:** 100% of Review 1 scope complete.
- **Multi-Load Simulation Experiments:** 100% complete (Low, Normal, Peak, Extreme).
- **Automated Unit & Boundary Testing:** 100% complete (23 passing automated tests).
- **Statistical & Hotspot Validation:** 100% complete (5-seed evaluation, top-3 hotspot ranking).
- **Dynamic Re-Routing & Intra-Aisle Deceleration:** 0% (Scoped for Review 2).
- **Live IoT / Message Broker Integration:** 0% (Scoped for Review 2).
- **Interactive UI Dashboard & Hardware:** 0% (Scoped for Review 3).

**Overall Estimated Project Completion: ~40–42%**

---

## 3. Fully Functioning Modules

| Module Path | Primary Responsibility | Maturity |
| :--- | :--- | :---: |
| [`src/data_generator.py`](file:///Users/ramyaramesh/Documents/coe_project/src/data_generator.py) | 2D coordinate grid (12 aisles, 3 zones), popularity hotspots, synthetic orders (120 workers, 350 orders), and Manhattan path generator. | **Working** |
| [`src/congestion.py`](file:///Users/ramyaramesh/Documents/coe_project/src/congestion.py) | Dynamic worker density calculation with zero-division guards and 4-tier classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). | **Working** |
| [`src/controller.py`](file:///Users/ramyaramesh/Documents/coe_project/src/controller.py) | Closed-loop wave-release gating (`ALLOW`, `DELAY`, `BLOCK`), configurable safe threshold, and autonomous `MANUAL FALLBACK` pacing. | **Working** |
| [`src/simulation.py`](file:///Users/ramyaramesh/Documents/coe_project/src/simulation.py) | Discrete-event execution engine supporting Baseline (unregulated) and Controlled wave dispatches with interval tracking. | **Working** |
| [`src/metrics.py`](file:///Users/ramyaramesh/Documents/coe_project/src/metrics.py) | KPI analytics (throughput, wait time, cost, emissions), dedicated hotspot analysis, and programmatic comparative tables. | **Working** |
| [`src/scenarios.py`](file:///Users/ramyaramesh/Documents/coe_project/src/scenarios.py) | Multi-load experimental pipeline (Low, Normal, Peak, Extreme), sensor failure handler, threshold sweeps, and 5-seed statistical validation. | **Working** |
| [`run_experiments.py`](file:///Users/ramyaramesh/Documents/coe_project/run_experiments.py) | Master automation runner executing all experiments, generating CSV summaries, and saving 10 publication-quality figures to `results/`. | **Working** |
| [`Aisle_Congestion_Simulator.ipynb`](file:///Users/ramyaramesh/Documents/coe_project/Aisle_Congestion_Simulator.ipynb) | 22-section interactive master notebook executable from top to bottom with zero manual intervention. | **Working** |

---

## 4. Empirical Validation Evidence

### A. Synthetic Dataset
- File: [`data/warehouse_simulation_data.csv`](file:///Users/ramyaramesh/Documents/coe_project/data/warehouse_simulation_data.csv)
- Scope: 120 workers, 350 orders, 990 pick records, 12 aisles across 3 zones. Non-uniform popularity heavily weights fast-moving automotive parts in Aisles A03 (22%) and A07 (20%).

### B. Multi-Load Experimental Conditions
- File: [`results/multi_scenario_comparison.csv`](file:///Users/ramyaramesh/Documents/coe_project/results/multi_scenario_comparison.csv)
- Conditions evaluated:
  - **Scenario A (Low Load):** 180 orders, 60 workers $\implies$ 103.43 orders/hr, 0.17s avg wait, 16 critical events.
  - **Scenario B (Normal Load):** 300 orders, 100 workers $\implies$ 172.05 orders/hr, 2.10s avg wait, 47 critical events.
  - **Scenario C (Peak Load):** 350 orders, 120 workers, 2.8x multiplier $\implies$ Baseline: 138 critical events vs Controlled: 132 critical events (4.35% reduction, 7.29s avg wait, 200.83 orders/hr).
  - **Scenario D (Extreme Load):** 450 orders, 150 workers, 3.5x multiplier $\implies$ 255.96 orders/hr, 17.00s avg wait, 184 critical events.

### C. Dedicated Hotspot Analysis
- File: [`results/hotspot_analysis.csv`](file:///Users/ramyaramesh/Documents/coe_project/results/hotspot_analysis.csv)
- Top 3 Congested Aisles:
  1. **A03 (Zone A Fast Moving):** Mean Congestion 65.88%, Max 266.67%, 70 Critical Events.
  2. **A07 (Zone B Engine Parts):** Mean Congestion 62.74%, Max 233.33%, 66 Critical Events.
  3. **A02 (Zone A Fast Moving):** Mean Congestion 12.26%, Max 100.00%, 2 Critical Events.

### D. Multi-Seed Statistical Stability (5 Seeds: 42, 101, 202, 303, 404)
- File: [`results/multirun_validation.csv`](file:///Users/ramyaramesh/Documents/coe_project/results/multirun_validation.csv)
- Baseline Critical Events: $123.00 \pm 9.12$
- Controlled Critical Events: $121.80 \pm 6.55$
- Controlled Average Waiting: $8.14 \pm 1.26$ seconds
- Delayed Orders: $62.80 \pm 5.88$ orders
- Controlled Throughput: $198.47 \pm 1.37$ orders/hour

### E. Automated Test Suite
- Executed via `pytest tests/ -v`:
- **23 automated tests passing** (100% success rate), covering calculation guardrails, classification tiers, boundary conditions ($74.9\%, 75.0\%, 75.1\%, 100.0\%$), sensor blackout fallbacks, distance geometry, multi-load scenarios, and multi-seed statistics.

### F. Analytical Visualizations (in `results/`)
1. `fig1_congestion_by_scenario.png`: Peak congestion across Low, Normal, Peak, Extreme loads.
2. `fig2_critical_events_by_scenario.png`: Critical bottleneck events across loads.
3. `fig3_throughput_comparison.png`: Warehouse fulfillment throughput.
4. `fig4_waiting_time_comparison.png`: Average staging delay comparison.
5. `fig5_baseline_vs_controlled.png`: Comparative analysis of key peak metrics.
6. `fig6_hotspot_aisle_analysis.png`: Top-congested aisles profile.
7. `fig7_threshold_sensitivity.png`: Safe threshold trade-off curve.
8. `fig8_controller_decisions_distribution.png`: ALLOW vs DELAY vs BLOCK across thresholds.
9. `fig9_worker_load_vs_congestion.png`: Dynamic time-series of A03 congestion.
10. `fig10_multirun_variability.png`: Error bars showing mean $\pm$ std across seeds.

---

## 5. Not Yet Implemented (Future Roadmap)

The following capabilities are deliberately scoped for subsequent reviews:

### Review 2 Target (~70% Completion):
- **Dynamic Re-Routing:** Real-time graph routing (A* / Dijkstra) diverting workers around downstream aisles that jam during active order picking.
- **Intra-Aisle Slowdown Dynamics:** Microscopic deceleration curves when multiple picker carts pass inside a narrow aisle.
- **Asynchronous Telemetry Stream:** Simulating IoT sensor packet streams via an MQTT / Kafka pub-sub broker.
- **Cyber-Security Adversarial Modeling:** Simulating sensor spoofing attacks (false zero-congestion injection) and developing cryptographic signature verification.

### Review 3 Target (Final Capstone Prototype):
- **Interactive Floor Dashboard:** Real-time 2D animated browser interface (Streamlit / Dash).
- **Heuristic / ML Wave Batching:** Machine-learning predictive order arrival clustering.
- **AGV Integration:** Automated Guided Vehicle path conflict resolution (Multi-Agent Path Finding - MAPF).
- **Physical Pilot Validation:** Benchmarking against automotive parts warehouse operational logs.
