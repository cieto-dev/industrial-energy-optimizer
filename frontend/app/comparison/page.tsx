"use client"

import React, { useState, useMemo } from "react"
import {
  ArrowRightLeft,
  MapPin,
  TrendingDown,
  Zap,
  Sun,
  Award,
  Factory
} from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from "recharts"

const INDUSTRIES = ["Textile", "Pharmaceuticals", "Leather", "Food & Beverage", "Ceramics", "Metal & Forging"]

// Mock Data for States
const STATE_PROFILES: Record<string, any> = {
  "Himachal Pradesh": {
    tariff: 5.5,
    biomassPrice: 4200,
    solarDni: 4.8,
    subsidyName: "Central Capital Investment Subsidy (CCIS)",
    subsidyPct: 30,
    capexModifier: 1.05,
  },
  "Uttar Pradesh": {
    tariff: 7.8,
    biomassPrice: 3800,
    solarDni: 5.2,
    subsidyName: "UP MSME Promotion Policy",
    subsidyPct: 25,
    capexModifier: 1.0,
  },
  "Jammu & Kashmir": {
    tariff: 4.2,
    biomassPrice: 4500,
    solarDni: 4.5,
    subsidyName: "J&K New Industrial Policy (NCSS)",
    subsidyPct: 30,
    capexModifier: 1.1,
  },
  "Tamil Nadu": {
    tariff: 8.2,
    biomassPrice: 3500,
    solarDni: 5.8,
    subsidyName: "TANGEDCO Green Open Access / ADEETIE",
    subsidyPct: 15,
    capexModifier: 0.95,
  },
  "Gujarat": {
    tariff: 7.2,
    biomassPrice: 3600,
    solarDni: 6.0,
    subsidyName: "Gujarat Industrial Green Incentive",
    subsidyPct: 20,
    capexModifier: 0.98,
  },
  "Punjab": {
    tariff: 6.5,
    biomassPrice: 3200,
    solarDni: 5.1,
    subsidyName: "Punjab Industrial Power Subsidy",
    subsidyPct: 15,
    capexModifier: 1.0,
  }
}

const STATES = Object.keys(STATE_PROFILES)

