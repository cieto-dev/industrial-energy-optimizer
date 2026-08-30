# 📝 Doubt Clearing Notes — For Script Page Revision

> **How to use this:** Each doubt has two parts —
> 1. **🧑‍🏫 Mentor Explanation** — Read this to deeply understand the concept
> 2. **✍️ Script Page Note** — Copy this short note to the end of your speech page for quick revision

---

## DOUBT 1 — What is JWT?

### 🧑‍🏫 Mentor Explanation

**JWT = JSON Web Token** (pronounced "jot")

Think of it like a **tamper-proof digital ID card**. When you go to a college event, you show your ID card at the gate — the guard doesn't call the registrar's office every time. The card itself proves who you are.

**How it works in URJIVA:**

1. The factory owner logs in with email + password on the frontend
2. The FastAPI backend verifies the credentials against bcrypt-hashed passwords in the database
3. If valid, the backend creates a **JWT token** — a long encoded string containing:
   - **Payload:** The user's email (`sub: "ramesh@factory.com"`)
   - **Expiration:** Token expires in 8 hours
   - **Signature:** Digitally signed with a secret key using **HS256 algorithm** (HMAC-SHA256)
4. This token is sent back to the frontend, stored in `localStorage`
5. Every subsequent API request includes this token in the header: `Authorization: Bearer <token>`
6. The backend decodes the token, verifies the signature, and allows access — **without hitting the database again**

**Why JWT and not sessions?**
- **Stateless** — The server doesn't need to remember anything. The token carries all the info.
- **Scalable** — If you have 100 servers, they all can verify the same token independently.
- **Standard** — Industry-standard (RFC 7519), used by Google, Facebook, and most modern APIs.

**Structure of a JWT (3 parts separated by dots):**
```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJyYW1lc2hAZmFjdG9yeS5jb20iLCJleHAiOjE3MjQ5fQ.dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
 ^^^^ HEADER ^^^^        ^^^^ PAYLOAD ^^^^                                    ^^^^ SIGNATURE ^^^^
```

### ✍️ Script Page Note

> **JWT (JSON Web Token):** A tamper-proof digital token used for authentication. After login, the server creates a signed token (contains user identity + expiry). Frontend sends this token with every API request. Backend verifies the signature without hitting the database. Algorithm: HS256. Expiry: 8 hours. Libraries used: `python-jose` (token creation), `passlib` + `bcrypt` (password hashing). Standard: RFC 7519.

---

## DOUBT 2 — What is GIS?

### 🧑‍🏫 Mentor Explanation

**GIS = Geographic Information System**

GIS is a system that **captures, stores, analyzes, and visualizes geographic (location-based) data on maps**. Basically — putting data ON a map instead of in a table.

**Everyday example:** Google Maps showing traffic, restaurants, and directions — that's a GIS application.

**How GIS is used in URJIVA:**

URJIVA has a dedicated `/gis` page that shows an **interactive map of India** with:

1. **Industrial Clusters** — Pins on the map showing major MSME clusters:
   - Tirupur (Textiles), Morbi (Ceramics), Surat (Textiles/Diamonds), Kanpur (Leather), Ludhiana (Hosiery/Steel), Panipat (Textiles), Vapi (Chemicals), Baddi (Pharma), etc.

2. **Each cluster pin shows:**
   - Annual energy spend (₹)
   - CO₂ footprint
   - Surplus biomass availability in nearby districts
   - Solar radiation potential (DNI — Direct Normal Irradiance)
   - State DISCOM electricity tariff

3. **Why GIS matters for this project:**
   - A factory's **location determines everything** — which biomass is available nearby, what the electricity tariff is, which state subsidies apply, how much solar energy is possible
   - Without GIS, you'd have to manually look up district data — GIS automates this

