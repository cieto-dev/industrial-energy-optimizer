# PROJECT_STATE.md

**Project:** AI-Powered Industrial Energy Transition Platform (working repo name: `industrial-energy-optimizer`)
**Track:** Smart India Hackathon (SIH) prototype → intended startup direction
**Team size:** 6 members
**Status date:** 17 August 2026 (re-verified against live repo same day — see §0)
**Repo:** https://github.com/cieto-dev/industrial-energy-optimizer

> This file is a living snapshot of where the project actually stands — problem, evidence, architecture, gaps, and next actions. It is reconciled against the team's own `SYSTEM_DESIGN.md`, `RESEARCH_NOTES.md`, `MENTOR_NOTES.md`, and `FEATURE_BACKLOG.md`. Update it whenever a research phase closes, a scope decision is made, or the architecture changes.

---

## 0. Correction notice (17 Aug 2026 — evening pass)

This revision supersedes the previous pass (17 Aug 2026, earlier in the day). Key changes:

1. **`decision-engine/policy/` is now scaffolded.** It has `__init__.py`, `eligibility.py`, `subsidy_matcher.py`, and `policy_engine.py` — all 0 bytes. Status changes from "missing" to "scaffolded." The team has de facto committed to Module 4a being in scope.
2. **`knowledge-base/master/tariffs.json` was updated** in commit `bb4d669` ("small update", 17 Aug 17:09) — 76 insertions/76 deletions, reformatting pass only. This is the latest commit.
3. **Sector scope creep is now clearer** — nine full industry profiles exist and policy scaffold is being built. Formal decision is overdue.
4. **Implementation bottleneck is now precisely scoped** — the exact files to write to unblock end-to-end are listed in §8.

---

## 1. The Problem (final framing — unchanged)

**We are NOT building:** "AI that replaces coal with solar" / generic renewable calculator / carbon footprint calculator / chatbot.

**We ARE building:** An engineering decision-support system combining engineering models, optimization, financial evaluation, and explainable AI to recommend the most suitable energy-transition pathway for a specific industrial MSME — supporting, not replacing, engineering judgment.

### Master Research Question (MRQ)
> Can a data-driven techno-economic decision-support system identify and compare technically feasible, economically viable, and lower-emission energy-transition pathways for individual Indian MSMEs under process, resource, reliability, and financial constraints?

### Six sub-questions (RQ1–RQ6)
1. **Baseline** — What are the dominant energy uses and fossil-fuel dependencies of the selected MSME process?
2. **Technology** — Which efficiency, electrification, renewable, alternative-fuel, and storage technologies are technically applicable?
3. **Local resources** — How do location-specific solar, biomass, and grid conditions affect feasibility?
4. **Economics** — How do CAPEX, OPEX, fuel/electricity prices, and financing affect pathway selection?
5. **Optimization** — Can multiple technologies be combined/sequenced to meet process-energy needs at minimum cost/emissions?
6. **Robustness** — How sensitive is the recommended pathway to price, resource, and production uncertainty?

---

## 2. Evidence base — unchanged, see `RESEARCH_NOTES.md`

No change since last revision. Full citation list: `research/bibliography.md`. Per-parameter sourcing lives inline in each `knowledge-base/**/*.json` file.

---

## 3. Sector & scope decision

**Selected first vertical: Textile dyeing / wet-processing MSME using solid fuel (coal/biomass) for steam.**

**⚠️ De facto scope creep — needs formal acknowledgement.** Nine full industry profiles exist. Policy scaffold is built. DOMAIN_MODEL.md documents Module 4a fields. The team is building for all nine sectors with policy eligibility in scope — the formal decisions have not been documented.

**Required action:** Update `FEATURE_BACKLOG.md` to record "9 sectors in scope" and "Module 4a: IN scope." Then build accordingly. Any API contract written without this decision will need rework.

---

## 4. System architecture

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
[ Policy & Eligibility Check — Module 4a — scaffolded, implementation pending ]
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

Full module reference: `docs/SYSTEM_DESIGN.md` §4 (authoritative) and `docs/DECISION_ENGINE_ARCHITECTURE.md`.

### Implementation status by layer (re-verified 17 Aug 2026 — evening)

