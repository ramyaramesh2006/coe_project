# Review 3 Progress Report
## Aisle Congestion Simulator and Wave-Release Controller for Automotive Parts Warehouse Containing Visually Similar Components

**Department:** Computer Science & Engineering (Cyber Security)  
**Review phase:** Review 3 — 30% project-completion submission  
**Repository:** https://github.com/ramyaramesh2006/coe_project  
**Development branch:** `review3-implementation`  
**Pull request:** https://github.com/ramyaramesh2006/coe_project/pull/1  
**Report status:** Implementation documented; execution and stakeholder evidence pending

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

The trace is exposed through `WarehouseSimulation.get_movement_trace()`. This allows the dashboard to display a worker at an interpolated position at a selected simulation time. The trace is generated from the existing simulation path and pick execution rather than from an unrelated demonstration dataset.

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

The scenario and its audit outputs are generated by the Review 3 experiment runner; its numerical output has not yet been executed and is not claimed as measured in this report.

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

The automated tests have been added for these cases. Their source count is reported below, but execution is still pending.

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

### 7.2 Review 3 target-versus-measured status

| Measure | Target / decision rule | Review 3 measured value | Status |
|:---|:---|:---|:---|
| Throughput | Controlled throughput greater than baseline | Pending experiment execution | Not yet demonstrated |
| Safe congestion | Maximum measured congestion at or below the configured 75% target | Pending experiment execution | Not yet verified |
| Waiting time | Report the increase/decrease against baseline | Pending experiment execution | Pending |
| Cost | Report labour, travel, delay, and mispick cost trade-offs | Pending experiment execution | Pending |
| Emissions | Report modelled CO₂e difference | Pending experiment execution | Pending |
| Reliability | Report completed/requested orders and failure recovery | Pending experiment execution | Pending |
| Security | Tampered packets rejected and fallback invoked | Covered by integration test source; execution pending | Not yet verified by run |

The 75% value is the configured safe release threshold used by the current experiment setup. It must not be confused with a guarantee that every sampled aisle congestion value remains below 75%; the actual maximum must be read from the generated result.

### 7.3 Error analysis method

After running the experiment script, compute:

- Throughput change (%) = `(controlled throughput − baseline throughput) / baseline throughput × 100`.
- Congestion margin (percentage points) = `75 − measured maximum congestion`. A negative value indicates the safe target was exceeded.
- Cost change (%) = `(controlled cost − baseline cost) / baseline cost × 100`.
- Emissions change (%) = `(controlled CO₂e − baseline CO₂e) / baseline CO₂e × 100`.
- Completion reliability (%) = `completed orders / requested orders × 100`.

For any numeric target with a specified value, absolute error is `|measured − target|`; relative error is `absolute error / |target| × 100` when the target is non-zero. The project currently has no real warehouse ground-truth dataset, so simulation-to-real-world prediction error cannot be calculated yet. Review 3 measurements must be reported as simulated experimental results, not real operational measurements.

## 8. Testing and validation status

A source-level count of test functions gives:

| Test file | Existing / new tests |
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
| **Review 3 additions** | **13** |
| **Expected source total** | **75** |

**Validation result:** GitHub Actions run #31 reported **75 passed in 3.19 seconds** on Python 3.11. The count and pass result include all three Review 3 test files. The later experiment/dashboard CI steps are a separate validation run and are not yet confirmed.

Required validation command:

```bash
python -m pytest tests/ -v
```

The optional dashboard launch check and Review 3 experiment runner are included in the expanded CI workflow. Their results are pending the next workflow run.

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

1. Run all 75 expected tests and fix any failures; attach the actual terminal/CI result.
2. Run `run_review3_experiments.py`; use generated CSVs to populate the measured-result table and error analysis.
3. Check whether throughput increases and measured congestion stays within the agreed safe limit. If either target is missed, report it and explain the trade-off rather than changing the numbers.
4. Launch the dashboard and capture genuine screenshots.
5. Conduct the short stakeholder walkthrough and complete the feedback record.
6. Review residual security and modelling risks; do not describe the simulation as a live or production warehouse deployment.
7. Update the report with actual test and experiment evidence, then request review and merge the draft pull request only after approval.

## 12. Conclusion

Review 3 adds a timestamped worker movement trace, an interactive 2D simulation dashboard, HMAC-authenticated telemetry integrated into the controller path, a tamper/fallback/store-and-forward experiment, and a reproducible experiment runner. It also adds movement, security, and integration tests and updates the repository documentation and risk record.

The implementation is on a separate branch and preserves the existing Review 1/2 project foundation. However, the full Review 3 evidence is not yet complete: tests and experiments have not been executed in the current environment, the dashboard has not been browser-verified, and stakeholder validation is pending. The next submission should include the generated measurements and real validation evidence rather than treating source-code additions as proof of successful results.
