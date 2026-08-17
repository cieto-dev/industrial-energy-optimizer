-- ============================================================================
-- 001_initial_schema.sql
-- Industrial Energy Transition Platform — Initial Database Schema
--
-- Derived from: docs/DOMAIN_MODEL.md (entities §1–§7)
-- Target DB:    PostgreSQL 15+
-- Created:      2026-08-17
--
-- DOMAIN_MODEL.md entity mapping:
--   §1 Factory              → factories
--   §2 Industry             → industries
--   §3 Technology           → technologies
--   §2↔§3 M:N relationship  → industry_technologies
--   §4 Scenario / Pathway   → scenarios
--   §5 Recommendation       → recommendations
--   §6 FinancialModel       → financial_models
--   §7 EmissionModel        → emission_models
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. ENUM TYPES
-- ============================================================================

-- §1 Factory.current_fuel
-- Values from DOMAIN_MODEL §1 + knowledge-base/emissions/emission_factors.json
CREATE TYPE fuel_type AS ENUM (
    'coal',
    'furnace_oil',
    'pet_coke',
    'biomass',
    'electricity',
    'mixed',
    'diesel',
    'lpg',
    'natural_gas',
    'biogas'
);

-- §3 Technology.input_energy_form / output_energy_form
CREATE TYPE energy_form AS ENUM (
    'biomass',
    'electricity',
    'solar',
    'waste_heat',
    'steam',
    'thermal'
);

-- §1 Factory.msme_classification
CREATE TYPE msme_class AS ENUM (
    'micro',
    'small',
    'medium'
);

-- §1 Factory.project_type
-- Full list from DOMAIN_MODEL §1 (Module 4a fields — nullable for MVP)
CREATE TYPE project_type_enum AS ENUM (
    'energy_efficiency',
    'electrification',
    'renewable_energy',
    'alternative_fuel',
    'biomass',
    'waste_heat_recovery',
    'energy_storage',
    'waste_management',
    'circular_economy',
    'clean_transport',
    'pollution_control',
    'green_infrastructure',
    'other'
);

-- §1 Factory.existing_or_new_project
CREATE TYPE project_lifecycle AS ENUM (
    'existing',
    'new'
);

-- §1 Factory.brownfield_or_greenfield
CREATE TYPE site_type AS ENUM (
    'brownfield',
    'greenfield',
    'not_applicable'
);


-- ============================================================================
-- 2. TABLES
-- ============================================================================

