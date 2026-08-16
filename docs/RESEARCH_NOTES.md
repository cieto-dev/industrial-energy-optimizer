# RESEARCH_NOTES.md

> **Purpose:** Central repository for all research findings, engineering assumptions, technical references, and implementation insights gathered during the project.
>
> This document is **not** a literature review. Instead, it contains distilled knowledge extracted from research papers, government reports, and technical documents that directly influence system design and implementation.
>
> **Rule:** Record only implementation-relevant findings. Avoid copying entire sections from source documents.

---

# RESEARCH SOURCES

Current references include:

- SIH Problem Statement
- Biomass Atlas
- Electrifying Industrial Heat in India
- FlexiHeat Research
- Green Transition of MSMEs Roadmap
- Decarbonizing MSMEs using Biomass
- IEA — Renewables for Industry / Heat Pump Monitor 2026
- IEA SHC — SHIP Task 49 / Task 64 (Solar Heat for Industrial Processes)
- DOE — Process Heating Sourcebook, Waste Heat Recovery Technology Assessment, Advanced Melting Technologies, Review of CHP Technologies
- BEE / PPAC / GAIL — Indian fuel pricing and emission factor data
- Bureau of Energy Efficiency (BEE) scheme documentation (ADEETIE, ZED, MSE-GIFT, etc.)
- Government Publications (MSME Ministry, MNRE, SIDBI, CGTMSE)
- Academic Papers

Full citation list: `research/bibliography.md`. Per-parameter source tracking now lives inline in each `knowledge-base/**/*.json` file (`source_id`, `confidence`, `last_verified` fields) rather than centrally — see the open question on `knowledge-base/references/` in `FEATURE_BACKLOG.md`.

---

# KEY RESEARCH AREAS

## 1. Industrial Decarbonization
Status: ✅ Research complete → ✅ Reflected in knowledge base
Implementation notes:
- Recommendations must balance technical feasibility, economics, and environmental impact.
- Different industries require different transition strategies — this is why `knowledge-base/industries/` exists as a separate folder rather than one generic profile.

## 2. MSME Energy Systems
Status: ✅ Research complete → ✅ Reflected in knowledge base
Implementation notes:
- MSMEs often have limited capital — decision support should prioritise practical, scalable solutions.
- MSME classification thresholds (turnover / investment tiers) are captured in `knowledge-base/constraints/budget.json` → `msme_classification_thresholds`.

## 3. Biomass Energy
Status: ✅ Research complete → ✅ `knowledge-base/technologies/biomass.json`
Implementation notes:
- Biomass suitability depends on local availability and process heat requirements.
- Fuel-level data (cost, GCV, CO₂ factor) for rice husk, wheat straw, bagasse, wood chips, briquettes, and pellets is in `datasets/industrial_fuels.csv` — e.g., rice husk pellets ≈ ₹10.50/kg, GCV ~14.2–15.9 MJ/kg, CO₂ factor ~1.52 kg/kg (BEE + IPCC).
- Logistics and storage should be considered before recommending biomass for a given site.

## 4. Industrial Electrification
Status: ✅ Research complete → ✅ `knowledge-base/technologies/electrification.json`
Implementation notes:
- Not suitable for every process — temperature requirements should guide recommendations.
- Example benchmark (from `datasets/temperature_ranges.csv`): Electric Resistance Heater covers an unusually wide range (80–1980°C), so it must not be treated as a single "one size fits all" electrification option in the constraint engine.

## 5. Industrial Heat Pumps
Status: ✅ Research complete → ✅ `knowledge-base/technologies/heat_pump.json`
Implementation notes:
- Heat pumps perform best in low-to-medium temperature processes.
- Concrete boundary (IEA, Renewables for Industry / Heat Pump Monitor 2026): useful process heat output 60–150°C. 60°C is treated as the MVP lower application boundary; higher-temperature systems are emerging but not yet the default assumption.

## 6. Solar Thermal
Status: ✅ Research complete → 🟡 `knowledge-base/technologies/solar_thermal.json` (thinner than other technology files — flagged for expansion)
Implementation notes:
- Geographic location significantly affects performance — this is why solar-related recommendations must be state/district-aware.
- Two distinct sub-technologies exist and should not be conflated: **non-concentrating** collectors (60–150°C, IEA SHC Task 64) and **concentrating** collectors (150–400°C, IEA SHC Task 49/64). The current `pathway_policy_matching` in `knowledge-base/policies/central_policies.json` only has a generic `solar_pv` key — it does not yet distinguish or even include solar *thermal* pathways. This needs to be added.

## 7. Waste Heat Recovery
Status: ✅ Research complete → ✅ `knowledge-base/technologies/waste_heat_recovery.json`
Implementation notes:
- Existing industrial infrastructure determines feasibility.
- Source temperature range (DOE, Waste Heat Recovery Technology Assessment): 90–1000°C describes the *recoverable waste-heat source stream*, not the useful output temperature — this distinction must be preserved when the constraint engine evaluates WHR feasibility, to avoid overstating achievable output.

## 8. Thermal Energy Storage
Status: ✅ Research complete → ✅ `knowledge-base/technologies/thermal_storage.json`
Implementation notes:
- Storage enhances system flexibility and helps pair intermittent sources (e.g., solar thermal) with continuous process demand.
- Storage/discharge temperature capability is highly medium-dependent — IEA identifies systems storing heat up to ~1000°C, but this is not a default assumption for every storage medium.

