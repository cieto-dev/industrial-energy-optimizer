# Intentionally Incomplete Items

To avoid over-claiming, explicitly disclose the following to mentors/judges:

1. **CAPEX/OPEX Financials:** Intentionally null for most technologies to adhere to strict data governance; we are awaiting validated vendor matrices rather than using LLM hallucinations.
2. **PDF/Excel Generation:** The UI shell and data contract are complete. Byte-stream file generation is pending server-side integration, so we rely on a high-fidelity client-side browser print fallback for the demo.
3. **Database Persistence & API Latency:** The current demo flow uses local browser storage. For the national stage demo, we have built a one-click **Demo Mode (`/demo`)** that instantly injects a pre-computed backend payload for a UP Textile factory directly into the browser. This bypasses live database and API latency to guarantee a flawless simulation of the "blocked state" for judges.
4. **Thermal Power Plants:** Explicitly scoped out of the current operational tool to focus on SME continuous process heat.
5. **Marketing Landing Page:** Left unpolished as the team allocated 100% of engineering bandwidth to hardening the core operational engine logic and data contracts.