| Component | Status | Notes |
|---|---|---|
| Research | ✅ Complete | All six RQs answered; sourced in KB |
| Knowledge base — industries, technologies, constraints, finance | ✅ Complete | Alignment pass closed; 9 sectors, 6 tech profiles, all consistency issues resolved |
| Knowledge base — policies, emissions, references | ✅ Complete | Internally consistent; policies consumed by `decision-engine/policy/` scaffold |
| Knowledge base — `solar_thermal.json` | 🟡 Thin | Smaller than other tech files; no concentrating/non-concentrating split |
| Documentation | 🟡 In progress | This pass — see `ROADMAP.md` for next-phase guidance |
| Database design | ⏳ Not started | Blocks `seed_database.py` and all backend persistence |
| Backend infrastructure | ⏳ Not started | `main.py`, `database.py`, `config.py`, `logger.py`, `utils.py` all 0 bytes |
| Backend APIs | ⏳ Not started | All 7 files under `backend/apis/` are 0 bytes |
| Models (`models/`) | ⏳ Not started | All 6 Python files are 0 bytes; `factory.py` mentioned but does not exist yet |
| Decision engine — technology | ✅ Implemented | `technology_engine.py` (1,844B), `technology_filter.py` (2,560B), `technology_matcher.py` (1,767B) — real code |
| Decision engine — emissions | ✅ Implemented | `co2_calculator.py` (1,411B), `emission_engine.py` (2,996B), `emission_factors.py` (955B) — real code |
| Decision engine — scenario | 🟡 Partial | `scenario_generator.py` (1,558B, real code); `scenario_filter.py` and `scenario_validator.py` are 0 bytes |
| Decision engine — baseline | ⏳ Not started | `baseline_engine.py`, `energy_calculator.py`, `fuel_calculator.py` all 0 bytes |
| Decision engine — economics | ⏳ Not started | `capex.py`, `opex.py`, `payback.py`, `roi.py`, `economics_engine.py` all 0 bytes |
| Decision engine — optimizer | ⏳ Not started | `mcda.py`, `optimization_engine.py`, `ranking.py`, `weights.py` all 0 bytes |
| Decision engine — reliability | ⏳ Not started | `confidence.py`, `reliability_engine.py`, `risk_score.py` all 0 bytes |
| Decision engine — policy | 🟡 Scaffolded | `__init__.py`, `eligibility.py`, `subsidy_matcher.py`, `policy_engine.py` — structure exists, all 0 bytes |
| Decision engine — reports | ⏳ Not started | `excel_report.py`, `pdf_report.py`, `report_generator.py` all 0 bytes |
| Scripts — KB support/validation | ✅ Complete | `create_district_discoms.py`, `create_districts_json.py`, `create_tariffs_json.py`, `validate_references.py` passing |
| Scripts — ETL pipeline | ⏳ Not started | `convert_datasets.py`, `pre_process.py`, `load_knowledge.py`, `seed_database.py`, `run_pipeline.py` all 0 bytes |
| Frontend | ⏳ Not started | Folder structure scaffolded; all files 0 bytes |
| Tests | ⏳ Not started | All test files 0 bytes |
| Deployment | ⏳ Scaffolded | Dockerfile, docker-compose.yml, nginx.conf exist but unused |
| Digital twin | Out of MVP | `digital-twin/future_scope.md` only |

**Net position:** Knowledge base and documentation are mature. Three decision-engine modules have working code (technology, emissions, scenario_generator). Everything else — backend, models, database, five decision-engine modules, reports, frontend — has not been started. This is the clear critical path. See `docs/ROADMAP.md`.

---

## 5. Knowledge base — final status

```
knowledge-base/
├── constraints/   (budget, fuel, grid, space, technology_rules, temperature)
├── emissions/     (emission_factors, grid_factors)
├── finance/       (electricity_tariffs, fuel_prices, subsidies, technology_costs)
├── industries/    (cement, chemical, dairy, food_processing, glass, paper,
│                   pharma, steel, textile) — 9 sectors, all fully populated
├── master/        (discoms, district_discoms, districts, fuels, industries,
│                   states, tariffs, technologies)
├── policies/      (carbon_pricing, central_policies, eligibility_rules,
│                   renewable_purchase_obligations, state_policies)
├── references/    (citations, sources)
└── technologies/  (biomass, electrification, heat_pump, solar_thermal,
                    thermal_storage, waste_heat_recovery)
```

### Resolved (as of this pass)