**Tech used for GIS in URJIVA:**
- **Leaflet** — Open-source JavaScript library for interactive maps
- **React-Leaflet** — React wrapper for Leaflet
- **PostGIS** — PostgreSQL extension for spatial/geographic database queries
- **Google Hybrid Tiles** — Satellite + terrain map imagery
- Backend: `decision_engine/geographic/geographic_intelligence.py` provides district coordinates, biomass atlas data, solar insolation, and DISCOM mappings

### ✍️ Script Page Note

> **GIS (Geographic Information System):** A system to capture, analyze, and visualize location-based data on interactive maps. In URJIVA, the `/gis` page shows a map of India with industrial cluster pins (Tirupur, Morbi, Surat, Kanpur, Ludhiana, etc.). Each pin shows energy spend, CO₂, local biomass, solar potential, and DISCOM tariffs. Tools: Leaflet (map library), React-Leaflet (React wrapper), PostGIS (spatial DB), Google Hybrid Tiles. Why needed: A factory's location determines biomass availability, electricity price, solar potential, and eligible state subsidies.

---

## DOUBT 3 — What are the industries we targeted?

### 🧑‍🏫 Mentor Explanation

URJIVA targets **9 energy-intensive MSME industrial sectors** (not 10 — this is confirmed from the master index in the codebase):

| # | Industry | Key Heat Processes | Typical Temp Range |
|---|----------|-------------------|-------------------|
| 1 | **Textile** | Dyeing, finishing, drying, washing, calendering | 80°C – 200°C |
| 2 | **Food Processing** | Blanching, pasteurization, sterilization, drying, frying | 60°C – 250°C |
| 3 | **Pharmaceutical** | API synthesis, distillation, drying, sterilization | 80°C – 300°C |
| 4 | **Chemical** | Reactions, distillation, evaporation, drying | 100°C – 500°C |
| 5 | **Paper** | Pulping, bleaching, drying, pressing | 100°C – 250°C |
| 6 | **Dairy** | Pasteurization, chilling, ghee making, spray drying | 60°C – 200°C |
| 7 | **Cement** | Kiln firing, clinker grinding, preheating | 900°C – 1450°C |
| 8 | **Steel** | Smelting, rolling, forging, heat treatment | 500°C – 1600°C |
| 9 | **Glass** | Melting, annealing, tempering, forming | 500°C – 1600°C |

**Why these 9?**
- These are India's **most energy-intensive MSME sectors** — they collectively consume the most fossil fuel for process heat
- They represent a **wide temperature spectrum** from low-heat (dairy at 60°C) to ultra-high-heat (steel at 1600°C), testing the full range of clean technologies
- They cover a **diverse geography** — textiles in Tamil Nadu, ceramics in Gujarat, pharma in Himachal Pradesh, leather in UP

**Each industry has its own JSON profile** in `knowledge-base/industries/` containing sector details, subsectors, thermal maps, applicable technologies, and constraint rules.

### ✍️ Script Page Note

> **9 Target Industries:** Textile, Food Processing, Pharmaceutical, Chemical, Paper, Dairy, Cement, Steel, Glass. Chosen because they are India's most energy-intensive MSME sectors with a wide temperature spectrum (60°C dairy to 1600°C steel). Each has a detailed JSON profile in the knowledge base with subsectors, thermal maps, and constraint rules. Combined, these 9 sectors represent the largest opportunity for industrial decarbonization in India.

---

## DOUBT 4 — What are the 40+ technologies?

### 🧑‍🏫 Mentor Explanation

The "40+" figure comes from counting **individual technology variants and subtypes** across the technology categories. Here's the breakdown:

### Master Technology Categories (9 categories)

