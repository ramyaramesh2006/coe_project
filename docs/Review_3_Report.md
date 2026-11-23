# Review 3 Progress Report
## Aisle Congestion Simulator and Wave-Release Controller for Automotive Parts Warehouse Containing Visually Similar Components

**Department:** Computer Science & Engineering (Cyber Security)  
**Review phase:** Review 3 — 30% project-completion submission  
**Repository:** https://github.com/ramyaramesh2006/coe_project  
**Development branch:** `review3-implementation`  
**Pull request:** https://github.com/ramyaramesh2006/coe_project/pull/1  
**Report status:** 76 automated tests passed; experiment runner and dashboard smoke test passed; stakeholder validation pending

---

## 1. Project objective

The project addresses congestion around popular aisles in an automotive parts warehouse containing visually similar components. It develops a warehouse aisle-congestion simulator and a wave-release controller using pick timestamps, worker counts, order waves, aisle capacities, and worker paths.

The system must expose the trade-offs among throughput, waiting time, operational cost, emissions, and reliability. It must compare baseline and controlled operation, run at least three operating scenarios, perform sensitivity analysis, show fallback behaviour when location/sensor/network data is unavailable, and provide an end-to-end working prototype with at least three edge/failure cases. The project also requires stakeholder assumptions, architecture, data schema, risk register, user guide, reproducible repository, target-versus-measured analysis, and short stakeholder validation.

This report covers the Review 3 implementation work while clearly identifying what still requires an actual run or real stakeholder evidence.

## 2. Review 1 and Review 2 foundation

The existing project has a modular Python implementation with:

- Synthetic warehouse dataset generation and a 12-aisle, three-zone layout.
- Worker/order assignment, aisle paths, pick steps, capacities, and release timestamps.
- Congestion calculation and LOW / MEDIUM / HIGH / CRITICAL classification.
- Wave-release decisions: ALLOW, DELAY, and BLOCK, including anti-starvation and manual fallback.
- Baseline-versus-controlled simulation and operational KPI calculations.
- Visual-similarity modelling for a 12-part automotive catalogue, including verification overhead and probabilistic mispick/return delay.
- Store-and-forward queueing with FIFO buffering, optional CSV spool, outage monitoring, and replay reconciliation.
- Congestion-aware path reordering/rerouting.
- Scenario functions A–H, sensitivity analysis, multi-seed validation, risk register, and stakeholder assumptions.

The Review 1 feedback specifically requested deeper modelling of visually similar parts, store-and-forward behaviour during telemetry outages, and formal risk/stakeholder documentation. These were implemented in the Review 2 baseline. The uploaded Review 2 feedback records acceptance with full marks and requires the remaining scope to be completed and evidenced for Review 3.

## 3. Review 3 implementation

All changes described below are on the separate `review3-implementation` branch. They have not been merged into `main`.

### 3.1 Timestamped worker movement trace

The simulation now records movement segments for each worker and order:

- Worker ID and order ID.
- Event type: TRAVEL or PICK.
- Aisle ID.
- Segment start and end simulation timestamps.
- Start and end warehouse-grid coordinates.

The trace is exposed through `WarehouseSimulation.get_movement_trace()`. This allows the dashboard to display a worker at an interpolated position at a selected simulation time. The trace is generated from the existing simulation path and pick execution rather than from an unrelated demonstration dataset. Controlled execution also checks projected occupancy (`current workers + entering worker`) before each aisle entry, rather than checking only the current count at the first aisle. A dedicated test covers a three-order, capacity-three hotspot case. Manual fallback combines its conservative fallback estimate with locally cached occupancy.

### 3.2 Interactive 2D warehouse dashboard

The optional Streamlit/Plotly dashboard is in `dashboard/app.py`. It provides:

- Normal, Peak, and Extreme synthetic operating scenarios.
- A wave-release controller on/off control.
- Simulation-time selection.
- Warehouse aisle locations, aisle capacity and congestion display.
- Worker markers derived from the timestamped movement trace.
- Order completion, average waiting time, throughput, and rerouting summaries.

Install the optional packages and launch the dashboard using:

```bash
pip install -r requirements-dashboard.txt
streamlit run dashboard/app.py
```

The dashboard is a simulation interface. It does not connect to live warehouse sensors, badge gates, MQTT brokers, or physical workers.

