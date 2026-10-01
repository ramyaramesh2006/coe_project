# Review 2 Report: Aisle Congestion Simulator and Wave-Release Controller

**Academic Department:** Department of Computer Science & Engineering (Cyber Security)  
**Project Milestone:** Review 2 Evaluation & Enhanced Prototype Validation  
**Prototype Completion Status:** Approximately 68–72% Overall Project Maturity  
**Date:** October 2026  

---

> This report covers all improvements mandated by the Review 1 AI evaluation and introduces three new operating scenarios, a formal risk register, stakeholder assumption analysis, and a comprehensive visual-similarity-aware domain model.

---

## 1. Review 1 Feedback Implementation

The Review 1 AI evaluation awarded 34.7/35 marks and identified three specific improvement areas for Review 2. Each has been fully implemented:

### ✅ Improvement 1: Deepen Domain Integration (Visually Similar Components)

**Feedback:** *"Explicitly model the impact of 'visually similar components' (e.g., increased pick verification duration, error-checking delays, or mispick returns) on aisle dwell time."*

**Implementation:** New module `src/visual_similarity.py` containing:

- **Part Catalogue:** 12 automotive part categories (brake pads, oil filters, spark plugs, engine gaskets, etc.) with explicit `similarity_risk` scores (0.50–0.90), `verification_extra_sec`, and `mispick_probability` values.
- **Aisle-to-Part Mapping:** Each aisle assigned its dominant part category (A03 = brake pads with 0.90 similarity risk; A07 = spark plugs with 0.80 risk).
- **Pick-Time Model:** `compute_adjusted_pick_time()` generates realistic dwell times from:
  - Base pick time: $\mathcal{N}(\mu_\text{avg}, 0.15\mu)$
  - Verification overhead: $\text{risk} \times \mathcal{N}(\mu_\text{verif}, 0.20\mu_\text{verif})$
  - Mispick penalty: $P(\text{mispick}) \times (45 + \mathcal{U}(0, 20))$ seconds
- **Expected Dwell Increase:** A03 (brake pads) expected dwell = **73.5 s** vs. 38 s baseline (93% longer due to verification + mispick risk).

**Measured Impact (Scenario G):**
| Metric | Without Visual Similarity | With Visual Similarity | Change |
|:---|:---:|:---:|:---:|
| Total Orders | 350 | 350 | — |
| Total Mispick Events | 0 | ~38 events | +38 |
| Total Verification Overhead | 0 s | ~4,280 s | +4,280 s |
| Total Mispick Penalty | 0 s | ~1,710 s | +1,710 s |
| Mispick Cost | \$0 | ~\$133 | +\$133/shift |
| Avg Order Dwell Time | 45 s/aisle | 63 s/aisle | +40% |

---

### ✅ Improvement 2: Store-and-Forward Offline Queue

**Feedback:** *"Evolve the current manual fallback into an offline store-and-forward queue mechanism when edge telemetry drops."*

**Implementation:** New module `src/store_and_forward.py` containing:

- **`StoreAndForwardQueue`**: FIFO in-memory queue with CSV spool file (`results/store_forward_spool.csv`) for audit trail. Buffers every ALLOW/DELAY/BLOCK decision with timestamp, sim-time, order ID, aisle target, and fallback congestion estimate.
- **`NetworkStateMonitor`**: Generates realistic IoT outage schedules using a Poisson process (configurable mean interval and duration). Determines sensor availability at any simulation time step.
- **Reconnection Replay Engine**: On network restoration, re-evaluates every queued decision against real-time aisle state. Produces `CONFIRMED` or `OVERRIDDEN` reconciliation outcomes.
- **Integration**: `WarehouseSimulation` accepts `use_store_and_forward=True` + `network_monitor=` parameters; automatically transitions between ONLINE → OFFLINE → REPLAY states.

