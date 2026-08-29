 # 🧠 URJIVA — Complete Architecture & Tech Stack Guide

> **Purpose:** This document will help you deeply understand every technology, module, framework, and tool used in URJIVA so you can confidently answer ANY question judges or teammates throw at you.
>
> **Format:** Every item follows the **5W1H** framework — What, Why, Who, Where, When, How.

---

## 📐 The Big Picture — 4-Layer Architecture

URJIVA's architecture is a clean **4-layer system**. Think of it like a building:

```
┌──────────────────────────────────────────────────────┐
│  🖥️  PRESENTATION LAYER  (What the user sees)        │  ← Next.js + TypeScript + Tailwind
├──────────────────────────────────────────────────────┤
│  ⚙️  APPLICATION LAYER  (The traffic controller)      │  ← FastAPI + Python + JWT
├──────────────────────────────────────────────────────┤
│  🧠  DECISION ENGINE  (The brain — core logic)        │  ← Pure Python algorithms
├──────────────────────────────────────────────────────┤
│  💾  DATA & KNOWLEDGE LAYER  (The memory)              │  ← PostgreSQL + JSON Knowledge Base
└──────────────────────────────────────────────────────┘
```

**Why 4 layers?**
- **Separation of Concerns** — Each layer has ONE job. The frontend doesn't know how MCDA works. The backend doesn't know how to render charts. The engine doesn't care about HTTP.
- **Scalability** — Each layer can be scaled or updated independently.
- **Testability** — The decision engine can be tested without running the frontend or backend.

---

# 🖥️ LAYER 1 — PRESENTATION LAYER

> This is the **user-facing layer** — what the MSME factory owner sees and interacts with.

---

## 1.1 Next.js (v15)

### What is it?
- A **React-based web framework** created by Vercel
- It is NOT just React — it adds server-side rendering (SSR), file-based routing, image optimization, and production builds on top of React

### Why do we use it?
- **App Router** — Each folder inside `app/` automatically becomes a URL route (e.g., `app/dashboard/page.tsx` → `/dashboard`)
- **Standalone Build** — Produces a self-contained production output perfect for Docker containers
- **Performance** — Server-side rendering makes pages load faster (good for factory owners with slow internet in industrial areas)
- **Developer Experience** — Hot reload, built-in TypeScript support, easy deployment

### Where is it used in URJIVA?
- The entire frontend lives in the `frontend/` folder
- Key pages: `/assessment` (input wizard), `/report` (results dashboard), `/scenario-playground` (what-if simulator), `/gis` (industrial cluster map), `/comparison` (state comparator)

### How does it work?
- The factory owner visits `localhost:3000` (or the deployed URL)
- Next.js renders the page, the user fills the assessment form
- On submission, it sends a POST request to the FastAPI backend at `localhost:8000`
- The response comes back as JSON, and Next.js renders the dashboard with charts and recommendations

---

## 1.2 TypeScript (v5.5)

### What is it?
- A **superset of JavaScript** created by Microsoft
- It adds **static types** — meaning you define the shape of your data before using it

### Why do we use it?
- **Catches bugs at compile time** — If the backend returns `payback_years` but your code expects `paybackYears`, TypeScript catches this immediately
- **Self-documenting** — Types like `FactoryProfile`, `OptimizationResponse`, `ScenarioInputs` act as living documentation
- **Team collaboration** — With 6 team members, types prevent miscommunication about data shapes

### Where is it used?
- Every `.tsx` and `.ts` file in the frontend
- Type definitions in `frontend/types/` — `api.ts`, `scenario.ts`, `recommendation.ts`, `technology.ts`

### How does it work?
- You write TypeScript → The compiler converts it to plain JavaScript → The browser runs the JavaScript
- Example: `interface FactoryProfile { industry: string; fuel_type: string; process_temp: number; }` — Now if someone tries to pass a string for `process_temp`, the compiler throws an error

---

## 1.3 Tailwind CSS (v3.4)

### What is it?
- A **utility-first CSS framework** — Instead of writing custom CSS classes, you compose styles directly in HTML using small utility classes

### Why do we use it?
- **Speed** — Writing `className="bg-green-600 text-white p-4 rounded-lg"` is faster than creating separate CSS files
- **Consistency** — Predefined spacing, color, and typography scales ensure the UI looks uniform
- **Dark Mode** — Built-in support for light/dark theme toggling (URJIVA uses `next-themes` for this)
- **Responsive Design** — Easy breakpoint prefixes like `md:`, `lg:` for mobile/desktop layouts

### Where is it used?
- Every component in the frontend — buttons, cards, forms, dashboards, navigation bars
- Custom theme colors defined in `frontend/tailwind.config.ts` and CSS variables in `frontend/app/global.css`