### 3.3 HMAC telemetry integrity integrated with the simulation

The Review 2 risk register identified sensor spoofing as a high-impact risk: false low-congestion readings could cause unsafe worker releases. Review 3 adds `src/telemetry_security.py`, which provides:

- HMAC-SHA256 message signing.
- Deterministic canonical serialization of the signed payload.
- Constant-time signature comparison.
- Timestamp freshness checks.
- Nonce-based replay detection.

The authenticated occupancy payload contains the aisle ID, observed worker count, and aisle capacity. The simulation verifies the packet before using the occupancy reading for a controller decision. If verification fails, the packet is rejected and the controller is directed to the existing MANUAL FALLBACK behaviour. When store-and-forward is enabled, the fallback decision is queued for later replay/reconciliation.

The integration is in `src/simulation.py`; the security component is therefore used by the simulation path and is not merely an isolated module.

**Security boundary:** This is a simulation-level integrity control. It is not a production IoT security deployment. Live device identity, TLS, broker authentication, secure key storage, key rotation, access control, and penetration testing remain future work. The deterministic scenario uses a simulation-only test key; it must not be reused as a production secret.

### 3.4 Telemetry tamper experiment

Scenario I, `run_telemetry_tamper_scenario()`, generates a 300-order peak workload by default and deliberately modifies a deterministic 10% subset of signed occupancy packets after signing. The experiment records accepted/rejected packets, rejection reasons, controller fallback decisions, and store-and-forward queue/replay summaries.

The scenario is designed to demonstrate the full defensive flow:

**Synthetic occupancy → HMAC signing → packet alteration → signature rejection → MANUAL FALLBACK → queueing → reconnection replay.**

CI experiment run #54 selected 30 of 300 order IDs for deliberate tampering. Across retry attempts it checked 1,450 packets, accepted 1,394, rejected 56 invalid signatures, and queued/replayed 56 fallback decisions. All 300 simulated orders completed. The repeated rejection count is higher than 30 because some tampered orders retried their first-aisle admission.

### 3.5 Reproducible experiment runner

The new `run_review3_experiments.py` script calls the existing scenario and analysis functions and writes generated CSV/JSON evidence under `results/`. It includes:

- Normal operation.
- Peak congestion: baseline and controlled.
- Extreme load: baseline and controlled.
- Sensor/network failure with manual fallback.
- Telemetry tampering with HMAC rejection and store-and-forward.
- Safe-threshold sensitivity sweep.
- Five-seed validation using seeds 42, 101, 202, 303, and 404.

Generated artifacts include a consolidated KPI summary, telemetry audit log, controller log, sensitivity results, multi-seed runs, multi-seed summary, and run metadata. The values are computed when the script is executed; the report does not insert invented values.

Run it from the repository root:

```bash
python run_review3_experiments.py
```

## 4. Architecture

```text
Synthetic order/pick data
        |
        v
Warehouse layout + aisle capacities + worker paths
        |
        v
Simulated occupancy telemetry
        |
        v
HMAC signature / freshness / replay verification
        |
        +---- valid ----> Congestion calculation
        |                       |
        |                       v
        |                Wave-release controller
        |                ALLOW / DELAY / BLOCK
        |                       |
        |                       v
        |                Worker execution
        |                pick + travel + reroute
        |                       |
        |                       v
        |                Timestamped movement trace
        |
        +---- invalid/offline -> MANUAL FALLBACK
                                  |
                                  v
                         Store-and-forward queue
                                  |
                         Network restoration
                                  |
                         Replay / reconciliation

Simulation results -> KPI metrics -> CSV experiment evidence
                   -> Streamlit / Plotly dashboard
```

## 5. Data schema and key assumptions

The synthetic input dataset includes the following fields:

| Field | Meaning |
|:---|:---|
| `worker_id` | Assigned warehouse worker |
| `order_id` | Unique order identifier |
| `aisle_id` | Aisle selected for the pick |
| `zone` | Warehouse zone |
| `aisle_capacity` | Maximum modelled simultaneous aisle occupancy |
| `worker_entry_time` / `worker_exit_time` | Generated pick interval timestamps |
| `pick_time` | Generated pick duration |
| `path` / `path_step` / `total_steps` | Order route and sequence |
| `distance_m` | Generated route distance |
| `release_time` | Requested order release timestamp |
| `scenario` | Operating scenario label |

