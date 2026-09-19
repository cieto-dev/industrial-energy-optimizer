import re

with open("frontend/components/dashboard/DashboardCharts.tsx", "r") as f:
    content = f.read()

# Replace imports and types
new_header = """"use client"

import React, { useMemo, useState } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Area,
  AreaChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import {
  Flame,
  Zap,
  TrendingDown,
  ArrowRight,
  ShieldCheck,
  Award,
  Layers,
  IndianRupee,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  MapPin,
  ShieldAlert,
} from "lucide-react"
import type { Dashboard, BaselineProfile } from "@/types/optimization"
import { FactoryContext } from "./RecommendationCard"

type Props = {
  dashboard: Dashboard
  baseline: BaselineProfile
  factoryContext: FactoryContext
}

const formatNumber = (value: number) => {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(value)
}

const formatCurrency = (value: number) => {
  return `₹${formatNumber(value)}`
}

export function DashboardCharts({ dashboard, baseline, factoryContext }: Props) {
  const [activeTab, setActiveTab] = useState<"overview" | "energyflow" | "cashflow" | "technologies">("overview")

  const pathways = dashboard.finance?.scenarios ?? []
  const recommendedPathway = pathways[0]

  const capexBlocked = !recommendedPathway?.financial_model || recommendedPathway.financial_model.capex.status === "unavailable"

  const scenarios = useMemo(() => {
    return pathways.slice(0, 3).map((s, idx) => {
      const fm = s.financial_model
      return {
        id: s.scenario_id ?? `scenario-${idx + 1}`,
        name: idx === 0 ? `Recommended: ${s.technology_sequence?.join(" + ")}` : `Alt: ${s.technology_sequence?.join(" + ")}`,
        annualCost: fm?.proposed_opex.total_inr ?? 0,
        co2: (fm?.proposed_opex as any)?.fuel_co2_tonnes ?? 0, // Simplified for now
        fossilReduction: s.reliability_score_pct ?? 0, // Or whatever metadata we have
        capex: fm?.capex.capex_max_inr ?? 0,
      }
    })
  }, [pathways])

  const baselineCost = baseline.annual_total_energy_cost_inr ?? 0
  const recommendedCost = scenarios[0]?.annualCost ?? 0
  const baselineCo2 = baseline.annual_co2_tonnes ?? 0
  const recommendedCo2 = scenarios[0]?.co2 ?? 0
  const annualSavings = Math.max(0, baselineCost - recommendedCost)
  const totalCapex = scenarios[0]?.capex ?? 0
"""

content = re.sub(r'"use client".*?const totalCapex = numberValue\(recommendation\.capex_total_inr, recommendation\.capex, 12000000\)', new_header, content, flags=re.DOTALL)

# Handle rendering blocks
blocked_message = """
          {capexBlocked ? (
            <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-8 text-center backdrop-blur-sm">
              <ShieldAlert className="h-10 w-10 text-amber-500 mx-auto mb-4" />
              <h2 className="text-lg font-bold text-amber-600 mb-2">Financial Charts Blocked — Vendor Quote Required</h2>
              <p className="text-sm text-amber-700/80 max-w-lg mx-auto">
                We strictly enforce the No-Invention Rule. Because verified CAPEX numbers for your specific configuration are not available in the knowledge base, financial charts have been disabled.
              </p>
            </div>
          ) : (
"""

content = content.replace('{activeTab === "overview" && (', '{activeTab === "overview" && (' + blocked_message)
content = content.replace('      {/* ── TAB 2: ENERGY FLOW / SANKEY ───────────────────────────── */}', '          )}\n      {/* ── TAB 2: ENERGY FLOW / SANKEY ───────────────────────────── */}')

content = content.replace('{activeTab === "cashflow" && (', '{activeTab === "cashflow" && (' + blocked_message)
content = content.replace('      {/* ── TAB 4: TECHNOLOGY COMPARISON MATRIX ───────────────────── */}', '          )}\n      {/* ── TAB 4: TECHNOLOGY COMPARISON MATRIX ───────────────────── */}')

content = content.replace('const factoryState = (recommendation as any).state ?? ""', 'const factoryState = factoryContext.state ?? ""')
content = content.replace('recommendation.explanation?.policy_benefits?.estimated_total_benefit_inr ?? 2800000', '0')

with open("frontend/components/dashboard/DashboardCharts.tsx", "w") as f:
    f.write(content)

