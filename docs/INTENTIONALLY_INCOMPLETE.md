# Intentionally Incomplete Items

To avoid over-claiming, explicitly disclose the following to mentors/judges:

1. **CAPEX/OPEX Financials:** Intentionally null for most technologies to adhere to strict data governance; we are awaiting validated vendor matrices rather than using LLM hallucinations.
2. **PDF/Excel Generation:** The UI shell and data contract are complete, but byte-stream file generation is pending server-side integration (WeasyPrint/openpyxl).
3. **Database Persistence:** The current demo flow uses local browser storage to pass state (Assessment → Dashboard → Report) to minimize latency during the pitch; cloud persistence is built but bypassed for the UI demo.
4. **Thermal Power Plants:** Explicitly scoped out of the current operational tool to focus on SME continuous process heat.
5. **Marketing Landing Page:** Left unpolished as the team allocated 100% of engineering bandwidth to hardening the core operational engine logic and data contracts.
