# SYSTEM_DESIGN.md

> **Purpose:** This document is the complete technical blueprint of the AI-Powered Industrial Energy Transition Platform.
>
> It defines how the system is designed, how individual modules interact, and how the project should be implemented.
>
> This document should evolve alongside the project and remain the primary technical reference throughout development.

---

# 1. SYSTEM OVERVIEW

The AI-Powered Industrial Energy Transition Platform is an engineering decision-support system designed to help industries identify technically feasible, economically viable, and environmentally sustainable pathways for industrial decarbonization.

Unlike a conventional calculator or chatbot, the platform combines engineering models, optimization techniques, financial evaluation, and explainable artificial intelligence to recommend the most suitable transition pathway for a specific industrial facility.

The system is intended to support — not replace — engineering decision making.

---

# 2. PROBLEM THE SYSTEM SOLVES

Industries often face multiple barriers while planning energy transition:

- Lack of technical expertise
- Multiple technology choices
- High capital investment
- Uncertainty regarding financial returns
- Difficulty evaluating environmental impact
- Lack of transparent decision-support tools

This platform addresses these issues by providing structured engineering analysis followed by AI-assisted recommendations.

---

# 3. HIGH LEVEL SYSTEM ARCHITECTURE

```
User Interface
      ↓
Application Layer (backend/)
      ↓
Input Validation
      ↓
Baseline Energy Model
      ↓
Technology Assessment
      ↓
Constraint Engine
      ↓
[ Policy & Eligibility Check — see §4a, scope pending ]
      ↓
Scenario Generator
      ↓
Optimization Engine
      ↓
Financial Analysis
      ↓
Environmental Impact Analysis
      ↓
AI Explanation Layer
      ↓
Dashboard & Reports
```

Each stage is independent and responsible for a single logical task.

---

# 4. SYSTEM MODULES

## Module 1 – User Input

Collects:

- Industry sector
- Production details
- Existing fuel consumption
- Electricity consumption
- Process temperature
- Budget
- Available infrastructure
- Geographic location (state/district)

**Open item:** if Module 4a (Policy & Eligibility) is confirmed in scope, this module must also collect MSME classification data — Udyam registration status, enterprise category, annual turnover, plant & machinery investment, project type, brownfield/greenfield status, cluster membership, and special-category status (women-owned, SC/ST-owned, NER/hill/island/aspirational-district). This is not currently collected and would need to be added here.

Output: Validated factory profile.

---

## Module 2 – Baseline Energy Assessment

Responsible for:

- Estimating present energy consumption.
- Determining useful process heat.
- Estimating operating cost.
- Calculating present emissions.

Output: Current energy baseline.

---

## Module 3 – Technology Assessment

Evaluates suitable technologies:

- Biomass
- Solar Thermal
- Heat Pumps
- Waste Heat Recovery
- Thermal Storage
- Industrial Electrification

Each technology entry contains: operating range, temperature capability, efficiency, infrastructure requirements, advantages, limitations. Sourced from `knowledge-base/technologies/*.json`.

Output: Candidate technology list.

---

## Module 4 – Constraint Engine

Checks technical feasibility using `knowledge-base/constraints/*.json`:

- Temperature limits
- Space availability
- Resource availability
- Grid capacity
- Budget constraints
- Retrofit compatibility

Only feasible pathways proceed further.

---

## Module 4a – Policy & Eligibility Engine *(status: IN scope — scaffolded, implementation pending)*

> **This module is now confirmed in scope.** `decision_engine/policy/` exists with `__init__.py`, `eligibility.py`, `subsidy_matcher.py`, and `policy_engine.py` — all 0 bytes (scaffolded, not yet implemented). `knowledge-base/policies/` is fully built and internally consistent. See `FEATURE_BACKLOG.md` for the formal scope decision and `docs/ROADMAP.md` Sprint 3 for the implementation plan.

This module:

- Determines which central/state government schemes, subsidies, and tax benefits a factory is eligible for, based on MSME classification, location, and project type.
- Applies eligibility rules from `knowledge-base/policies/eligibility_rules.json`.
- Feeds eligible subsidy/incentive values into Module 7 (Financial Analysis) to adjust effective capital cost and payback period.