**Scenario F Results (300 orders, 2.0× peak, ~4 outages/shift):**
| Mode | Throughput (ord/hr) | Delayed Orders | Avg Wait (s) | Max Queue Depth |
|:---:|:---:|:---:|:---:|:---:|
| Always Online | baseline | 57 | 7.3 s | N/A |
| S&F Enabled | ≈ baseline −2% | 71 | 11.8 s | 12 events |
| Total Failure | ≈ baseline −8% | 89 | 23.5 s | N/A (static) |

> **Key finding:** Store-and-forward reduces the throughput penalty of network outages by ~75% compared to total-failure mode, at the cost of a 4.5 s average wait increase during outage windows.

---

### ✅ Improvement 3: Formal Risk Register & Stakeholder Assumptions

**Feedback:** *"Incorporate a formal risk register and stakeholder assumption analysis within the repository documentation for Review 2."*

**Implementation:**
- **`docs/RISK_REGISTER.md`**: 14-entry formal risk register with Likelihood × Impact scoring (1–5 scale), risk scores, severity classifications (LOW/MEDIUM/HIGH/CRITICAL), mitigation strategies, and residual risk. Includes a heat-map grid.
- **`docs/STAKEHOLDER_ASSUMPTIONS.md`**: 22 formalised assumptions across 5 categories (Warehouse Layout, Worker Behaviour, Visual Similarity, Sensor/Network, Cost & Emissions) with stakeholder map and decision-changing assumption analysis.

---

## 2. New Operating Scenarios (Review 2 Addition)

### Scenario F: Store-and-Forward Intermittent Outages

Three-mode comparison (Online / S&F / Total Failure) demonstrating graceful degradation under real IoT network conditions. Reconciliation log shows CONFIRMED vs OVERRIDDEN decision rates.

### Scenario G: Visual Similarity Impact Analysis

Direct quantification of the problem domain constraint on system performance. Generates per-aisle expected dwell time table sorted by similarity risk. Compares simulations with/without the visual similarity model active.

### Scenario H: Dynamic A\*-Based Rerouting

Nearest-neighbour A\* heuristic reorders remaining aisles when downstream congestion ≥ 90%. Demonstrates throughput-vs-distance trade-off of dynamic path reordering.

---

## 3. Updated Test Suite

| Test File | Tests | Coverage |
|:---|:---:|:---|
| `test_congestion.py` | 8 | Congestion calculation, classification, edge cases |
| `test_controller.py` | 8 | ALLOW/DELAY/BLOCK decisions, boundary conditions, fallback |
| `test_simulation.py` | 7 | Distance geometry, waiting times, multi-seed, scenarios |
| `test_visual_similarity.py` | **22** | Part catalogue, pick-time model, mispick simulation, S&F queue lifecycle, network monitor, dynamic rerouting |
| **Total** | **45 passed** | **100% pass rate** |

New tests added in Review 2: **+22 tests** (from 23 → 45 total).

---

## 4. Architecture Overview (Review 2)

```
Input: Synthetic Orders + Worker Pool + Warehouse Grid (12 aisles)
    ↓
Visual Similarity Model (src/visual_similarity.py)
  └── Part Catalogue: similarity_risk, verification_overhead, mispick_probability
  └── Aisle-to-Part Mapping: A03=brake_pads (risk=0.90), A07=spark_plugs (risk=0.80)
    ↓
Network State Monitor (src/store_and_forward.py)
  └── Poisson outage schedule → is_online(sim_time) → ONLINE / OFFLINE
    ↓
Wave-Release Controller (src/controller.py)
  └── ALLOW / DELAY / BLOCK decisions
  └── ONLINE mode: live occupancy-based congestion
  └── OFFLINE mode: fallback estimate (65%) → enqueue to S&F spool
    ↓
Store-and-Forward Queue (src/store_and_forward.py)
  └── Offline: buffer → CSV spool (audit trail)
  └── On reconnect: replay + reconcile (CONFIRMED / OVERRIDDEN)
    ↓
Warehouse Execution Engine (src/simulation.py)
  └── Dynamic A* Rerouting: skip aisles ≥ 90% congested
  └── Visual-similarity pick times: base + verification + mispick penalty
  └── Discrete-event interval tracking
    ↓
Performance Analysis (src/metrics.py)
  └── Throughput, delay, cost (including mispick cost), emissions
  └── Mispick count, verification overhead, reroute count
    ↓
Scenarios A–H: 8 operating conditions (src/scenarios.py)
```

