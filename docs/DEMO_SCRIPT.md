# End-to-End Live Demo Script

**Context for the Presenter:**
This script is designed for you to record your screen starting from the landing page, manually typing in the values as a real Plant Manager would, and running the live backend. *Do not use the /demo shortcut; run this live.*

---

## 🎬 [0:00 - 0:15] The Landing Page
*Start recording on the URJIVA homepage (or dashboard).*
**Voiceover:** "Welcome to URJIVA. This is the operational decision-support interface used by plant engineers and managers. We're going to step into the shoes of a manager running a mid-sized textile plant in Uttar Pradesh looking to decarbonize, but they don't have a firm capital budget yet."
*Action:* Click **"Start Assessment"** or navigate to `/assessment`.

---

## 🎬 [0:15 - 0:45] The Assessment Wizard (Step 1-3)
*Action: Fill out the form live with these exact values.*

**Step 1: Factory Profile**
*   **Factory Name:** "UP Textile Mills - Unit 1"
*   **Industry:** Select `Textile` 
    *(Voiceover: "Notice that when we select 'Textile', the system will smartly align expectations for low-to-medium heat.")*
*   **State:** Select `Uttar Pradesh`
*   **District:** Type `Kanpur`
*   **Production Volume:** `500` kg/day
*   **Operating Hours:** `16` (2 shifts)

**Step 2: Energy Baseline**
*   **Current Fuel:** Select `Coal`
*   **Process Temperature:** `160` °C *(Voiceover: "We need 160 degrees for our dyeing process.")*
*   **Fuel Consumption:** `2000` kg/day
*   **Electricity Consumption:** `800` kWh/day

**Step 3: Constraints & Financials**
*   **Available Roof Area:** `1200` sqm
*   **CAPEX Budget:** **LEAVE THIS COMPLETELY BLANK**
    *(Voiceover: "Crucially, we are leaving the CAPEX budget blank. We want to see how the engine handles financial uncertainty.")*

*Action:* Click **"Run Optimization Engine"**. 
*(Voiceover while loading: "The engine is now cross-referencing our precise thermodynamic needs against its verified knowledge base of technologies and policies...")*

---

## 🎬 [0:45 - 1:45] The Blocked State & Technical Feasibility
*Action: The Results page loads, showing the Amber 'Blocked' State.*
**Voiceover:** "Because we lack a firm CAPEX budget and the specific equipment cost isn't in our verified knowledge base, the engine halts the financial recommendation. This is our **'No-Invention Rule'** in action—we never fake numbers or let AI hallucinate costs."

*Action: Scroll down slightly to show the Technical Rankings.*
**Voiceover:** "However, beneath the data gap warnings, the engine still provides Preliminary Technical Rankings based purely on thermodynamics and operational reliability."

---

## 🎬 [1:45 - 2:30] Pathway Detail
*Action: Click into the #1 ranked technical pathway (e.g., Biomass + Solar).*
**Voiceover:** "Clicking into the top technical pathway, the plant manager sees exactly *why* it was chosen—specifically its operational fit and production neutrality. It guarantees we hit our 160°C requirement without risking downtime."

*Action: Point out the missing financial metrics.*
**Voiceover:** "In the Financial Reality Check section, payback and savings are honestly disabled, instructing the user that a validated vendor quote is required to proceed."

---

## 🎬 [2:30 - 3:15] Report Generation & Closing
*Action: Click "Export Report" or navigate to the Report page.*
**Voiceover:** "Finally, the plant manager can export this exact view. Our report generation previews the methodology, the explicitly flagged data gaps, and our strict No-Invention disclaimer, ensuring absolute transparency when they take this to management or a bank."

*Action: Show the print preview or the methodology disclaimer.*
**Voiceover:** "Once real CAPEX data is ingested or entered, the ranges will automatically collapse into firm payback and NPV figures, unlocking the final investment decision. This is how you decarbonize without risking production."
*End recording.*
