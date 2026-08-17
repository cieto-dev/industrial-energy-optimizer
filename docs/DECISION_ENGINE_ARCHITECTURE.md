# DECISION_ENGINE_ARCHITECTURE.md

Documents every module inside `decision_engine/`, its inputs, outputs, and how it fits the overall flow. Companion to `architecture/decision_flow.drawio` (visual) and `DOMAIN_MODEL.md` (entities). Where a module's actual internal logic isn't yet confirmed from code, that's flagged explicitly — this doc describes intended contracts; whoever owns each module should confirm/correct against the real implementation.

## Overall flow

```
Factory (input)
   │
   ▼
[baseline/]        → current energy/fuel/CO2/cost profile (immutable once computed)
   │
   ▼
[technology/]       → filters knowledge-base technologies by feasibility (temperature,
   │                   industry, budget, space) for this Factory
   ▼
[scenario/]         → generates 3–5 candidate pathways (ordered technology combinations)
   │
   ▼
[economics/]        → CAPEX/OPEX/payback/ROI per scenario
[emissions/]         → CO2 baseline vs. pathway per scenario
[reliability/]       → confidence score + sensitivity range per scenario
   │  (these three run per-scenario, can be parallel)
   ▼
[optimizer/]        → MCDA ranking across cost + emissions + risk (NOT least-cost-only)
   │
   ▼
[policy/]           → applies subsidy/eligibility rules to the ranked scenarios
   │
   ▼
[reports/]           → generates explanation + PDF/Excel output
```

---

## Module reference

### `baseline/`
**Files:** `baseline_engine.py`, `energy_calculator.py`, `fuel_calculator.py`

**Role:** Builds the Factory's current-state energy profile from raw inputs. This is functionally the "Digital Twin" described in the original architecture plan — see the open question in `PROJECT_STATE.md` about whether `digital-twin/` should be merged into this or built out separately.

- **Input:** raw Factory fields (production, fuel type/consumption, electricity consumption, operating hours)
- **Output:** baseline energy profile — total thermal + electrical demand, current fuel cost, current CO2 (feeds `emissions/`), current efficiency
- **Depends on:** `knowledge-base/constraints/fuel.json`, `knowledge-base/finance/fuel_prices.json`
- **Must be immutable** once computed — pathways are evaluated against this baseline, never by mutating it.

### `technology/`
**Files:** `technology_engine.py`, `technology_filter.py`, `technology_matcher.py`

**Role:** Determines which technologies from the knowledge base are even *feasible* for this Factory, before any pathway is generated. This is the "Technology Feasibility Filter" from the plan — explicitly rule-based, not AI-decided (per the AI boundary rule in `PROJECT_STATE.md` Section 4).

- **Input:** Factory baseline + `knowledge-base/technologies/*.json` + `knowledge-base/constraints/technology_rules.json`, `temperature.json`, `space.json`, `budget.json`
- **Output:** two lists — `feasible_technologies[]` and `rejected_technologies[]` with a reason per rejection (e.g. "process temp 800°C exceeds heat pump's max range")
- **Critical for explainability:** the rejection reasons generated here are what powers the "Why not?" feature downstream in `reports/`.

### `scenario/`
**Files:** `scenario_filter.py`, `scenario_generator.py`, `scenario_validator.py`

**Role:** Combines feasible technologies into 3–5 candidate ordered pathways (e.g. "efficiency → biomass → solar" vs. "efficiency → electrification → solar"). Deliberately generates multiple pathways rather than one answer, per the explicit design decision in research phase Section 9 ("generate pathways, not one answer").