**What remains before this can be implemented:**
- Write `eligibility.py` — MSME/Udyam/enterprise-category/turnover/state checks.
- Write `subsidy_matcher.py` — load policy JSON, match schemes, rank by benefit.
- Write `policy_engine.py` — orchestrate the above.
- Connect to `backend/apis/policy_api.py` (stub exists, 0 bytes).
- Extend Module 1 to collect all required MSME/eligibility fields (see `DOMAIN_MODEL.md` §1 Module 4a fields).

---

## Module 5 – Scenario Generator

Generates multiple technology combinations, e.g.:

```
Current System → Solar Thermal → Solar + Biomass → Heat Pump + Solar
→ Biomass + Thermal Storage → Electrification
```

Each scenario becomes one possible transition pathway.

---

## Module 6 – Optimization Engine

Ranks feasible scenarios using multiple criteria:

- Capital Cost
- Operating Cost
- Payback
- Emission Reduction
- Fossil Fuel Reduction
- Reliability
- Overall Score

---

## Module 7 – Financial Analysis

Calculates:

- Capital Investment
- Annual Operating Cost
- Expected Savings
- Payback Period
- Return on Investment

If Module 4a is in scope, this module also nets out eligible subsidies/incentives against capital cost.

---

## Module 8 – Environmental Impact

Estimates:

- Carbon emissions
- Fossil fuel reduction
- Renewable energy contribution
- Sustainability indicators

Depends on `knowledge-base/emissions/emission_factors.json` — populated (7 fuels, IPCC-based, sourced), confirmed against live repo 16 Aug 2026. No longer blocked on data; `decision_engine/emissions/` (`co2_calculator.py`, `emission_engine.py`, `emission_factors.py`) already contains implementation code, functional/tested status unconfirmed.

---

## Module 9 – AI Explanation Engine

Generates human-readable explanations covering: why this pathway, why alternatives were rejected, major engineering assumptions, advantages, limitations, confidence level.

---

# 5. DATA FLOW

```
Factory Input
      ↓
Validation
      ↓
Baseline Model
      ↓
Technology Screening
      ↓
Constraint Validation
      ↓
[ Policy & Eligibility Check — scope pending ]
      ↓
Scenario Generation
      ↓
Optimization
      ↓
Financial Analysis
      ↓
Environmental Analysis
      ↓
Recommendation Engine
      ↓
Dashboard
```

---

# 6. DESIGN PRINCIPLES

- **Documentation before development** — every component documented before implementation.
- **Modular architecture** — each module performs one responsibility.
- **Research-backed assumptions** — engineering values originate from verified sources, tracked via `knowledge-base/references/`.
- **Explainability** — every recommendation is understandable.
- **Independent modules** — modules communicate through well-defined data contracts.
- **Documentation tracks reality** — this document is updated whenever the actual repo structure or module scope changes, not just when new modules are added.

---

# 7. SHARED DATA CONTRACTS

```
Factory Profile → Baseline Results → Technology Options → Feasible Scenarios
→ [ Eligible Incentives, if Module 4a in scope ] → Optimized Pathways → Final Recommendation
```

Changing internal implementation should not affect other modules if contracts remain unchanged.

---

# 8. REPOSITORY STRUCTURE

*(Updated to match the actual repository — see root `README.md` for the fully annotated version.)*

```
industrial-energy-optimizer/
├── backend/            (apis/, config.py, database.py, logger.py, main.py, utils.py)
├── frontend/           (app/, components/, hooks/, services/, styles/, types/, utils/)
├── models/             (industry.py, technology.py, emission.py, financial.py, scenario.py, recommendation.py)
├── decision_engine/    (baseline/, technology/, economics/, emissions/, optimizer/, scenario/, reliability/, reports/)
├── knowledge-base/     (industries/, technologies/, constraints/, finance/, emissions/, policies/, references/)
├── datasets/           (raw + semi-processed source data, incl. electricity_tariffs/)
├── scripts/            (convert_datasets.py, pre_process.py, load_knowledge.py, seed_database.py, run_pipeline.py)
├── architecture/       (diagrams: system architecture, data flow, API flow, DB ER, decision flow, deployment)
├── deployment/         (Dockerfile, docker-compose.yml, nginx.conf)
├── digital-twin/       (future-scope notes)
├── research/           (bibliography.md)
├── tests/              (test_baseline.py, test_constraints.py, test_optimizer.py, test_recommendations.py)
├── docs/               (this document + PROJECT_STATE, FEATURE_BACKLOG, SESSION_LOG, MENTOR_NOTES, RESEARCH_NOTES)
└── README.md
```

