# DOMAIN_MODEL.md

Defines the core entities the system operates on and how they relate. This is the single source of truth for what a "Factory," "Pathway," or "Recommendation" actually means in code — every model in `models/`, every knowledge-base JSON schema, and every frontend `types/*.ts` file should trace back to an entity here. If a new field or entity is needed anywhere in the codebase, add it here first, then implement it.

> Maps directly to confirmed `models/`: `industry.py`, `technology.py`, `scenario.py`, `financial.py`, `emission.py`, `recommendation.py`.

---

## 1. Factory (a.k.a. MSME Profile / Digital Twin baseline)

The root entity. Everything else is computed *for* a Factory.

| Field | Type | Notes |
|---|---|---|
| `factory_id` | string | unique |
| `name` | string | display name (real or scenario name, e.g. "Scenario T1") |
| `industry` | Industry ref | → `knowledge-base/industries/*.json` |
| `state` | string | drives `finance/electricity_tariffs.json` lookup (state-specific, not national) |
| `district` | string | drives biomass/solar resource lookups |
| `production_per_day` | number + unit | e.g. kg/day, tonnes/day |
| `operating_hours_per_day` | number | |
| `current_fuel` | Fuel ref | coal / furnace oil / pet coke / biomass / electricity / mixed |
| `fuel_consumption` | number + unit | current baseline |
| `electricity_consumption_kwh_day` | number | |
| `required_process_temperature_c` | number | **critical constraint** — filters technology feasibility |
| `roof_area_sqm` | number | for solar feasibility |
| `available_land_sqm` | number | optional |
| `budget_inr` | number | investment ceiling |
| `grid_reliability_pct` | number | affects electrification feasibility |
| `msme_classification` | enum | micro / small / medium (Udyam thresholds — see `knowledge-base` Step 1 research) |
| `udyam_registered` | boolean | **gates subsidy eligibility** (CLCSS, MNRE CFA, PSL rates all require this) |
| `udyam_number` | string \| null | optional; required only if `udyam_registered` is true |
| `annual_turnover_inr` | number | **required for Module 4a** — feeds `enterprise_category` derivation and scheme eligibility (see `knowledge-base/policies/eligibility_rules.json`) |
| `plant_and_machinery_or_equipment_investment_inr` | number | **required for Module 4a** — Udyam classification threshold input, distinct from `budget_inr` (project budget) |
| `project_type` | enum | one of: energy_efficiency / electrification / renewable_energy / alternative_fuel / biomass / waste_heat_recovery / energy_storage / waste_management / circular_economy / clean_transport / pollution_control / green_infrastructure / other — **required for Module 4a**, drives scheme matching |
| `project_cost_inr` | number | **required for Module 4a** — distinct from `budget_inr`; total cost of the specific transition project being evaluated |
| `loan_amount_inr` | number \| null | optional — required only for credit-guarantee schemes (e.g. CGTMSE) |
| `existing_or_new_project` | enum | existing / new — **required for Module 4a** (e.g. gates PMEGP eligibility) |
| `brownfield_or_greenfield` | enum \| null | brownfield / greenfield / not_applicable — optional |
| `cluster_name` | string \| null | optional |
| `cluster_is_adeetie_identified` | boolean \| null | optional — gates ADEETIE eligibility |
| `annual_energy_savings_percent` | number \| null | optional — gates ADEETIE eligibility (≥10% threshold) |
| `special_category` | object \| null | optional — booleans: `women_owned`, `sc_st_owned`, `pwd_owned`, `agniveer_owned`, `transgender_owned`, `north_east_region`, `jammu_kashmir`, `ladakh`, `aspirational_district`, `identified_credit_deficient_district` |

**Field source note:** the Module 4a fields above are copied field-for-field from `knowledge-base/policies/eligibility_rules.json`'s `factory_profile_requirements.required_fields` block — that file is the source of truth for exact names/types/enums; keep this table in sync with it if it changes.

**Immutability rule (from architecture plan):** the Factory's current-state baseline, once computed, is immutable. Pathways are computed *against* it, never by mutating it.

---

## 2. Industry

Sector-level defaults and constraints. One Factory belongs to one Industry.

| Field | Type | Notes |
|---|---|---|
| `industry_id` | string | e.g. `textile`, `food_processing`, `cement`, `steel`, `chemical`, `pharma` |
| `typical_temperature_range_c` | [min, max] | |
| `typical_energy_split` | { electricity_pct, thermal_pct } | e.g. 15/85 for MSME sector avg (World Bank/TERI figure) |
| `applicable_technologies` | Technology[] ref | which of the six technology files apply to this sector |
| `sub_process` | string | e.g. "dyeing / wet-processing" for textile — **scope-critical**, see note below |

⚠️ **Open question (see PROJECT_STATE.md Section 5 flag):** confirm whether the prototype's Factory instances are restricted to `industry_id = textile` only, or genuinely span all six. This model supports either, but the decision-engine logic (feasibility filters, scenario generation) should be built and tested against one industry first.

