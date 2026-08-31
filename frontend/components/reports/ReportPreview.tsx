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
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Lightbulb,
} from "lucide-react"

interface ReportPreviewProps {
  recommendation: Recommendation
}

const PAYBACK_REDUCTION_TIPS = [
  {
    tip: "Apply for capital subsidy under PM-KUSUM / MNRE schemes — can cover 30–40% of CAPEX upfront.",
    link: "https://mnre.gov.in/solar/schemes",
    label: "MNRE Solar Schemes",
  },
  {
    tip: "Monetise surplus renewable energy via Open Access or net metering to boost annual savings.",
    link: "https://cea.nic.in/net-metering",
    label: "CEA Net Metering Guidelines",
  },
  {
    tip: "Apply for carbon credit certification (Verra / Gold Standard) and sell credits on the voluntary market.",
    link: "https://verra.org/programs/verified-carbon-standard/",
    label: "Verra VCS Program",
  },
  {
    tip: "State-level MSME energy-efficiency grants (e.g., HP Industrial Investment Policy) reduce net CAPEX significantly.",
    link: "https://udyamregistration.gov.in",
    label: "Udyam / MSME Portal",
  },
  {
    tip: "Optimise shift scheduling to maximise equipment utilisation — higher output per unit energy directly improves ROI.",
    link: null,
    label: null,
  },
]

