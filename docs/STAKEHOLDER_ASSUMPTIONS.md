# Stakeholder Assumptions Document
# Aisle Congestion Simulator & Wave-Release Controller

**Document:** Stakeholder Assumption Analysis  
**Project:** Aisle Congestion Simulator and Wave-Release Controller  
**Review Stage:** Review 2 (70% Prototype Maturity)  
**Date:** October 2026  

---

## 1. Purpose

This document formalises the key assumptions made about the operating environment, stakeholder expectations, and system constraints. Assumptions that prove incorrect will directly change the design decisions and simulation outcomes, as detailed in the sensitivity analysis.

---

## 2. Stakeholder Map

| Stakeholder | Role | Primary Concern | KPI of Interest |
|:---|:---|:---|:---|
| **Warehouse Operations Manager** | End-user / operator | Worker safety; throughput maintenance | Congestion events < 10/hr; Throughput ≥ baseline |
| **Logistics Director** | Business sponsor | Cost per order; SLA compliance | Cost < \$3.50/order; Delayed orders < 20% |
| **IT / Infrastructure Team** | System integrator | Network reliability; sensor uptime | Sensor availability ≥ 95%; S&F recovery < 5 min |
| **Quality Assurance Lead** | Domain expert | Mispick rate; pick accuracy | Mispick rate < 8%; Re-pick cost < \$150/shift |
| **Sustainability Officer** | Regulatory compliance | Carbon emissions | Emissions reduced ≥ 5% vs baseline |
| **Health & Safety Officer** | Regulatory compliance | Physical safety in aisles | Zero CRITICAL congestion events (≥100%) per shift |
| **CSE Research Team** | Academic evaluators | Technical rigor; reproducibility | All 45+ tests passing; results reproducible across 5 seeds |

---

## 3. Assumption Categories

### 3.1 Warehouse Layout Assumptions

| ID | Assumption | Impact if Wrong | Evidence / Source |
|:---|:---|:---|:---|
| WL-001 | Warehouse has 12 aisles arranged in a 3×4 grid with 15 m spacing | Different layout changes travel distances ±30%; rerouting paths change | Industry standard orthogonal warehouse grid; tunable via `DEFAULT_AISLES` |
| WL-002 | Aisles A03 and A07 are hotspots (22% and 20% of order demand respectively) | If demand is distributed evenly, congestion events reduce by ~60% | Automotive maintenance parts follow Pareto distribution; validated against published SKU velocity data |
| WL-003 | Aisle physical capacity = 3–5 workers simultaneously (narrow aisle: 3; wide: 5) | Higher capacity reduces critical events; lower capacity increases BLOCK frequency | Standard warehousing: 1.5 m minimum aisle width per worker; OSHA regulations |
| WL-004 | Depot/staging is at coordinate (0,0), closest to Aisle A01 | Changed depot position alters travel time distribution | Standard warehouse layout with staging at entry |

### 3.2 Worker Behaviour Assumptions

| ID | Assumption | Impact if Wrong | Sensitivity |
|:---|:---|:---|:---|
| WB-001 | Workers travel at constant 1.0 m/s (Manhattan grid) | Faster speed (1.5 m/s) reduces congestion peak duration by ~25%; slower increases dwell time | Medium – see `walking_speed_mps` parameter |
| WB-002 | Workers comply with wave-release gating (do not enter aisles before ALLOW signal) | Non-compliance makes controller ineffective; safety risk escalates | High – physical badge gates required for enforcement (Review 3) |
| WB-003 | Each worker handles exactly one order at a time (single-order picking) | Batch picking reduces trips by ~30% but changes congestion patterns significantly | High – scope constraint for current prototype |
| WB-004 | Workers do not communicate with each other about aisle congestion | Informal coordination could reduce congestion by ~10–15% beyond the controller | Low – controller is the authoritative gating mechanism |

### 3.3 Visual Similarity Assumptions