-- --------------------------------------------------------------------------
-- 2.1 industries  (DOMAIN_MODEL §2)
--
-- Sector-level defaults and constraints.
-- One Factory belongs to one Industry.
-- --------------------------------------------------------------------------
CREATE TABLE industries (
    industry_id              TEXT        PRIMARY KEY,
        -- e.g. 'textile', 'food_processing', 'cement', 'steel', 'chemical',
        --      'pharma', 'dairy', 'glass', 'paper'
        -- Matches knowledge-base/industries/*.json filenames

    typical_temperature_min_c NUMERIC    NOT NULL,
    typical_temperature_max_c NUMERIC    NOT NULL,
        -- §2 typical_temperature_range_c: [min, max]

    typical_energy_split     JSONB       NOT NULL DEFAULT '{}',
        -- §2: { "electricity_pct": N, "thermal_pct": N }

    sub_process              TEXT,
        -- §2: e.g. "dyeing / wet-processing" for textile

    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_temp_range CHECK (typical_temperature_min_c <= typical_temperature_max_c)
);

COMMENT ON TABLE  industries IS 'DOMAIN_MODEL §2 — Industry sector-level defaults and constraints.';
COMMENT ON COLUMN industries.typical_energy_split IS 'JSON: {"electricity_pct": N, "thermal_pct": N}';


-- --------------------------------------------------------------------------
-- 2.2 technologies  (DOMAIN_MODEL §3)
--
-- One entry per intervention type. Matches confirmed files:
-- biomass.json, electrification.json, heat_pump.json, solar_thermal.json,
-- thermal_storage.json, waste_heat_recovery.json, biogas.json
-- --------------------------------------------------------------------------
CREATE TABLE technologies (
    technology_id            TEXT        PRIMARY KEY,

    input_energy_form        energy_form NOT NULL,
        -- §3: biomass / electricity / solar / waste_heat

    output_energy_form       energy_form NOT NULL,
        -- §3: steam / thermal / electricity

    temperature_min_c        NUMERIC     NOT NULL,
    temperature_max_c        NUMERIC     NOT NULL,
        -- §3 temperature_range_c: [min, max]
        -- FEASIBILITY GATE — technology_filter.py checks this first

    capex_inr_min            NUMERIC     NOT NULL,
    capex_inr_max            NUMERIC     NOT NULL,
        -- §3 capex_inr_range: [min, max]

    opex_inr_per_unit        NUMERIC     NOT NULL,
        -- §3: operating cost per unit

    efficiency_pct           NUMERIC     NOT NULL,
        -- §3: technology efficiency percentage

    capacity_min             NUMERIC,
    capacity_max             NUMERIC,
    capacity_unit            TEXT,
        -- §3 capacity_range: [min, max] + unit

    lifetime_years           NUMERIC     NOT NULL,
        -- §3: expected operational lifetime

    emission_factor          NUMERIC     NOT NULL,
        -- §3: kg CO2 / unit output

    local_availability_dependent BOOLEAN NOT NULL DEFAULT FALSE,
        -- §3: true for biomass — triggers biomass-logistics check

    constraints              JSONB       NOT NULL DEFAULT '[]',
        -- §3: string[] e.g. ["requires grid capacity upgrade",
        --     "requires existing boiler retrofit compatibility"]

    source_citation          JSONB       NOT NULL DEFAULT '{}',
        -- §3: ref → references/citations.json
        -- "every number here must be traceable"

    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_tech_temp_range  CHECK (temperature_min_c  <= temperature_max_c),
    CONSTRAINT chk_tech_capex_range CHECK (capex_inr_min      <= capex_inr_max),
    CONSTRAINT chk_tech_cap_range   CHECK (capacity_min IS NULL OR capacity_min <= capacity_max),
    CONSTRAINT chk_efficiency       CHECK (efficiency_pct >= 0 AND efficiency_pct <= 100)
);

COMMENT ON TABLE  technologies IS 'DOMAIN_MODEL §3 — One entry per intervention / technology type.';
COMMENT ON COLUMN technologies.constraints IS 'JSON array of string constraint descriptions.';
COMMENT ON COLUMN technologies.source_citation IS 'JSON ref to references/citations.json — traceability requirement.';


-- --------------------------------------------------------------------------
-- 2.3 industry_technologies  (DOMAIN_MODEL §2 ↔ §3 M:N)
--
-- §2 Industry.applicable_technologies → Technology[] ref
-- §3 Technology.suitable_industries   → Industry[] ref
-- --------------------------------------------------------------------------
CREATE TABLE industry_technologies (
    industry_id    TEXT NOT NULL REFERENCES industries(industry_id) ON DELETE CASCADE,
    technology_id  TEXT NOT NULL REFERENCES technologies(technology_id) ON DELETE CASCADE,

    PRIMARY KEY (industry_id, technology_id)
);

COMMENT ON TABLE industry_technologies IS 'M:N junction: which technologies apply to which industries (DOMAIN_MODEL §2–§3).';


-- --------------------------------------------------------------------------
-- 2.4 factories  (DOMAIN_MODEL §1)
--
-- The root entity. Everything else is computed *for* a Factory.
-- Immutability rule: baseline is immutable once computed. Pathways are
-- computed *against* it, never by mutating it.
-- --------------------------------------------------------------------------
CREATE TABLE factories (
    factory_id               TEXT        PRIMARY KEY,
        -- §1: unique identifier

    name                     TEXT        NOT NULL,
        -- §1: display name (real or scenario name, e.g. "Scenario T1")

    industry_id              TEXT        NOT NULL
                             REFERENCES industries(industry_id) ON DELETE RESTRICT,
        -- §1: Industry ref → knowledge-base/industries/*.json

    state                    TEXT        NOT NULL,
        -- §1: drives finance/electricity_tariffs.json lookup (state-specific)

    district                 TEXT        NOT NULL,
        -- §1: drives biomass/solar resource lookups

    production_per_day       NUMERIC     NOT NULL,
    production_unit          TEXT        NOT NULL,
        -- §1 production_per_day: number + unit (e.g. kg/day, tonnes/day)

    operating_hours_per_day  NUMERIC     NOT NULL,

    current_fuel             fuel_type   NOT NULL,
        -- §1: coal / furnace_oil / pet_coke / biomass / electricity / mixed

    fuel_consumption         NUMERIC     NOT NULL,
    fuel_consumption_unit    TEXT        NOT NULL,
        -- §1 fuel_consumption: number + unit (current baseline)

    electricity_consumption_kwh_day NUMERIC NOT NULL,

    required_process_temperature_c  NUMERIC NOT NULL,
        -- §1: **critical constraint** — filters technology feasibility

    roof_area_sqm            NUMERIC     NOT NULL,
        -- §1: for solar feasibility

    available_land_sqm       NUMERIC,
        -- §1: optional

    budget_inr               NUMERIC     NOT NULL,
        -- §1: investment ceiling

    grid_reliability_pct     NUMERIC     NOT NULL,
        -- §1: affects electrification feasibility

    -- ---- MSME classification fields ----

    msme_classification      msme_class,
        -- §1: micro / small / medium (Udyam thresholds)
        -- Nullable for MVP — Module 4a deferred

    udyam_registered         BOOLEAN,
        -- §1: **gates subsidy eligibility** (CLCSS, MNRE CFA, PSL rates)

    udyam_number             TEXT,
        -- §1: required only if udyam_registered is true

    annual_turnover_inr      NUMERIC,
        -- §1: feeds enterprise_category derivation and scheme eligibility

    plant_and_machinery_or_equipment_investment_inr NUMERIC,
        -- §1: Udyam classification threshold input, distinct from budget_inr

    -- ---- Module 4a fields (nullable — deferred to post-MVP) ----

    project_type             project_type_enum,
        -- §1: drives scheme matching

    project_cost_inr         NUMERIC,
        -- §1: distinct from budget_inr; total cost of transition project

    loan_amount_inr          NUMERIC,
        -- §1: optional — for credit-guarantee schemes (e.g. CGTMSE)

    existing_or_new_project  project_lifecycle,
        -- §1: gates PMEGP eligibility

    brownfield_or_greenfield site_type,

    cluster_name             TEXT,
    cluster_is_adeetie_identified BOOLEAN,

    annual_energy_savings_percent NUMERIC,
        -- §1: gates ADEETIE eligibility (≥10% threshold)

    special_category         JSONB,
        -- §1: optional booleans object:
        -- {
        --   "women_owned": bool,
        --   "sc_st_owned": bool,
        --   "pwd_owned": bool,
        --   "agniveer_owned": bool,
        --   "transgender_owned": bool,
        --   "north_east_region": bool,
        --   "jammu_kashmir": bool,
        --   "ladakh": bool,
        --   "aspirational_district": bool,
        --   "identified_credit_deficient_district": bool
        -- }

    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_grid_reliability CHECK (grid_reliability_pct >= 0 AND grid_reliability_pct <= 100),
    CONSTRAINT chk_operating_hours  CHECK (operating_hours_per_day >= 0 AND operating_hours_per_day <= 24),
    CONSTRAINT chk_udyam_number     CHECK (
        (udyam_registered IS NOT TRUE) OR
        (udyam_registered IS TRUE AND udyam_number IS NOT NULL)
    )
);

COMMENT ON TABLE  factories IS 'DOMAIN_MODEL §1 — Root entity. Everything else is computed *for* a Factory. Baseline is immutable once computed.';
COMMENT ON COLUMN factories.special_category IS 'JSON object with boolean flags: women_owned, sc_st_owned, pwd_owned, agniveer_owned, transgender_owned, north_east_region, jammu_kashmir, ladakh, aspirational_district, identified_credit_deficient_district';
COMMENT ON COLUMN factories.required_process_temperature_c IS 'Critical constraint — filters technology feasibility.';


-- --------------------------------------------------------------------------
-- 2.5 scenarios  (DOMAIN_MODEL §4 — Scenario / Pathway)
--
-- A candidate combination of technologies applied to a Factory.
-- The system generates MULTIPLE Pathways per Factory (3–5), never just one.
-- --------------------------------------------------------------------------
CREATE TABLE scenarios (
    scenario_id              TEXT        PRIMARY KEY,

    factory_id               TEXT        NOT NULL
                             REFERENCES factories(factory_id) ON DELETE CASCADE,

    technology_sequence      JSONB       NOT NULL DEFAULT '[]',
        -- §4: Technology[] — ordered array of technology_ids
        -- e.g. ["efficiency", "biomass", "solar"]
        -- Stored as JSONB to preserve ordering

    capex_total_inr          NUMERIC     NOT NULL,
        -- §4: computed total capital expenditure

    annual_opex_inr          NUMERIC     NOT NULL,
        -- §4: computed annual operating expenditure

    fossil_fuel_reduction_pct NUMERIC    NOT NULL,
        -- §4: computed

    co2_reduction_pct        NUMERIC     NOT NULL,
        -- §4: computed

    payback_years_low        NUMERIC     NOT NULL,
    payback_years_high       NUMERIC     NOT NULL,
        -- §4 payback_years: [low, high]
        -- RANGE, not a point estimate — sensitivity analysis requirement

    reliability_score_pct    NUMERIC     NOT NULL,

    financing_eligible_schemes JSONB     NOT NULL DEFAULT '[]',
        -- §4: Subsidy[] ref — from finance/subsidies.json

    rejected_technologies    JSONB       NOT NULL DEFAULT '[]',
        -- §4: { technology_id, reason }[]
        -- For the "Why not?" explainability feature

    objective_scores         JSONB       NOT NULL DEFAULT '{}',
        -- §4: { cost, emissions, risk }
        -- Inputs to the MCDA ranking in optimizer/mcda.py

    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_payback_range     CHECK (payback_years_low <= payback_years_high),
    CONSTRAINT chk_fossil_reduction  CHECK (fossil_fuel_reduction_pct >= 0 AND fossil_fuel_reduction_pct <= 100),
    CONSTRAINT chk_co2_reduction     CHECK (co2_reduction_pct >= 0 AND co2_reduction_pct <= 100),
    CONSTRAINT chk_reliability       CHECK (reliability_score_pct >= 0 AND reliability_score_pct <= 100)
);

COMMENT ON TABLE  scenarios IS 'DOMAIN_MODEL §4 — Candidate technology combination pathways for a Factory. System generates 3–5 per Factory.';
COMMENT ON COLUMN scenarios.technology_sequence IS 'Ordered JSON array of technology_ids, e.g. ["efficiency","biomass","solar"].';
COMMENT ON COLUMN scenarios.rejected_technologies IS 'JSON array of {technology_id, reason} objects — explainability feature.';
COMMENT ON COLUMN scenarios.objective_scores IS 'JSON: {cost: N, emissions: N, risk: N} — MCDA inputs.';


-- --------------------------------------------------------------------------
-- 2.6 financial_models  (DOMAIN_MODEL §6)
--
-- Embedded in Scenario but defined separately since financial.py exists
-- standalone. One-to-one with scenarios.
-- --------------------------------------------------------------------------
CREATE TABLE financial_models (
    id                       SERIAL      PRIMARY KEY,

    scenario_id              TEXT        NOT NULL UNIQUE
                             REFERENCES scenarios(scenario_id) ON DELETE CASCADE,
        -- 1:1 with scenarios

    capex_gross_inr          NUMERIC     NOT NULL,

    eligible_subsidy_inr     NUMERIC     NOT NULL DEFAULT 0,
        -- §6: from finance/subsidies.json + policies/eligibility_rules.json
        -- Gated by udyam_registered

    interest_subvention_pct  NUMERIC     NOT NULL DEFAULT 0,
        -- §6: e.g. ADEETIE's 5%/3% (micro-small / medium)

    net_financed_cost_inr    NUMERIC     NOT NULL,
        -- §6: capex_gross - eligible_subsidy (adjusted)

    npv_inr                  NUMERIC,
        -- §6: optional, if roi.py computes it

    simple_payback_years     NUMERIC     NOT NULL,

    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE financial_models IS 'DOMAIN_MODEL §6 — FinancialModel, 1:1 with scenarios. Standalone because financial.py exists separately.';


-- --------------------------------------------------------------------------
-- 2.7 emission_models  (DOMAIN_MODEL §7)
--
-- Embedded in Scenario, defined separately since emission.py exists
-- standalone. One-to-one with scenarios.
-- --------------------------------------------------------------------------
CREATE TABLE emission_models (
    id                       SERIAL      PRIMARY KEY,

    scenario_id              TEXT        NOT NULL UNIQUE
                             REFERENCES scenarios(scenario_id) ON DELETE CASCADE,
        -- 1:1 with scenarios

    baseline_co2_tonnes_year NUMERIC     NOT NULL,

    pathway_co2_tonnes_year  NUMERIC     NOT NULL,

    reduction_pct            NUMERIC     NOT NULL,

    grid_emission_factor_used NUMERIC    NOT NULL,
        -- §7: from emissions/grid_factors.json
        -- MUST match the Factory's state — grid mix varies by state

    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_emission_reduction CHECK (reduction_pct >= 0 AND reduction_pct <= 100)
);

COMMENT ON TABLE  emission_models IS 'DOMAIN_MODEL §7 — EmissionModel, 1:1 with scenarios. Grid emission factor must match Factory state.';
COMMENT ON COLUMN emission_models.grid_emission_factor_used IS 'From emissions/grid_factors.json — must match the Factory state (grid mix varies by state).';


-- --------------------------------------------------------------------------
-- 2.8 recommendations  (DOMAIN_MODEL §5)
--
-- The final output shown to the user — one Scenario elevated to
-- "recommended," plus the comparison context.
-- --------------------------------------------------------------------------
CREATE TABLE recommendations (
    id                       SERIAL      PRIMARY KEY,

    factory_id               TEXT        NOT NULL
                             REFERENCES factories(factory_id) ON DELETE CASCADE,

    recommended_scenario_id  TEXT        NOT NULL
                             REFERENCES scenarios(scenario_id) ON DELETE CASCADE,
        -- §5: the winning scenario

    all_scenario_ids         JSONB       NOT NULL DEFAULT '[]',
        -- §5 all_scenarios: full comparison set
        -- Stored as JSON array of scenario_ids
        -- UI shows all, not just the winner

    explanation              JSONB       NOT NULL DEFAULT '{}',
        -- §5: {
        --   "why_selected": string[],
        --   "why_others_rejected": [{scenario_id, reason}]
        -- }

    sensitivity_notes        JSONB       NOT NULL DEFAULT '[]',
        -- §5: string[]
        -- e.g. "payback extends to 4.4yr if electricity price rises 15%"

    generated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),

    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  recommendations IS 'DOMAIN_MODEL §5 — Final recommendation output. One Scenario elevated to recommended, plus comparison context.';
COMMENT ON COLUMN recommendations.explanation IS 'JSON: {why_selected: string[], why_others_rejected: [{scenario_id, reason}]}';
COMMENT ON COLUMN recommendations.sensitivity_notes IS 'JSON array of sensitivity analysis strings.';
COMMENT ON COLUMN recommendations.all_scenario_ids IS 'JSON array of scenario_ids — full comparison set. UI shows all, not just the winner.';


-- ============================================================================
-- 3. INDEXES
-- ============================================================================

-- Foreign key indexes (PostgreSQL doesn't auto-index FK columns)
CREATE INDEX idx_factories_industry       ON factories(industry_id);
CREATE INDEX idx_scenarios_factory        ON scenarios(factory_id);
CREATE INDEX idx_financial_models_scenario ON financial_models(scenario_id);
CREATE INDEX idx_emission_models_scenario ON emission_models(scenario_id);
CREATE INDEX idx_recommendations_factory  ON recommendations(factory_id);
CREATE INDEX idx_recommendations_scenario ON recommendations(recommended_scenario_id);

-- Query-path indexes
CREATE INDEX idx_factories_state          ON factories(state);
CREATE INDEX idx_factories_district       ON factories(state, district);
CREATE INDEX idx_scenarios_co2_reduction  ON scenarios(co2_reduction_pct DESC);

COMMIT;