export default function StateComparisonPage() {
  const [industry, setIndustry] = useState("Textile")
  const [stateA, setStateA] = useState("Himachal Pradesh")
  const [stateB, setStateB] = useState("Tamil Nadu")

  const dataA = STATE_PROFILES[stateA]
  const dataB = STATE_PROFILES[stateB]

  // Base factory metrics (pre-state adjustments)
  const baseCapex = 25000000 // 2.5 Cr
  const baseEnergyDemandMWh = 12000 // Annual energy

  const calcMetrics = (data: any) => {
    const grossCapex = baseCapex * data.capexModifier
    const subsidyAmount = grossCapex * (data.subsidyPct / 100)
    const netCapex = grossCapex - subsidyAmount

    // Rough OPEX calculation based on local prices
    const gridOpex = (baseEnergyDemandMWh * 0.3 * 1000) * data.tariff
    const thermalOpex = (baseEnergyDemandMWh * 0.7 * 1000 / 4) * (data.biomassPrice / 1000)
    const totalOpex = gridOpex + thermalOpex
    
    // Baseline OPEX assuming diesel/coal
    const baselineOpex = baseEnergyDemandMWh * 4500
    const annualSavings = baselineOpex - totalOpex

    const payback = netCapex / annualSavings

    return { grossCapex, subsidyAmount, netCapex, totalOpex, annualSavings, payback }
  }

  const metricsA = calcMetrics(dataA)
  const metricsB = calcMetrics(dataB)

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v)

  const chartData = [
    {
      name: "Gross CAPEX",
      [stateA]: metricsA.grossCapex,
      [stateB]: metricsB.grossCapex,
    },
    {
      name: "Net CAPEX (After Subsidy)",
      [stateA]: metricsA.netCapex,
      [stateB]: metricsB.netCapex,
    },
    {
      name: "Annual OPEX",
      [stateA]: metricsA.totalOpex,
      [stateB]: metricsB.totalOpex,
    },
    {
      name: "Annual Savings",
      [stateA]: metricsA.annualSavings,
      [stateB]: metricsB.annualSavings,
    },
  ]

  return (
    <main className="min-h-full bg-zinc-950 p-4 text-white sm:p-6 pb-20">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <section className="flex flex-col gap-4 border-b border-white/10 pb-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/10 px-3 py-1 text-xs font-medium text-sky-300">
              <ArrowRightLeft className="h-3.5 w-3.5" />
              Geographical Impact Analysis
            </div>

            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
              State-by-State Comparison
            </h1>

            <p className="mt-2 text-sm text-zinc-400 sm:text-base">
              Analyze how regional policies, energy tariffs, and climate data impact the financial viability of decarbonizing identical factories.
            </p>
          </div>
        </section>

        {/* Controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-zinc-900/50 p-6 rounded-2xl border border-white/5">
          <div>
            <label className="text-xs font-bold uppercase tracking-widest text-zinc-500 mb-2 block">Factory Type</label>
            <div className="relative">
              <Factory className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full appearance-none rounded-xl border border-white/10 bg-zinc-950 py-3 pl-10 pr-4 text-sm font-medium text-white outline-none focus:border-emerald-500"
              >
                {INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs font-bold uppercase tracking-widest text-zinc-500 mb-2 block">State A</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-400" />
              <select
                value={stateA}
                onChange={(e) => setStateA(e.target.value)}
                className="w-full appearance-none rounded-xl border border-white/10 bg-zinc-950 py-3 pl-10 pr-4 text-sm font-medium text-white outline-none focus:border-emerald-500"
              >
                {STATES.map(s => <option key={s} value={s} disabled={s === stateB}>{s}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs font-bold uppercase tracking-widest text-zinc-500 mb-2 block">State B</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-blue-400" />
              <select
                value={stateB}
                onChange={(e) => setStateB(e.target.value)}
                className="w-full appearance-none rounded-xl border border-white/10 bg-zinc-950 py-3 pl-10 pr-4 text-sm font-medium text-white outline-none focus:border-blue-500"
              >
                {STATES.map(s => <option key={s} value={s} disabled={s === stateA}>{s}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Comparison Board */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* State A Panel */}
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/10 overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-emerald-500"></div>
            <div className="p-6 border-b border-emerald-500/10 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <MapPin className="text-emerald-500 h-6 w-6" />
                {stateA}
              </h2>
              <span className="text-emerald-400 text-sm font-semibold">{industry}</span>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-zinc-900/80 p-4 rounded-xl border border-white/5">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1.5 mb-1"><Zap className="h-3 w-3" /> Grid Tariff</p>
                  <p className="text-xl font-bold text-white">₹{dataA.tariff.toFixed(2)}<span className="text-sm font-medium text-zinc-500">/kWh</span></p>
                </div>
                <div className="bg-zinc-900/80 p-4 rounded-xl border border-white/5">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1.5 mb-1"><Sun className="h-3 w-3" /> Solar DNI</p>
                  <p className="text-xl font-bold text-white">{dataA.solarDni}<span className="text-sm font-medium text-zinc-500"> kWh/m²</span></p>
                </div>
                <div className="bg-zinc-900/80 p-4 rounded-xl border border-white/5 col-span-2">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1.5 mb-1"><Award className="h-3 w-3" /> Primary Subsidy</p>
                  <p className="text-base font-bold text-emerald-300">{dataA.subsidyName}</p>
                  <p className="text-sm text-zinc-400 mt-1">Up to {dataA.subsidyPct}% CAPEX grant</p>
                </div>
              </div>

              <div className="pt-6 border-t border-white/10 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400 text-sm">Net CAPEX</span>
                  <span className="text-lg font-bold text-white">{formatCurrency(metricsA.netCapex)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400 text-sm">Annual OPEX</span>
                  <span className="text-lg font-bold text-white">{formatCurrency(metricsA.totalOpex)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                  <span className="text-emerald-300 font-semibold">Final Payback</span>
                  <span className="text-2xl font-black text-emerald-400">{metricsA.payback.toFixed(1)} Years</span>
                </div>
              </div>
            </div>
          </div>

          {/* State B Panel */}
          <div className="rounded-2xl border border-blue-500/20 bg-blue-950/10 overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-blue-500"></div>
            <div className="p-6 border-b border-blue-500/10 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <MapPin className="text-blue-500 h-6 w-6" />
                {stateB}
              </h2>
              <span className="text-blue-400 text-sm font-semibold">{industry}</span>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-zinc-900/80 p-4 rounded-xl border border-white/5">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1.5 mb-1"><Zap className="h-3 w-3" /> Grid Tariff</p>
                  <p className="text-xl font-bold text-white">₹{dataB.tariff.toFixed(2)}<span className="text-sm font-medium text-zinc-500">/kWh</span></p>
                </div>
                <div className="bg-zinc-900/80 p-4 rounded-xl border border-white/5">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1.5 mb-1"><Sun className="h-3 w-3" /> Solar DNI</p>
                  <p className="text-xl font-bold text-white">{dataB.solarDni}<span className="text-sm font-medium text-zinc-500"> kWh/m²</span></p>
                </div>
                <div className="bg-zinc-900/80 p-4 rounded-xl border border-white/5 col-span-2">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1.5 mb-1"><Award className="h-3 w-3" /> Primary Subsidy</p>
                  <p className="text-base font-bold text-blue-300">{dataB.subsidyName}</p>
                  <p className="text-sm text-zinc-400 mt-1">Up to {dataB.subsidyPct}% CAPEX grant</p>
                </div>
              </div>

              <div className="pt-6 border-t border-white/10 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400 text-sm">Net CAPEX</span>
                  <span className="text-lg font-bold text-white">{formatCurrency(metricsB.netCapex)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400 text-sm">Annual OPEX</span>
                  <span className="text-lg font-bold text-white">{formatCurrency(metricsB.totalOpex)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
                  <span className="text-blue-300 font-semibold">Final Payback</span>
                  <span className="text-2xl font-black text-blue-400">{metricsB.payback.toFixed(1)} Years</span>
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Visual Chart Comparison */}
        <div className="rounded-2xl border border-white/10 bg-zinc-900/50 p-6">
          <h3 className="font-bold text-lg mb-6 flex items-center gap-2">
            <TrendingDown className="h-5 w-5 text-emerald-400" />
            Financial Breakdown Comparison
          </h3>
          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#71717a" tick={{ fill: "#a1a1aa", fontSize: 12 }} />
                <YAxis 
                  stroke="#71717a" 
                  tick={{ fill: "#a1a1aa", fontSize: 12 }}
                  tickFormatter={(val) => `₹${(val/10000000).toFixed(1)}Cr`}
                />
                <RechartsTooltip
                  cursor={{ fill: "rgba(255,255,255,0.02)" }}
                  contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a", borderRadius: '12px' }}
                  formatter={(val: number) => formatCurrency(val)}
                />
                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                <Bar dataKey={stateA} fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey={stateB} fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </main>
  )
}
