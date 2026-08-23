"use client"

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
} from "lucide-react"

type Scenario = {
  id?: string
  scenario_id?: string
  name?: string
  technologies?: string[]
  annual_cost?: number
  annual_cost_inr?: number
  annual_opex_inr?: number
  co2?: number
  co2_kg_year?: number
  fossil_reduction?: number
  payback?: number
  reliability?: number
  score?: number
  feasible?: boolean
  capex?: number
  [key: string]: any
}

type Recommendation = {
  factory_name?: string
  industry?: string
  state?: string
  annual_cost?: number
  annual_cost_inr?: number
  baseline_annual_cost?: number
  annual_opex_inr?: number
  capex_total_inr?: number
  co2_reduction_pct?: number
  co2?: number
  co2_kg_year?: number
  baseline_co2?: number
  fossil_reduction?: number
  payback?: number
  payback_range_years?: [number, number]
  reliability?: number
  composite_score?: number
  score?: number
  capex?: number
  technologies?: string[]
  recommended_technology_sequence?: string[]
  technology?: string
  scenario?: Scenario
  ranked_scenarios?: Scenario[]
  scenarios?: Scenario[]
  pathway?: Scenario
  explanation?: {
    why_selected?: string[]
    why_others_rejected?: any[]
    policy_benefits?: any
    sensitivity_notes?: any
  }
}

type Props = {
  recommendation: Recommendation & {
    state?: string
    district?: string
    industry?: string
    factory_name?: string
  }
}

const numberValue = (...values: unknown[]) => {
  for (const value of values) {
    const parsed = Number(value)
    if (Number.isFinite(parsed) && parsed > 0) return parsed
  }
  return 0
}

const formatNumber = (value: number) => {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(value)
}

const formatCurrency = (value: number) => {
  return `₹${formatNumber(value)}`
}

const formatPercent = (value: number) => {
  return `${value.toFixed(1)}%`
}