---

## 1.4 Recharts (v2.13)

### What is it?
- A **React charting library** built on top of D3.js
- Provides ready-made chart components — BarChart, LineChart, AreaChart, PieChart

### Why do we use it?
- Renders the key visualizations on the report dashboard:
  - **Bar Charts** — Baseline vs Recommended cost and CO₂ comparison
  - **Area Charts** — 10-year cumulative cash flow with breakeven markers
  - **Line Charts** — CO₂ abatement trajectory over time
  - **MCDA Score Distribution** — Horizontal bars comparing pathway scores

### Where is it used?
- `components/dashboard/DashboardCharts.tsx` — The 4-tab powerhouse chart component
- `components/dashboard/ScenarioComparison.tsx` — MCDA score bar chart

---

## 1.5 Leaflet + React-Leaflet

### What is it?
- **Leaflet** is the most popular open-source JavaScript library for interactive maps
- **React-Leaflet** wraps Leaflet in React components

### Why do we use it?
- The **GIS Map** page (`/gis`) shows an interactive map of India with industrial clusters (Tirupur, Morbi, Surat, Kanpur, Ludhiana, Panipat, etc.)
- Each cluster pin shows energy data — annual spend, CO₂ footprint, surplus biomass, solar radiation (DNI), and DISCOM tariffs
- Uses Google hybrid satellite/terrain tiles for real-world visualization

### How does it work?
- Loaded dynamically with `next/dynamic` and `ssr: false` (because Leaflet requires the browser's `window` object, which doesn't exist during server-side rendering)
- Custom HTML pin markers rendered using React's `renderToString`

---

## 1.6 Other Frontend Tools

| Tool | What | Why |
|------|------|-----|
| **React Hook Form** | Form state management library | Manages the 5-step assessment wizard efficiently without unnecessary re-renders |
| **Zod** | Schema validation library | Validates factory profile data on the client side before sending to backend |
| **Framer Motion** | Animation library | Smooth transitions, scroll-linked animations on the subsidies page, card entry effects |
| **Radix UI** | Headless UI component primitives | Accessible modals (login dialog), select dropdowns, labels — unstyled so we control the look |
| **Axios** | HTTP client | Sends API requests to FastAPI backend with JWT token auto-attached via interceptors |
| **Lucide React** | Icon library | Clean, consistent SVG icons throughout the UI |
| **next-themes** | Theme manager | Light/dark mode toggle across the entire app |

---

# ⚙️ LAYER 2 — APPLICATION LAYER

> This is the **traffic controller** — it receives requests from the frontend, coordinates the Decision Engine, and sends back results.

---

## 2.1 FastAPI (v0.135)

### What is it?
- A **modern Python web framework** for building APIs
- Created by Sebastián Ramírez — it's the fastest-growing Python web framework

### Why do we use it? (Instead of Django/Flask)
- **Automatic API documentation** — FastAPI auto-generates Swagger UI docs at `/docs` — great for demos
- **Pydantic integration** — Request/response data is automatically validated against Pydantic models
- **Async support** — Can handle multiple requests concurrently (important when multiple users run optimizations)
- **Performance** — One of the fastest Python frameworks (built on Starlette + Uvicorn)
- **Type hints** — Python type annotations become the API contract — no separate schema files needed

### Where is it used?
- The entire `backend/` folder — `main.py` is the entry point
- Every API endpoint is a FastAPI router in `backend/apis/`

### How does it work?
1. FastAPI app is created in `main.py`
2. Routers are registered for each domain: `/optimization`, `/technologies`, `/policies`, `/scenario-playground`, etc.
3. When the frontend sends a POST to `/optimization/optimize`, FastAPI validates the input using Pydantic, passes it to the Decision Engine, and returns the JSON result

### API Endpoints (The Doors Into Our System)

| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/optimization/optimize` | POST | **The main pipeline** — Takes factory profile → Runs full 8-stage decision engine → Returns ranked recommendations |
| `/technologies` | GET | Returns all available clean technologies |
| `/technologies/filter` | POST | Checks which technologies are feasible for a specific factory |
| `/policies/evaluate` | POST | Evaluates subsidy and policy eligibility |
| `/recommendations/{id}` | GET | Fetches detailed recommendation with explanations |
| `/scenario-playground/evaluate` | POST | Runs what-if simulation with modified parameters |
| `/geographic/profile` | GET | Returns location-specific intelligence (biomass, tariffs, solar) |
| `/reports/{id}/pdf` | GET | Generates downloadable PDF report |
| `/reports/{id}/excel` | GET | Generates downloadable Excel report |
| `/auth/login` | POST | Authenticates user, returns JWT token |
| `/health` | GET | Service health check |

---

## 2.2 Uvicorn (v0.42)

### What is it?
- An **ASGI server** — the actual program that runs the FastAPI application and listens for HTTP requests

### Why do we use it?
- FastAPI needs a server to run — Uvicorn is the recommended one
- It's lightning fast and supports async operations
- In production, runs as: `uvicorn main:app --host 0.0.0.0 --port 8000`

### Simple analogy
- FastAPI = the recipe book (defines what to do for each request)
- Uvicorn = the chef (actually runs the recipes and serves the food)

---

## 2.3 JWT Authentication (JSON Web Tokens)

### What is it?
- A **stateless authentication mechanism** — the server gives the client a signed token after login, and the client sends it with every subsequent request

### Why do we use it?
- No need to store sessions on the server (stateless = scalable)
- The token contains the user's identity (email) and an expiration time (8 hours)
- Protected endpoints check the token before allowing access

### How does it work in URJIVA?
1. User logs in via `/auth/login` with email + password
2. Password is verified using **bcrypt** hashing (the actual password is never stored — only its hash)
3. If valid, the server creates a JWT signed with a secret key using **HS256 algorithm**
4. Frontend stores the token in `localStorage` and attaches it to every API request via an Axios interceptor
5. Protected endpoints decode the token and verify the user

### Where is it implemented?
- `backend/auth.py` — Token creation, password hashing, and user verification
- `frontend/services/api.ts` — Axios interceptor that attaches `Authorization: Bearer <token>`

---

## 2.4 Pydantic (v2.12)

### What is it?
- A **data validation library** for Python
- You define the shape of your data using Python classes, and Pydantic automatically validates incoming data

### Why do we use it?
- **Request validation** — If the frontend sends `process_temp: "hot"` instead of `process_temp: 450`, Pydantic rejects it with a clear error
- **Domain modeling** — Our shared models (`Factory`, `Technology`, `Scenario`, `Recommendation`) are Pydantic models, ensuring data consistency across the entire system
- **Serialization** — Converts Python objects to JSON automatically for API responses

### Where is it used?
- `models/` folder — `factory.py`, `technology.py`, `scenario.py`, `recommendation.py`, `biomass.py`, `financial.py`, `emission.py`
- Every FastAPI endpoint that accepts or returns structured data

---

## 2.5 SQLAlchemy + PostgreSQL

### What is SQLAlchemy?
- A **Python ORM (Object-Relational Mapper)** — lets you interact with a database using Python objects instead of raw SQL queries

### What is PostgreSQL?
- An **advanced open-source relational database** — the most powerful free database available
- URJIVA uses PostgreSQL 17 with two extensions:
  - **PostGIS** — For geographic/spatial queries (district-level industrial cluster mapping)
  - **pgvector** — For vector search over policy/research documents

### Why this combination?
- SQLAlchemy provides a clean Python interface to the database
- PostgreSQL handles complex queries, geospatial data, and scales well
- In development, it falls back to SQLite for simplicity

### What's stored in the database?
- User accounts (email, hashed password, active status)
- Future: Factory profiles, saved recommendations, audit logs

---

# 🧠 LAYER 3 — DECISION ENGINE (The Brain)

> This is the **core intellectual property** of URJIVA. Pure Python. No AI/ML. Fully deterministic and auditable.

---

## 3.1 The Complete Pipeline (8 Stages)

```
Factory Profile
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 1: Baseline Engine                                │
│  → Computes current energy, cost, and CO₂ emissions      │
├─────────────────────────────────────────────────────────┤
│  STAGE 2: Technology Feasibility Filter                   │
│  → Screens 40+ technologies, rejects infeasible ones      │
├─────────────────────────────────────────────────────────┤
│  STAGE 3: Scenario Generator                              │
│  → Creates 3-5 candidate transition pathways              │
├─────────────────────────────────────────────────────────┤
│  STAGE 4a: Economics Engine (CAPEX, OPEX, Payback, ROI)   │
│  STAGE 4b: Emissions Engine (CO₂ reduction calculation)   │  ← Run in PARALLEL
│  STAGE 4c: Reliability Engine (Monte Carlo simulation)    │
├─────────────────────────────────────────────────────────┤
│  STAGE 5: MCDA Optimizer (12-criteria ranking)            │
├─────────────────────────────────────────────────────────┤
│  STAGE 6: Policy & Subsidy Engine                         │
├─────────────────────────────────────────────────────────┤
│  STAGE 7: Recommendation Builder + Explainability         │
├─────────────────────────────────────────────────────────┤
│  STAGE 8: Report Generator (JSON / PDF / Excel)           │
└─────────────────────────────────────────────────────────┘
      │
      ▼
