# Knowledge-Base Audit Report – URJIVA

## 1. Executive Summary
The URJIVA knowledge base exhibits a strong structural foundation in its finance modules (which utilize a rigorous v2.0 schema) but suffers from critical gaps in technology parameterization and inconsistent application of provenance metadata across industry and emissions data. The most urgent risk to the Baseline Engine is the severely incomplete state of the `technologies/` files, which currently lack the quantitative data (efficiencies, costs, constraints) required for decision logic. To enable a production-credible engine and future large-industry expansion, the team must immediately standardize the v2.0 nested-parameter schema (mandating source, date, and confidence tags) across all data domains.

## 2. Critical Gaps (must fix before Baseline Engine hardening)
- **File / parameter affected:** `knowledge-base/technologies/*.json` (e.g., `biomass.json`)
  - **Why it is critical:** Technology files are currently mere stubs containing only definitions (IDs, categories, text content). They completely lack thermodynamic limits, efficiencies, CAPEX/OPEX ranges, and maturity metrics. The decision engine cannot calculate LCOH or verify process feasibility without this data.
  - **Recommended action:** Restructure all technology files to include quantitative `performance_parameters`, `economic_parameters`, and `operational_constraints` using the v2.0 schema format. 
  - **Suggested public source category:** Verifiable OEM technical data sheets and BEE/MNRE technology reports.
  
- **File / parameter affected:** `knowledge-base/emissions/emission_factors.json`
  - **Why it is critical:** Core fossil fuel emission factors (coal, diesel, natural gas) lack `confidence` tags and explicit `last_verified` dates. While they reference generic source IDs (e.g., "SRC003"), the lack of time-bound metadata violates the governance rules.
  - **Recommended action:** Wrap every emission factor and NCV in the nested parameter schema, explicitly adding `confidence` and `last_verified` (date).
  - **Suggested public source category:** IPCC 2006 guidelines and CEA CO2 Baseline Database (latest version).

## 3. High-Priority Improvements (should fix soon)
- **File / parameter affected:** `knowledge-base/industries/*.json` (e.g., `textile.json`)
  - **Why it is critical:** While rich in process details and temperature bands, many quantitative data points (e.g., `sector_level_fuel_mix_percent`, `min_c`/`max_c`) are missing confidence tags and explicit validation dates. The flat structure makes automated auditing difficult.
  - **Recommended action:** Retrofit the industry JSONs to ensure all numbers use a standardized parameter block containing `value`, `unit`, `source_id`, `last_verified`, and `confidence`.
  - **Suggested public source category:** BEE Sectoral Reports, NITI Aayog roadmaps.

- **File / parameter affected:** `knowledge-base/references/sources.json` (and implicit source mappings)
  - **Why it is critical:** Source IDs like "SRC003" or "SRC_INDUSTRIAL_FUELS_CSV" are used, but their exact provenance (URL, publication date, institutional author) must be centrally managed and auditable to prevent silent data degradation.
  - **Recommended action:** Ensure the central sources registry contains complete bibliographic data for every `SRC_ID` used in the knowledge base.
  - **Suggested public source category:** N/A (Internal structural fix).

## 4. Medium / Low Priority Observations
- **File / parameter affected:** `knowledge-base/finance/fuel_prices.json`
  - **Why it is critical:** Currently uses internal estimation for some MSME delivered costs (e.g., `price_delivered_msme_estimate`).
  - **Recommended action:** Ensure the engine's frontend explicitly flags these as "Estimated Delivered Cost" with wide uncertainty bands, rather than presenting them as official benchmarks.
  - **Suggested public source category:** State-level commercial indices where available.

## 5. Provenance & Confidence Tag Status
- **Percentage of quantitative parameters that currently lack proper source + date + confidence tag:** Approximately **60%** (The finance directory performs well, but technologies, emissions, and industries largely fail this requirement).
- **List of the most important untagged parameters:**
  - Technology CAPEX and OPEX values (currently missing entirely).
  - Technology thermal efficiencies and COP limits.
  - Coal and Diesel base emission factors (`emission_factors.json`).
  - Specific Energy Consumption (SEC) targets within industry profiles.

## 6. Structural Recommendations
- **Universal Schema Adoption:** Mandate the `fuel_prices.json` schema architecture across the entire knowledge base. Every single quantitative number must be an object containing `value`, `unit`, `status`, `confidence`, `source_id`, and `last_verified`.
- **Constraint Segregation:** Move process constraints (e.g., "cannot use biomass if space < 500 sqm") out of generic text and into explicit, machine-readable logic arrays inside `constraints/`.
- **Large-Industry Readiness:** Introduce an `applicability` filter object to all parameters (already present in finance). This allows the engine to gracefully handle multi-site or continuous-process plants in the future by filtering data specifically tagged for "large_industry" versus "msme".
- **Strict Thermodynamic Failsafes:** Architect the data models such that a technology's `max_output_temperature_c` is explicitly compared against the industry's `required_process_temperature_c`. If the former is lower, the pathway must be hard-blocked.

## 7. Recommended Immediate Action List
1. **Flesh out Technology Profiles:** Populate `technologies/*.json` with real efficiencies, CAPEX, OPEX, and thermodynamic limits from OEM data and BEE reports.
2. **Upgrade Emissions Metadata:** Rewrite `emission_factors.json` to include exact dates and confidence tags for all fuels.
3. **Refactor Industry JSONs:** Convert flat numerical estimates in files like `textile.json` into nested parameter objects with full provenance.
4. **Harden the Sources Registry:** Map every `SRC_ID` used in the JSONs to a concrete BEE/CEA/IEA URL and publication year in a central registry.
5. **Implement Missing-Data Failsafes:** Ensure the backend API throws a warning or expands uncertainty ranges if it encounters a parameter with a confidence score below 0.7 or a missing `last_verified` date.
6. **Cross-Check Industry Baselines:** Validate all specific energy consumption (SEC) metrics in `industries/` against the latest PAT (Perform Achieve Trade) scheme cycle data from BEE.
