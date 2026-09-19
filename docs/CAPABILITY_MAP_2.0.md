# URJIVA Capability Map 2.0 (Product Blueprint)

This document outlines the Level 1 (L1) capabilities of the Urjiva Engine using enterprise-neutral language. It represents the structural transition from a hackathon prototype (SIH-MVP) to a scalable, enterprise-grade decision-support system.

To ensure long-term scalability, **all MSME-specific logic is strictly isolated** within the *Policy & Incentives Management* capability. The core physics, thermodynamics, and financial engines remain entirely agnostic to the size or classification of the facility.

---

## 1. Facility Assessment & Digital Twin
**Tag:** [Core]

Captures the current thermodynamic, operational, and financial reality of an industrial facility to establish a verified, immutable baseline.

*   **Sub-Capabilities:**
    *   Energy & Mass Balance Modeling
    *   Fuel & Utility Cost Baselines
    *   Scope 1 & 2 Emissions Benchmarking
*   **Module Mapping:** 
    *   Mapped to `baseline/` (Modules: `baseline_engine.py`, `energy_calculator.py`, `fuel_calculator.py`)

## 2. Technology Feasibility Engine
**Tag:** [Core]

Applies rigid thermodynamic, spatial, and operational constraints to filter out commercially mature technologies that cannot integrate with the facility's current processes.

*   **Sub-Capabilities:**
    *   Temperature & Pressure Matching
    *   Footprint & Spatial Constraint Solving
    *   Operational Feasibility Filtering
*   **Module Mapping:** 
    *   Mapped to `technology/` (Modules: `technology_engine.py`, `technology_filter.py`)

## 3. Transition Decisioning (Scenario & MCDA)
**Tag:** [Core]

The heart of the system. Generates, scores, and ranks multi-technology transition pathways using Multi-Criteria Decision Analysis (MCDA), evaluating trade-offs between capital expenditure, operational disruption, and decarbonization impact.

*   **Sub-Capabilities:**
    *   Pathway Generation & Validation
    *   CAPEX/OPEX Financial Modeling (LCOE/LCOH, NPV, Payback)
    *   Emissions Trajectory Modeling
    *   MCDA Optimization Engine
*   **Module Mapping:** 
    *   Mapped to `scenario/` (Pathway generation)
    *   Mapped to `economics/` (Financial modeling)
    *   Mapped to `emissions/` (Carbon modeling)
    *   Mapped to `optimizer/` (MCDA ranking)

## 4. Operational Risk & Reliability
**Tag:** [SIH-MVP / Core]

Performs sensitivity analyses and stochastic perturbations to ensure recommended pathways do not compromise production continuity under supply chain or pricing volatility.

*   **Sub-Capabilities:**
    *   Grid & Supply Chain Reliability Scoring
    *   Fuel Price Sensitivity Analysis
    *   Production Neutrality Verification
*   **Module Mapping:** 
    *   Mapped to `reliability/` (Modules: `reliability_engine.py`, `risk_score.py`)

## 5. Policy & Incentives Management
**Tag:** [SIH-MVP / Future Expansion]

Evaluates facility eligibility against governmental subsidies, tax incentives, and carbon market mechanisms.
> **Architectural Rule:** ALL MSME-specific logic (e.g., Udyam registration checks, MSME categorization, CLCSS scheme rules) MUST be isolated here. The core decision engine (Capabilities 1-4) must remain enterprise-neutral.

*   **Sub-Capabilities:**
    *   Subsidy Matching (e.g., MNRE CFA, ADEETIE)
    *   Carbon Credit Eligibility (Future)
    *   MSME Compliance & Registration Validation (SIH-MVP)
*   **Module Mapping:** 
    *   Mapped to `policy/` (Module: `policy_api.py`)

## 6. Audit, Reporting & Export
**Tag:** [Core]

Translates engine outputs into bank-grade, transparent artifacts for management and external financiers, adhering strictly to the No-Invention Rule.

*   **Sub-Capabilities:**
    *   Decision Explainability & Rejection Logging
    *   Bank-grade PDF/Excel Export
    *   Methodology & Confidence Declarations
*   **Module Mapping:** 
    *   Mapped to `reports/` (Module: `report_api.py`)
    *   Mapped to Frontend (`/reports` route, `RecommendationCard`, `RejectionLog`)

## 7. Multi-Site Optimization & Fleet Management
**Tag:** [Future]

Expands the single-factory architecture to optimize energy arbitrage, load balancing, and aggregate emission reductions across a fleet of distributed industrial facilities.

*   **Sub-Capabilities:**
    *   Fleet-level Energy Arbitrage
    *   Aggregated Carbon Reporting
    *   Supply Chain Grid Balancing
*   **Module Mapping:** 
    *   *Unmapped (Future Track)*
