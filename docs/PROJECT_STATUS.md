# Project Status: Aisle Congestion Simulator and Wave-Release Controller

**Academic Milestone:** Review 3 implementation in progress  
**Department:** Computer Science & Engineering (Cyber Security)  
**Base:** Review 2 prototype (scenarios A–H)

---

## 1. Current implementation

The Review 2 baseline contains a discrete-event warehouse simulation, wave-release controller, congestion metrics, visual-similarity-aware pick model, store-and-forward offline queue, and dynamic aisle rerouting.

Review 3 work on branch `review3-implementation` currently adds:

- **Worker movement trace:** timestamped `TRAVEL` and `PICK` segments with worker/order IDs and grid coordinates, exposed by `WarehouseSimulation.get_movement_trace()`.
- **Interactive 2D dashboard:** `dashboard/app.py`, built with Streamlit and Plotly. It displays a synthetic floor layout, worker positions, aisle congestion/capacity, and order metrics for Normal, Peak, and Extreme scenarios.
- **Telemetry integrity component:** `src/telemetry_security.py` uses HMAC-SHA256, constant-time comparison, timestamp freshness, and nonce-based replay detection.
- **Automated test workflow:** `.github/workflows/tests.yml` runs the pytest suite on the Review 3 branch and pull requests to main.
- **Review 3 tests:** two movement-trace tests and eight telemetry-security tests have been added.

These additions are on the Review 3 development branch and are not merged into `main`.

## 2. Validation status

- The existing Review 2 test guide lists 58 tests.
- Review 3 adds 10 tests, making 68 the expected suite count.
- **Review 3 CI status: pending confirmation.** The expected count is not a claim that all tests pass.
- Dashboard execution has not yet been verified in a live browser session.

Run locally from the repository root:

```bash
python -m pytest tests/ -v
pip install -r requirements-dashboard.txt
streamlit run dashboard/app.py
```

## 3. Remaining Review 3 work

1. Confirm CI results and fix any failing tests.
2. Connect signed telemetry verification to a simulated sensor-data path and add a spoof/tamper experiment.
3. Add a repeatable baseline-versus-controlled experiment report with sensitivity, cost, time, emissions, and reliability comparisons.
4. Add at least three clearly documented failure/edge scenarios and quantify fallback behaviour.
5. Conduct and record short stakeholder/user validation; do not invent participant feedback.
6. Evaluate whether ML wave batching and AGV/MAPF integration are required by the final Review 3 rubric; they are not implemented in this branch yet.
7. Update screenshots, results, limitations, and final report from actual runs.

## 4. Scope and limitations

The dashboard uses synthetic simulation data. It is not a live warehouse deployment, does not connect to MQTT sensors or physical badge gates, and does not provide real AGV control. HMAC is currently a reusable simulation-layer security component; production use would also require TLS, authenticated device identity, secure key provisioning/rotation, and operational monitoring.
