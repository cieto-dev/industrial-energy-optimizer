# PROJECT_STATE.md

**Project:** AI-Powered Industrial Energy Transition Platform (working repo name: `msme-energy-optimizer`)
**Track:** Smart India Hackathon (SIH) prototype → intended startup direction
**Team size:** 6 members
**Status date:** 16 August 2026 (re-verified against live repo same day — see §0)
**Repo:** https://github.com/cieto-dev/industrial-energy-optimizer

> This file is a living snapshot of where the project actually stands — problem, evidence, architecture, gaps, and next actions. It is reconciled against the team's own `SYSTEM_DESIGN.md`, `RESEARCH_NOTES.md`, `MENTOR_NOTES.md`, and `FEATURE_BACKLOG.md`, which are the authoritative sources where they conflict with earlier drafts of this file. Update it whenever a research phase closes, a scope decision is made, or the architecture changes.

---

## 0. Correction notice (16 Aug 2026, updated)

An earlier version of this file, built from repo folder/file screenshots alone, was **too optimistic** about implementation status. The team's own `SYSTEM_DESIGN.md` status table (§10) and `FEATURE_BACKLOG.md` are explicit: **backend is scaffolding only, frontend is folder structure only, database/AI/testing/deployment are all still pending.** File names existing is not the same as logic existing — this file now reflects that distinction accurately. Treat `SYSTEM_DESIGN.md`, `RESEARCH_NOTES.md`, and `FEATURE_BACKLOG.md` as the primary sources of truth for status going forward; this file summarizes and cross-links them.

**Second correction (16 Aug 2026, same day):** this file had also drifted stale in the other direction — several items logged as gaps had already been fixed by the time this was re-checked against the live repo (via GitHub API/tarball, actual file content, not folder screenshots). See §5 and §8 for the specific corrections. Lesson: this file needs to be re-verified against live repo content periodically, not just written once and trusted.

---

## 1. The Problem (current, final framing)

**We are NOT building:** "AI that replaces coal with solar" / a generic renewable-energy calculator / a carbon footprint calculator / an energy audit app / a chatbot.

**We ARE building:** An engineering decision-support system that combines engineering models, optimization, financial evaluation, and explainable AI to recommend the most suitable energy-transition pathway for a specific industrial MSME — supporting, not replacing, engineering judgment.

### Master Research Question (MRQ)
> Can a data-driven techno-economic decision-support system identify and compare technically feasible, economically viable, and lower-emission energy-transition pathways for individual Indian MSMEs under process, resource, reliability, and financial constraints?

### Six sub-questions (RQ1–RQ6)
1. **Baseline** — What are the dominant energy uses and fossil-fuel dependencies of the selected MSME process?
2. **Technology** — Which efficiency, electrification, renewable, alternative-fuel, and storage technologies are technically applicable?
3. **Local resources** — How do location-specific solar, biomass, and grid conditions affect feasibility?
4. **Economics** — How do CAPEX, OPEX, fuel/electricity prices, and financing affect pathway selection?
5. **Optimization** — Can multiple technologies be combined/sequenced to meet process-energy needs at minimum cost/emissions?
6. **Robustness** — How sensitive is the recommended pathway to price, resource, and production uncertainty?

### Why this framing
- Solar/wind aren't "inefficient" — their output is variable while industrial loads are often continuous. The real engineering problem is **generation + intermittency + storage + dispatch + economics + reliability**, not generation volume.
- The bottleneck isn't that clean technologies don't exist. The bottleneck is **decision-making**: which combination is right for *this* factory, under *its* constraints — and being able to explain why.

---

## 2. Evidence base (why this problem is real and 2026-relevant)

Converging January–April 2026 signals, now also formally listed in `RESEARCH_NOTES.md`:

| Source | Key contribution |
|---|---|
| **NITI Aayog** — *Roadmap for Green Transition of MSMEs* (Jan 2026) | Models 35–55% shift away from coal/high-emission fuels; names priority MSME clusters |
| **MNRE + GIZ** — *Decarbonizing MSMEs: Biomass for Green Steam & Heat* (Jan 2026) | MSMEs get 80%+ of manufacturing energy from process heat; biomass supply-chain reliability is the real constraint, not technology availability |
| **BEE — ADEETIE programme** | 60 clusters, 14 sectors; proves the audit/technology-database layer is already solved — our gap is the decision layer above it |
| **Energy Innovation** — *Electrifying Industrial Heat in India* (Apr 2026) | Electrified heat now cheaper than coal in bands covering ~55% of India's industrial heat demand — the optimizer must not assume biomass is always the answer |
| **IEA** — Renewables for Industry / Heat Pump Monitor 2026, SHC Task 49/64 | Concrete technology boundaries now baked into the knowledge base (see §5) |
| **DOE** — Process Heating Sourcebook, WHR Technology Assessment, CHP review | Source used for waste-heat and storage temperature ranges |

