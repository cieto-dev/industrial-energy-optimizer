# Baseline Engine Hardening — Technical Specification

**Date:** 12 September 2026  
**Status:** Implemented  
**Governing docs:** Data Governance Rules v1.0, Product Boundary & Research Rules

---

## A. Mathematical Definitions

All formulae use only values present in the v2.0 knowledge base.  
Accessors shown are the Python helpers — no raw dict reads permitted.

### A.1 Annual Fuel Energy Input

```
E_input (MJ/yr) = C_daily (kg/day or m³/day)
                  × D_op   (operating days/yr)
                  × NCV    (MJ/kg  or  MJ/m³)
```

| Symbol | Source | Helper |
|---|---|---|
| `C_daily` | `factory.fuel_consumption` | — |
| `D_op` | `factory.operating_days_per_year` | — |
| `NCV` | `emission_factors.json[fuel].ncv.value` | `get_ncv_value(fuel)` |

**Unit note:** `TJ/kt` and `MJ/kg` are numerically identical. The engine
reads `ncv.unit` from the nested parameter object and branches accordingly.

### A.2 Thermal Energy Balance (three-stage chain)

```
Q_boiler  = E_input × η_boiler          [MJ/yr]
Q_distrib = Q_boiler × η_distribution   [MJ/yr]
Q_process = Q_distrib × η_process_util  [MJ/yr]  ← Useful heat demand
```

All three `η` values come from the `assumption_registry` (planning defaults,
tagged `"assumption_status": "planning_default"`).  
Conservation check (mandatory): `|E_input − (Q_process + Σlosses)| < 1×10⁻⁶ MJ`

### A.3 Specific Energy Consumption

```
SEC (MJ/tonne) = Q_process (MJ/yr) / P_annual (tonnes/yr)
P_annual = factory.production_per_day × D_op
```

### A.4 Annual Fuel Cost

```
C_fuel (INR/yr) = C_daily × D_op × P_fuel (INR/kg or INR/L)
```

`P_fuel` → `fuel_prices.json` via `get_fuel_price_record(fuel)`.

### A.5 Scope 1 CO₂ (Fuel Combustion)

```
CO₂_scope1 (tCO₂/yr) = E_input_TJ × EF_fuel (tCO₂/TJ)
E_input_TJ            = E_input_MJ / 1 000 000
EF_fuel               = emission_factors.json[fuel].emission_factor.value
```

Helper: `get_emission_factor_value(fuel)` — raises `ValueError` if absent.

**Biogenic accounting:** Physical CO₂ is always calculated using the IPCC
factor. Biogenic credit is applied by the recommendation layer only.

### A.6 Scope 2 CO₂ (Grid Electricity)

```
CO₂_scope2 (tCO₂e/yr) = E_elec_kWh/yr × GEF (kgCO₂e/kWh) / 1 000
```

`GEF` → `grid_factors.json`, CEA weighted-average including RES & captive,
FY 2024-25. Retrieved via `get_grid_emission_factor()`.

### A.7 Electricity Energy

```
E_elec (MJ/yr) = factory.electricity_consumption_kwh_day × D_op × 3.6
```

---

## B. Required Factory Input Fields

### B.1 Mandatory (engine raises `ValueError` if absent)

| Field | Type | Validation |
|---|---|---|
| `current_fuel` | `str` | Key must exist in `emission_factors.json` |
| `fuel_consumption.value` | `float` | > 0 |
| `fuel_consumption.unit` | `str` | Must convert to `emission_factors.json[fuel].input_unit` |
| `operating_days_per_year` | `int` | 1–365 |
| `electricity_consumption_kwh_day` | `float` | ≥ 0 |
| `state` | `str` | Must resolve in `electricity_tariffs.json` |

### B.2 Optional with KB-sourced planning defaults

| Field | Default source | Status tag |
|---|---|---|
| `boiler_efficiency` | `assumption_registry` | `planning_default` |
| `steam_distribution_efficiency` | `assumption_registry` | `planning_default` |
| `process_heat_utilization` | `assumption_registry` | `planning_default` |
| `production_per_day` | None (SEC omitted) | — |
| Grid emission basis | `grid_factors.json` | `weighted_average_including_res_and_captive` |

### B.3 Validation Rules

1. Fuel must match a key in `emission_factors.json`
2. NCV must be non-null and numeric after v2.0 unwrapping
3. Emission factor must be non-null and numeric
4. Energy balance residual < 1×10⁻⁶ MJ
5. `confidence == "Low"` → `DataQualityWarning` (non-blocking)
6. `source_id` absent on any mandatory param → `firm_recommendation_blocked = True`
7. `value is None` on any mandatory param → `firm_recommendation_blocked = True`

---

## C. Output Data Structure

### New model: `DataQualityWarning` (`decision_engine/baseline/models.py`)

```python
class DataQualityWarning(BaseModel):
    field: str              # Parameter key (e.g. "ncv")
    fuel_or_context: str    # e.g. "biomass"
    confidence: str | None  # "Low", "Medium", "High", or None
    source_id: str | None
    message: str            # Human-readable, surface in UI/report
    is_blocking: bool       # True when it caused firm_recommendation_blocked
```

### New fields on `BaselineProfile`