Ranked Recommendations with Full Audit Trail
```

---

## 3.2 Stage 1 — Baseline Engine

**📁 Location:** `decision_engine/baseline/`

### What does it do?
- Computes the factory's **current state** — how much energy it uses, how much it costs, and how much CO₂ it emits TODAY (before any changes)

### Why is this important?
- You can't recommend a solution if you don't know the problem
- The baseline is the **reference point** — all improvements are measured against it
- It's treated as **immutable** — once computed, it never changes (the "digital twin" of current operations)

### How does it compute? (The Engineering Formula)

The thermal energy balance chain:

```
Chemical Energy (fuel) × η_boiler → Steam/Heat × η_distribution → Delivered Heat × η_process → Useful Process Heat
```

- **η_boiler** = 75% (typical industrial boiler efficiency)
- **η_distribution** = 85% (steam pipe losses)
- **η_process** = 80% (process utilization efficiency)

It also calculates:
- **Annual fuel cost** = (Fuel quantity per day × price per unit × operating days per year)
- **Annual CO₂ emissions** = Energy input (TJ) × Emission factor (tCO₂/TJ)

### Key files:
| File | What it does |
|------|-------------|
| `baseline_engine.py` | Main orchestrator — calls all sub-calculators |
| `energy_calculator.py` | Computes the energy balance chain |
| `fuel_calculator.py` | Calculates annual fuel costs |
| `_units.py` | Converts between kg, tonnes, litres, SCM, MJ, TJ |
| `models.py` | Defines `BaselineProfile` and `EnergyBalance` data structures |

---

## 3.3 Stage 2 — Technology Feasibility Filter

**📁 Location:** `decision_engine/technology/` (filtered via `backend/apis/technology_api.py`)

### What does it do?
- Checks every clean energy technology in the database against the factory's specific constraints
- Answers the question: **"Can this technology physically work for THIS factory?"**

### What does it check? (Filter Dimensions)

| Check | Example |
|-------|---------|
| **Temperature compatibility** | Heat pumps max out at ~160°C → Rejected for a steel plant needing 1200°C |
| **Roof area** | Solar thermal needs ~5 m²/kWp → Rejected if factory has < 100 m² roof |
| **Grid capacity** | Electric boilers need heavy grid connection → Rejected if grid reliability < 60% |
| **Fuel replacement compatibility** | Not all technologies can replace all fuels (coal → biomass ✅, coal → heat pump ❌ for high temp) |
| **Industry/sector rules** | Some technologies are sector-specific (e.g., waste heat recovery mainly for cement, glass, steel) |
| **Budget constraints** | Technology rejected if minimum CAPEX exceeds factory's budget |

### Why is this NOT AI/ML?
- It's purely **rule-based** — like a checklist
- Rules are stored in `knowledge-base/constraints/technology_rules.json`
- This is intentional — for industrial decisions, you need deterministic, explainable logic, not probabilistic guesses

### Key output:
- `feasible_technologies[]` — Technologies that pass all checks
- `rejected_technologies[]` — Technologies that failed, WITH EXPLICIT REASONS (e.g., "Rejected: Process temperature 800°C exceeds heat pump maximum of 160°C")

---

## 3.4 Stage 3 — Scenario Generator

**📁 Location:** `decision_engine/scenario/`

### What does it do?
- Takes the feasible technologies and **combines them into ordered transition pathways**
- Generates **3 to 5 candidate pathways** for the factory

### What is a "pathway"?
- A pathway is a sequence of technology adoptions, like:
  - **Pathway 1:** Biomass Boiler (replace coal, 60% heat demand)
  - **Pathway 2:** Solar Thermal + Biomass Boiler (hybrid — solar for base load, biomass for peak)
  - **Pathway 3:** Energy Efficiency + Heat Pump + Solar PV (electrification route)

### How does it generate pathways?
1. **Single-technology pathways** — Each feasible technology as a standalone solution
2. **Sequential combinations** — Technologies applied in phases (e.g., efficiency first, then fuel switch)
3. **Hybrid thermal combinations** — Two heat sources combined (handled by `scenario_hybrid_generator.py`)

### What validation does it do?
- **Load consistency check** — Prevents two technologies from each claiming 100% of the same thermal load
- **Deduplication** — Removes pathways that are essentially the same in different order
- **Physical consistency** — Validates that the combined technologies make engineering sense

### Key files:
| File | What it does |
|------|-------------|
| `scenario_generator.py` | Main pathway generation logic |
| `scenario_hybrid_generator.py` | Creates hybrid thermal combinations |
| `scenario_validator.py` | Checks physical and load consistency |
| `scenario_filter.py` | Additional rule-based filtering |
| `scenario_feasibility.py` | Multi-dimensional screening |

---

## 3.5 Stage 4a — Economics Engine

**📁 Location:** `decision_engine/economics/`

### What does it do?
- Calculates the **financial metrics** for each candidate pathway

### Key calculations:

#### CAPEX (Capital Expenditure) — How much does it cost to install?
```
CAPEX = Unit Cost (₹/kW or ₹/kWth) × Required Capacity
```
- Returns a range: `capex_min`, `capex_max`, and `capex_estimate` (midpoint)
- Handles unit conversions (USD/kW → INR/kW using exchange rates)

#### OPEX (Operating Expenditure) — How much does it cost to run annually?
```
Annual OPEX = Fuel Cost + Electricity Cost + Maintenance (% of CAPEX) + Labour
```

#### Annual Savings
```
Annual Savings = Baseline OPEX − Proposed OPEX
```

#### Simple Payback Period — When does the investment pay for itself?
```
Payback (years) = CAPEX ÷ Annual Savings
```
- Returns a range: `payback_min` to `payback_max`

#### Return on Investment (ROI)
```
ROI (%) = [(Annual Savings × Lifetime) − CAPEX] ÷ CAPEX × 100
```

#### Viability Check
- A pathway is **viable** only if:
  - Annual Savings > 0 (it actually saves money)
  - Payback_min ≤ Technology Lifetime (pays back before equipment dies)

---

## 3.6 Stage 4b — Emissions Engine

**📁 Location:** `decision_engine/emissions/`

### What does it do?
- Calculates **CO₂ reduction** for each pathway

### How does it calculate?

```
CO₂ (tonnes/year) = Energy Input (TJ/year) × Emission Factor (tCO₂/TJ)
```

### Two scopes of emissions:
- **Scope 1 (Direct):** CO₂ from burning fuel (coal, furnace oil, diesel, LPG, natural gas)
- **Scope 2 (Indirect):** CO₂ from grid electricity consumption

### Key distinction:
- **Fossil fuels** (coal, oil, gas) → Count as emissions
- **Biogenic fuels** (biomass pellets, briquettes, biogas) → Considered carbon-neutral (the CO₂ was absorbed by the plant during growth)

### Where do emission factors come from?
- **Fuel emission factors:** IPCC guidelines (Net Calorific Values and tCO₂/TJ)
- **Grid emission factors:** CEA (Central Electricity Authority) CO₂ Baseline Database v21.0 → `0.7117 kgCO₂e/kWh` (national weighted average)

---

## 3.7 Stage 4c — Reliability & Uncertainty Engine

**📁 Location:** `decision_engine/reliability/`

### What does it do?
- Replaces **single-number estimates** with **probability distributions**
- Answers: "How much could the payback period vary if fuel prices change or costs overrun?"

### How does Monte Carlo simulation work?

1. **Define perturbation ranges** (from `knowledge-base/finance/perturbation_config.json`):
   - Fuel price: ±15–25%
   - Electricity tariff: ±10–20%
   - Biomass cost: ±20–30%
   - Equipment efficiency: 0.9× to 1.1× of baseline
   - CAPEX overrun: +10–30%

2. **Run N iterations** (typically 100–10,000):
   - In each iteration, randomly perturb the parameters within their ranges
   - Recalculate payback period with the perturbed values

3. **Compute output distribution:**
   - **P10** = 10th percentile → Optimistic scenario (90% chance payback is longer than this)
   - **P50** = 50th percentile → Expected/median scenario
   - **P90** = 90th percentile → Pessimistic scenario (only 10% chance it's worse)
   - **Spread Ratio** = (P90 − P10) ÷ P50 → Measures how uncertain the estimate is

4. **Risk Classification:**
   - **LOW** risk: Spread ratio < 0.15
   - **MEDIUM** risk: 0.15 – 0.30
   - **HIGH** risk: 0.30 – 0.50
   - **VERY HIGH** risk: > 0.50

### Why is this important?
- A pathway with 5-year payback and LOW spread is better than one with 4-year payback but HIGH spread
- It protects factory owners from making decisions based on overly optimistic single estimates
- Judges LOVE this — it shows statistical rigor

### Additional outputs:
- **OAT (One-At-a-Time) Tornado Analysis** — Shows which single parameter has the biggest impact on payback (is it fuel price? electricity? CAPEX?)
- **Best / Expected / Worst** deterministic scenarios

---

## 3.8 Stage 5 — MCDA Optimizer (The Ranking Algorithm)

**📁 Location:** `decision_engine/optimizer/`

### What is MCDA?
- **Multi-Criteria Decision Analysis** — A mathematical framework for ranking options when multiple conflicting objectives exist
- You can't just pick the cheapest — what if it's risky? Or barely reduces emissions?
- MCDA balances ALL factors simultaneously

### The 12 Evaluation Criteria

| # | Criterion | Weight | Type | What it measures |
|---|-----------|--------|------|-----------------|
| 1 | Technical Feasibility | 0.12 | Benefit ↑ | How well the tech fits the factory |
| 2 | Financial Viability (LCC) | 0.12 | Benefit ↑ | Overall life-cycle cost effectiveness |
| 3 | Resource Availability | 0.08 | Benefit ↑ | Local fuel/resource availability |
| 4 | Policy Support | 0.06 | Benefit ↑ | Government subsidy coverage |
| 5 | Risk / Spread Ratio | 0.10 | Cost ↓ | Financial uncertainty (lower = better) |
| 6 | Technology Maturity (TRL) | 0.08 | Benefit ↑ | Proven vs experimental |
| 7 | Implementation Complexity | 0.06 | Cost ↓ | Difficulty of installation |
| 8 | Supply Reliability | 0.10 | Benefit ↑ | Fuel supply chain reliability |
| 9 | Grid Dependence | 0.05 | Cost ↓ | Reliance on unreliable grid |
| 10 | Biomass Supply Dependence | 0.05 | Cost ↓ | Seasonal biomass risk |
| 11 | Carbon Reduction % | 0.12 | Benefit ↑ | CO₂ emission reduction achieved |
| 12 | Evidence Confidence | 0.06 | Benefit ↑ | Data source quality |
| | **Total** | **1.00** | | |

### How does the scoring algorithm work?

**Step 1 — Build the Decision Matrix**
- Create an N × 12 matrix where N = number of candidate pathways

**Step 2 — Min-Max Normalization** (scales everything to 0–1)
- For **Benefit criteria** (higher is better):
  ```
  Normalized = (value − min) / (max − min)
  ```
- For **Cost criteria** (lower is better):
  ```
  Normalized = (max − value) / (max − min)
  ```
- If all values are the same → normalized score = 1.0

**Step 3 — Weighted Sum**
```
Composite Score = Σ (weight_j × normalized_score_j)  for j = 1 to 12
```

**Step 4 — Hierarchical Ranking** (tie-breaking)
1. Highest composite score → Rank 1
2. If tied: lower risk wins
3. If still tied: higher emission reduction wins
4. If still tied: lower cost wins

### Why not just pick the cheapest?
- The cheapest pathway might have HIGH risk (fuel price volatility)
- Or LOW emission reduction (defeating the decarbonization purpose)
- Or rely on immature technology (TRL < 7)
- MCDA ensures the **most balanced** pathway wins

---

## 3.9 Stage 6 — Policy & Subsidy Engine

**📁 Location:** `decision_engine/policy/`

### What does it do?
- Automatically checks if the factory is eligible for **central and state government subsidies**
- Calculates the **financial benefit** from each eligible scheme

### How does it work? (Two-step process)

**Step 1 — Eligibility Check (`eligibility.py`)**
- Checks MSME classification:
  - Micro: Investment < ₹1 Cr AND Turnover < ₹5 Cr
  - Small: Investment < ₹10 Cr AND Turnover < ₹50 Cr
  - Medium: Investment < ₹50 Cr AND Turnover < ₹250 Cr
- Checks Udyam registration status
- Checks industry sector, state, project type
- Checks special categories (Women-owned, SC/ST, Aspirational District)

**Step 2 — Subsidy Matching (`subsidy_matcher.py`)**
- Matches against schemes:
  - **ADEETIE** (BEE) — 30–50% capital subsidy for energy efficiency projects
  - **MSE-GIFT** — Interest subvention + credit guarantee for Micro & Small enterprises
  - **ZED** — Zero Defect Zero Effect certification incentives
  - **PM Surya Ghar** — Solar rooftop subsidies
  - **CLCSS** — Capital Linked Credit Subsidy Scheme
  - **State policies** — Tamil Nadu, Gujarat, HP, UP, Punjab, J&K capital subsidies

### Anti-double-counting
- Some subsidies can't be combined ("stacked")
- The engine flags uncertain stackability with: `total_benefit_verified: false`
- Adds a disclaimer about convergence rules

---

## 3.10 Stages 7 & 8 — Recommendation & Reports

**📁 Location:** `decision_engine/recommendation/` and `decision_engine/reports/`

### What does the Recommendation Builder do?
- Assembles the final output:
  - **Recommended Pathway** — The top-ranked scenario from MCDA
  - **"Why Selected"** — Multi-point explanation (e.g., "Lowest payback period, moderate risk, highest policy support")
  - **"Why Others Rejected"** — Specific reasons for each non-selected pathway
  - **Policy Benefits** — List of eligible schemes with estimated ₹ value
  - **Sensitivity Notes** — P10/P50/P90 distributions and dominant risk factors
  - **Evidence Citations** — Every number traced to its source

### Report Generation
| Format | Tool Used | What it contains |
|--------|-----------|-----------------|
| **JSON** | Python `dict` | Machine-readable API response for the frontend dashboard |
| **PDF** | ReportLab | Executive-ready document with Indian currency formatting (Lakhs/Crores) |
| **Excel** | openpyxl | Multi-tab spreadsheet (financials, emissions, sensitivity, eligibility tables) |

---

# 💾 LAYER 4 — DATA & KNOWLEDGE LAYER

---

## 4.1 Knowledge Base (JSON)

**📁 Location:** `knowledge-base/`

### What is it?
- A **versioned repository of curated datasets** stored as JSON files
- NOT a database — these are flat files checked into Git for version control and auditability

### What data does it contain?

| Directory | Contents | Examples |
|-----------|----------|---------|
| `industries/` | 9 industry sector profiles | `textile.json`, `cement.json`, `steel.json`, `pharma.json`, `dairy.json` |
| `technologies/` | Clean energy technology specs | `biomass.json`, `heat_pump.json`, `solar_thermal.json`, `electrification.json` |
| `constraints/` | Feasibility rules | `technology_rules.json`, `temperature.json`, `space.json`, `budget.json` |
| `emissions/` | Emission factors | IPCC NCV values, CEA grid emission factors |
| `finance/` | Cost data | Technology costs, electricity tariffs, fuel prices, subsidy amounts |
| `policies/` | Government schemes | Central policies (ADEETIE, MSE-GIFT), state policies, eligibility rules |
| `master/` | Reference indexes | Technologies, industries, fuels, states, districts, DISCOMs |
| `references/` | Citations & sources | Bibliography metadata — NITI Aayog, CEA, MNRE, BEE |
| `assumptions/` | Default parameters | Boiler efficiency 75%, distribution 85%, process 80% |

### Why JSON and not a database?
- **Auditability** — Every change is tracked in Git history
- **Portability** — No database setup needed for the decision engine to run
- **Citation integrity** — Each data point can be traced to a government/academic source
- **Hackathon practicality** — Easy to update, review, and demo

---

## 4.2 Knowledge Runtime

**📁 Location:** `knowledge_runtime/`

### What is it?
- A **high-performance in-memory data access layer** that sits on top of the JSON knowledge base
- Think of it as a **caching + indexing** layer

### Why do we need it?
- Reading JSON files from disk for every API request would be slow
- The runtime loads everything into memory once, builds indexes, and serves data instantly

### Key components:
| File | What it does |
|------|-------------|
| `loader.py` | Loads JSON files with caching and path traversal protection |
| `cache.py` | In-memory cache with shared (zero-copy) and owned semantics |
| `repository.py` | Single API for querying technologies, industries, biomass by index |
| `evidence.py` | Resolves citation keys to full metadata from `sources.json` |
| `research_updates.py` | Safely applies data updates with SHA-256 checksums and rollback |

---

## 4.3 PostgreSQL (v17)

### What is it?
- An **advanced open-source relational database**

### What extensions does URJIVA use?
- **PostGIS** — Enables geographic queries (finding nearest biomass source, industrial cluster radius searches)
- **pgvector** — Enables vector similarity search (for policy/research document matching)

### What's stored?
- User accounts (authentication)
- Future: Persisted factory profiles, recommendation history, audit logs

---

## 4.4 CSV & JSON Datasets

**📁 Location:** `datasets/`

| Dataset | What it contains |
|---------|-----------------|
| `biomass_atlas.csv` | District-wise biomass availability — rice husk, bagasse, cotton stalk — surplus tonnage, moisture %, calorific values, farmgate costs |
| `district_coordinates.csv` | Latitude/longitude for Indian districts (for GIS mapping and transport cost estimation) |
| `electricity_tariffs/` | State and DISCOM-specific industrial tariff slabs, Time-of-Day rates |
| `industrial_fuels.csv` | Energy densities (MJ/kg) and CO₂ emission factors for coal, furnace oil, diesel, LPG, natural gas, biomass |
| `temperature_ranges.csv` | Operating temperature spans for each technology (Heat Pumps: 40–120°C, Biomass Boilers: 120–800°C, etc.) |
| `case_studies.json` | Real-world validated industrial transition benchmarks |

---

# 🐳 DEVOPS & DEPLOYMENT

---

## 5.1 Docker & Docker Compose

### What is Docker?
- A **containerization platform** — packages your application with all its dependencies into a portable "container"
- Guarantees: "If it works on my machine, it works everywhere"

### URJIVA's 4-Container Architecture

```
┌─────────────────────────────────────────────────┐
│                   NGINX (Port 80)                │  ← Reverse proxy
│  Routes /api/* → Backend | Everything else → FE  │
├──────────────────┬──────────────────────────────┤
│  Next.js Frontend│  FastAPI Backend              │
│  (Port 3000)     │  (Port 8000)                 │
├──────────────────┴──────────────────────────────┤
│  PostgreSQL 17 + PostGIS + pgvector              │
│  (Port 5432)                                     │
└─────────────────────────────────────────────────┘
```

### Why Docker Compose?
- Defines all 4 containers in a single `docker-compose.yml` file
- One command: `docker compose up` → entire system is running
- Perfect for hackathon demos — no manual setup needed

---

## 5.2 Nginx

### What is it?
- A **reverse proxy and web server**
- In URJIVA, it sits in front of both frontend and backend

### What does it do?
- Routes API requests (`/auth`, `/optimization`, `/recommendations`, etc.) → FastAPI backend
- Routes all other requests → Next.js frontend
- Single entry point on port 80 — clean URL, no port numbers for users

---

## 5.3 Git & GitHub

### What is Git?
- **Version control system** — tracks every change to every file, who made it, and when

### Why GitHub?
- **Collaboration** — 6 team members working on the same codebase
- **Branch management** — Each feature developed in isolation, then merged
- **Code review** — Pull requests before merging ensure quality
- **History** — Complete audit trail of the project's evolution

---

# 🔗 How Everything Connects — The Complete Flow

```
🧑‍🏭 Factory Owner (Browser)
      │
      │  Fills 5-step assessment form
      ▼
🖥️ Next.js Frontend (Port 3000)
      │
      │  POST /optimization/optimize  (with JWT token)
      ▼
⚙️ FastAPI Backend (Port 8000)
      │
      │  Validates input with Pydantic
      │  Calls Decision Engine modules
      ▼
🧠 Decision Engine (Pure Python)
      │
      ├── 1. Baseline Engine → Current energy, cost, CO₂
      ├── 2. Technology Filter → Feasible vs rejected technologies
      ├── 3. Scenario Generator → 3-5 candidate pathways
      ├── 4a. Economics → CAPEX, OPEX, Payback, ROI
      ├── 4b. Emissions → CO₂ reduction per pathway
      ├── 4c. Reliability → Monte Carlo P10/P50/P90
      ├── 5. MCDA Optimizer → 12-criteria ranking
      ├── 6. Policy Engine → Subsidy eligibility & benefits
      ├── 7. Recommendation → "Why selected" + "Why rejected"
      └── 8. Reports → JSON / PDF / Excel
      │
      │  Reads data from:
      ▼
💾 Knowledge Base (JSON) + PostgreSQL
      │
      │  Returns structured JSON response
      ▼
⚙️ FastAPI Backend → Returns to Frontend
      │
      ▼
🖥️ Next.js Frontend → Renders Dashboard
      │
      │  Charts, KPIs, Recommendations, Rejection Log
      ▼
🧑‍🏭 Factory Owner sees the recommended pathway with full transparency
```

---

# 🎯 Quick Revision Cheatsheet

| Question | Answer |
|----------|--------|
| **What framework is the frontend?** | Next.js 15 with App Router |
| **What language is the frontend?** | TypeScript |
| **What's the CSS framework?** | Tailwind CSS |
| **What's the backend framework?** | FastAPI (Python) |
| **What runs FastAPI?** | Uvicorn (ASGI server) |
| **What's the database?** | PostgreSQL 17 with PostGIS + pgvector |
| **How does auth work?** | JWT tokens with bcrypt password hashing |
| **What's the optimization algorithm?** | MCDA (Multi-Criteria Decision Analysis) with 12 weighted criteria |
| **How many criteria in MCDA?** | 12 — summing to weight 1.0 |
| **What's the normalization method?** | Min-Max normalization |
| **How do we handle uncertainty?** | Monte Carlo simulation → P10/P50/P90 distributions |
| **How many industries are covered?** | 9 (Textile, Food, Chemical, Pharma, Paper, Dairy, Glass, Cement, Steel) |
| **How many technologies?** | 40+ (Biomass, Heat Pump, Solar Thermal, Electric Boiler, WHR, etc.) |
| **Where do emission factors come from?** | IPCC guidelines + CEA Grid Baseline Database v21.0 |
| **What deployment tool?** | Docker Compose (4 containers: Nginx + Frontend + Backend + PostgreSQL) |
| **What's the knowledge base format?** | Version-controlled JSON files in Git |
| **What makes URJIVA different?** | Fully deterministic, explainable, auditable — NOT a black-box AI |
