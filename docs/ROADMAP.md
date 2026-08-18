# ROADMAP.md

> **Purpose:** Sprint-by-sprint implementation plan from the current state (17 Aug 2026) to the SIH demonstration milestone.
>
> **Basis:** Derived from `PROJECT_STATE.md` §8 and `FEATURE_BACKLOG.md`. Every item maps to a real, identifiable 0-byte file or missing component in the repo.
>
> **Rule:** Mark items done only when the file is non-empty, the logic is real (not a placeholder), and it has been manually verified to produce correct output for at least one test input.

---

## Current position (as of 17 Aug 2026)

### What is done
- ✅ All research (RQ1–RQ6)
- ✅ Complete knowledge base (9 industries, 6 tech profiles, constraints, finance, policies, emissions, references)
- ✅ KB validation scripts
- ✅ Decisionengine: `technology/` (3 files), `emissions/` (3 files), `scenario_generator.py`
- ✅ Architecture documentation, domain model, system design
- ✅ Folder structure for all components

### What is NOT done (zero bytes, confirmed 17 Aug 2026 evening)
- ❌ `models/` — all 6 Python files
- ❌ `backend/` — all infrastructure and API files
- ❌ `decision_engine/baseline/` — all 3 files
- ❌ `decision_engine/economics/` — all 5 files
- ❌ `decision_engine/optimizer/` — all 4 files
- ❌ `decision_engine/reliability/` — all 3 files
- ❌ `decision_engine/policy/` — all 4 files (scaffolded structure, 0 bytes)
- ❌ `decision_engine/reports/` — all 3 files
- ❌ `decision_engine/scenario/scenario_filter.py` and `scenario_validator.py`
- ❌ `scripts/` ETL pipeline — 5 files
- ❌ `tests/` — all 4 test files
- ❌ `frontend/` — all components

---

# Sprint 0 Scope Decisions

## Decision 1 – Policy & Eligibility (Module 4A)

Status: Deferred (Post-MVP)

Reason:
- MVP will display applicable schemes only.
- Automatic eligibility verification is out of scope.
- Future enhancement.

---

## Decision 2 – Sector Coverage

Status: Approved

Implementation:
- Support all 9 industrial sectors.
- Use configuration-driven sector profiles.
- Single recommendation engine for every sector.
---

## Sprint 1 — Foundation: Database + Backend Core + Models

**Goal:** A running FastAPI backend that accepts a factory profile, persists it, and returns a valid response.

**Estimated effort:** ~3–4 days for 2 people working in parallel.

### 1.1 Database Schema Design
- [ ] Derive schema from `docs/DOMAIN_MODEL.md` entities: Factory, Industry, Technology, Scenario, FinancialModel, EmissionModel, Recommendation
- [ ] Write as `scripts/migrations/001_initial_schema.sql` or SQLAlchemy declarative models
- [ ] Document FK relationships, enums, JSON columns
- **Gate:** Schema agreed before any model or API is written

### 1.2 Backend Infrastructure
- [ ] `backend/config.py` — read env vars (DB URL, debug, port) from `.env`
- [ ] `backend/database.py` — SQLAlchemy engine, session factory, `get_db()` dependency
- [ ] `backend/logger.py` — structured logging with request ID
- [ ] `backend/utils.py` — unit conversion helpers (MJ to kWh, tonnes to kg, etc.)
- [ ] `backend/main.py` — FastAPI app init, CORS, route registration, health check
- **Gate:** `python backend/main.py` starts without errors; `GET /health` returns 200

### 1.3 Domain Models
- [ ] `models/factory.py` — Factory Pydantic model (all fields from `DOMAIN_MODEL.md` §1, including Module 4a fields)
- [ ] `models/industry.py` — Industry model
- [ ] `models/technology.py` — Technology model
- [ ] `models/scenario.py` — Scenario model (`payback_years` as [low, high] range — not a point)
- [ ] `models/financial.py` — FinancialModel
- [ ] `models/emission.py` — EmissionModel
- [ ] `models/recommendation.py` — Recommendation model
- **Gate:** All models instantiate with test data and serialize to JSON without errors

### 1.4 First APIs
- [ ] `backend/apis/health_api.py` — `GET /health` and `GET /version`
- [ ] `backend/apis/industry_api.py` — `GET /industries` (reads from `knowledge-base/industries/` JSON)
- **Gate:** Both endpoints return correct JSON

---

## Sprint 2 — Decision Engine Core: Baseline + Economics + Scenario Completion

**Goal:** A factory input can be processed from baseline calculation through unranked scenario generation.

**Estimated effort:** ~4–5 days for 2–3 people.