The existing peak scenario preserves the repository's 120-worker, 350-order, 12-aisle configuration. Other existing scenarios intentionally use different worker/order volumes to represent low, normal, and extreme loads.

The model uses synthetic data and assumptions including a 1.0 m/s walking speed, fixed aisle coordinates/capacities, static aisle-to-part mapping, and configurable cost/emissions factors. These assumptions are documented in `docs/STAKEHOLDER_ASSUMPTIONS.md`; they are not substitutes for measurements from a real warehouse.

## 6. Scenarios and failure cases

The existing repository provides low-load, normal, peak, extreme, sensor/network failure, store-and-forward, visual-similarity, and dynamic-rerouting scenarios. Review 3 adds the telemetry tamper scenario.

The following defensive cases are covered by code and tests:

1. **Tampered telemetry:** payload is changed after signing; HMAC verification rejects it and the simulation falls back to manual pacing. The integration test also checks store-and-forward queueing.
2. **Stale telemetry:** packets older than the configured freshness window are rejected.
3. **Replay attack:** a nonce already accepted by the authenticator is rejected if reused.
4. **Future-dated packet:** timestamps beyond the allowed future tolerance are rejected.
5. **Sensor/network outage:** the existing manual fallback and store-and-forward queue handle missing telemetry and replay decisions after reconnection.
6. **Invalid key/signature:** empty keys, wrong keys, and invalid signatures are rejected or raise the documented validation error.

The automated tests cover these cases. GitHub Actions run #31 executed the complete 75-test suite, including the new telemetry security and integration tests, and reported 75 passed in 3.19 seconds.

## 7. Experiments, targets, and error analysis

The assigned objective requires a throughput improvement while keeping congestion below a safe threshold, with cost, time, emissions, and reliability trade-offs exposed. The Review 3 runner measures:

- Throughput (orders/hour).
- Average and maximum waiting time.
- Average and maximum aisle congestion and critical events.
- Worker travel distance.
- Estimated operational cost and emissions.
- Verification overhead and mispick counts.
- Rerouted orders.
- Order completion reliability (completed orders divided by requested orders).
- Telemetry packets accepted/rejected and store-and-forward queue/replay activity.

### 7.1 Historical Review 2 comparison (not a Review 3 rerun)

The Review 2 report recorded the following peak comparison:

| Metric | Baseline | Controlled | Interpretation |
|:---|---:|---:|:---|
| Throughput | 200.83 orders/hr | 200.83 orders/hr | Maintained; no throughput increase shown |
| Critical congestion events | 138 | 132 | 4.3% fewer events in the reported run |
| Average waiting time | 0 s | 9.1 s | Controlled release introduced staging delay |
| Total estimated cost | $1,170 | $1,183 | 1.1% higher in the reported run |
| CO₂e | Baseline | Approximately baseline | Reported difference below 0.5% |

These are values recorded in the Review 2 report, not newly measured Review 3 results. They show that the earlier comparison maintained throughput and reduced critical events slightly, but did not demonstrate the strict requirement of throughput improvement. The Review 3 runner is intended to repeat the comparisons and provide fresh evidence.

### 7.2 Review 3 measured results