## 9. Financial Evaluation
Status: ✅ Research complete → ✅ `knowledge-base/finance/*.json`
Metrics: Capital Cost, Operating Cost, Payback Period, ROI, Annual Savings.
Implementation notes:
- Financial metrics will be calculated for every feasible scenario, not just the top recommendation, to support scenario comparison (per mentor-style best practice — see `MENTOR_NOTES.md` example).
- Example concrete data point: ADEETIE (BEE flagship scheme) provides 5% interest subvention for micro/small enterprises and 3% for medium enterprises on eligible loans — currently recorded in **both** `knowledge-base/policies/central_policies.json` and `knowledge-base/finance/subsidies.json`. Needs deduplication (see `FEATURE_BACKLOG.md`).

## 10. Government Policy, Subsidies & Eligibility
Status: ✅ Research complete → ✅ Reflected in knowledge base (built beyond current confirmed MVP scope)
Implementation notes:
- Central schemes researched include ADEETIE, MSE-GIFT, MSE-SPICE, ZED, MSME-LEAN, CGTMSE, PMEGP, RAMP, MSE-CDP, and MNRE bioenergy CFA schemes.
- Eligibility depends on Udyam registration, enterprise category (micro/small/medium), annual turnover, and special-category status (women-owned, SC/ST-owned, NER/hill/island/aspirational-district) — none of which the current User Input module design collects yet.
- **Scope for MVP is not yet finalized** — see the open decision box in `FEATURE_BACKLOG.md`.

## 11. Emission Factors
Status: ✅ Research complete → ✅ Ported into `knowledge-base/emissions/emission_factors.json` (confirmed populated against live repo 16 Aug 2026 — 7 fuels, IPCC-based, sourced)
Implementation notes:
- Per-fuel CO₂ factors researched and ported from `datasets/industrial_fuels.csv` into the knowledge base.
- Previous "still empty" status here was stale documentation, not a real gap. `decision-engine/emissions/` already has implementation code consuming this file — functional/tested status of that code is separately unconfirmed.

## 12. AI & Decision Support
Status: 🔄 Ongoing
AI should: explain recommendations, compare scenarios, improve user understanding.
AI should NOT: replace engineering calculations, ignore technical constraints, produce unsupported recommendations.

---

# ENGINEERING ASSUMPTIONS

*(Real assumptions currently baked into the knowledge base — kept here so they're visible outside the raw JSON. Update whenever a new assumption is added to any `knowledge-base/**/*.json` file.)*

| Assumption | Value / Range | Source | Confidence |
|---|---|---|---|
| Industrial heat pump useful output range | 60–150°C | IEA, Heat Pump Monitor 2026 | High |
| Non-concentrating solar thermal output range | 60–150°C | IEA SHC Task 64 | High |
| Concentrating solar thermal output range | 150–400°C | IEA SHC Task 49/64 | High |
| Biomass boiler steam/process heat output | 150–450°C | DOE + industrial boiler literature | Medium (design-dependent) |
| Waste heat recovery source stream range | 90–1000°C (source, not output) | DOE WHR Technology Assessment | High |
| ADEETIE interest subvention — micro/small | 5% | BEE (SRC_ADEETIE_BEE) | High (0.85) |
| ADEETIE interest subvention — medium | 3% | BEE (SRC_ADEETIE_BEE) | High (0.85) |
| CGTMSE guarantee coverage | 75–90% (per `budget.json` and `central_policies.json`, which agree) vs 75–85% (per `finance/subsidies.json`) | CGTMSE scheme docs | **Conflicting — needs reconciliation against current cgtmse.in figures before fixing; previous version of this row misidentified which two files disagreed** |

---

# OPEN RESEARCH QUESTIONS

- Industry-specific datasets for `paper`, `dairy`, and `glass` — referenced in `constraints/technology_rules.json` but not yet researched into a full `industries/*.json` profile.
- State-wise biomass availability, granular enough to support the constraint engine's resource-availability check.
- Carbon credit mechanisms applicable to Indian MSMEs (currently out of MVP scope, per `FEATURE_BACKLOG.md`).
- Whether `solar_pv` and `solar_thermal` should have distinct policy pathway mappings in `knowledge-base/policies/central_policies.json` (currently only `solar_pv` exists there).

---

# IMPLEMENTATION REFERENCES

| Research Finding | Engineering Decision | Affected Module | Source |
|---|---|---|---|
| Heat pump output caps at ~150°C | Heat pump excluded as a candidate for any process requiring >150°C | Module 4 — Constraint Engine | IEA Heat Pump Monitor 2026 |
| WHR source vs. output temperature distinction | Constraint engine must not equate source-stream temperature with achievable useful output | Module 3/4 — Technology Assessment, Constraint Engine | DOE WHR Technology Assessment |
| ADEETIE eligibility tied to Udyam registration | User Input module must collect Udyam status if Policy Engine (Module 4a) is in scope | Module 1 — User Input, Module 4a | BEE scheme documentation |

---

# FUTURE RESEARCH

Topics that may be explored after the MVP:

- Digital Twins
- IoT Integration
- Predictive Analytics
- Smart Grid Integration
- Carbon Trading
- Life Cycle Assessment (LCA)

---

# NOTES

This document should grow gradually throughout the project. Only implementation-relevant findings should be recorded here. Original research papers and the inline `source_id`/`confidence` fields in `knowledge-base/**/*.json` remain the authoritative reference.