| # | Category | Individual Variants |
|---|----------|-------------------|
| 1 | **Biomass Boiler** | Variants by fuel: wood chips, pellets, briquettes, rice husk, bagasse, sawdust, agricultural residues |
| 2 | **Biogas Boiler** | Anaerobic digestion → biogas combustion for steam/hot water |
| 3 | **Heat Pump** | Industrial Heat Pump (IHP), Electric Resistance Heating |
| 4 | **Electric Boiler** | Electrode boiler, resistance boiler (replaces fossil-fuel steam boilers) |
| 5 | **Solar Thermal** | Flat Plate Collector (FPC), Evacuated Tube Collector (ETC), Parabolic Trough, Linear Fresnel, Parabolic Dish |
| 6 | **Solar PV** | Rooftop PV, ground-mount PV (electricity generation) |
| 7 | **Thermal Storage** | Sensible heat storage (hot water, molten salt, packed bed) |
| 8 | **Waste Heat Recovery** | Economizer, Heat Exchanger (plate/shell-and-tube), Condensate Recovery, Flash Steam Recovery |
| 9 | **Grid Electricity** | Direct electrification from the power grid |

### Additional Technology Variants (within electrification.json)
- **Process Electrification** — Resistance heating, induction heating, infrared heating, microwave heating, electric arc furnaces
- **Boiler Electrification** — Electric steam generation
- **Dryer Electrification** — Electric hot-air and direct heating

### How "40+" is reached:
When you count **each specific variant** (e.g., 7 biomass fuel types × boiler = 7 variants, 5 solar thermal collector types = 5 variants, 4 WHR types, 5 electrification subtypes, etc.) **AND** their applicability across 9 different industry contexts with different temperature and constraint profiles, you get 40+ unique technology-application combinations that the feasibility filter evaluates.

### ✍️ Script Page Note

> **40+ Technologies:** Organized into 9 master categories — Biomass Boiler, Biogas, Heat Pump, Electric Boiler, Solar Thermal (5 collector types: FPC, ETC, Parabolic Trough, Linear Fresnel, Parabolic Dish), Solar PV, Thermal Storage, Waste Heat Recovery (4 types: Economizer, Heat Exchanger, Condensate Recovery, Flash Steam), and Electrification (3 types: Process, Boiler, Dryer — each with subtypes like induction, infrared, microwave). The "40+" count comes from individual variants and their cross-applicability across 9 industries, each with unique temperature and constraint profiles.

---

## DOUBT 5 — What are the important formulas we used?

### 🧑‍🏫 Mentor Explanation

Here are the **most important formulas** — the ones you should know by heart:

### ⚡ Energy Balance (Baseline Engine)
```
Fuel Input (MJ) × η_boiler → Steam Heat × η_distribution → Delivered Heat × η_process → Useful Process Heat
```
- η_boiler = 75% (default)
- η_distribution = 85% (default)
- η_process = 80% (default)
- Overall efficiency ≈ 75% × 85% × 80% = **51%** (roughly half the fuel energy reaches the process)

### 💰 Financial Formulas
```
Annual Savings = Baseline OPEX − Proposed OPEX

Simple Payback (years) = CAPEX ÷ Annual Savings

ROI (%) = [(Annual Savings × Lifetime) − CAPEX] ÷ CAPEX × 100
```

### 🏭 Emissions Formula
```
CO₂ (tCO₂/year) = Energy Input (TJ/year) × Emission Factor (tCO₂/TJ)
```

### 📊 MCDA Normalization
```
For Benefit criteria (higher is better):
    Normalized = (value − min) ÷ (max − min)

For Cost criteria (lower is better):
    Normalized = (max − value) ÷ (max − min)

Composite Score = Σ (weight_j × normalized_j)  for j = 1 to 12
```

### 🎲 Monte Carlo Spread Ratio
```
Spread Ratio = (P90 − P10) ÷ P50
```

### ✍️ Script Page Note

> **Key Formulas:**
> - **Energy Balance:** Fuel × η_boiler(75%) × η_distribution(85%) × η_process(80%) = Useful Heat (~51% overall)
> - **Annual Savings:** Baseline OPEX − Proposed OPEX
> - **Payback:** CAPEX ÷ Annual Savings (in years)
> - **ROI:** [(Savings × Lifetime) − CAPEX] ÷ CAPEX × 100
> - **CO₂ Emissions:** Energy (TJ) × Emission Factor (tCO₂/TJ)
> - **MCDA Benefit Norm:** (value − min) ÷ (max − min)
> - **MCDA Cost Norm:** (max − value) ÷ (max − min)
> - **Composite Score:** Σ(weight × normalized) for 12 criteria
> - **Spread Ratio:** (P90 − P10) ÷ P50