### 2.1 Baseline Engine
- [ ] `decision_engine/baseline/energy_calculator.py` — thermal and electrical demand from factory inputs
- [ ] `decision_engine/baseline/fuel_calculator.py` — fuel consumption and cost (reads `knowledge-base/finance/fuel_prices.json`)
- [ ] `decision_engine/baseline/baseline_engine.py` — outputs BaselineProfile (CO2, cost, useful heat)
- **Critical:** BaselineProfile is immutable once computed — pathways evaluate against it, never mutate it
- **Gate:** Textile MSME test input → BaselineProfile with correct thermal demand, CO2, cost (validate against known benchmark)

### 2.2 Scenario Completion
- [ ] `decision_engine/scenario/scenario_filter.py` — remove duplicate or inconsistent combinations
- [ ] `decision_engine/scenario/scenario_validator.py` — validate no double-counted thermal load, no mutually exclusive technologies combined
- **Gate:** 3–5 unique, internally consistent scenarios produced for test input

### 2.3 Economics Engine
- [ ] `decision_engine/economics/capex.py` — CAPEX per technology (reads `knowledge-base/finance/technology_costs.json`); branches on MSME vs. large-industry eligibility
- [ ] `decision_engine/economics/opex.py` — annual OPEX per scenario
- [ ] `decision_engine/economics/payback.py` — simple payback as [low, high] range (not a point estimate)
- [ ] `decision_engine/economics/roi.py` — NPV and ROI
- [ ] `decision_engine/economics/economics_engine.py` — orchestrates the above; outputs FinancialModel per scenario
- **Gate:** Each generated scenario has a FinancialModel with CAPEX, OPEX, payback range, ROI

### 2.4 Technology API
- [ ] `backend/apis/technology_api.py` — `GET /technologies` and `POST /technologies/filter`
- **Gate:** Given a factory profile, returns feasible and rejected technology lists with rejection reasons

---

## Sprint 3 — Optimization + Policy + Reports + Pipeline

**Goal:** Full pipeline from factory input to ranked explainable recommendation. `run_pipeline.py` produces readable output without a frontend.

**Estimated effort:** ~5–6 days for 3 people.

### 3.1 Reliability Engine
- [ ] `decision_engine/reliability/confidence.py` — confidence scoring based on data quality and assumption uncertainty
- [ ] `decision_engine/reliability/risk_score.py` — risk score per scenario (fuel price volatility, grid reliability, biomass logistics)
- [ ] `decision_engine/reliability/reliability_engine.py` — real sensitivity sweep (perturbations across fuel price +/-X%, production +/-X%, solar +/-X%); outputs payback range
- **Critical:** Real perturbations, not a static risk label — this is what answers RQ6
- **Gate:** Payback range widens meaningfully under adverse input assumptions

### 3.2 Optimizer / MCDA
- [ ] `decision_engine/optimizer/weights.py` — default weight set (cost/emissions/risk); document whether fixed or adjustable
- [ ] `decision_engine/optimizer/mcda.py` — normalizes scores, applies weights
- [ ] `decision_engine/optimizer/ranking.py` — ranked scenario list with objective scores
- [ ] `decision_engine/optimizer/optimization_engine.py` — orchestrates the above
- **Critical:** Ranking must NOT always pick the cheapest scenario — this is the core technical differentiator
- **Gate:** Recommended scenario is explainably not always the cheapest

### 3.3 Policy Engine
- [ ] `decision_engine/policy/eligibility.py` — MSME registration, enterprise category, investment limits, turnover limits, state requirements
- [ ] `decision_engine/policy/subsidy_matcher.py` — reads `knowledge-base/policies/` JSON, matches eligible schemes, ranks by benefit
- [ ] `decision_engine/policy/policy_engine.py` — orchestrates eligibility + matching; accepts Factory, returns eligible schemes with benefit estimates
- **Gate:** Udyam-registered small enterprise in Tamil Nadu → correct subset of CLCSS/MNRE CFA/ADEETIE schemes with benefit estimates

### 3.4 Reports
- [ ] `decision_engine/reports/report_generator.py` — generates Recommendation object with `why_selected`, `why_others_rejected`, `sensitivity_notes`
- [ ] `decision_engine/reports/pdf_report.py` — PDF export
- [ ] `decision_engine/reports/excel_report.py` — Excel export with scenario comparison table
- **Gate:** Human-readable explanation produced that a non-expert can understand

### 3.5 Full Pipeline
- [x] `scripts/run_pipeline.py` — full sequence: factory input → baseline → technology filter → scenarios → economics + emissions + reliability → optimizer → policy → reports
- **Gate:** `python scripts/run_pipeline.py` with Scenario T1 input produces complete recommendation without errors

### 3.6 Core APIs
- [ ] `backend/apis/optimization_api.py` — `POST /optimize`
- [ ] `backend/apis/policy_api.py` — `POST /policy/evaluate`
- [ ] `backend/apis/recommendation_api.py` — `GET /recommendation/{id}`
- [ ] `backend/apis/report_api.py` — `GET /report/{id}/pdf` and `/excel`