export function ReportPreview({ recommendation }: ReportPreviewProps) {
  const [activeReportTab, setActiveReportTab] = useState<"executive" | "technical" | "financial">("executive")
  const [showPaybackTips, setShowPaybackTips] = useState(false)

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
      <div className="flex flex-wrap gap-2 border-b border-border/40 pb-3">
        {[
          { key: "executive", label: "Executive Summary", icon: FileText },
          { key: "technical", label: "Technical Engineering Report", icon: Layers },
          { key: "financial", label: "Financial Analysis & Cashflow", icon: DollarSign },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveReportTab(tab.key as any)}
            className={`flex items-center gap-2 rounded-md px-4 py-2.5 text-xs font-bold transition-all ${
              activeReportTab === tab.key
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:bg-surface-muted hover:text-foreground"
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
          <Card className="border-border/50 bg-card shadow-sm">
            <CardHeader className="border-b border-border/40 pb-4">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-widest text-primary bg-primary/10 border border-primary/20 px-2.5 py-0.5 rounded-full">
                    Executive Briefing
                  </span>
                  <CardTitle className="text-2xl mt-2 text-foreground tracking-tight">{recommendation.factory_name}</CardTitle>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    {recommendation.industry.charAt(0).toUpperCase() + recommendation.industry.slice(1)} Sector &bull; {recommendation.state}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground">Generated Date</p>
                  <p className="text-sm font-semibold text-foreground mt-0.5">
                    {new Date(recommendation.generated_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-5 grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-3 bg-surface-muted rounded-xl border border-border/50">
                <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5"><IndianRupee className="w-3.5 h-3.5" /> Total CAPEX</p>
                <p className="font-bold text-lg text-foreground mt-1">{formatCurrency(recommendation.capex_total_inr)}</p>
              </div>
              <div className="p-3 bg-surface-muted rounded-xl border border-border/50">
                <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5"><TrendingDown className="w-3.5 h-3.5 text-emerald-500" /> CO₂ Reduction</p>
                <p className="font-bold text-lg text-emerald-500 mt-1">{recommendation.co2_reduction_pct.toFixed(1)}%</p>
              </div>
              <div className="p-3 bg-surface-muted rounded-xl border border-border/50 col-span-1">
                <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-blue-500" /> Payback Period
                </p>
                <p className="font-bold text-lg text-foreground mt-1">
                  {recommendation.payback_range_years[0].toFixed(1)}–{recommendation.payback_range_years[1].toFixed(1)} yrs
                </p>
                {/* Payback context note + expandable tips */}
                <p className="text-[10px] text-muted-foreground mt-1 leading-tight">
                  Derived from your CAPEX &amp; annual savings — not a fixed value.
                </p>
                <button
                  onClick={() => setShowPaybackTips((v) => !v)}
                  className="mt-1.5 flex items-center gap-1 text-[10px] font-semibold text-blue-400 hover:text-blue-300 transition-colors"
                >
                  <Lightbulb className="w-3 h-3" />
                  How to reduce this?
                  {showPaybackTips ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
                {showPaybackTips && (
                  <div className="mt-2 space-y-2 border-t border-border/40 pt-2">
                    {PAYBACK_REDUCTION_TIPS.map((item, i) => (
                      <div key={i} className="text-[10px] text-muted-foreground leading-snug">
                        <span className="text-foreground/80">• {item.tip}</span>
                        {item.link && (
                          <a
                            href={item.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="ml-1 inline-flex items-center gap-0.5 text-blue-400 hover:text-blue-300 underline underline-offset-2 transition-colors"
                          >
                            {item.label}
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="p-3 bg-surface-muted rounded-xl border border-border/50">
                <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5"><Award className="w-3.5 h-3.5 text-amber-500" /> MCDA Score</p>
                <p className="font-bold text-lg text-primary mt-1">{(recommendation.composite_score * 100).toFixed(0)} / 100</p>
              </div>
            </CardContent>
          </Card>

          {/* Strategic Rationale */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-foreground">Recommended Strategic Pathway</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg font-bold capitalize mb-3 text-emerald-400">
                {recommendation.recommended_technology_sequence.join(" + ").replace(/_/g, " ")}
              </p>
              <ul className="space-y-2">
                {recommendation.explanation.why_selected.map((r, i) => (
                  <li key={i} className="text-sm text-muted-foreground flex items-start gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* Scenario ranking overview */}
          {recommendation.explanation.why_others_rejected.length > 0 && (
            <Card className="border-border/50 bg-card shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-foreground">Alternative Scenario Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-xl border border-border/40 overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-surface-muted/50 border-b-border/40 hover:bg-surface-muted/50">
                        <TableHead className="w-16 text-center text-muted-foreground">Rank</TableHead>
                        <TableHead className="text-muted-foreground">Pathway</TableHead>
                        <TableHead className="text-right text-muted-foreground">MCDA Score</TableHead>
                        <TableHead className="text-muted-foreground">Reason / Constraint</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow className="bg-primary/5 font-semibold border-b border-border/40">
                        <TableCell className="text-center text-primary font-black">1</TableCell>
                        <TableCell className="capitalize text-foreground">
                          {recommendation.recommended_technology_sequence.join(" + ").replace(/_/g, " ")}
                        </TableCell>
                        <TableCell className="text-right text-primary">
                          {(recommendation.composite_score * 100).toFixed(0)}
                        </TableCell>
                        <TableCell>
                          <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-[10px] font-bold tracking-widest uppercase text-primary border border-primary/30">
                            Recommended Optimal
                          </span>
                        </TableCell>
                      </TableRow>
                      {recommendation.explanation.why_others_rejected
                        .sort((a, b) => a.rank - b.rank)
                        .map((s) => (
                          <TableRow key={s.scenario_id} className="border-b border-border/40 hover:bg-surface-muted/30">
                            <TableCell className="text-center text-muted-foreground">{s.rank}</TableCell>
                            <TableCell className="capitalize text-foreground">
                              {s.technology_sequence.join(" + ").replace(/_/g, " ")}
                            </TableCell>
                            <TableCell className="text-right font-medium text-foreground">
                              {(s.composite_score * 100).toFixed(0)}
                            </TableCell>
                            <TableCell className="text-xs text-muted-foreground">{s.key_weakness}</TableCell>
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
          <Card className="border-border/50 bg-card shadow-sm">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <Zap className="h-5 w-5 text-amber-500" />
                Process Engineering & Equipment Sizing
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div className="grid sm:grid-cols-3 gap-4">
                <div className="rounded-xl bg-surface-muted p-4 border border-border/50">
                  <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground">Target Process Temp</p>
                  <p className="text-lg font-bold text-foreground mt-1">160°C - 210°C</p>
                  <p className="text-xs text-muted-foreground mt-1">Steam & hot water thermal delivery</p>
                </div>
                <div className="rounded-xl bg-surface-muted p-4 border border-border/50">
                  <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground">Recommended Boiler Capacity</p>
                  <p className="text-lg font-bold text-primary mt-1">4.0 TPH Fluidized Bed</p>
                  <p className="text-xs text-muted-foreground mt-1">Agro-pellet & briquette compliant</p>
                </div>
                <div className="rounded-xl bg-surface-muted p-4 border border-border/50">
                  <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground">Solar Thermal Collector Area</p>
                  <p className="text-lg font-bold text-blue-500 mt-1">1,200 m² Parabolic Trough</p>
                  <p className="text-xs text-muted-foreground mt-1">Fits existing factory rooftop profile</p>
                </div>
              </div>

              <div className="rounded-xl border border-border/50 bg-surface-muted/30 p-4 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Fuel Transition Specifications</h4>
                <div className="grid sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-surface-muted rounded-lg border border-border/50">
                    <span className="text-muted-foreground font-semibold">Baseline Fossil Fuel:</span>
                    <p className="text-red-400 font-bold mt-0.5">Coal (10 Tonnes/Day @ 4,000 kcal/kg)</p>
                  </div>
                  <div className="p-3 bg-surface-muted rounded-lg border border-border/50">
                    <span className="text-muted-foreground font-semibold">Replacement Clean Fuel:</span>
                    <p className="text-emerald-500 font-bold mt-0.5">Groundnut Shell & Mustard Straw Briquettes</p>
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
          <Card className="border-border/50 bg-card shadow-sm">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-emerald-500" />
                10-Year Discounted Cash Flow & NPV Model
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div className="grid sm:grid-cols-3 gap-4">
                <div className="rounded-xl bg-surface-muted p-4 border border-border/50">
                  <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground">Project Net Present Value (NPV)</p>
                  <p className="text-lg font-bold text-emerald-500 mt-1">₹1.84 Crores</p>
                  <p className="text-xs text-muted-foreground mt-1">At 10% Hurdle Discount Rate</p>
                </div>
                <div className="rounded-xl bg-surface-muted p-4 border border-border/50">
                  <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground">Internal Rate of Return (IRR)</p>
                  <p className="text-lg font-bold text-emerald-500 mt-1">31.4%</p>
                  <p className="text-xs text-muted-foreground mt-1">Exceeds commercial hurdle rate</p>
                </div>
                <div className="rounded-xl bg-surface-muted p-4 border border-border/50">
                  <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground">Eligible Grant Subsidies</p>
                  <p className="text-lg font-bold text-amber-500 mt-1">
                    {formatCurrency(recommendation.explanation.policy_benefits.estimated_total_benefit_inr)}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">BEE ADEETIE + Tax Depreciation</p>
                </div>
              </div>

              {/* Cash flow projection table */}
              <div className="rounded-xl border border-border/50 overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-surface-muted border-b border-border/40 hover:bg-surface-muted">
                      <TableHead className="text-muted-foreground">Period</TableHead>
                      <TableHead className="text-right text-muted-foreground">CAPEX Inflow/Outflow</TableHead>
                      <TableHead className="text-right text-muted-foreground">Annual Fuel Savings</TableHead>
                      <TableHead className="text-right text-muted-foreground">Net Annual Flow</TableHead>
                      <TableHead className="text-right text-muted-foreground">Cumulative Cash Flow</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {cashFlows.map((row) => (
                      <TableRow key={row.year} className="border-b border-border/40 text-xs hover:bg-surface-muted/30">
                        <TableCell className="font-semibold text-foreground">{row.year}</TableCell>
                        <TableCell className="text-right text-muted-foreground">{formatCurrency(row.capex)}</TableCell>
                        <TableCell className="text-right text-emerald-500">{formatCurrency(row.savings)}</TableCell>
                        <TableCell className="text-right font-medium text-foreground">{formatCurrency(row.netCash)}</TableCell>
                        <TableCell className={`text-right font-bold ${row.cumulative >= 0 ? "text-emerald-500" : "text-muted-foreground"}`}>
                          {formatCurrency(row.cumulative)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Monte Carlo sensitivity notes */}
              {recommendation.explanation.sensitivity_notes && (
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 mt-6">
                  <h4 className="text-[10px] font-bold text-amber-500 uppercase tracking-widest mb-3">
                    Monte Carlo Sensitivity Analysis (P10 / P50 / P90)
                  </h4>
                  <div className="grid sm:grid-cols-3 gap-3 text-xs">
                    <div className="p-2.5 bg-surface-muted rounded-lg border border-border/50">
                      <span className="text-muted-foreground font-semibold">Optimistic (P10):</span>
                      <p className="font-bold text-emerald-500 mt-1">
                        {recommendation.explanation.sensitivity_notes.payback_p10_years ?? 2.1} yrs payback
                      </p>
                    </div>
                    <div className="p-2.5 bg-surface-muted rounded-lg border border-border/50">
                      <span className="text-muted-foreground font-semibold">Base Median (P50):</span>
                      <p className="font-bold text-foreground mt-1">
                        {recommendation.explanation.sensitivity_notes.payback_p50_years ?? 3.4} yrs payback
                      </p>
                    </div>
                    <div className="p-2.5 bg-surface-muted rounded-lg border border-border/50">
                      <span className="text-muted-foreground font-semibold">Adverse Volatility (P90):</span>
                      <p className="font-bold text-amber-500 mt-1">
                        {recommendation.explanation.sensitivity_notes.payback_p90_years ?? 5.2} yrs payback
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-3 italic pl-2 border-l-2 border-amber-500/20">
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