The expanded GitHub Actions workflow executed the Review 3 experiment runner with seed 42 and five-seed validation (42, 101, 202, 303, 404). The generated CSV files were uploaded as the `review3-experiment-evidence` artifact in [GitHub Actions run #54](https://github.com/ramyaramesh2006/coe_project/actions/runs/45189372797).

| Scenario | Mode | Completed / requested | Throughput (orders/hr) | Avg wait (s) | Max congestion (%) | Critical events | Cost ($) | CO₂e (kg) |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| Normal | Controlled | 300/300 | 169.73 | 15.20 | 166.67 | 53 | 1,213.18 | 4.1917 |
| Peak | Baseline | 350/350 | 201.34 | 0.00 | 266.67 | 157 | 1,357.60 | 4.5945 |
| Peak | Controlled | 350/350 | 199.72 | 69.17 | 233.33 | 161 | 1,440.66 | 4.5765 |
| Extreme | Baseline | 450/450 | 252.13 | 0.00 | 366.67 | 234 | 1,699.75 | 5.6835 |
| Extreme | Controlled | 450/450 | 242.37 | 185.40 | 300.00 | 252 | 2,070.15 | 5.6385 |
| Sensor/network failure | Manual fallback | 300/300 | 170.31 | 26.70 | 65.00* | 0* | 1,221.41 | 4.0072 |
| Telemetry tamper | HMAC + fallback + S&F | 300/300 | 169.02 | 60.30 | 200.00 | 123 | 1,299.80 | 3.8767 |

`*` In the sensor/network failure row, congestion is the configured fallback estimate (65%), not a live physical occupancy measurement. The zero critical-event figure therefore describes the fallback telemetry view, not independently observed warehouse safety.

All rows completed the requested simulated orders (100% modelled order-completion reliability). This is a simulation completion ratio, not a real warehouse uptime or safety certification.

### 7.3 Target attainment and trade-off analysis

The configured safe release threshold is 75%. The controller now checks projected occupancy at each entry, but the aggregate simulation still records maximum congestion above 75% in peak and extreme runs. The target of keeping the *measured maximum* below the safe threshold is therefore **not achieved** in these full-load experiments. The dedicated single-hotspot test passes, but it does not establish a global guarantee across all arrival schedules.

Peak controlled versus baseline:
- Throughput: 201.34 → 199.72 orders/hr (**−0.80%**).
- Maximum congestion: 266.67% → 233.33% (**−33.34 percentage points; 12.50% relative reduction**), but still above 75%.
- Critical events: 157 → 161 (**+2.55%**, worse).
- Average wait: 0 → 69.17 s.
- Estimated cost: $1,357.60 → $1,440.66 (**+6.12%**).
- CO₂e: 4.5945 → 4.5765 kg (**−0.39%**).
- Travel distance: 30,630 → 30,510 m (**−0.39%**).

Extreme controlled versus baseline:
- Throughput: 252.13 → 242.37 orders/hr (**−3.87%**).
- Maximum congestion: 366.67% → 300.00% (**−66.67 percentage points; 18.18% relative reduction**), but still above 75%.
- Critical events: 234 → 252 (**+7.69%**, worse).
- Average wait: 0 → 185.40 s.
- Estimated cost: $1,699.75 → $2,070.15 (**+21.79%**).
- CO₂e: 5.6835 → 5.6385 kg (**−0.79%**).
- Travel distance: 37,890 → 37,590 m (**−0.79%**).

Five-seed validation:
- Mean baseline throughput: 197.30 orders/hr; mean controlled throughput: 194.69 orders/hr (**−1.32%**).
- Mean baseline critical events: 152.4; mean controlled: 150.2 (mean reduction **1.49%**, standard deviation 2.43 percentage points; range −2.55% to +3.85%).
- Mean controlled waiting time: 75.77 s (standard deviation 13.26 s).
- Mean baseline cost: $1,360.96; mean controlled cost: $1,456.82 (**+7.04%**).

Sensitivity analysis (seed 42) shows the decision changes materially between the 65% and 70% threshold settings. At 60%, throughput was 185.01 orders/hr, average wait 297.17 s, and cost $1,764.05. At 65%, throughput was 181.98 orders/hr, average wait 283.54 s, and cost $1,752.32. At 70% and 75%, throughput was 195.13 orders/hr, average wait 56.83 s, and cost $1,413.58. At 80–90%, throughput was 192.85 orders/hr, average wait 63.60 s, and cost $1,409.61. The maximum congestion remained 200–300% across these sweeps, so changing the threshold alone did not satisfy the global safe-congestion target.

### 7.4 Error analysis and decision

The measured results show the trade-off clearly: projected occupancy gating reduces some congestion and rerouting/travel effects, but in the tested peak and extreme cases it introduces substantial waiting and cost, does not improve throughput, and does not keep maximum congestion below 75%. Five-seed mean throughput is also lower in controlled mode. The project must not claim that the assigned throughput-and-safe-congestion objective has been fully met.

The results indicate that the current order-by-order execution and arrival scheduling still permit future/overlapping reservations to produce high aggregate occupancy even when individual entry decisions pass their projected-occupancy check. A more complete event-queue/reservation model and calibrated arrival-time handling are needed before claiming a global congestion cap. The threshold sensitivity sweep alone is insufficient.

For any numeric target with a specified value, absolute error is `|measured − target|`; relative error is `absolute error / |target| × 100` when the target is non-zero. The project has no real warehouse ground-truth dataset, so simulation-to-real-world prediction error cannot yet be calculated. All figures above are synthetic simulation outputs, not real operational measurements.

## 8. Testing and validation status

A source-level count of test functions gives:

| Test file | Test functions |
|:---|---:|
| `test_congestion.py` | 8 |
| `test_controller.py` | 8 |
| `test_simulation.py` | 7 |
| `test_visual_similarity.py` | 22 |
| `test_error_boundaries.py` | 17 |
| **Existing Review 2 source total** | **62** |
| `test_movement_trace.py` | 2 |
| `test_telemetry_security.py` | 8 |
| `test_telemetry_integration.py` | 3 |
| `test_projected_occupancy_gate.py` | 1 |
| **Review 3 additions** | **14** |
| **Total** | **76** |

**Validation result:** GitHub Actions run #54 reported **76 passed in 1.81 seconds** on Python 3.11. In the same run, the Review 3 experiment script completed, the CSV/JSON evidence artifact uploaded successfully, and the Streamlit dashboard health endpoint returned HTTP 200.

Required validation command:

```bash
python -m pytest tests/ -v
```

The dashboard smoke test confirms that Streamlit starts and returns HTTP 200 from its health endpoint. This is a startup check, not a manual visual/usability review.

## 9. Risk management and stakeholder assumptions

The existing risk register contains 14 identified risks and likelihood-impact scoring. Review 3 updates R-008: HMAC-SHA256 integrity, freshness, and replay verification are now integrated into the simulation telemetry path, with invalid data routed to fallback. Residual risk remains because production device identity, secure key management, TLS, broker authentication, and security testing are not implemented.

R-010 (simulation-to-warehouse realism) remains open. The model still uses centroid/grid coordinates and constant walking speed; microscopic crowd dynamics and physical validation are future work. Emissions estimates also remain limited to the existing battery-electric cart distance factor and are not a full lifecycle assessment.

Stakeholder roles and assumptions remain documented in `docs/STAKEHOLDER_ASSUMPTIONS.md`. A short walkthrough and anonymous feedback template is available in `docs/STAKEHOLDER_VALIDATION.md`. **A real stakeholder walkthrough has not yet been conducted**, so no participant ratings or feedback are claimed.

## 10. User guide

From the repository root:

```bash
# 1. Install core dependencies
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 2. Run existing project experiments
python run_experiments.py

# 3. Run Review 3 experiments and generate CSV evidence
python run_review3_experiments.py

# 4. Run all automated tests
python -m pytest tests/ -v

# 5. Install optional dashboard packages and launch dashboard
pip install -r requirements-dashboard.txt
streamlit run dashboard/app.py
```

Generated Review 3 CSV and JSON evidence is written under `results/`. Review those files before copying numerical results into a final submission.

## 11. Remaining work before final submission

1. Keep the 76-test suite passing; GitHub Actions run #54 reports 76 passed in 1.81 seconds.
2. Retain and review the generated experiment CSV/JSON evidence from run #54; the measured results are now included in this report.
3. Improve global event scheduling/reservation because measured maximum congestion still exceeds 75%, and controlled throughput falls in peak/extreme runs.
4. Manually inspect the dashboard, capture genuine screenshots, and complete usability feedback. CI confirms startup only.
5. Conduct the short stakeholder walkthrough and complete the feedback record.
6. Review residual security and modelling risks; do not describe the simulation as a live or production warehouse deployment.
7. Update the report after the remaining validations, then request review and merge the draft pull request only after approval.

## 12. Conclusion

Review 3 adds a timestamped worker movement trace, an interactive 2D simulation dashboard, HMAC-authenticated telemetry integrated into the controller path, a tamper/fallback/store-and-forward experiment, and a reproducible experiment runner. It also adds movement, security, and integration tests and updates the repository documentation and risk record.

The implementation is on a separate branch and preserves the existing Review 1/2 project foundation. The 76-test suite passed in GitHub Actions run #54; the experiment runner, artifact upload, and dashboard startup smoke test also passed. Actual measurements are included above. However, the strict throughput-improvement and global safe-congestion objectives were not achieved in the tested peak/extreme runs, the dashboard still needs manual visual review, and stakeholder validation is pending. These limitations are reported openly rather than hiding them or changing measured values.