| Field | Type | Description |
|---|---|---|
| `data_quality_warnings` | `list[DataQualityWarning]` | All warnings from quality gate |
| `firm_recommendation_blocked` | `bool` | `True` if any mandatory param is absent/unsourced |
| `firm_recommendation_blocked_reasons` | `list[str]` | Human-readable block reasons |
| `parameter_confidence_summary` | `dict[str, str]` | param → confidence level |

---

## D. Implementation Summary

### Files modified

| File | Change |
|---|---|
| `decision_engine/baseline/models.py` | Added `DataQualityWarning`; added 4 quality-gate fields to `BaselineProfile` |
| `decision_engine/baseline/energy_calculator.py` | Fixed v2.0 breaking bug: NCV/EF reads now use helpers; confidence metadata propagated |
| `decision_engine/baseline/baseline_engine.py` | Fixed v2.0 breaking bug in `_build_fuel_profile`; added quality-gate pass (step 11.5) in `compute_baseline()` |
| `decision_engine/emissions/emission_factors.py` | Added `_unwrap_value`, `get_emission_factor_value`, `get_ncv_value` |
| `decision_engine/emissions/co2_calculator.py` | Full rewrite using helpers; added `calculate_fuel_co2()`; confidence in output |
| `knowledge_runtime/repository.py` | Added `extract_value`, `get_parameter`, `validate_parameter` static helpers |

### Function call chain in `compute_baseline()`

```
factory
  → calculate_energy_balance(factory)          [energy_calculator.py]
      → get_emission_factor(fuel)               [emission_factors.py]
      → get_ncv_value(fuel)     ← v2.0 FIX
      → get_emission_factor_value(fuel)  ← v2.0 FIX
  → calculate_annual_energy_cost(factory)      [fuel_calculator.py]
  → calculate_fuel_emissions(fuel, daily_q)    [emission_engine.py]
  → get_grid_emission_factor()                 [emission_factors.py]
  → KnowledgeRepository.validate_parameter()   ← NEW quality gate
      → DataQualityWarning objects
  → BaselineProfile(...)                        [models.py]
      .data_quality_warnings
      .firm_recommendation_blocked
      .firm_recommendation_blocked_reasons
      .parameter_confidence_summary
```

---

## E. Verified Test Cases

All four test groups pass (run with `PYTHONPATH=. python3 decision_engine/baseline/tests/test_quality_gate.py`):

### E.1 — Textile Dyeing, Coal (500 kg/day, 280 op-days, 800 kWh/day)

Derived from KB values only:

| Quantity | Value | Source |
|---|---|---|
| NCV (coal) | 19.63 MJ/kg | `emission_factors.json` `SRC004` |
| EF (coal) | 96.10 tCO2/TJ | `emission_factors.json` `SRC001` |
| Annual fuel input | 2,748,200 MJ | formula A.1 |
| Scope 1 CO₂ | ~264.1 tCO2/yr | formula A.5 |
| Scope 2 CO₂ | ~159.4 tCO2e/yr | formula A.6 |
| Quality: EF | High confidence, no warning | ✅ |
| Quality: NCV | Medium confidence, no warning | ✅ |
| Firm recommendation blocked | False | ✅ |

### E.2 — Dairy, Biomass (300 kg/day, 300 op-days, 400 kWh/day)

| Quantity | Value | Note |
|---|---|---|
| NCV (biomass) | 15.6 MJ/kg | `emission_factors.json` — **confidence = Low** |
| EF (biomass) | 100.0 tCO2/TJ | `emission_factors.json` `SRC001` |
| Annual fuel input | 1,404,000 MJ | formula A.1 |
| Scope 1 CO₂ | 140.4 tCO2/yr (biogenic gross) | formula A.5 |
| Quality: NCV | Low confidence → **DataQualityWarning generated** | ✅ |
| NCV warning is non-blocking | True (value and source_id present) | ✅ |
| Firm recommendation blocked | False (data present, just uncertain) | ✅ |

**Required UI message:** "NCV for 'biomass' has Low confidence. Site-specific moisture and NCV measurement required before a firm recommendation."

### E.3 — Missing `source_id` → Blocked

Synthetic record with `source_id` absent:
- `validate_parameter()` → `ok = False`
- Error: "must be traceable to an allowable source"
- `firm_recommendation_blocked = True` ✅

### E.4 — Null `value` → Blocked

Synthetic record with `"value": null`:
- `validate_parameter()` → `ok = False`
- Error: "Cannot produce a firm recommendation without it"
- `firm_recommendation_blocked = True` ✅

---

## F. Remaining Data Gaps

Cannot be computed reliably from current v2.0 KB. **Do not invent values.**

| Gap | Impact | Required source |
|---|---|---|
| Site-specific biomass NCV | CO₂ and SEC unreliable | Plant proximate analysis; BEE |
| Boiler efficiency (measured) | All three η stages are planning defaults | Stack-gas analysis / BEE energy audit |
| Steam distribution losses | Distribution η is planning default | Steam trap survey; condensate metering |
| Condensate recovery % | Affects net makeup water and heat loss | Site metering |
| Technology CAPEX (all) | Payback cannot be computed | OEM quotes |
| Contracted kVA demand | Demand-charge component excluded | Electricity bill / contract |
| District-level biomass price | OPEX unreliable | MNRE/agro-market data |