---

## Sprint 4 — ETL Pipeline + Tests

**Goal:** KB data loadable into DB. All decision_engine modules have unit tests. Integration test confirms end-to-end correctness.

**Estimated effort:** ~3–4 days for 2 people.

### 4.1 ETL Pipeline
- [ ] `scripts/convert_datasets.py` — convert CSV datasets (biomass atlas, tariffs, temperature ranges) to canonical internal format
- [ ] `scripts/pre_process.py` — clean, normalize, validate converted datasets
- [ ] `scripts/load_knowledge.py` — load `knowledge-base/` JSON into DB
- [ ] `scripts/seed_database.py` — seed DB with reference data (industries, technologies, emission factors, defaults)
- **Gate:** After full ETL sequence, `GET /industries` returns all 9 industries from DB with correct data

### 4.2 Unit Tests
- [ ] `tests/test_baseline.py` — test `baseline_engine.py` with known input/output pairs for textile MSME
- [ ] `tests/test_constraints.py` — test `technology_filter.py` with inputs that should reject specific technologies
- [ ] `tests/test_optimizer.py` — test MCDA ranking; confirm it does not always pick least-cost
- [ ] `tests/test_recommendations.py` — test `report_generator.py` explanation output; confirm rejection reasons populated
- **Gate:** `pytest tests/` passes with no failures

### 4.3 KB Cleanup (opportunistic, low effort)
- [x] Expand `technologies/solar_thermal.json` — concentrating vs. non-concentrating split, temperature ranges per type
- [x] Add `solar_thermal` key to `central_policies.json` pathway matching
- [x] Verify `master/technologies.json` IDs match what `technology_filter.py` expects

---

## Sprint 5 — Frontend + Integration + Demo Prep

**Goal:** Working end-to-end demo in the browser. SIH-ready.

**Estimated effort:** ~5–6 days for 2 people.

### 5.1 Factory Input Form
- [ ] All Module 1 fields including Module 4a eligibility fields
- [ ] TypeScript types match backend Pydantic schemas
- [ ] Submit to `POST /optimize`

### 5.2 Recommendation Dashboard
- [ ] Recommended scenario display with explanation
- [ ] Scenario comparison table (all 3–5 scenarios: CAPEX, payback range, CO2 reduction, score)
- [ ] "Why not X?" technology rejection log

### 5.3 Reports
- [ ] Download PDF → `GET /report/{id}/pdf`
- [ ] Download Excel → `GET /report/{id}/excel`

### 5.4 Integration & Hardening
- [ ] End-to-end frontend → backend → decision engine connection
- [ ] Error handling for invalid inputs
- [ ] Docker deployment configuration

### 5.5 Demo Preparation
- [ ] Scenario T1 pre-loaded as default demo input (textile MSME, coal boiler, 200°C, Rajasthan)
- [ ] Verify recommendation is explainable and defensible in front of SIH jury
- [ ] Final `pytest tests/` green
- [ ] Final `validate_references.py` green

---

## Dependency chain (do not skip any step)

```
Scope decisions documented
         ↓
DB schema design
         ↓
backend/database.py + config.py
         ↓
models/ (all 6 files)
         ↓
backend/main.py
         ↓
decision_engine/baseline/    ← feeds everything downstream
         ↓
decision_engine/economics/
decision_engine/reliability/  ← parallel
         ↓
decision_engine/optimizer/
         ↓
decision_engine/policy/
         ↓
decision_engine/reports/
         ↓
backend/apis/ (all endpoints)
         ↓
scripts/ ETL pipeline (parallel with APIs post-schema)
         ↓
tests/
         ↓
frontend/
         ↓
End-to-end demo — Scenario T1
```

---

## Python import hygiene — action required before Sprint 2

`decision_engine/` uses a hyphen. Python cannot import packages with hyphens. Before any cross-module imports are written, rename the folder to `decision_engine/` (underscore). Update all references in `README.md`, `SYSTEM_DESIGN.md`, and `DECISION_ENGINE_ARCHITECTURE.md` simultaneously.

---

## Post-SIH / Future Scope

Outside the current MVP regardless of scope decisions:

| Feature | Notes |
|---|---|
| IoT sensor integration | Real-time energy monitoring |
| Digital twin (live) | `digital-twin/future_scope.md` |
| Live energy price feeds | API integration |
| GIS / geospatial layer | Map-based resource visualization |
| Carbon credit analysis | VCM market integration |
| Multi-factory optimization | Portfolio-level decision support |
| Predictive analytics | ML-based equipment health |
| Industry benchmarking | Peer comparison across MSMEs |

---

> **"The knowledge base is done. The architecture is documented. Now build the thing."**