- **Input:** `feasible_technologies[]` from `technology/`
- **Output:** `Scenario[]` (see `DOMAIN_MODEL.md` §4) — unscored, unranked at this stage
- **`scenario_validator.py`** likely enforces that a generated combination is internally consistent (e.g. doesn't combine two technologies that both claim the full thermal load)

### `economics/`
**Files:** `capex.py`, `opex.py`, `payback.py`, `roi.py`, `economics_engine.py`

**Role:** Computes CAPEX/OPEX/payback/ROI for each Scenario.

- **Input:** Scenario's technology sequence + `knowledge-base/finance/technology_costs.json`, `electricity_tariffs.json`, `fuel_prices.json`, `subsidies.json`
- **Output:** `FinancialModel` per Scenario (see `DOMAIN_MODEL.md` §6)
- **Note:** subsidy eligibility depends on `Factory.udyam_registered` and `Factory.msme_classification` — confirm `capex.py` actually checks these before applying CLCSS/MNRE CFA rates, since large vs. MSME eligibility differs substantially (see Step 4 research: MSME gets 40%/20% solar CFA tiers + CLCSS 15%; large industry gets accelerated depreciation only).

### `emissions/`
**Files:** `co2_calculator.py`, `emission_engine.py`, `emission_factors.py`

**Role:** Computes baseline vs. pathway CO2 for each Scenario.

- **Input:** Scenario's technology sequence, fuel displaced, `knowledge-base/emissions/emission_factors.json`, `grid_factors.json`
- **Output:** `EmissionModel` per Scenario (see `DOMAIN_MODEL.md` §7)
- **Note:** grid emission factor should be looked up by `Factory.state`, since India's grid mix varies by state — confirm `grid_factors.json` is keyed by state, not a single national average.

### `reliability/`
**Files:** `confidence.py`, `reliability_engine.py`, `risk_score.py`

**Role:** Sensitivity/uncertainty analysis — this is the module that answers RQ6 ("how sensitive is the recommended pathway to price/resource/production uncertainty?") and implements the deliberate design choice to output ranges, not point estimates.

- **Input:** Scenario + assumed variance ranges (fuel price ±X%, biomass price ±X%, production ±X%, solar output ±X%)
- **Output:** confidence score, `risk_score`, and adjusted `payback_years` range
- **Note:** confirm this actually runs multiple perturbations (a real sensitivity sweep) rather than a single static risk label — the value of this module depends on that.

### `optimizer/`
**Files:** `mcda.py`, `optimization_engine.py`, `ranking.py`, `weights.py`

**Role:** Multi-criteria ranking of the scored Scenarios (cost + emissions + risk — explicitly NOT least-cost-only, matching the "cheapest isn't always correct" principle from research and the FlexiHeat-DST reference paper's MCDA approach).

- **Input:** all Scenarios with their `FinancialModel`, `EmissionModel`, and reliability scores
- **Output:** ranked `Scenario[]` with `objective_scores`
- **`weights.py`** presumably lets the relative importance of cost/emissions/risk be tuned — worth documenting whether these weights are fixed, user-adjustable, or industry-specific defaults.

### `policy/`
**Files:** `__init__.py`, `eligibility.py`, `subsidy_matcher.py`, `policy_engine.py` *(confirmed 17 Aug 2026 — all 0 bytes, structure scaffolded, not yet implemented)*

**Role (intended):** applies subsidy eligibility (`knowledge-base/policies/eligibility_rules.json`, `central_policies.json`, `state_policies.json`) and regulatory constraints (e.g. `renewable_purchase_obligations.json`, `carbon_pricing.json`) to the ranked scenarios.

- **`eligibility.py`** — checks MSME registration, enterprise category, investment limits, turnover limits, state-specific requirements. Answers: "Is this factory eligible?"
- **`subsidy_matcher.py`** — loads policy JSON, matches applicable schemes, removes duplicates, ranks by benefit value, estimates total benefit.
- **`policy_engine.py`** — orchestrator: accepts Factory, calls EligibilityChecker then SubsidyMatcher, returns eligible schemes.
- **`__init__.py`** — exposes `EligibilityChecker`, `SubsidyMatcher`, `PolicyEngine` as package public API.
- **Status:** IN scope (see `FEATURE_BACKLOG.md`). Implementation target: Sprint 3 (see `docs/ROADMAP.md`).

### `reports/`
**Files:** `excel_report.py`, `pdf_report.py`, `report_generator.py`

**Role:** Produces the final Recommendation output — the "Explainability Engine" from the plan. Generates the "Why selected / Why not / What if" narrative and exports to PDF/Excel.

- **Input:** ranked Scenarios + rejection reasons collected from `technology/` and `scenario/`
- **Output:** `Recommendation` object (see `DOMAIN_MODEL.md` §5) + downloadable report files
- **This is the module the SIH demo and any real MSME user will actually see** — its explanation quality is arguably as important as the optimizer's correctness, since an unexplained recommendation is not "decision support," it's just an unverified answer.

---

## Cross-cutting rules (from the original architecture plan — restate here so this doc is self-contained)

1. **AI boundary:** no module above should use an LLM to decide technical feasibility, ranking, or financial eligibility. LLMs (if used at all) sit outside this pipeline — parsing free-text user input into structured Factory fields, and turning `Recommendation.explanation` into natural language. Everything inside `decision_engine/` stays rule-based and mathematical, so results are auditable.
2. **Every number must be traceable** to `knowledge-base/references/citations.json` — this is what separates the system from "AI guesses a percentage."
3. **Outputs are ranges where uncertainty exists** (payback, CO2 reduction under variable grid mix), not false-precision point values.
4. **The pipeline is linear and debuggable** — Factory → baseline → feasibility filter → scenarios → scoring → ranking → policy → report. If `scripts/run_pipeline.py` doesn't follow this exact order, reconcile the code with this doc (or update this doc to match reality, whichever is correct).

---

## Open items for module owners to confirm

- [x] `policy/` folder contents — **confirmed 17 Aug 2026:** `__init__.py`, `eligibility.py`, `subsidy_matcher.py`, `policy_engine.py`
- [ ] Whether `optimizer/weights.py` is fixed, configurable, or per-industry defaults (document in `weights.py` header before implementing)
- [ ] Whether `reliability/` runs real perturbation sweeps or static risk labels (must be real sweeps — see architecture note above)
- [ ] Whether `economics/capex.py` correctly branches on MSME vs. large-industry subsidy eligibility
- [ ] Whether `emissions/grid_factors.json` is state-keyed (required — India's grid mix varies by state)
- [ ] End-to-end test: does `scripts/run_pipeline.py` produce a sane, explainable output for Scenario T1?

---

## ⚠️ Python import hygiene — action required before cross-module imports are written

This folder is named `decision_engine/` with a **hyphen**. Python cannot import packages with hyphens. The following will fail:

```python
from decision_engine.policy import PolicyEngine  # SyntaxError
```

Before any module in this folder imports from another module in the same folder, the folder **must be renamed** to `decision_engine/` (underscore). Update all references in `README.md`, `SYSTEM_DESIGN.md`, and this file simultaneously. This is low-effort but must happen before Sprint 2 implementation begins.