---

## DOUBT 6 — What is the concept of Monte Carlo?

### 🧑‍🏫 Mentor Explanation

**Monte Carlo Simulation** is a technique where you **run the same calculation thousands of times with slightly different random inputs** to see how the output varies.

**Named after:** The Monte Carlo Casino in Monaco — because it uses randomness, just like gambling. The method was developed during the Manhattan Project (1940s) by scientists Stanislaw Ulam and John von Neumann.

### Real-life analogy:
Imagine you're estimating how long your commute to college takes. Some days it's 30 minutes, some days 45 minutes (traffic), rarely 60 minutes (accident). If you just say "35 minutes," you might be late on bad days.

Instead, you simulate 1000 commutes:
- Randomly vary traffic (light/medium/heavy)
- Randomly vary weather (clear/rain)
- Randomly vary bus timing

After 1000 simulations, you get a **distribution**: "My commute is 28–55 minutes, with 50% chance it's under 35 minutes."

### How URJIVA uses Monte Carlo:
We don't want to tell a factory owner "Your payback period is 5 years" as a single number — because that's **misleadingly precise**. Fuel prices can change, CAPEX can overrun, biomass supply can vary.

Instead, we:
1. **Define uncertainty ranges** for key parameters:
   - Fuel price: ±15–25% variation
   - Electricity tariff: ±10–20% variation
   - Biomass cost: ±20–30% variation
   - Equipment efficiency: 0.9× to 1.1× of expected
   - CAPEX overrun: +10–30%

2. **Run 100–10,000 iterations:**
   - In each iteration, randomly pick values within these ranges (using **triangular distribution**)
   - Recalculate the payback period with these perturbed values