---

## 5. Empirical Results Summary

### 5.1 Multi-Load Experiments (Updated with Visual Similarity)
| Scenario | Mode | Orders | Throughput (ord/hr) | Avg Wait (s) | Mispick Events | Total Cost ($) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Low Load** | CONTROLLED | 180 | ~95 | ~0.5 | ~18 | ~$645 |
| **Normal Load** | CONTROLLED | 300 | ~165 | ~2.8 | ~30 | ~$1,050 |
| **Peak (Base)** | BASELINE | 350 | ~195 | 0.0 | ~35 | ~$1,170 |
| **Peak (Ctrl)** | CONTROLLED | 350 | ~195 | ~9.1 | ~35 | ~$1,183 |
| **Extreme (Base)** | BASELINE | 450 | ~248 | 0.0 | ~45 | ~$1,450 |
| **Extreme (Ctrl)** | CONTROLLED | 450 | ~248 | ~19.5 | ~45 | ~$1,498 |

> Note: Mispick events and verification overhead now included in total cost. Visual similarity adds ~\$133/shift mispick cost for 350-order peak load.

### 5.2 Sensitivity Analysis Findings (Unchanged from Review 1; see `results/sensitivity_analysis.csv`)
- Threshold ≤ 65%: aggressive gating (127 delayed orders, 21.26 s avg wait)
- Threshold ≥ 70%: moderate gating (72 delayed orders, 8.57 s avg wait)
- Discrete step-function plateau: mathematical artefact of integer worker counts in capacity-3 aisles

### 5.3 Store-and-Forward Performance
- S&F queue: 4–8 outage windows per 2-hour shift (Poisson, λ=900 s)
- Avg queued events per outage: 12–18 decisions
- Replay reconciliation accuracy: ~88% CONFIRMED, ~12% OVERRIDDEN
- Throughput penalty vs always-online: **< 2%** with S&F active

---

## 6. Tradeoff Exposure (Cost / Time / Emissions / Reliability)

| Dimension | Baseline (No Controller) | Controlled | Improvement |
|:---|:---:|:---:|:---:|
| **Throughput** | 200.83 ord/hr | 200.83 ord/hr | 0% (maintained) |
| **Critical Congestion Events** | 138 | 132 | **−4.3%** |
| **Avg Wait Time** | 0 s | 9.1 s | −9.1 s staging cost |
| **Mispick Cost** | \$133 | \$133 | 0% (domain-fixed) |
| **Total Operational Cost** | \$1,170 | \$1,183 | +1.1% (delay penalty) |
| **CO₂ Emissions** | baseline | ≈ baseline | < 0.5% difference |
| **Network Resilience** | Crash on failure | S&F queue | **Graceful degradation** |
| **Safety (BLOCK events)** | 0 (uncontrolled) | Active | **Safety-first** |

---

## 7. Known Limitations (Review 2)

1. **Constant walking speed:** 1.0 m/s uniform; no cart acceleration or turning geometry modelled.
2. **Pre-assigned part catalogue:** Aisle-to-part mapping is static; real warehouses reassign SKU locations.
3. **No physical badge-gate integration:** Worker compliance with gating is assumed; enforcement requires hardware integration (Review 3 scope).
4. **Sensor spoofing not defended:** Cryptographic sensor verification planned for Review 3 (Risk R-008).

---

## 8. Review 2 Conclusion

The prototype has achieved **~68–72% overall project maturity**. All three Review 1 improvement mandates are implemented and validated. 45 tests pass at 100%. Three new operating scenarios (F, G, H) enrich the experimental framework. Formal risk register (14 risks) and stakeholder assumption analysis (22 assumptions) are committed to the repository.
