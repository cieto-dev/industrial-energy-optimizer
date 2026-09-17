# CAPEX Data Acquisition Plan

To maintain the No-Invention rule, CAPEX data must be sourced legally and verifiably. If a source does not yield a number for a specific capacity, the field remains null.

## Prioritized Allowable Sources

1. **BEE (Bureau of Energy Efficiency) PAT Cycle Reports:** Extract sector-specific normalization reports for Textile, Cement, and Iron & Steel benchmark costs.
2. **MNRE (Ministry of New and Renewable Energy) Guidelines:** Extract benchmark capital costs for Solar Thermal and Biomass co-generation (usually updated annually in INR/kW).
3. **IEA (International Energy Agency) IETD:** Query the Industrial Energy Technology Database for mature technology standard costs (requires EUR/USD to INR conversion with explicit exchange rate timestamping).
4. **NITI Aayog Decarbonization Papers:** Use for generic subsidy bounds and macroeconomic OPEX estimates.

## Data Governance Rule
Search source documents. If no direct INR/kW or USD/kW (converted) figure exists for the exact capacity range, the value must remain `null`. Never use generic "Google search" bounds.