| ID | Assumption | Impact if Wrong | Sensitivity |
|:---|:---|:---|:---|
| VS-001 | Brake pad SKUs (A03) have 90% visual similarity risk and 12% mispick probability | Lower mispick rate (5%) reduces total mispick cost by \$105–\$140/shift | **High** – domain-critical assumption directly modelling the problem statement |
| VS-002 | Verification overhead = `similarity_risk × verification_extra_sec` | If verification is purely time-constant (not risk-proportional), A03 dwell time reduces by ~8 s/pick | Medium |
| VS-003 | Mispick return time = 45 s base + uniform(0, 20) s | If return time is 90 s (longer aisles), mispick cost doubles | Medium – tunable via `MISPICK_RETURN_TIME_SEC` |
| VS-004 | Workers perform dual-scan verification for high-risk SKUs (brakes, gaskets) | Without verification, mispick probability rises to ~20–25% | High – training assumption |

### 3.4 Sensor / Network Assumptions

| ID | Assumption | Impact if Wrong | Sensitivity |
|:---|:---|:---|:---|
| SN-001 | IoT sensors report aisle occupancy in real time (< 1 s latency under normal conditions) | > 5 s latency causes stale congestion reads; controller makes incorrect ALLOW decisions | Medium |
| SN-002 | Network outages follow a Poisson process (mean interval 15 min; mean duration 3 min) | More frequent outages (5-min interval) triple S&F queue load; reconciliation delay increases | High – tunable via `NetworkStateMonitor` parameters |
| SN-003 | Fallback congestion estimate = 65% (conservative) during sensor blackout | If actual congestion is 90% during blackout, the 65% estimate causes unsafe ALLOW decisions | **High** – critical safety assumption; sensitivity: ±15% fallback changes delay count by ±40 orders |
| SN-004 | Sensor data is authentic (no spoofing attacks) | Sensor spoofing (injecting false low-congestion) causes uncontrolled release; safety breach | High – cyber-security mitigation planned for Review 3 |

### 3.5 Cost & Emission Assumptions

| ID | Assumption | Impact if Wrong | Sensitivity |
|:---|:---|:---|:---|
| CE-001 | Worker cost = \$0.35/min (\$21/hr standard picker wage) | Higher wage (\$28/hr) increases labor cost by 33%; changes ROI calculation | Low for relative comparison |
| CE-002 | Delay SLA penalty = \$0.25/min per delayed order | Higher SLA penalty (\$0.75/min) makes controlled mode costlier vs baseline | Medium |
| CE-003 | Mispick cost = \$3.50 per mispick event (re-pick labour + SLA) | If mispick cost is \$8.00 (includes returns shipping), controlled mode shows stronger ROI | **High** for cost trade-off decision |
| CE-004 | Emissions = 0.00015 kg CO₂e/m (battery-electric cart only; no HVAC/lighting) | Full LCA including HVAC adds ~0.0008 kg CO₂e/m; total emissions increase 5× | Medium – scope limitation documented |

---

## 4. Assumption Sensitivity Summary: Decision-Changing Assumptions

The following assumptions, if changed, would alter the **go/no-go decision** to deploy the wave-release controller:

| Priority | Assumption ID | If Changed To | Decision Impact |
|:---:|:---:|:---|:---|
| 🔴 1 | VS-001 | Mispick probability < 3% for all parts | Verification overhead becomes dominant cost; simpler uniform pick model sufficient |
| 🔴 2 | SN-003 | Fallback congestion set to actual 85% | Controller in S&F mode becomes overly conservative; throughput drops 15% |
| 🟠 3 | WB-002 | Workers do not comply with gating | Physical badge gates required before deployment; controller is advisory only |
| 🟠 4 | SN-002 | Outage mean interval < 5 min | S&F queue becomes primary operating mode; real-time controller becomes secondary |
| 🟡 5 | CE-003 | Mispick cost = \$8.00 | ROI breakeven shifts from 12 months to 7 months; accelerates deployment decision |

---

## 5. Assumption Validation Plan

| Phase | Validation Activity |
|:---|:---|
| **Review 2** | Sensitivity sweeps across VS-001, SN-003 assumptions (done in `run_sensitivity_analysis`) |
| **Review 3** | Physical pilot in warehouse: measure actual mispick rate, network uptime, walking speed |
| **Post-deployment** | A/B comparison: controlled shift vs uncontrolled shift across 20 working days |

---

*Document version: 2.0 — Review 2 Edition*
