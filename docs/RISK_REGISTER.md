# Risk Register — Aisle Congestion Simulator & Wave-Release Controller

**Document:** Formal Risk Register  
**Project:** Aisle Congestion Simulator and Wave-Release Controller for Automotive Parts Warehouse  
**Review Stage:** Review 2 (70% Prototype Maturity)  
**Date:** October 2026  
**Owner:** CSE Cyber Security Capstone Team  

---

## 1. Risk Classification Scale

| Likelihood | Description |
|:---:|:---|
| 1 – Rare | < 10% chance of occurrence |
| 2 – Unlikely | 10–30% chance |
| 3 – Possible | 30–60% chance |
| 4 – Likely | 60–85% chance |
| 5 – Almost Certain | > 85% chance |

| Impact | Description |
|:---:|:---|
| 1 – Negligible | No measurable effect on throughput or safety |
| 2 – Minor | < 5% throughput degradation; no safety breach |
| 3 – Moderate | 5–20% throughput degradation or minor congestion breach |
| 4 – Major | > 20% degradation or safety threshold exceeded repeatedly |
| 5 – Critical | System shutdown, worker injury, or data loss |

**Risk Score = Likelihood × Impact**  
- 1–4: LOW (monitor)  
- 5–9: MEDIUM (mitigate)  
- 10–19: HIGH (urgent mitigation)  
- 20–25: CRITICAL (immediate action)

---

## 2. Risk Register Table

| # | Risk ID | Category | Risk Description | Likelihood | Impact | Score | Severity | Mitigation Strategy | Residual Risk | Owner |
|:---:|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---|:---:|:---:|
| 1 | R-001 | **Operational** | Aisle congestion exceeds safe threshold (>75%) during peak-demand waves causing worker gridlock and SLA breach | 4 | 4 | **16** | HIGH | Wave-release controller gates dispatches at 75% threshold; anti-starvation ensures no order waits > 600 s | 6 | Simulation Lead |
| 2 | R-002 | **Domain** | Visual similarity causes mispick errors; workers spend extra time re-picking wrong SKUs, extending aisle dwell time | 5 | 3 | **15** | HIGH | Verified pick + barcode scan workflow modelled; `visual_similarity.py` adds explicit re-pick delay (avg +45 s); workers trained on dual-scan confirmation | 8 | Operations |
| 3 | R-003 | **Technical** | IoT sensor / network failure causes telemetry blackout; controller operates blind on estimated congestion | 4 | 4 | **16** | HIGH | Store-and-forward queue buffers decisions offline (Scenario F); replay reconciliation corrects decisions on reconnection; fallback congestion = 65% conservative estimate | 6 | Infrastructure |
| 4 | R-004 | **Technical** | Wave-release controller delay stacks (>20 retries) causing order starvation for specific aisles | 3 | 4 | **12** | HIGH | Anti-starvation cap (max 20 retries, ~10 min hold); BLOCK decisions escalate to supervisor alert; no order held beyond 600 s | 5 | Controller Dev |
| 5 | R-005 | **Safety** | Worker congestion in narrow aisles (capacity 3) causes physical collision risk between pickers | 3 | 5 | **15** | HIGH | CRITICAL congestion classification (≥100%) triggers immediate BLOCK decision; physically modelled capacity constraints | 7 | Safety Officer |
| 6 | R-006 | **Domain** | Hotspot aisles (A03, A07) permanently saturated due to structural demand skew despite controller action | 4 | 3 | **12** | HIGH | Dynamic rerouting (Scenario H) diverts workers around >90% congested aisles; demand redistributed via wave scheduling | 6 | Warehouse Mgr |
| 7 | R-007 | **Data** | Synthetic dataset does not faithfully represent real automotive parts demand patterns | 3 | 3 | **9** | MEDIUM | Peak multiplier (2.8×) calibrated against industry benchmarks; 5-seed Monte Carlo validation confirms statistical stability (σ < 5%) | 6 | Data Team |
| 8 | R-008 | **Technical** | Sensor spoofing attack injects false zero-congestion readings causing uncontrolled worker release | 2 | 5 | **10** | HIGH | Cryptographic sensor verification planned for Review 3; current mitigation: range-check anomaly detection (congestion drop > 30% in 1 step flagged) | 7 | Cyber Security |
| 9 | R-009 | **Operational** | Worker path reordering (dynamic rerouting) increases total travel distance, raising costs and emissions | 3 | 2 | **6** | MEDIUM | A* nearest-neighbour heuristic minimises distance increase; rerouting only triggered at ≥90% congestion threshold | 4 | Operations |
| 10 | R-010 | **Project** | Simulation model diverges from physical warehouse (centroid coordinates, constant walking speed) | 3 | 3 | **9** | MEDIUM | Documented as known limitation; future work: microscopic crowd dynamics, variable speed model, real warehouse telemetry calibration | 6 | Research Lead |
| 11 | R-011 | **Compliance** | Emissions accounting model underestimates carbon footprint (omits HVAC, lighting loads) | 2 | 2 | **4** | LOW | Current model: 0.00015 kg CO₂e/m battery-electric cart only; documented scope limitation; full LCA planned for Review 3 | 3 | Sustainability |
| 12 | R-012 | **Technical** | Store-and-forward spool file grows unbounded during extended outages, exhausting edge-device storage | 2 | 3 | **6** | MEDIUM | Spool size limit: 10,000 events before oldest events dropped (FIFO eviction); outage alerts triggered > 15 min | 4 | Infrastructure |
| 13 | R-013 | **Operational** | Workers gaming the system by entering high-risk aisles before congestion check | 2 | 3 | **6** | MEDIUM | Physical badge-gate integration (Review 3); current: controller checks physical occupancy intervals | 4 | Operations |
| 14 | R-014 | **Project** | Review 2 prototype not reaching 70% maturity target | 2 | 4 | **8** | MEDIUM | Three new scenarios (F, G, H), 22 new tests, formal documentation added; current estimate: ~68–72% | 5 | Project Manager |

---

## 3. Top Risk Heat Map

```
Impact
  5 │ .    .    R005 .    R008
  4 │ R004 .    R001 R003 .
  3 │ .    R009 R006 R007 R002
  2 │ R011 .    R012 R013 .
  1 │ .    .    .    .    .
    └───────────────────────────
      1    2    3    4    5  Likelihood
```

*Circle size = risk score. Shaded region = HIGH/CRITICAL.*

---

## 4. Risk Monitoring Schedule

| Frequency | Activity |
|:---|:---|
| Per simulation run | Check `critical_events_count` stays below baseline; alert if > 150 |
| Per Review cycle | Re-score all risks based on new prototype capabilities |
| Post-outage simulation | Verify S&F queue drains cleanly; replay reconciliation rate ≥ 95% |
| Before Review 3 | Implement cryptographic sensor verification (R-008); microscopic crowd dynamics (R-010) |

---

*Document version: 2.0 — Review 2 Edition*