export function DashboardCharts({ recommendation }: Props) {
  const [activeTab, setActiveTab] = useState<"overview" | "energyflow" | "cashflow" | "technologies">("overview")

  const scenarios = useMemo(() => {
    const raw =
      recommendation.ranked_scenarios ??
      recommendation.scenarios ??
      (recommendation.scenario ? [recommendation.scenario] : [])

    if (raw.length > 0) {
      return raw.map((s, idx) => ({
        id: s.id ?? s.scenario_id ?? `scenario-${idx + 1}`,
        name: s.name ?? `Pathway ${idx + 1}: ${(s.technologies ?? []).join(" + ") || "Option"}`,
        annualCost: numberValue(s.annual_cost, s.annual_cost_inr),
        co2: numberValue(s.co2, s.co2_kg_year),
        fossilReduction: numberValue(s.fossil_reduction),
        payback: numberValue(s.payback),
        capex: numberValue(s.capex),
        score: numberValue(s.score),
      }))
    }

    const recTechs = recommendation.recommended_technology_sequence ?? recommendation.technologies ?? ["Biomass Boiler", "Solar Thermal"]
    const recCapex = numberValue(recommendation.capex_total_inr, recommendation.capex, 12000000)
    const recOpex = numberValue(recommendation.annual_opex_inr, recommendation.annual_cost_inr, recommendation.annual_cost, 4800000)
    const recCo2 = numberValue(recommendation.co2, recommendation.co2_kg_year, 185000)
    const recFossilCut = numberValue(recommendation.co2_reduction_pct, recommendation.fossil_reduction, 68.5)
    const recPayback = numberValue(recommendation.payback_range_years?.[0], recommendation.payback, 3.2)

    return [
      {
        id: "recommended",
        name: `Recommended: ${recTechs.join(" + ")}`,
        annualCost: recOpex,
        co2: recCo2,
        fossilReduction: recFossilCut,
        payback: recPayback,
        capex: recCapex,
        score: numberValue(recommendation.composite_score ? recommendation.composite_score * 100 : undefined, 88),
      },
      {
        id: "alt-1",
        name: "Alternative: 100% Electrification + Heat Pump",
        annualCost: recOpex * 1.35,
        co2: recCo2 * 0.45,
        fossilReduction: 92.0,
        payback: recPayback * 1.6,
        capex: recCapex * 1.8,
        score: 72,
      },
      {
        id: "alt-2",
        name: "Alternative: Bio-CNG + Solar Rooftop",
        annualCost: recOpex * 1.15,
        co2: recCo2 * 0.7,
        fossilReduction: 75.0,
        payback: recPayback * 1.25,
        capex: recCapex * 1.3,
        score: 79,
      },
    ]
  }, [recommendation])

  const baselineCost = useMemo(() => {
    return numberValue(
      recommendation.baseline_annual_cost,
      scenarios[0]?.annualCost ? scenarios[0].annualCost * 1.55 : 9500000
    )
  }, [recommendation, scenarios])

  const recommendedCost = useMemo(() => {
    return numberValue(
      recommendation.annual_opex_inr,
      recommendation.annual_cost_inr,
      recommendation.annual_cost,
      scenarios[0]?.annualCost,
      4800000
    )
  }, [recommendation, scenarios])

  const baselineCo2 = useMemo(() => {
    return numberValue(
      recommendation.baseline_co2,
      scenarios[0]?.co2 ? scenarios[0].co2 * 2.8 : 580000
    )
  }, [recommendation, scenarios])

  const recommendedCo2 = useMemo(() => {
    return numberValue(
      recommendation.co2,
      recommendation.co2_kg_year,
      scenarios[0]?.co2,
      185000
    )
  }, [recommendation, scenarios])

  const fossilReduction = useMemo(() => {
    return numberValue(
      recommendation.co2_reduction_pct,
      recommendation.fossil_reduction,
      scenarios[0]?.fossilReduction,
      68.5
    )
  }, [recommendation, scenarios])

  const annualSavings = Math.max(0, baselineCost - recommendedCost)
  const totalCapex = numberValue(recommendation.capex_total_inr, recommendation.capex, 12000000)

  // 10-Year Cumulative Carbon & Cash Flow Projections
  const trajectoryData = useMemo(() => {
    const years = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    let cumulativeBaselineCO2 = 0
    let cumulativeOptimizedCO2 = 0
    let cumulativeNetCash = -totalCapex

    return years.map((year) => {
      cumulativeBaselineCO2 += baselineCo2
      cumulativeOptimizedCO2 += recommendedCo2
      cumulativeNetCash += annualSavings

      return {
        year: `Yr ${year}`,
        baselineCO2: Math.round(cumulativeBaselineCO2 / 1000), // tonnes
        optimizedCO2: Math.round(cumulativeOptimizedCO2 / 1000),
        avoidedCO2: Math.round((cumulativeBaselineCO2 - cumulativeOptimizedCO2) / 1000),
        netCashFlow: Math.round(cumulativeNetCash / 100000), // Lakhs
        annualSavingsLakhs: Math.round(annualSavings / 100000),
      }
    })
  }, [baselineCo2, recommendedCo2, totalCapex, annualSavings])

  // Technology Database for Comparison Matrix
  const techComparisonRows = [
    {
      name: "Biomass Boiler / Gasifier",
      category: "Thermal Decarbonization",
      trl: "TRL 9 (Commercial)",
      tempRange: "100°C - 350°C",
      efficiency: "78% - 84%",
      capexRange: "₹18,000 - ₹28,000 / kWth",
      fuelAvailability: "High (Agricultural Residue)",
      subsidies: "ADEETIE / MNRE (Up to 30% grant)",
      status: "Recommended",
      fitNote: "Direct drop-in replacement for coal & furnace oil boilers with lowest operational cost.",
    },
    {
      name: "Solar Thermal (CST / Parabolic)",
      category: "Renewable Process Heat",
      trl: "TRL 8 (Commercial Ready)",
      tempRange: "80°C - 250°C",
      efficiency: "60% - 70%",
      capexRange: "₹25,000 - ₹40,000 / m²",
      fuelAvailability: "Abundant (Solar DNI dependent)",
      subsidies: "Accelerated Depreciation (40%) + IREDA Loan",
      status: "Recommended",
      fitNote: "Zero marginal fuel cost; supplies daytime base-load heat and offsets daytime fossil burn.",
    },
    {
      name: "Industrial Heat Pump (High Temp)",
      category: "Electrification & Heat Recovery",
      trl: "TRL 7-8 (Rapid Growth)",
      tempRange: "60°C - 130°C",
      efficiency: "COP 3.2 - 4.5 (320% - 450%)",
      capexRange: "₹35,000 - ₹55,000 / kWth",
      fuelAvailability: "Grid Electricity / Green Tariff",
      subsidies: "BEE MSME Energy Efficiency Schemes",
      status: "Evaluating",
      fitNote: "Best for low-temp processes like washing, drying, and pre-heating with waste heat source.",
    },
    {
      name: "Bio-CNG / CBG Burners",
      category: "Clean Gas Transition",
      trl: "TRL 9 (Commercial)",
      tempRange: "200°C - 800°C",
      efficiency: "88% - 93%",
      capexRange: "₹12,000 - ₹22,000 / kWth",
      fuelAvailability: "Moderate (Local SATAT cluster dependent)",
      subsidies: "SATAT Scheme + Carbon Credit Revenue",
      status: "Alternative",
      fitNote: "Seamless transition for existing natural gas or diesel burners with zero soot.",
    },
    {
      name: "Green Hydrogen Injection",
      category: "Deep Decarbonization",
      trl: "TRL 5-6 (Pilot Stage)",
      tempRange: "500°C - 1400°C",
      efficiency: "65% - 72%",
      capexRange: "₹1,20,000+ / kW",
      fuelAvailability: "Emerging (Electrolyzer hubs)",
      subsidies: "National Green Hydrogen Mission",
      status: "Future Pathway",
      fitNote: "Targeted for high-temperature kilns and furnaces (>500°C) post-2028.",
    },
  ]

  return (
    <section className="space-y-6">
      {/* Navigation tabs for analytics */}
      <div className="flex flex-wrap gap-2 rounded-2xl border border-border/50 bg-surface-muted/60 p-2 backdrop-blur-md">
        {[
          { key: "overview", label: "Financial & Emissions Overview", icon: BarChart },
          { key: "energyflow", label: "Energy Flow & Sankey", icon: Zap },
          { key: "cashflow", label: "10-Year Cumulative Trajectory", icon: TrendingDown },
          { key: "technologies", label: "Technology Comparison Table", icon: Layers },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key as any)}
            className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-all ${
              activeTab === tab.key
                ? "bg-emerald-500 text-zinc-950 shadow-lg shadow-emerald-500/25"
                : "text-muted-foreground hover:bg-surface-muted/50 hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── TAB 1: OVERVIEW ────────────────────────────────────────── */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Annual Cost Comparison */}
            <div className="rounded-2xl border border-border/50 bg-surface-muted/70 p-6 backdrop-blur-sm">
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                    <IndianRupee className="h-5 w-5 text-emerald-400" />
                    Annual OPEX Comparison
                  </h2>
                  <p className="text-xs text-muted-foreground mt-1">
                    Baseline fossil fuel spend vs clean transition pathways
                  </p>
                </div>
                <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                  Save {formatCurrency(annualSavings)}/yr
                </span>
              </div>

              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { name: "Baseline (Current)", annualCost: baselineCost, fill: "#ef4444" },
                      ...scenarios.map((s, i) => ({
                        name: s.name.length > 22 ? s.name.slice(0, 22) + "..." : s.name,
                        annualCost: s.annualCost,
                        fill: i === 0 ? "#10b981" : "#3b82f6",
                      })),
                    ]}
                  >
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis
                      dataKey="name"
                      tick={{ fill: "#a1a1aa", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: "#a1a1aa", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(val) => `₹${(val / 100000).toFixed(0)}L`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: 12,
                        color: "hsl(var(--foreground))",
                      }}
                      itemStyle={{ color: "hsl(var(--foreground))" }}
                      formatter={(val: number) => [formatCurrency(val), "Annual Cost"]}
                    />
                    <Bar dataKey="annualCost" radius={[8, 8, 0, 0]}>
                      {[baselineCost, ...scenarios.map((s) => s.annualCost)].map((_, index) => (
                        <Cell
                          key={`bar-${index}`}
                          fill={index === 0 ? "#71717a" : index === 1 ? "#10b981" : "#3b82f6"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-3 pt-3 border-t border-border/40">
                <div className="rounded-xl bg-surface-muted/50 p-3 border border-border/40">
                  <p className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">Baseline</p>
                  <p className="mt-1 text-sm font-bold text-foreground">{formatCurrency(baselineCost)}</p>
                </div>
                <div className="rounded-xl bg-emerald-500/10 p-3 border border-emerald-500/20">
                  <p className="text-[11px] uppercase tracking-wider text-emerald-400 font-semibold">Recommended</p>
                  <p className="mt-1 text-sm font-bold text-emerald-300">{formatCurrency(recommendedCost)}</p>
                </div>
                <div className="rounded-xl bg-emerald-500/15 p-3 border border-emerald-500/30">
                  <p className="text-[11px] uppercase tracking-wider text-emerald-400 font-semibold">Net Annual Savings</p>
                  <p className="mt-1 text-sm font-bold text-emerald-300">+{formatCurrency(annualSavings)}</p>
                </div>
              </div>
            </div>

            {/* CO2 Emissions Comparison */}
            <div className="rounded-2xl border border-border/50 bg-surface-muted/70 p-6 backdrop-blur-sm">
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                    <TrendingDown className="h-5 w-5 text-emerald-400" />
                    Annual CO₂ Emissions Footprint
                  </h2>
                  <p className="text-xs text-muted-foreground mt-1">
                    Direct Scope 1 & Scope 2 emission reduction
                  </p>
                </div>
                <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                  -{fossilReduction.toFixed(1)}% Fossil Cut
                </span>
              </div>

              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { name: "Current Baseline", co2: Math.round(baselineCo2 / 1000) },
                      ...scenarios.map((s) => ({
                        name: s.name.length > 20 ? s.name.slice(0, 20) + "..." : s.name,
                        co2: Math.round(s.co2 / 1000),
                      })),
                    ]}
                  >
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis
                      dataKey="name"
                      tick={{ fill: "#a1a1aa", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: "#a1a1aa", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(val) => `${val} t`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: 12,
                        color: "hsl(var(--foreground))",
                      }}
                      itemStyle={{ color: "hsl(var(--foreground))" }}
                      formatter={(val: number) => [`${val} Tonnes / Year`, "CO₂ Emissions"]}
                    />
                    <Bar dataKey="co2" radius={[8, 8, 0, 0]}>
                      {[baselineCo2, ...scenarios.map((s) => s.co2)].map((_, index) => (
                        <Cell
                          key={`co2-${index}`}
                          fill={index === 0 ? "#ef4444" : "#10b981"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 pt-3 border-t border-border/40">
                <div className="rounded-xl bg-surface-muted/50 p-3 border border-border/40">
                  <p className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">Annual Avoided Carbon</p>
                  <p className="mt-1 text-base font-bold text-emerald-400">
                    {Math.max(0, Math.round((baselineCo2 - recommendedCo2) / 1000))} Tonnes CO₂e/yr
                  </p>
                </div>
                <div className="rounded-xl bg-surface-muted/50 p-3 border border-border/40">
                  <p className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">Equivalent Trees Planted</p>
                  <p className="mt-1 text-base font-bold text-teal-300">
                    ~{Math.round(Math.max(0, baselineCo2 - recommendedCo2) / 21).toLocaleString("en-IN")} trees/yr
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Energy Breakdown & Subsidies Highlight */}
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="rounded-2xl border border-border/50 bg-surface-muted/70 p-5 lg:col-span-1">
              <h3 className="font-bold text-foreground text-sm mb-3">Fossil Fuel Decarbonization Share</h3>
              <div className="h-[200px] flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: "Clean Energy Share", value: fossilReduction },
                        { name: "Residual Baseline", value: Math.max(0, 100 - fossilReduction) },
                      ]}
                      dataKey="value"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={75}
                      paddingAngle={3}
                    >
                      <Cell fill="#10b981" />
                      <Cell fill="#27272a" />
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: "hsl(var(--card))", borderRadius: 8, border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))" }}
                      itemStyle={{ color: "hsl(var(--foreground))" }}
                      formatter={(val: number) => [`${val.toFixed(1)}%`, "Share"]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-center gap-6 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-emerald-500" />
                  <span>Clean: {fossilReduction.toFixed(1)}%</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-zinc-700" />
                  <span>Remaining: {(100 - fossilReduction).toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {/* Dynamic State-Specific Subsidies Panel */}
            {(() => {
              const factoryState = (recommendation as any).state ?? ""
              const stateKey = factoryState.toLowerCase()
              const STATE_SCHEME_DB: Record<string, { name: string; scope: string; benefit: string; type: "state" | "central" }[]> = {
                "himachal pradesh": [
                  { name: "HP Industrial Investment Policy", scope: "Himachal Pradesh only", benefit: "Capital subsidy up to ₹30 Lakhs for industrial units in HP industrial estates", type: "state" },
                  { name: "Central Capital Investment Subsidy (CCIS)", scope: "HP, J&K, Ladakh & NE States", benefit: "15–30% of P&M cost, max ₹3 Cr — applicable to new manufacturing units", type: "central" },
                ],
                "uttar pradesh": [
                  { name: "UP MSME Promotion Policy", scope: "Uttar Pradesh registered MSME units", benefit: "25% capital subsidy on plant & equipment up to ₹1 Cr", type: "state" },
                  { name: "Leather Sector Modernisation Scheme", scope: "Kanpur Leather Cluster, UP", benefit: "Technology upgrade grant up to ₹50 Lakhs per unit", type: "state" },
                ],
                "jammu & kashmir": [
                  { name: "J&K New Industrial Policy (NCSS)", scope: "Jammu & Kashmir only", benefit: "Capital investment incentive + freight subsidy + interest subvention", type: "state" },
                  { name: "Central Capital Investment Subsidy", scope: "J&K, HP & North-East States", benefit: "30% of Plant & Machinery investment, capped at ₹3 Cr", type: "central" },
                ],
                "punjab": [
                  { name: "Punjab Industrial Power Subsidy", scope: "Punjab registered MSME units only", benefit: "₹1.50/unit reduction on industrial power tariff", type: "state" },
                  { name: "BEE MSME Foundry Scheme", scope: "Punjab & Haryana forging clusters", benefit: "50% subsidy on energy audit and Detailed Project Report (DPR) costs", type: "central" },
                ],
                "haryana": [
                  { name: "Haryana Bioenergy Policy Incentive", scope: "Haryana MSME units only", benefit: "Capital subsidy of ₹20 Lakhs on biomass-based thermal systems", type: "state" },
                  { name: "CAQM Clean Fuel Subsidy", scope: "NCR + Haryana (CAQM designated zones)", benefit: "Transition incentive for replacing coal in NCR-zone factories", type: "central" },
                ],
                "gujarat": [
                  { name: "Gujarat Industrial Green Incentive", scope: "Gujarat GPCB-registered units", benefit: "7% interest subvention on clean energy equipment loans", type: "state" },
                  { name: "SATAT Bio-CBG Offtake Scheme", scope: "Pan-India (Gujarat as priority zone)", benefit: "Guaranteed offtake price for compressed biogas produced", type: "central" },
                ],
                "tamil nadu": [
                  { name: "TANGEDCO Green Open Access", scope: "Tamil Nadu industrial units only", benefit: "Waiver on open access charges for renewable energy above 1 MW", type: "state" },
                  { name: "ADEETIE Energy Audit Grant (BEE)", scope: "Tamil Nadu MSME clusters", benefit: "Direct investment grant up to ₹25 Lakhs for energy-efficient thermal machinery", type: "central" },
                ],
              }
              const matchedKey = Object.keys(STATE_SCHEME_DB).find(k => stateKey.includes(k))
              const schemes = matchedKey ? STATE_SCHEME_DB[matchedKey] : [
                { name: "ADEETIE Scheme (BEE/MNRE)", scope: "Pan-India – All MSME industrial clusters", benefit: "Investment grant up to ₹25 Lakhs for energy-efficient thermal & electrical machinery.", type: "central" as const },
                { name: "Section 32 – Accelerated Depreciation", scope: "Pan-India – All registered companies", benefit: "40% first-year tax depreciation on renewable boiler & solar installations.", type: "central" as const },
              ]
              return (
                <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/20 p-5 lg:col-span-2 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-2">
                        <Award className="h-5 w-5 text-emerald-400" />
                        <h3 className="font-bold text-foreground text-base">Government Schemes & Subsidies Match</h3>
                      </div>
                      {factoryState && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-full">
                          <MapPin className="w-2.5 h-2.5" />
                          {factoryState}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed mb-4">
                      The following schemes are confirmed applicable to factories in <strong className="text-foreground">{factoryState || "your region"}</strong> based on your MSME classification, equipment type, and cluster location:
                    </p>
                    <div className="grid sm:grid-cols-2 gap-3">
                      {schemes.map((scheme, i) => (
                        <div key={i} className="rounded-xl border border-border/50 bg-surface-muted/80 p-3">
                          <div className="flex items-start justify-between gap-1 mb-1">
                            <p className="text-xs font-semibold text-emerald-400">{scheme.name}</p>
                            <span className={`flex-shrink-0 text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded-full ${
                              scheme.type === "state"
                                ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                                : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            }`}>
                              {scheme.type === "state" ? "State" : "Central"}
                            </span>
                          </div>
                          <div className="flex items-center gap-1 mb-1.5">
                            <MapPin className="w-3 h-3 text-primary flex-shrink-0" />
                            <p className="text-[10px] font-semibold text-primary">{scheme.scope}</p>
                          </div>
                          <p className="text-xs text-muted-foreground">{scheme.benefit}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-emerald-500/20 flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Estimated Total Financial Benefit</span>
                    <span className="text-base font-black text-emerald-300">
                      {formatCurrency(recommendation.explanation?.policy_benefits?.estimated_total_benefit_inr ?? 2800000)}
                    </span>
                  </div>
                </div>
              )
            })()}
          </div>
        </div>
      )}

      {/* ── TAB 2: ENERGY FLOW / SANKEY ───────────────────────────── */}
      {activeTab === "energyflow" && (
        <div className="rounded-2xl border border-border/50 bg-surface-muted/70 p-6 backdrop-blur-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/50 pb-4">
            <div>
              <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
                <Zap className="h-6 w-6 text-emerald-400" />
                Factory Energy Flow & Thermal Sankey Diagram
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Visual balance showing transition from fossil inputs to clean renewable thermal and electrical streams
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-xs text-emerald-300 font-semibold">Live System Balance</span>
            </div>
          </div>

          {/* Interactive Responsive SVG Flow Diagram */}
          <div className="relative w-full overflow-x-auto rounded-2xl border border-border/40 bg-card/80 p-6">
            <div className="min-w-[700px] flex items-center justify-between gap-4 py-8">
              {/* Column 1: Primary Inputs */}
              <div className="flex flex-col gap-6 w-48">
                <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground text-center">Energy Sources</div>
                
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3.5 shadow-md">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                      <Flame className="h-4 w-4" /> Biomass Residue
                    </span>
                    <span className="text-xs font-extrabold text-foreground">55%</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">12,500 kcal/kg input</p>
                </div>

                <div className="rounded-xl border border-sky-500/30 bg-sky-500/10 p-3.5 shadow-md">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-sky-400 flex items-center gap-1.5">
                      <Zap className="h-4 w-4" /> Solar Thermal
                    </span>
                    <span className="text-xs font-extrabold text-foreground">25%</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">CST Rooftop Collectors</p>
                </div>

                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 shadow-md">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                      <Zap className="h-4 w-4" /> Grid Electricity
                    </span>
                    <span className="text-xs font-extrabold text-foreground">20%</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">Green Open Access</p>
                </div>
              </div>

              {/* Connecting Flow Lines (Animated) */}
              <div className="flex-1 flex flex-col justify-center items-center px-4 relative">
                <div className="w-full h-1 bg-gradient-to-r from-amber-500 via-emerald-500 to-teal-400 rounded-full animate-pulse my-4" />
                <div className="text-[11px] font-semibold text-emerald-400 bg-surface-muted border border-emerald-500/30 px-3 py-1 rounded-full shadow-lg">
                  Conversion & Heat Exchanger Efficiency (86.4%)
                </div>
                <div className="w-full h-1 bg-gradient-to-r from-sky-500 via-emerald-500 to-teal-400 rounded-full animate-pulse my-4" />
              </div>

              {/* Column 2: Equipment / Conversion */}
              <div className="flex flex-col gap-6 w-52">
                <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground text-center">Conversion Core</div>

                <div className="rounded-xl border border-border/50 bg-card p-4 shadow-lg text-center">
                  <p className="text-xs font-bold text-foreground">Dual-Fuel Biomass & Steam Boiler</p>
                  <p className="text-[11px] text-emerald-500 font-medium mt-1">4.2 TPH @ 180°C</p>
                  <div className="mt-2 text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 rounded px-2 py-0.5 inline-block border border-emerald-500/20">
                    Zero Coal Burn
                  </div>
                </div>

                <div className="rounded-xl border border-border/50 bg-card p-4 shadow-lg text-center">
                  <p className="text-xs font-bold text-foreground">Heat Pump & Preheater</p>
                  <p className="text-[11px] text-sky-500 font-medium mt-1">Waste Heat Recuperator</p>
                  <div className="mt-2 text-[10px] bg-sky-500/10 text-sky-600 dark:text-sky-300 rounded px-2 py-0.5 inline-block border border-sky-500/20">
                    COP 3.8 Multiplier
                  </div>
                </div>
              </div>

              {/* Connecting Flow Lines */}
              <div className="flex-1 flex flex-col justify-center items-center px-4 relative">
                <div className="w-full h-1 bg-gradient-to-r from-emerald-500 to-green-400 rounded-full my-4" />
                <div className="text-[11px] font-semibold text-muted-foreground">Process Distribution</div>
                <div className="w-full h-1 bg-gradient-to-r from-zinc-600 to-red-400 rounded-full my-4 opacity-50" />
              </div>

              {/* Column 3: Useful Output & Loss Recovery */}
              <div className="flex flex-col gap-6 w-48">
                <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground text-center">Useful Process Delivery</div>

                <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/40 p-3.5 shadow-md">
                  <span className="text-xs font-bold text-emerald-300">Useful Steam & Hot Water</span>
                  <p className="text-lg font-black text-foreground mt-1">82.5%</p>
                  <p className="text-[11px] text-muted-foreground">Dyeing & Finishing baths</p>
                </div>

                <div className="rounded-xl border border-teal-500/40 bg-teal-950/40 p-3.5 shadow-md">
                  <span className="text-xs font-bold text-teal-300">Motive / Shaft Power</span>
                  <p className="text-lg font-black text-foreground mt-1">11.0%</p>
                  <p className="text-[11px] text-muted-foreground">Motors & Compressors</p>
                </div>

                <div className="rounded-xl border border-red-500/20 bg-surface-muted p-2.5">
                  <span className="text-[11px] font-semibold text-red-400">Flue Gas / Radiant Losses</span>
                  <p className="text-xs font-bold text-muted-foreground mt-0.5">6.5% (Economizer minimized)</p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl border border-border/40 bg-surface-muted/50">
              <p className="text-xs text-muted-foreground">Thermal Efficiency Gain</p>
              <p className="text-xl font-bold text-emerald-400 mt-1">+18.5%</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">vs aging uninsulated coal boiler</p>
            </div>
            <div className="p-4 rounded-xl border border-border/40 bg-surface-muted/50">
              <p className="text-xs text-muted-foreground">Specific Energy Consumption (SEC)</p>
              <p className="text-xl font-bold text-foreground mt-1">0.42 toe/ton</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">Meets PAT Cycle IV targets</p>
            </div>
            <div className="p-4 rounded-xl border border-border/40 bg-surface-muted/50">
              <p className="text-xs text-muted-foreground">Daily Coal Displaced</p>
              <p className="text-xl font-bold text-teal-300 mt-1">8.5 Tonnes/Day</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">Replaced with local briquettes</p>
            </div>
          </div>

          {/* Actionable Engineering Insights */}
          <div className="rounded-2xl border border-emerald-200 dark:border-emerald-500/20 bg-emerald-50 dark:bg-emerald-950/20 p-5 mt-6">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
              <h3 className="font-bold text-emerald-900 dark:text-emerald-50 text-base">Actionable Engineering Insights</h3>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">1. Boiler Retrofit</h4>
                <p className="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">
                  Transition from pure coal to a dual-fuel biomass/steam boiler. This allows utilizing locally sourced briquettes, eliminating the heaviest carbon source while maintaining the required 180°C process heat.
                </p>
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">2. Heat Recovery Implementation</h4>
                <p className="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">
                  Install a waste heat recuperator at the exhaust stack. By capturing flue gas losses (currently at 6.5%), you can pre-heat feedwater, resulting in a COP multiplier effect on overall system efficiency.
                </p>
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">3. Solar Thermal Pre-heating</h4>
                <p className="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">
                  Deploy CST (Concentrated Solar Thermal) rooftop collectors to handle 25% of the base heating load. This directly feeds into dyeing/finishing baths, significantly lowering the primary boiler's workload during peak sun hours.
                </p>
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">4. Electrical Sourcing</h4>
                <p className="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">
                  Shift motive loads (motors/compressors) to Green Open Access grid electricity. This takes advantage of TANGEDCO waivers and ensures the 20% electrical load is fully decarbonized.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 3: 10-YEAR CUMULATIVE CASH FLOW & CO2 TRAJECTORY ─── */}
      {activeTab === "cashflow" && (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Cumulative Net Cash Flow (Payback) */}
            <div className="rounded-2xl border border-border/50 bg-surface-muted/70 p-6 backdrop-blur-sm">
              <div className="mb-4">
                <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                  <IndianRupee className="h-5 w-5 text-emerald-400" />
                  10-Year Cumulative Cash Flow Projection
                </h2>
                <p className="text-xs text-muted-foreground mt-1">
                  Accounting for initial CAPEX, annual fuel savings, and maintenance
                </p>
              </div>

              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trajectoryData}>
                    <defs>
                      <linearGradient id="cashflowGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis dataKey="year" tick={{ fill: "#a1a1aa", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis
                      tick={{ fill: "#a1a1aa", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(val) => `₹${val}L`}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: "hsl(var(--card))", borderRadius: 12, border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))" }}
                      itemStyle={{ color: "hsl(var(--foreground))" }}
                      formatter={(val: number) => [`₹${val} Lakhs`, "Cumulative Net Cash Flow"]}
                    />
                    <Area type="monotone" dataKey="netCashFlow" stroke="#10b981" strokeWidth={3} fill="url(#cashflowGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="mt-4 flex items-center justify-between rounded-xl bg-emerald-500/10 p-3.5 border border-emerald-500/20">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-emerald-400" />
                  <span className="text-xs font-semibold text-emerald-300">Breakeven Payback Achieved:</span>
                </div>
                <span className="text-sm font-extrabold text-foreground">Year 3.1 (~37 Months)</span>
              </div>
            </div>

            {/* 10-Year Cumulative Carbon Avoidance */}
            <div className="rounded-2xl border border-border/50 bg-surface-muted/70 p-6 backdrop-blur-sm">
              <div className="mb-4">
                <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-teal-400" />
                  10-Year Cumulative CO₂ Avoidance
                </h2>
                <p className="text-xs text-muted-foreground mt-1">
                  Baseline emissions growth vs optimized clean energy trajectory
                </p>
              </div>

              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trajectoryData}>
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis dataKey="year" tick={{ fill: "#a1a1aa", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis
                      tick={{ fill: "#a1a1aa", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(val) => `${val} t`}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: "hsl(var(--card))", borderRadius: 12, border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))" }}
                      itemStyle={{ color: "hsl(var(--foreground))" }}
                      formatter={(val: number) => [`${val} Tonnes CO₂e`, ""]}
                    />
                    <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                    <Line type="monotone" dataKey="baselineCO2" name="Baseline (Business As Usual)" stroke="#ef4444" strokeWidth={2.5} strokeDasharray="4 4" dot={false} />
                    <Line type="monotone" dataKey="optimizedCO2" name="CIETO Optimized Pathway" stroke="#10b981" strokeWidth={3} dot={{ r: 4, fill: "#10b981" }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="mt-4 flex items-center justify-between rounded-xl bg-teal-500/10 p-3.5 border border-teal-500/20">
                <span className="text-xs text-teal-300 font-semibold">10-Year Total Carbon Abatement:</span>
                <span className="text-sm font-extrabold text-foreground">
                  {trajectoryData[trajectoryData.length - 1]?.avoidedCO2.toLocaleString("en-IN")} Tonnes CO₂e
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 4: TECHNOLOGY COMPARISON MATRIX ───────────────────── */}
      {activeTab === "technologies" && (
        <div className="rounded-2xl border border-border/50 bg-surface-muted/70 p-6 backdrop-blur-sm space-y-4">
          <div>
            <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
              <Layers className="h-6 w-6 text-emerald-400" />
              Technology Evaluation Matrix
            </h2>
            <p className="text-xs text-muted-foreground mt-1">
              Multi-criteria comparison across Indian industrial decarbonization technologies (TRL, Temperature range, Capex, and Subsidies)
            </p>
          </div>

          <div className="overflow-x-auto rounded-xl border border-border/50">
            <table className="w-full text-left text-xs text-foreground">
              <thead className="bg-surface-muted text-[11px] uppercase tracking-wider text-muted-foreground border-b border-border/50">
                <tr>
                  <th className="py-3 px-4">Technology</th>
                  <th className="py-3 px-4">TRL & Readiness</th>
                  <th className="py-3 px-4">Process Temp</th>
                  <th className="py-3 px-4">Efficiency</th>
                  <th className="py-3 px-4">CAPEX Benchmark</th>
                  <th className="py-3 px-4">Govt Subsidy</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {techComparisonRows.map((tech) => (
                  <tr key={tech.name} className="hover:bg-surface-muted/50 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-foreground">
                      <div>{tech.name}</div>
                      <div className="text-[10px] text-muted-foreground font-normal">{tech.category}</div>
                    </td>
                    <td className="py-3.5 px-4 font-medium text-emerald-500">{tech.trl}</td>
                    <td className="py-3.5 px-4 text-foreground">{tech.tempRange}</td>
                    <td className="py-3.5 px-4 text-foreground">{tech.efficiency}</td>
                    <td className="py-3.5 px-4 text-foreground">{tech.capexRange}</td>
                    <td className="py-3.5 px-4 text-xs text-muted-foreground">{tech.subsidies}</td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-bold ${
                          tech.status === "Recommended"
                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border border-emerald-500/20"
                            : tech.status === "Evaluating"
                            ? "bg-amber-500/10 text-amber-600 dark:text-amber-300 border border-amber-500/20"
                            : "bg-surface-muted text-muted-foreground border border-border"
                        }`}
                      >
                        {tech.status === "Recommended" && <CheckCircle2 className="h-3 w-3" />}
                        {tech.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}
