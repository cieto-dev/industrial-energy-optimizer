# Industrial Energy Transition Optimizer

A techno-economic decision-support system that helps individual Indian MSMEs identify which combination of energy-efficiency measures, alternative fuels, electrification, renewables, and storage can reduce their fossil-fuel dependence — without compromising production, reliability, or financial viability.

Built for Smart India Hackathon 2026, with an intended path toward a standalone product.

## The problem

Indian MSMEs that depend on coal, furnace oil, or pet coke for process heat and electricity often lack an accessible, data-driven way to determine which combination of interventions is right for *their specific factory* — its process temperature, production schedule, local fuel/resource availability, and budget. The technologies already exist (efficiency upgrades, biomass boilers, electrification, solar thermal, heat pumps, waste-heat recovery); what's missing is the decision layer that tells a factory owner which combination, in what order, actually works for them — and why.

**Research question:** Can a data-driven techno-economic decision-support system identify and compare technically feasible, economically viable, lower-emission energy-transition pathways for individual Indian MSMEs under process, resource, reliability, and financial constraints?

This is deliberately **not** "AI recommends solar panels." It's a constrained optimization system: rule-based feasibility filtering, multi-criteria ranking across cost/emissions/risk, and full explainability for every recommendation — see `docs/DECISION_ENGINE_ARCHITECTURE.md`.

## Architecture

```
Factory input → Baseline (Digital Twin) → Technology Feasibility Filter
             → Scenario Generator (3–5 candidate pathways)
             → Economics + Emissions + Reliability scoring (per pathway)
             → Multi-Criteria Optimizer (MCDA ranking)
             → Policy/Subsidy eligibility
             → Explainable Recommendation + Report
```

Full module-by-module documentation: [`docs/DECISION_ENGINE_ARCHITECTURE.md`](docs/DECISION_ENGINE_ARCHITECTURE.md)
Domain entities: [`docs/DOMAIN_MODEL.md`](docs/DOMAIN_MODEL.md)
System diagrams: [`architecture/`](architecture/) (drawio files for API flow, data flow, database ER, decision flow, deployment)

## Stack

- **Backend:** Python (FastAPI-style), domain-separated APIs (`backend/apis/`)
- **Decision engine:** independent modules for baseline, technology filtering, scenario generation, economics, emissions, reliability/sensitivity, MCDA optimization, policy, and reporting — see `decision-engine/`
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind
- **Knowledge base:** structured JSON + cited sources across constraints, emissions, finance, industries, policies, and technologies — see `knowledge-base/`
- **Deployment:** Docker + Docker Compose + nginx

## Project structure

```
architecture/       System diagrams (drawio) + summary
backend/             FastAPI app: apis/, config, database, logger, utils
datasets/            Raw CSV/reference datasets (tariffs, biomass atlas, coordinates)
decision-engine/     Core product logic — see docs/DECISION_ENGINE_ARCHITECTURE.md
deployment/          Docker, nginx config
digital-twin/        [status TBD — see docs/PROJECT_STATE.md]
docs/                Architecture, research, project state, mentor notes, backlog
frontend/            Next.js app, components, hooks, services, types
knowledge-base/      Structured, cited domain data (constraints, tech, finance, policy...)
models/              Shared domain models (matches docs/DOMAIN_MODEL.md)
research/            Source PDFs, notes, government reports, bibliography
scripts/             Data pipeline: convert_datasets, load_knowledge, run_pipeline, seed_database
tests/               Test suite
```

## Getting started

> Fill in actual commands once confirmed — placeholders below based on repo structure.

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in real values
python main.py
```

**Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local   # if applicable
npm run dev
```

**Full stack via Docker**
```bash
docker-compose up --build
```

**Run the data pipeline** (loads knowledge base into the working database)
```bash
python scripts/run_pipeline.py
```

**Run tests**
```bash
pytest tests/
```

## Current status

See [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) for a detailed, honest snapshot of what's built, what's confirmed working, and open decisions the team needs to make (sector scope, digital-twin ownership, test coverage).

## Team

6-member team — see `docs/PROJECT_STATE.md` Section 6 for ownership areas.

## Research & evidence base

Grounded in January–April 2026 Indian policy developments: NITI Aayog's *Roadmap for Green Transition of MSMEs*, MNRE/GIZ's *Decarbonizing MSMEs: Biomass for Green Steam & Heat*, BEE's ADEETIE programme, and Energy Innovation's *Electrifying Industrial Heat in India*. Full source list and citations in `knowledge-base/references/` and `research/bibliography.md`.