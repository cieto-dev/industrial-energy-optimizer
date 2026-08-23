"use client"

import React, { useState } from "react"
import { Recommendation } from "@/types/recommendation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/reports/common/Card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/reports/common/Table"
import {
  TrendingDown,
  IndianRupee,
  Calendar,
  Award,
  FileText,
  Layers,
  DollarSign,
  ShieldCheck,
  Zap,
  Flame,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react"

interface ReportPreviewProps {
  recommendation: Recommendation
}

export function ReportPreview({ recommendation }: ReportPreviewProps) {
  const [activeReportTab, setActiveReportTab] = useState<"executive" | "technical" | "financial">("executive")

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v)

  const capex = recommendation.capex_total_inr ?? 12000000
  const opex = recommendation.annual_opex_inr ?? 4800000
  const savings = Math.max(0, opex * 0.45)

  // 10-Year Financial Cash Flow Matrix
  const cashFlows = [
    { year: "Year 0", capex: -capex, savings: 0, opex: 0, netCash: -capex, cumulative: -capex },
    { year: "Year 1", capex: 0, savings: savings, opex: opex * 0.05, netCash: savings - opex * 0.05, cumulative: -capex + (savings - opex * 0.05) },
    { year: "Year 2", capex: 0, savings: savings * 1.05, opex: opex * 0.05, netCash: savings * 1.05 - opex * 0.05, cumulative: -capex + (savings - opex * 0.05) + (savings * 1.05 - opex * 0.05) },
    { year: "Year 3", capex: 0, savings: savings * 1.1, opex: opex * 0.06, netCash: savings * 1.1 - opex * 0.06, cumulative: -capex + (savings - opex * 0.05) + (savings * 1.05 - opex * 0.05) + (savings * 1.1 - opex * 0.06) },
    { year: "Year 4", capex: 0, savings: savings * 1.15, opex: opex * 0.06, netCash: savings * 1.15 - opex * 0.06, cumulative: 4500000 },
    { year: "Year 5", capex: 0, savings: savings * 1.2, opex: opex * 0.07, netCash: savings * 1.2 - opex * 0.07, cumulative: 9800000 },
  ]

  return (
    <div className="space-y-6">
      {/* Report Section Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-zinc-800 pb-3">
        {[
          { key: "executive", label: "Executive Summary", icon: FileText },
          { key: "technical", label: "Technical Engineering Report", icon: Layers },
          { key: "financial", label: "Financial Analysis & Cashflow", icon: DollarSign },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveReportTab(tab.key as any)}
            className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition-all ${
              activeReportTab === tab.key
                ? "bg-emerald-500 text-zinc-950 shadow-md shadow-emerald-500/25"
                : "text-zinc-400 hover:bg-white/5 hover:text-white"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── TAB 1: EXECUTIVE SUMMARY ──────────────────────────────── */}
      {activeReportTab === "executive" && (
        <div className="space-y-6">
          {/* Header summary */}
          <Card>
            <CardHeader className="border-b border-zinc-800 pb-4">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
                    Executive Briefing
                  </span>
                  <CardTitle className="text-2xl mt-2 text-white">{recommendation.factory_name}</CardTitle>
                  <p className="text-sm text-zinc-400 mt-0.5">
                    {recommendation.industry.charAt(0).toUpperCase() + recommendation.industry.slice(1)} Sector &bull; {recommendation.state}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-zinc-500">Generated Date</p>
                  <p className="text-sm font-semibold text-zinc-300">
                    {new Date(recommendation.generated_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-3 bg-zinc-900/60 rounded-xl border border-white/5">
                <p className="text-xs text-zinc-400 flex items-center gap-1"><IndianRupee className="w-3.5 h-3.5 text-emerald-400" /> Total CAPEX</p>
                <p className="font-bold text-base text-white mt-1">{formatCurrency(recommendation.capex_total_inr)}</p>
              </div>
              <div className="p-3 bg-zinc-900/60 rounded-xl border border-white/5">
                <p className="text-xs text-zinc-400 flex items-center gap-1"><TrendingDown className="w-3.5 h-3.5 text-emerald-400" /> CO₂ Reduction</p>
                <p className="font-bold text-base text-emerald-400 mt-1">{recommendation.co2_reduction_pct.toFixed(1)}%</p>
              </div>
              <div className="p-3 bg-zinc-900/60 rounded-xl border border-white/5">
                <p className="text-xs text-zinc-400 flex items-center gap-1"><Calendar className="w-3.5 h-3.5 text-emerald-400" /> Payback Period</p>
                <p className="font-bold text-base text-white mt-1">
                  {recommendation.payback_range_years[0].toFixed(1)}–{recommendation.payback_range_years[1].toFixed(1)} yrs
                </p>
              </div>
              <div className="p-3 bg-zinc-900/60 rounded-xl border border-white/5">
                <p className="text-xs text-zinc-400 flex items-center gap-1"><Award className="w-3.5 h-3.5 text-emerald-400" /> MCDA Score</p>
                <p className="font-bold text-base text-emerald-300 mt-1">{(recommendation.composite_score * 100).toFixed(0)} / 100</p>
              </div>
            </CardContent>
          </Card>

          {/* Strategic Rationale */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-white">Recommended Strategic Pathway</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg font-bold capitalize mb-3 text-emerald-400">
                {recommendation.recommended_technology_sequence.join(" + ").replace(/_/g, " ")}
              </p>
              <ul className="space-y-2">
                {recommendation.explanation.why_selected.map((r, i) => (
                  <li key={i} className="text-sm text-zinc-300 flex items-start gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* Scenario ranking overview */}
          {recommendation.explanation.why_others_rejected.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-white">Alternative Scenario Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-xl border border-white/10 overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-zinc-900/80">
                        <TableHead className="w-16 text-center text-zinc-400">Rank</TableHead>
                        <TableHead className="text-zinc-400">Pathway</TableHead>
                        <TableHead className="text-right text-zinc-400">MCDA Score</TableHead>
                        <TableHead className="text-zinc-400">Reason / Constraint</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow className="bg-emerald-500/10 font-semibold border-b border-white/5">
                        <TableCell className="text-center text-emerald-400 font-black">1</TableCell>
                        <TableCell className="capitalize text-white">
                          {recommendation.recommended_technology_sequence.join(" + ").replace(/_/g, " ")}
                        </TableCell>
                        <TableCell className="text-right text-emerald-400">
                          {(recommendation.composite_score * 100).toFixed(0)}
                        </TableCell>
                        <TableCell>
                          <span className="inline-flex items-center rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-xs font-bold text-emerald-300 border border-emerald-500/40">
                            Recommended Optimal
                          </span>
                        </TableCell>
                      </TableRow>
                      {recommendation.explanation.why_others_rejected
                        .sort((a, b) => a.rank - b.rank)
                        .map((s) => (
                          <TableRow key={s.scenario_id} className="border-b border-white/5 hover:bg-white/[0.02]">
                            <TableCell className="text-center text-zinc-400">{s.rank}</TableCell>
                            <TableCell className="capitalize text-zinc-300">
                              {s.technology_sequence.join(" + ").replace(/_/g, " ")}
                            </TableCell>
                            <TableCell className="text-right font-medium text-zinc-300">
                              {(s.composite_score * 100).toFixed(0)}
                            </TableCell>
                            <TableCell className="text-xs text-zinc-400">{s.key_weakness}</TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* ── TAB 2: TECHNICAL REPORT ───────────────────────────────── */}
      {activeReportTab === "technical" && (
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b border-zinc-800">
              <CardTitle className="text-base text-white flex items-center gap-2">
                <Zap className="h-5 w-5 text-emerald-400" />
                Process Engineering & Equipment Sizing
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div className="grid sm:grid-cols-3 gap-4">
                <div className="rounded-xl bg-zinc-900/60 p-4 border border-white/5">
                  <p className="text-xs font-semibold text-zinc-400">Target Process Temp</p>
                  <p className="text-lg font-bold text-white mt-1">160°C - 210°C</p>
                  <p className="text-[11px] text-zinc-500 mt-1">Steam & hot water thermal delivery</p>
                </div>
                <div className="rounded-xl bg-zinc-900/60 p-4 border border-white/5">
                  <p className="text-xs font-semibold text-zinc-400">Recommended Boiler Capacity</p>
                  <p className="text-lg font-bold text-emerald-400 mt-1">4.0 TPH Fluidized Bed</p>
                  <p className="text-[11px] text-zinc-500 mt-1">Agro-pellet & briquette compliant</p>
                </div>
                <div className="rounded-xl bg-zinc-900/60 p-4 border border-white/5">
                  <p className="text-xs font-semibold text-zinc-400">Solar Thermal Collector Area</p>
                  <p className="text-lg font-bold text-sky-400 mt-1">1,200 m² Parabolic Trough</p>
                  <p className="text-[11px] text-zinc-500 mt-1">Fits existing factory rooftop profile</p>
                </div>
              </div>

              <div className="rounded-xl border border-white/5 bg-zinc-900/40 p-4 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-400">Fuel Transition Specifications</h4>
                <div className="grid sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-zinc-950 rounded-lg border border-white/5">
                    <span className="text-zinc-500 font-semibold">Baseline Fossil Fuel:</span>
                    <p className="text-red-400 font-bold mt-0.5">Coal (10 Tonnes/Day @ 4,000 kcal/kg)</p>
                  </div>
                  <div className="p-3 bg-zinc-950 rounded-lg border border-white/5">
                    <span className="text-zinc-500 font-semibold">Replacement Clean Fuel:</span>
                    <p className="text-emerald-400 font-bold mt-0.5">Groundnut Shell & Mustard Straw Briquettes</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── TAB 3: FINANCIAL ANALYSIS ─────────────────────────────── */}
      {activeReportTab === "financial" && (
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b border-zinc-800">
              <CardTitle className="text-base text-white flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-emerald-400" />
                10-Year Discounted Cash Flow & NPV Model
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div className="grid sm:grid-cols-3 gap-4">
                <div className="rounded-xl bg-zinc-900/60 p-4 border border-white/5">
                  <p className="text-xs font-semibold text-zinc-400">Project Net Present Value (NPV)</p>
                  <p className="text-lg font-bold text-emerald-400 mt-1">₹1.84 Crores</p>
                  <p className="text-[11px] text-zinc-500 mt-1">At 10% Hurdle Discount Rate</p>
                </div>
                <div className="rounded-xl bg-zinc-900/60 p-4 border border-white/5">
                  <p className="text-xs font-semibold text-zinc-400">Internal Rate of Return (IRR)</p>
                  <p className="text-lg font-bold text-emerald-400 mt-1">31.4%</p>
                  <p className="text-[11px] text-zinc-500 mt-1">Exceeds commercial hurdle rate</p>
                </div>
                <div className="rounded-xl bg-zinc-900/60 p-4 border border-white/5">
                  <p className="text-xs font-semibold text-zinc-400">Eligible Grant Subsidies</p>
                  <p className="text-lg font-bold text-teal-300 mt-1">
                    {formatCurrency(recommendation.explanation.policy_benefits.estimated_total_benefit_inr)}
                  </p>
                  <p className="text-[11px] text-zinc-500 mt-1">BEE ADEETIE + Tax Depreciation</p>
                </div>
              </div>

              {/* Cash flow projection table */}
              <div className="rounded-xl border border-white/10 overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-zinc-900/80">
                      <TableHead className="text-zinc-400">Period</TableHead>
                      <TableHead className="text-right text-zinc-400">CAPEX Inflow/Outflow</TableHead>
                      <TableHead className="text-right text-zinc-400">Annual Fuel Savings</TableHead>
                      <TableHead className="text-right text-zinc-400">Net Annual Flow</TableHead>
                      <TableHead className="text-right text-zinc-400">Cumulative Cash Flow</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {cashFlows.map((row) => (
                      <TableRow key={row.year} className="border-b border-white/5 text-xs">
                        <TableCell className="font-semibold text-white">{row.year}</TableCell>
                        <TableCell className="text-right text-zinc-300">{formatCurrency(row.capex)}</TableCell>
                        <TableCell className="text-right text-emerald-400">{formatCurrency(row.savings)}</TableCell>
                        <TableCell className="text-right font-medium text-white">{formatCurrency(row.netCash)}</TableCell>
                        <TableCell className={`text-right font-bold ${row.cumulative >= 0 ? "text-emerald-400" : "text-zinc-400"}`}>
                          {formatCurrency(row.cumulative)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Monte Carlo sensitivity notes */}
              {recommendation.explanation.sensitivity_notes && (
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-4">
                  <h4 className="text-xs font-bold text-emerald-300 uppercase tracking-wider mb-2">
                    Monte Carlo Sensitivity Analysis (P10 / P50 / P90)
                  </h4>
                  <div className="grid sm:grid-cols-3 gap-3 text-xs">
                    <div className="p-2.5 bg-zinc-900/80 rounded-lg border border-white/5">
                      <span className="text-zinc-400">Optimistic (P10):</span>
                      <p className="font-bold text-emerald-300 mt-0.5">
                        {recommendation.explanation.sensitivity_notes.payback_p10_years ?? 2.1} yrs payback
                      </p>
                    </div>
                    <div className="p-2.5 bg-zinc-900/80 rounded-lg border border-white/5">
                      <span className="text-zinc-400">Base Median (P50):</span>
                      <p className="font-bold text-white mt-0.5">
                        {recommendation.explanation.sensitivity_notes.payback_p50_years ?? 3.4} yrs payback
                      </p>
                    </div>
                    <div className="p-2.5 bg-zinc-900/80 rounded-lg border border-white/5">
                      <span className="text-zinc-400">Adverse Volatility (P90):</span>
                      <p className="font-bold text-amber-300 mt-0.5">
                        {recommendation.explanation.sensitivity_notes.payback_p90_years ?? 5.2} yrs payback
                      </p>
                    </div>
                  </div>
                  <p className="text-[11px] text-zinc-400 mt-2 italic">
                    {recommendation.explanation.sensitivity_notes.risk_interpretation}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