**Existing adjacent tools (so we don't overclaim novelty):** NREL STEP 1, FlexiHeat-DST, BEE/SIDHIEE. None integrate India-specific process constraints + local resources + Indian tariffs/financing + uncertainty + explainability into one MSME-facing pathway optimizer. **That integration is the claimed gap** — stated carefully, never as "nobody has built this."

Full citation list: `research/bibliography.md`. Per-parameter sourcing lives inline in each `knowledge-base/**/*.json` file via `source_id`/`confidence`/`last_verified` fields (a deliberate design choice — see `RESEARCH_NOTES.md`).

---

## 3. Sector & scope decision

**Selected first vertical: Textile dyeing / wet-processing MSME using solid fuel (coal/biomass) for steam.**

Reasoning unchanged from earlier research: process heat is central, strong 2026 Indian evidence exists, and it avoids the furnace-modeling complexity of cement/steel.

**⚠️ Status conflict to resolve:** `knowledge-base/industries/` has six populated sectors (cement, chemical, food_processing, pharma, steel, textile) — confirmed "✅ Completed" in `FEATURE_BACKLOG.md` Phase 1. The original plan was to scope the *prototype* to textile only, with other sectors as future data. **This has not been explicitly re-confirmed since the knowledge base expanded** — resolve and record the answer here.

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
[ Policy & Eligibility Check — Module 4a, scope pending, see §5a ]
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

Full module-by-module reference: `docs/SYSTEM_DESIGN.md` §4 (authoritative) and `docs/DECISION_ENGINE_ARCHITECTURE.md` (companion doc — needs a pass to align its module list with `SYSTEM_DESIGN.md`'s numbering, since the two were written independently and use slightly different module boundaries/names for the same logic).

### Implementation status by layer (per `SYSTEM_DESIGN.md` §10 and `FEATURE_BACKLOG.md` — authoritative, corrects earlier optimism)

| Component | Status |
|---|---|
| Research | ✅ Complete |
| Knowledge base — industries, technologies, constraints, finance | 🟡 Populated, consistency pass in progress |
| Knowledge base — policies, emissions, references | 🟡 Built, not yet integrated / has real gaps (see §5) |
| Documentation | 🟡 In progress |
| Database design | ⏳ Pending |
| Backend | ⏳ **Pending — scaffolding only.** Files exist (`apis/*.py`, `main.py`, etc.) but per the team's own status table this is structure, not working logic. |
| Frontend | ⏳ **Pending — folder structure only.** Same caveat as backend. |
| Decision engine | 🟡 Mixed — `emissions/` (co2_calculator.py, emission_engine.py, emission_factors.py) and `technology/` (technology_engine.py, technology_filter.py, technology_matcher.py) contain real implementation code, not stubs (confirmed by reading file content 16 Aug 2026). `scenario/scenario_generator.py` also has logic. `baseline/`, `economics/`, `optimizer/`, `reliability/`, `reports/` are still 0-byte stubs. Code existing ≠ tested/integrated — functional status of the written modules is still unconfirmed, but this is further along than the earlier "all pending" read. |
| AI layer | ⏳ Pending |
| Testing | ⏳ Pending — test file stubs only, no logic yet |
| Deployment | ⏳ Pending — Docker/nginx config scaffolded, unused |
| Digital twin | Out of MVP — `digital-twin/future_scope.md` only, correctly deferred to Future Improvements |

**Net correction:** the repo has excellent, consistent *scaffolding* across every layer — this reflects real planning discipline. But almost nothing is confirmed functionally working yet outside the knowledge base and research. Progress should now be measured by modules moving from "scaffolded" to "implemented and tested," per `FEATURE_BACKLOG.md`'s lifecycle (Planned → In Progress → Testing → Completed).

---

## 5. Knowledge base — status and real gaps

Structure (seven sub-domains) confirmed via repo screenshots and now cross-verified against `FEATURE_BACKLOG.md` Phase 1 and `RESEARCH_NOTES.md`:

```
knowledge-base/
├── constraints/   (budget, fuel, grid, space, technology_rules, temperature)
├── emissions/     (emission_factors, grid_factors)
├── finance/       (electricity_tariffs, fuel_prices, subsidies, technology_costs)
├── industries/    (cement, chemical, food_processing, pharma, steel, textile)
├── master/        (discoms, district_discoms, districts, fuels, industries,
│                   states, tariffs, technologies) — NOT previously documented here;
│                   found via live repo check 16 Aug 2026, appears generated by
│                   scripts/create_district_discoms.py, create_districts_json.py,
│                   create_tariffs_json.py (also undocumented until now)
├── policies/      (carbon_pricing, central_policies, eligibility_rules,
│                   renewable_purchase_obligations, state_policies)
├── references/    (citations, sources)
└── technologies/  (biomass, electrification, heat_pump, solar_thermal,
                    thermal_storage, waste_heat_recovery)
```

### Confirmed real gaps and issues (per `FEATURE_BACKLOG.md` Phase 1 + `RESEARCH_NOTES.md`)

| Issue | Severity | Detail |
|---|---|---|
| ~~`emissions/emission_factors.json` empty~~ | ✅ Resolved | Populated — 7 fuels (coal, diesel, LPG, natural gas, biomass, biogas, furnace oil), IPCC-based emission factors + NCV, sourced (`SRC003`/`SRC004`). Confirmed against live repo content 16 Aug 2026. Previous "empty/blocking" status was stale documentation, not a real gap. |
| `technologies/solar_thermal.json` thinner than other technology files | 🟡 | Confirmed still true (2,048 bytes vs. 4–9KB for other technology files). Needs expansion; also doesn't yet distinguish non-concentrating (60–150°C) vs. concentrating (150–400°C) sub-technologies |
| Subsidy data duplicated across 3 files | 🟠 | Confirmed — `policies/central_policies.json`, `finance/subsidies.json`, and `constraints/budget.json` all carry a CGTMSE entry independently. Needs deduplication into one source of truth before database schema design |
| **Conflicting CGTMSE guarantee coverage number — corrected** | 🟠 | Previous entry here was itself wrong (`central_policies.json` "75%" vs. `budget.json` "75–90%") — re-checked against live file content 16 Aug 2026: `budget.json` and `central_policies.json` actually **agree** (75–90%). The real conflict is `finance/subsidies.json`, which says **75–85%** (max differs from the other two by 5 points). Someone needs to check the current CGTMSE source (cgtmse.in) and fix whichever file is wrong — not guessing the correct number here. Still blocks Phase 3 per `FEATURE_BACKLOG.md`. |
| `constraints/technology_rules.json` references `paper`, `dairy`, `glass` industries | 🟢 | No corresponding `industries/*.json` profile exists yet for these three — flagged as an open research question, not urgent |
| ~~`references/` folder empty~~ | ✅ Resolved | Populated — `citations.json` (13.3KB) + `sources.json` (9.8KB). Confirmed against live repo content 16 Aug 2026. Previous "empty" status was stale documentation. |
| `policies/` fully built but **not yet integrated** — see §5a | 🔴 Blocking (scope) | See below |
| `knowledge-base/master/` folder and its generating scripts undocumented | 🟢 | Found via live repo check 16 Aug 2026 — see §3 diagram above. Not a functional gap, but nobody wrote down what this folder is for or that the scripts exist; needs a short doc entry so it doesn't get rediscovered again |

### 5a. ⚠️ OPEN SCOPE DECISION — Policy & Eligibility Engine (Module 4a)

This is the single most important open decision in the project right now, and it's explicitly flagged as blocking in `FEATURE_BACKLOG.md`.

`knowledge-base/policies/` is fully built (central/state policies, eligibility rules, carbon pricing, renewable purchase obligations) — well beyond what a "future enhancement" would normally have. But:
- No corresponding module exists yet in `decision-engine/` or is confirmed in scope in `SYSTEM_DESIGN.md` (documented there as "Module 4a — status: scope not yet finalized").
- If it's brought into MVP scope, the User Input module needs new fields (Udyam registration, enterprise category, turnover, investment, project type, cluster membership, special-category status) that **are not currently being collected**.
- If it's brought into MVP scope, the subsidy-data duplication issue above must be resolved first.

**Decide one of:**
- **(A) Bring it into MVP scope** as Module 4a — requires the User Input extension and data dedup above.
- **(B) Confirm it stays out of MVP** — freeze further `policies/` work, keep it as a head start for post-SIH development.

**Until decided:** per `FEATURE_BACKLOG.md`, no further content should be added to `knowledge-base/policies/` — resolve the decision first so effort isn't wasted either direction.

**Owner:** _[assign]_ **Target decision date:** _[fill in]_ — *(both currently blank in `FEATURE_BACKLOG.md` — this needs an owner assigned this week, not left open indefinitely)*

---

## 6. Team structure (6 members, ownership not silos)

| Member | Owns | Output |
|---|---|---|
| 1 | Domain / process research | Textile dyeing process model |
| 2 | Energy & technology research | Technology knowledge base |
| 3 | Data & geospatial | MSME/solar/biomass/tariff datasets |
| 4 | Economics & finance | CAPEX/OPEX/financing model |
| 5 | Optimization / backend | Constraint engine, optimizer, sensitivity analysis |
| 6 | Product / frontend / validation | UI, comparison dashboard, demo, docs |

Everyone should understand the whole system — these are ownership areas, not walls.

---

## 7. What's genuinely solved elsewhere (be honest about this in the pitch)

Energy audits, technology databases, MSME EE schemes, financial support, solar/biomass/waste-heat/induction feasibility tools, carbon calculators, and industrial decarbonization roadmaps **all already exist**. Never claim any of these individually as novel.

**Claimed novelty = integration + India/MSME-specific constraint modeling + accessibility + explainability**, not any single component.

---

## 8. Immediate next actions

Per `FEATURE_BACKLOG.md`'s own "Next Development Target" list (authoritative — reproduced here for visibility), in order:

1. **Resolve the Module 4a subsidy/policy scope decision** (§5a) — assign an owner and target date this week; this blocks meaningful further knowledge-base and decision-engine work on that module.
2. **Finish the knowledge-base consistency pass** — `emission_factors.json` is already done (see §5 correction); remaining work is: dedupe subsidy data across 3 files, reconcile the CGTMSE 85%-vs-90% conflict against a real source, expand `solar_thermal.json`.
3. **Design database schema** from the now-consistent knowledge-base structure — explicitly blocked on step 2.
4. **Build the `scripts/` ETL pipeline**: `convert_datasets.py` → `pre_process.py` → `load_knowledge.py` → `seed_database.py`.
5. **Define API contracts** for `backend/apis/` — this is what turns the current file scaffolding into real interfaces the frontend and decision-engine can build against.
6. **Start backend implementation** (`backend/database.py`, `backend/main.py`, then `models/`).

**Additional items from this file's own review:**
7. **Log mentor/jury feedback** — `MENTOR_NOTES.md` currently has zero entries despite being fully templated. If any mentor sessions have happened, backfill them now before details are forgotten; if none have happened yet, prioritize getting one scheduled given the project's maturity.
8. **Start using `SESSION_LOG.md`** — referenced as "actively used" in `FEATURE_BACKLOG.md`/`SYSTEM_DESIGN.md` §12 but not yet reviewed here — confirm it's actually being kept current.
9. ~~Verify README.md status~~ — ✅ Resolved 16 Aug 2026: root `README.md` is 5,145 bytes, fully written (problem statement, architecture, stack, project structure, getting-started commands, status, team, research base). `FEATURE_BACKLOG.md`'s "complete" mark was correct; the earlier "23-byte stub" note was itself the stale claim.
10. Once steps 1–6 are done: **run the full pipeline end-to-end against one representative textile MSME scenario** — this remains the real measure of progress, more meaningful than any file count.

---

## 9. Open risks / honesty checks

- **Backend and frontend are still scaffolded, not implemented** — confirmed unchanged 16 Aug 2026 (all backend `.py` files and nearly all frontend files are 0 bytes). **Decision-engine is no longer fully in this bucket** — its `emissions/` and `technology/` modules contain real code (confirmed by reading file content, not just size); `baseline/`, `economics/`, `optimizer/`, `reliability/`, `reports/` remain empty. Don't let this correction become the next overclaim — "has code" is not the same as "tested and integrated."
- **Module 4a (policy/eligibility) is a real, unassigned, undated open decision** — see §5a. This is scope risk, not just a technical gap.
- **Knowledge base has a blocking gap** (`emission_factors.json` empty) and **a real data-integrity issue** (conflicting CGTMSE numbers) that should be fixed before the database schema is designed, since the schema will inherit whatever inconsistencies exist at that point.
- **Sector scope re-confirmation needed** — six industries built vs. original one-sector prototype plan.
- **Novelty claim is real but narrow** — must be pitched as "integration of fragmented existing tools into an India/MSME-specific pathway system," never as "no such system exists."
- **`MENTOR_NOTES.md` unused** — zero mentor feedback logged despite the project's maturity; this is a missed opportunity for external validation before further build time is spent.
- **Documentation quality is a genuine strength** — `SYSTEM_DESIGN.md`, `RESEARCH_NOTES.md`, and `FEATURE_BACKLOG.md` are unusually disciplined and self-correcting (they flag their own inconsistencies, e.g. the CGTMSE conflict, the subsidy duplication, the Module 4a gap). This is worth preserving as a habit through the build phase, not just the planning phase.