| Issue | Resolution |
|---|---|
| Subsidy data duplicated across `policies/`, `finance/subsidies.json`, `constraints/budget.json` | ✅ Canonical `financial_data_ownership` rule in `central_policies.json` |
| Conflicting CGTMSE guarantee-coverage number | ✅ Full category table in `subsidies.json`; other files reference only |
| Redundant `source_id` fields | ✅ Commit `c9e3ed5` — 33 fields removed |
| `industries/` missing `paper`, `dairy`, `glass` | ✅ All three populated (16 Aug 2026) |
| `references/` consistency | ✅ Confirmed |
| `master/` undocumented | ✅ Documented above |

### Still open

| Item | Status |
|---|---|
| `technologies/solar_thermal.json` thin (2,048B vs 4–9KB others) | 🟡 No concentrating/non-concentrating split; no `solar_thermal` policy key |
| `master/technologies.json` lists 9 IDs but only 6 have full profiles | 🟡 `electric_boiler`, `solar_pv`, `biogas` master-list only |

### 5a. Module 4a — Policy & Eligibility Engine

**Status change from previous revision:** `decision-engine/policy/` scaffold now exists with correct files. The blocker is now implementation, not scope. What remains:
- Implement `eligibility.py` — MSME/Udyam/enterprise-category/turnover/state checks
- Implement `subsidy_matcher.py` — load policy JSON, match schemes, rank by benefit
- Implement `policy_engine.py` — orchestrate the above
- Connect to `backend/apis/policy_api.py`
- Extend Module 1 to collect all required MSME eligibility fields

---

## 6. Team structure — unchanged

| Member | Owns | Output |
|---|---|---|
| 1 | Domain / process research | Textile dyeing process model |
| 2 | Energy & technology research | Technology knowledge base |
| 3 | Data & geospatial | MSME/solar/biomass/tariff datasets |
| 4 | Economics & finance | CAPEX/OPEX/financing model |
| 5 | Optimization / backend | Constraint engine, optimizer, sensitivity analysis |
| 6 | Product / frontend / validation | UI, comparison dashboard, demo, docs |

---

## 7. What's genuinely solved elsewhere — unchanged

**Claimed novelty = integration + India/MSME-specific constraint modeling + accessibility + explainability**, not any single component.

---

## 8. Immediate next actions (implementation phase — dependency-ordered)

1. **Formally document scope decisions** — update `FEATURE_BACKLOG.md`: "9 sectors in scope" + "Module 4a: IN scope."
2. **Design database schema** from `DOMAIN_MODEL.md` entities → write as migration in `scripts/migrations/`.
3. **Implement `backend/database.py` and `backend/config.py`** — required before any model or API can persist.
4. **Implement `models/`** — all 6 Python domain model files (Pydantic/dataclass, trace to `DOMAIN_MODEL.md`).
5. **Implement `backend/main.py`** — FastAPI app init, route registration.
6. **Implement `decision-engine/baseline/`** — feeds every downstream module; first pipeline step.
7. **Implement `decision-engine/economics/`** — CAPEX/OPEX/payback/ROI per scenario.
8. **Implement `decision-engine/reliability/`** — sensitivity/confidence scoring.
9. **Implement `decision-engine/optimizer/`** — MCDA ranking.
10. **Implement `decision-engine/policy/`** — eligibility + subsidy matching.
11. **Implement `decision-engine/reports/`** — explainability narrative + PDF/Excel export.
12. **Implement backend APIs** — wire each `backend/apis/*.py` to its engine module.
13. **Build ETL pipeline** — `convert_datasets.py` → `seed_database.py` → `run_pipeline.py`.
14. **Build frontend** — factory input form and recommendation display first.
15. **Write tests** — unit tests per decision-engine module, integration tests for full pipeline.
16. **End-to-end demo** — run Scenario T1 (textile MSME) through the full pipeline.

See `docs/ROADMAP.md` for sprint-by-sprint breakdown.

---

## 9. Open risks / honesty checks

- **Backend, models, and tests are fully unimplemented** — all 0 bytes as of 17 Aug 2026 evening. Clear critical path.
- **Five decision-engine modules are unimplemented** — baseline, economics, optimizer, reliability, reports.
- **No sprint plan existed until `ROADMAP.md` was created this pass.**
- **`MENTOR_NOTES.md` has zero real entries** — fill after next faculty/jury interaction.
- **`solar_thermal.json` remains the one KB gap.**
- **Python import hygiene** — `decision-engine/` uses a hyphen, invalid for Python package imports. Rename to `decision_engine/` before cross-module imports are written.
- **Documentation quality is a genuine strength** — maintain the self-correction practice into the implementation phase.