3. **Collect all results and compute percentiles:**
   - Sort all 10,000 payback values
   - P10 = optimistic (90% chance it's longer)
   - P50 = expected/median
   - P90 = pessimistic (only 10% chance it's worse)

4. **Compute spread ratio** = (P90 − P10) ÷ P50 → tells you how "spread out" (uncertain) the estimate is

**Why triangular distribution (not normal/Gaussian)?**
- We know the minimum, maximum, and most likely value — but we DON'T have enough historical data for a proper bell curve
- Triangular distribution is the standard choice in engineering risk analysis when you have limited data — defined by just 3 parameters (low, mode, high)

### ✍️ Script Page Note

> **Monte Carlo Simulation:** A technique of running calculations 1000s of times with randomly varied inputs to produce a probability distribution instead of a single misleading estimate. Named after the Monte Carlo Casino (uses randomness). In URJIVA: we perturb fuel price (±15-25%), electricity (±10-20%), biomass cost (±20-30%), efficiency (±10%), and CAPEX (overrun 10-30%) across 100-10,000 iterations using triangular distribution. Output: P10/P50/P90 payback ranges + spread ratio. Purpose: Tells the factory owner "payback is likely 5-8 years" instead of a false-precision "5.2 years."

---

## DOUBT 7 — What is P10, P50, P90? And why not P(some other number)?

### 🧑‍🏫 Mentor Explanation

**P10, P50, P90 are percentiles** — they describe where a value falls in a sorted distribution.

### What each means:

| Percentile | Meaning | In Plain Hindi/English |
|------------|---------|----------------------|
| **P10** | 10th percentile — only 10% of results were BELOW this value | **Best case** — "Itna achha toh mushkil se hoga" |
| **P50** | 50th percentile — exactly half the results were above, half below | **Most likely case** — Median/expected value |
| **P90** | 90th percentile — 90% of results were BELOW this value | **Worst case** — "Itna bura hone ke chances bahut kam hain (only 10%)" |

### Example from URJIVA:
If Monte Carlo gives: **P10 = 4.5 years, P50 = 6.2 years, P90 = 9.8 years**

This means:
- **Best case:** Payback could be as low as 4.5 years (if fuel stays cheap, no CAPEX overrun)
- **Expected:** Most likely around 6.2 years
- **Worst case:** Even in bad conditions, 90% chance it won't exceed 9.8 years

### Why P10/P50/P90 specifically? Why not P25/P75 or P5/P95?

**P10/P50/P90 is the global standard in engineering risk analysis and energy project finance:**

1. **Oil & Gas Industry** — The Society of Petroleum Engineers (SPE) established P10/P50/P90 as the standard for reserve estimation. When ONGC or Reliance estimates oil reserves, they use P10/P50/P90.

2. **Project Finance & Banking** — Banks and investors use P10/P50/P90 to evaluate project risk. The World Bank, IFC, and IREDA all require P10/P50/P90 analysis for renewable energy project funding.

3. **Why not P25/P75?**
   - P25/P75 captures only the **middle 50%** — too narrow, misses tail risks
   - P10/P90 captures the **middle 80%** — wide enough to show real risk, narrow enough to be actionable

4. **Why not P5/P95?**
   - P5/P95 represents **extreme outliers** — a 1-in-20 scenario
   - For MSME decision-making, extreme scenarios are less useful than likely ones
   - P10/P90 is the sweet spot: captures meaningful risk without being unrealistic

5. **The Spread Ratio** uses P10 and P90 specifically:
   ```
   Spread Ratio = (P90 − P10) ÷ P50
   ```
   - < 0.15 → LOW risk
   - 0.15–0.30 → MEDIUM risk
   - 0.30–0.50 → HIGH risk
   - \> 0.50 → VERY HIGH risk

### ✍️ Script Page Note

> **P10/P50/P90 (Percentiles):**
> - **P10** = Optimistic/best case (only 10% chance of doing better)
> - **P50** = Median/expected/most likely case
> - **P90** = Pessimistic/worst case (90% chance it's better than this)
> - **Why P10/P50/P90?** Global standard in energy project finance (used by SPE, World Bank, IFC, IREDA). P25/P75 is too narrow (misses tail risks). P5/P95 is too extreme (unrealistic for MSME decisions). P10/P90 captures the middle 80% — the practical risk window.
> - **Spread Ratio** = (P90 − P10) ÷ P50 → LOW (<0.15), MEDIUM (0.15–0.30), HIGH (0.30–0.50), VERY HIGH (>0.50).

---

## DOUBT 8 — What are the 12 criteria used under MCDA?

### 🧑‍🏫 Mentor Explanation

MCDA uses **12 weighted criteria** to score and rank each candidate pathway. They sum to **1.00 (100%)**.

Think of it like a college entrance exam with 12 subjects — each subject has a different weightage, and your total score determines your rank.

| # | Criterion | Weight | Type | What it measures | Easy way to remember |
|---|-----------|--------|------|-----------------|---------------------|
| 1 | **Technical Feasibility** | 12% | Benefit ↑ | Can this tech physically work here? | "Does it FIT?" |
| 2 | **Financial Viability** | 12% | Benefit ↑ | Is the lifecycle cost reasonable? | "Can they AFFORD it?" |
| 3 | **Resource Availability** | 8% | Benefit ↑ | Are local resources available (roof, land, grid)? | "Do they HAVE what's needed?" |
| 4 | **Policy Support** | 6% | Benefit ↑ | How many government subsidies apply? | "Will the GOVERNMENT help?" |
| 5 | **Risk (Spread Ratio)** | 10% | Cost ↓ | How uncertain is the payback? | "How RISKY is it?" |
| 6 | **Technology Maturity (TRL)** | 8% | Benefit ↑ | Is it commercially proven or experimental? | "Is it PROVEN?" |
| 7 | **Implementation Complexity** | 6% | Cost ↓ | How hard is it to install and retrofit? | "Is it EASY to install?" |
| 8 | **Supply Reliability** | 10% | Benefit ↑ | How reliable is the fuel/energy supply chain? | "Will supply be STEADY?" |
| 9 | **Grid Dependence** | 5% | Cost ↓ | How much does it rely on unreliable grid? | "GRID dependency?" |
| 10 | **Biomass Dependence** | 5% | Cost ↓ | How exposed to seasonal biomass risk? | "BIOMASS dependency?" |
| 11 | **Carbon Reduction %** | 12% | Benefit ↑ | How much CO₂ does it actually reduce? | "How GREEN is it?" |
| 12 | **Evidence Confidence** | 6% | Benefit ↑ | How reliable is the data backing this? | "Can we TRUST the numbers?" |

**Benefit type (↑)** = Higher is better → Normalized as (value − min) ÷ (max − min)
**Cost type (↓)** = Lower is better → Normalized as (max − value) ÷ (max − min)

### Why these specific 12?
- Criteria 1–4 answer: **"Is it possible and supported?"**
- Criteria 5–10 answer: **"What are the risks?"**
- Criteria 11–12 answer: **"Does it actually deliver on decarbonization, and can we trust it?"**

### ✍️ Script Page Note

> **12 MCDA Criteria (sum = 1.00):**
> 1. Technical Feasibility (12%, ↑)
> 2. Financial Viability (12%, ↑)
> 3. Resource Availability (8%, ↑)
> 4. Policy Support (6%, ↑)
> 5. Risk / Spread Ratio (10%, ↓)
> 6. Technology Maturity / TRL (8%, ↑)
> 7. Implementation Complexity (6%, ↓)
> 8. Supply Reliability (10%, ↑)
> 9. Grid Dependence (5%, ↓)
> 10. Biomass Dependence (5%, ↓)
> 11. Carbon Reduction % (12%, ↑)
> 12. Evidence Confidence (6%, ↑)
>
> **↑ = Benefit (higher is better), ↓ = Cost (lower is better)**
> Top 3 heaviest weights: Technical (12%) + Financial (12%) + Carbon Reduction (12%) = 36% of total score.

---

## DOUBT 9 — What is ADEETIE, MSE-GIFT, and ZED?

### 🧑‍🏫 Mentor Explanation

These are **central government schemes** that provide financial support to MSMEs for adopting clean/efficient technologies. URJIVA's Policy Engine automatically matches factories against these.

---

### 🏛️ ADEETIE

**Full Form:** Assistance for Deployment of Energy Efficient Technologies in Industries and Establishments

**Who runs it?** Bureau of Energy Efficiency (BEE), under the Ministry of Power, Government of India

**What does it do?**
- Provides **interest subvention** (i.e., the government pays part of your loan interest) for MSMEs adopting energy-efficient technologies
- **5% interest subvention** for Micro and Small enterprises
- **3% interest subvention** for Medium enterprises
- Also provides energy audit support
- Targets **60 MSME clusters** across **14 energy-intensive sectors**

**Why it matters for URJIVA:**
- Directly reduces the effective loan cost for the factory owner
- URJIVA's Policy Engine checks if the factory's industry and project type qualify

---

### 💰 MSE-GIFT

**Full Form:** MSE Green Investment and Financing for Transformation

**Who runs it?** Ministry of MSME, implemented through SIDBI (Small Industries Development Bank of India) under the RAMP programme (Raising and Accelerating MSME Performance — World Bank supported)

**What does it do?**
- Provides **green loans** specifically for MSMEs transitioning to clean technologies
- **Interest subvention** — reduces the interest rate on loans for green projects
- **Credit support** — helps MSMEs get loans they normally couldn't (many MSMEs lack collateral)
- Targets clean energy adoption, energy efficiency improvements, and pollution reduction

**Why it matters for URJIVA:**
- Reduces the financial barrier — many MSMEs can't afford ₹50L–₹2Cr CAPEX upfront
- MSE-GIFT makes loans cheaper and more accessible

---

### ✅ ZED

**Full Form:** Zero Defect Zero Effect

**Who runs it?** Ministry of MSME, implemented by QCI (Quality Council of India)

**What does it do?**
- A **certification programme** that rates MSMEs on manufacturing quality (Zero Defect) AND environmental impact (Zero Effect)
- Three certification levels: **Bronze, Silver, Gold**
- MSMEs get **financial subsidies** for achieving each level:
  - Bronze: ₹10,000
  - Silver: ₹20,000  
  - Gold: ₹50,000–₹1,00,000
- Certified MSMEs get **priority in government procurement** (25% of central PSU procurement is reserved for MSMEs, and ZED-certified ones get preference)

**Why it matters for URJIVA:**
- URJIVA's clean technology recommendations help factories achieve ZED Silver/Gold certification
- The certification itself brings procurement benefits beyond the subsidy amount

---

### Other schemes in the system:

| Scheme | Full Form | Key Benefit |
|--------|-----------|-------------|
| **CGTMSE** | Credit Guarantee Trust for Micro & Small Enterprises | Collateral-free loans up to ₹5 Cr |
| **CLCSS** | Credit Linked Capital Subsidy Scheme | 15% capital subsidy on technology upgradation |
| **PM Surya Ghar** | PM Solar Rooftop Programme | Solar rooftop installation subsidies |
| **MSE-CDP** | Micro & Small Enterprise Cluster Development Programme | Common Facility Centres & green infrastructure |
| **RAMP** | Raising & Accelerating MSME Performance | World Bank-backed strategic greening support |

### ✍️ Script Page Note

> **Key Government Schemes:**
> - **ADEETIE** (BEE/Ministry of Power) — Interest subvention: 5% for Micro/Small, 3% for Medium. Targets 60 MSME clusters, 14 sectors. Reduces loan cost.
> - **MSE-GIFT** (Ministry of MSME/SIDBI/RAMP) — Green loans + interest subvention + credit support for clean tech adoption. Makes loans cheaper and accessible. World Bank backed.
> - **ZED** (Ministry of MSME/QCI) — Zero Defect Zero Effect certification. Bronze/Silver/Gold levels. Provides subsidies + priority in government procurement (25% PSU quota).
> - Others: CGTMSE (collateral-free loans), CLCSS (15% capital subsidy), PM Surya Ghar (solar rooftop), MSE-CDP (cluster development), RAMP (World Bank MSME programme).

---

## DOUBT 10 — What is CEA and IPCC?

### 🧑‍🏫 Mentor Explanation

These are the **two authoritative sources** from which URJIVA gets its emission factors (the numbers used to calculate CO₂).

---

### 🇮🇳 CEA — Central Electricity Authority

**What is it?**
- A **statutory body** under the **Ministry of Power, Government of India**
- Headquarters: New Delhi
- Established under the Electricity (Supply) Act, 1948

**What does it do?**
- Advises the government on power sector policy
- **Publishes India's grid emission factor** — the number that tells you how much CO₂ is produced per unit of electricity from the Indian grid
- Maintains the **CO₂ Baseline Database** (currently version 21.0)

**How URJIVA uses CEA data:**
- The grid emission factor from CEA = **0.7117 kgCO₂e/kWh** (national weighted average including RES and captive)
- This means: every kWh of electricity consumed from the Indian grid causes 0.7117 kg of CO₂ emissions
- Used in **Scope 2 emissions calculation** — when a factory uses grid electricity, we multiply kWh × 0.7117 to get CO₂

**Why CEA and not some random source?**
- CEA is the **legally recognized authority** for grid emission calculations in India
- Required for carbon credit methodologies (CDM, VCS, Gold Standard)
- Using CEA numbers makes URJIVA's calculations legally defensible

---

### 🌍 IPCC — Intergovernmental Panel on Climate Change

**What is it?**
- The **United Nations body** that assesses the science of climate change
- Created in **1988** by WMO (World Meteorological Organization) and UNEP (UN Environment Programme)
- Has **195 member countries** including India
- Won the **Nobel Peace Prize in 2007** (shared with Al Gore)

**What does it do?**
- Publishes comprehensive assessment reports on climate change (AR1 through AR6)
- Provides **standardized emission factors** for all types of fuels worldwide
- Sets the scientific basis for international climate policy (Paris Agreement, etc.)

**How URJIVA uses IPCC data:**
- **Net Calorific Values (NCV)** — How much energy each fuel contains:
  - Coal: 19.6–25.8 TJ/kt
  - Furnace Oil: 40.4 TJ/kt
  - Diesel: 43.0 TJ/kt
  - Natural Gas: 48.0 TJ/kt (per kt equivalent)
- **Emission Factors (tCO₂/TJ)** — How much CO₂ each fuel produces per unit of energy:
  - Coal: 95.7–96.1 tCO₂/TJ
  - Furnace Oil: 77.4 tCO₂/TJ
  - Diesel: 74.1 tCO₂/TJ
  - Natural Gas: 56.1 tCO₂/TJ
  - Biomass (biogenic): 0 tCO₂/TJ (carbon neutral)

**Why IPCC and not some other source?**
- IPCC emission factors are the **global gold standard** — accepted by every country and every carbon trading framework
- Using IPCC ensures URJIVA's CO₂ calculations are internationally comparable and credible

### ✍️ Script Page Note

> **CEA (Central Electricity Authority):** Statutory body under Ministry of Power, India. Publishes India's grid emission factor (CO₂ Baseline Database v21.0). Grid EF = 0.7117 kgCO₂e/kWh. Used for Scope 2 (electricity) emission calculations. Legally recognized authority for Indian grid carbon accounting.
>
> **IPCC (Intergovernmental Panel on Climate Change):** UN body (195 countries, Nobel Prize 2007). Provides standardized fuel emission factors — NCV (TJ/kt) and EF (tCO₂/TJ) for coal, oil, gas, diesel, biomass. The global gold standard for carbon accounting. Used for Scope 1 (fuel combustion) emission calculations.
>
> **In URJIVA:** CEA → Scope 2 (electricity CO₂), IPCC → Scope 1 (fuel CO₂). Both are the highest-authority sources possible, making our calculations credible and auditable.

---

# 🎯 Master Quick-Reference Strip (Cut & Paste to Script Page Bottom)

```
JWT = JSON Web Token (stateless auth, HS256, 8hr expiry)
GIS = Geographic Information System (maps + location data)
Industries = 9 (Textile, Food, Pharma, Chemical, Paper, Dairy, Cement, Steel, Glass)
Technologies = 9 categories, 40+ variants (Biomass, Biogas, Heat Pump, Electric Boiler, Solar Thermal, Solar PV, TES, WHR, Electrification)
Key Formulas = Payback = CAPEX/Savings | ROI = [(Savings×Life)−CAPEX]/CAPEX×100 | CO₂ = Energy(TJ)×EF(tCO₂/TJ)
Monte Carlo = 1000s of random simulations → probability distribution (not single estimate)
P10/P50/P90 = Optimistic/Expected/Pessimistic percentiles (industry standard for energy project risk)
12 MCDA Criteria = Technical(12%) Financial(12%) Resource(8%) Policy(6%) Risk(10%) TRL(8%) Complexity(6%) Supply(10%) Grid(5%) Biomass(5%) Carbon(12%) Confidence(6%)
ADEETIE = BEE interest subvention (5%/3%) | MSE-GIFT = Green loans via SIDBI | ZED = Zero Defect Zero Effect certification
CEA = India grid emission factor (0.7117 kgCO₂/kWh) | IPCC = Global fuel emission factors (tCO₂/TJ)
```