---

## 3. Technology

One entry per intervention type. Matches confirmed files: `biomass.json`, `electrification.json`, `heat_pump.json`, `solar_thermal.json`, `thermal_storage.json`, `waste_heat_recovery.json`.

| Field | Type | Notes |
|---|---|---|
| `technology_id` | string | |
| `input_energy_form` | enum | biomass / electricity / solar / waste heat |
| `output_energy_form` | enum | steam / thermal / electricity |
| `suitable_industries` | Industry[] ref | |
| `temperature_range_c` | [min, max] | **feasibility gate** — this is what `technology_filter.py` should check first |
| `capex_inr_range` | [min, max] | |
| `opex_inr_per_unit` | number | |
| `efficiency_pct` | number | |
| `capacity_range` | [min, max] + unit | |
| `lifetime_years` | number | |
| `emission_factor` | number | kg CO2 / unit output |
| `local_availability_dependent` | boolean | true for biomass — triggers the biomass-logistics check |
| `constraints` | string[] | e.g. "requires grid capacity upgrade," "requires existing boiler retrofit compatibility" |
| `source_citation` | ref → `references/citations.json` | **every number here must be traceable** |

---

## 4. Scenario / Pathway

A candidate combination of technologies applied to a Factory. The system generates **multiple** Pathways per Factory (3–5), never just one.

| Field | Type | Notes |
|---|---|---|
| `scenario_id` | string | |
| `factory_id` | Factory ref | |
| `technology_sequence` | Technology[] | e.g. [efficiency, biomass, solar] — ordered |
| `capex_total_inr` | number | computed |
| `annual_opex_inr` | number | computed |
| `fossil_fuel_reduction_pct` | number | computed |
| `co2_reduction_pct` | number | computed |
| `payback_years` | [low, high] | **range, not a point estimate** — sensitivity analysis requirement |
| `reliability_score_pct` | number | |
| `financing_eligible_schemes` | Subsidy[] ref | from `finance/subsidies.json` |
| `rejected_technologies` | { technology_id, reason }[] | **for the "Why not?" explainability feature** |
| `objective_scores` | { cost, emissions, risk } | inputs to the MCDA ranking in `optimizer/mcda.py` |

---

## 5. Recommendation

The final output shown to the user — one Scenario elevated to "recommended," plus the comparison context.

| Field | Type | Notes |
|---|---|---|
| `factory_id` | Factory ref | |
| `recommended_scenario_id` | Scenario ref | |
| `all_scenarios` | Scenario[] | full comparison set — UI shows all, not just the winner |
| `explanation` | { why_selected: string[], why_others_rejected: {scenario_id, reason}[] } | |
| `sensitivity_notes` | string[] | e.g. "payback extends to 4.4yr if electricity price rises 15%" |
| `generated_at` | timestamp | |

---

## 6. FinancialModel (embedded in Scenario, but worth defining separately since `financial.py` exists standalone)

| Field | Type | Notes |
|---|---|---|
| `capex_gross_inr` | number | |
| `eligible_subsidy_inr` | number | from `finance/subsidies.json` + `policies/eligibility_rules.json`, gated by `udyam_registered` |
| `interest_subvention_pct` | number | e.g. ADEETIE's 5%/3% (micro-small / medium) |
| `net_financed_cost_inr` | number | |
| `npv_inr` | number | optional, if `roi.py` computes it |
| `simple_payback_years` | number | |

---

## 7. EmissionModel (embedded in Scenario, `emission.py`)

| Field | Type | Notes |
|---|---|---|
| `baseline_co2_tonnes_year` | number | |
| `pathway_co2_tonnes_year` | number | |
| `reduction_pct` | number | |
| `grid_emission_factor_used` | number | from `emissions/grid_factors.json` — **must match the Factory's state**, grid mix varies by state |

---

## Entity relationship summary

```
Factory ──belongs to──> Industry ──lists──> Technology[] (applicable)
   │
   └──generates──> Scenario[] (pathways)
                       │
                       ├── uses ──> Technology[] (selected, ordered)
                       ├── has  ──> FinancialModel
                       ├── has  ──> EmissionModel
                       └── scored by ──> optimizer/mcda.py ──> objective_scores

Recommendation ──selects one of──> Scenario[]
               ──explains via──> rejected_technologies + why_others_rejected
```

---

## Notes for implementers

- **Every `Technology` and `Industry` field with a real-world number must carry a `source_citation`** pointing into `references/citations.json`. This is what makes the explainability engine defensible in front of SIH judges — "why biomass?" should be answerable by walking this citation chain, not by trusting a hardcoded number.
- **`payback_years` and other financial/technical outputs should be ranges, not points** — this was a deliberate design decision from the research phase (H4, RQ6) to avoid presenting false precision.
- If `digital-twin/` becomes a real separate module (see PROJECT_STATE.md flag), it should own the `Factory` baseline computation currently living in `decision-engine/baseline/`, and this entity definition doesn't need to change — only where the computation code lives.