---

# 9. BUILD SEQUENCE

*(Updated 17 Aug 2026 — see `docs/ROADMAP.md` for sprint-by-sprint detail)*

1. ✅ Repository setup
2. ✅ Knowledge base consistency pass — closed 17 Aug 2026
3. ✅ Architecture documentation — closed 17 Aug 2026
4. ⬅ **NOW:** Database schema design (derive from `DOMAIN_MODEL.md`)
5. Backend infrastructure (`backend/config.py`, `backend/database.py`, `backend/main.py`)
6. Domain models (`models/` — all 6 Python files)
7. Decision_engine baseline (`decision_engine/baseline/` — first pipeline module)
8. Decision_engine economics + reliability (parallel)
9. Decision_engine optimizer (MCDA)
10. Decision_engine policy (Module 4a — confirmed in scope)
11. Decision_engine reports (explainability + PDF/Excel)
12. Backend APIs (wire each to its engine module)
13. `scripts/` ETL pipeline (parallel with APIs post-schema)
14. Frontend
15. Tests
16. End-to-end demo (Scenario T1)
17. Deployment

---

# 10. CURRENT ARCHITECTURE STATUS

*(Re-verified 17 Aug 2026 — evening. See `PROJECT_STATE.md` §4 for full file-level detail.)*

| Component | Status |
|-----------|--------|
| Research | ✅ Complete |
| Knowledge base — all sub-domains | ✅ Complete — alignment pass closed 17 Aug 2026 |
| Documentation | ✅ Completed this pass — `ROADMAP.md` added |
| Decision engine — technology, emissions | ✅ Implemented (real code) |
| Decision engine — scenario | 🟡 Partial (`scenario_generator.py` done; filter/validator 0 bytes) |
| Decision engine — policy | 🟡 Scaffolded (folder + files exist, all 0 bytes) |
| Decision engine — baseline, economics, optimizer, reliability, reports | ⏳ Not started |
| Database Design | ⏳ Not started — Sprint 1 |
| Backend | ⏳ Not started — all files 0 bytes — Sprint 1 |
| Models | ⏳ Not started — all 6 Python files 0 bytes — Sprint 1 |
| Frontend | ⏳ Not started — folder structure only — Sprint 5 |
| ETL Pipeline | ⏳ Not started — Sprint 4 |
| Testing | ⏳ Not started — Sprint 4 |
| Deployment | ⏳ Scaffolded (Docker/nginx config exists, unused) |

---

# 11. FUTURE IMPROVEMENTS

Enhancements beyond the current SIH MVP scope:

- GIS integration
- Live energy pricing
- Digital twin support (see `digital-twin/future_scope.md`)
- IoT sensor integration
- Predictive maintenance
- Multi-factory optimization
- Cloud deployment
- Industry benchmarking

> **Note:** Government subsidy/policy integration is *not* listed here. Per the Module 4a discussion in §4, this needs an explicit in/out-of-MVP decision rather than a default "future enhancement" label, given how much of `knowledge-base/policies/` is already built. See `FEATURE_BACKLOG.md`.

---

# 12. DOCUMENT MAINTENANCE

Whenever a new module is added or an architectural decision changes:

- Update this document first.
- Reflect the change in `PROJECT_STATE.md` if it affects the project roadmap.
- Update `FEATURE_BACKLOG.md` if new functionality is introduced.
- Log the change in `SESSION_LOG.md`.

This document is the technical blueprint for the entire project.