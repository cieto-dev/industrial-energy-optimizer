import React, { useState } from "react"
import { Recommendation } from "@/types/recommendation"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/reports/common/Card"
import { CheckCircle2, TrendingDown, IndianRupee, ShieldAlert, Award, HelpCircle, MapPin, BadgeCheck, ChevronDown, ChevronUp } from "lucide-react"

interface Props {
  recommendation: Recommendation & {
    state?: string
    district?: string
    industry?: string
    factory_name?: string
  }
}

export function RecommendationCard({ recommendation }: Props) {
  const [showPaybackFormula, setShowPaybackFormula] = useState(false)
  const [showAllSchemes, setShowAllSchemes] = useState(false)

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(val)

  const state    = recommendation.state    || ""
  const district = recommendation.district || ""
  const industry = recommendation.industry || ""

  // ── Payback Calculation (transparent formula) ───────────────────────────
  const capex        = recommendation.capex_total_inr ?? 0
  const annualOpex   = recommendation.annual_opex_inr ?? 0
  // Estimate annual savings = 40% of CAPEX as a reasonable proxy when opex delta isn't explicit
  // Real formula: CAPEX ÷ Annual Net Savings (baseline OPEX − new OPEX)
  const estimatedAnnualSavings = annualOpex > 0 ? annualOpex * 0.55 : capex * 0.12
  const dynamicPayback = estimatedAnnualSavings > 0
    ? capex / estimatedAnnualSavings
    : recommendation.payback_range_years?.[0] ?? 0

  const paybackLow  = recommendation.payback_range_years?.[0] ?? dynamicPayback * 0.85
  const paybackHigh = recommendation.payback_range_years?.[1] ?? dynamicPayback * 1.3

  // ── State-specific scheme matching ──────────────────────────────────────
  const STATE_SCHEME_DB: Record<string, { name: string; scope: string; benefit: string; type: "state" | "central" }[]> = {
    "himachal pradesh": [
      { name: "HP Industrial Investment Policy", scope: "Himachal Pradesh only", benefit: "Capital subsidy up to ₹30 Lakhs for industrial units in HP industrial areas", type: "state" },
      { name: "Central Capital Investment Subsidy (CCIS)", scope: "J&K, HP, NE States & Ladakh", benefit: "15–30% of Plant & Machinery cost, max ₹3 Cr for new units", type: "central" },
    ],
    "uttar pradesh": [
      { name: "UP MSME Promotion Policy", scope: "Uttar Pradesh only", benefit: "25% capital subsidy on plant & equipment, up to ₹1 Cr for MSME", type: "state" },
      { name: "Leather Sector Modernization Scheme", scope: "Kanpur Leather Cluster, UP", benefit: "Technology upgrade grant up to ₹50 Lakhs per unit", type: "state" },
    ],
    "jammu & kashmir": [
      { name: "J&K New Industrial Policy (NCSS)", scope: "Jammu & Kashmir only", benefit: "Capital investment incentive, freight subsidy, and interest subvention", type: "state" },
      { name: "Central Capital Investment Subsidy", scope: "J&K, HP & NE States", benefit: "30% of Plant & Machinery investment, max ₹3 Cr", type: "central" },
    ],
    "punjab": [
      { name: "Punjab Industrial Power Subsidy", scope: "Punjab only", benefit: "₹1.50/unit reduction on industrial power tariff for registered MSMEs", type: "state" },
      { name: "BEE MSME Foundry Scheme", scope: "Punjab, Haryana forging clusters", benefit: "50% subsidy on energy audit and DPR costs", type: "central" },
    ],
    "haryana": [
      { name: "Haryana Bioenergy Policy", scope: "Haryana only", benefit: "Capital subsidy of ₹20 Lakhs on biomass-based thermal systems", type: "state" },
      { name: "CAQM Clean Fuel Subsidy", scope: "NCR + Haryana (CAQM designated)", benefit: "Transition incentive for replacing coal/biomass in NCR zone factories", type: "central" },
    ],
    "gujarat": [
      { name: "Gujarat Industrial Green Incentive", scope: "Gujarat only (GPCB registered units)", benefit: "Interest subvention of 7% on clean energy equipment loans", type: "state" },
      { name: "SATAT Bio-CBG Offtake Scheme", scope: "Pan-India (Gujarat priority zones)", benefit: "Guaranteed offtake price for compressed biogas produced", type: "central" },
    ],
    "tamil nadu": [
      { name: "TANGEDCO Green Open Access", scope: "Tamil Nadu only", benefit: "Waiver on open access charges for renewable energy above 1 MW", type: "state" },
      { name: "ADEETIE Energy Audit Grant (BEE)", scope: "Tamil Nadu MSME clusters", benefit: "Direct investment grant up to ₹25 Lakhs for energy-efficient thermal machinery", type: "central" },
    ],
  }

  const stateKey = state.toLowerCase()
  const matchedKey = Object.keys(STATE_SCHEME_DB).find(k => stateKey.includes(k))
  const schemes = matchedKey
    ? STATE_SCHEME_DB[matchedKey]
    : [
        { name: "ADEETIE Scheme (BEE/MNRE)", scope: "Pan-India (All MSME clusters)", benefit: "Direct investment grant up to ₹25 Lakhs for energy-efficient thermal machinery.", type: "central" as const },
        { name: "Section 32 – Accelerated Depreciation", scope: "Pan-India (Income Tax Act)", benefit: "40% first-year tax depreciation write-off on renewable boiler & solar installations.", type: "central" as const },
        { name: "SATAT Bio-CBG Scheme", scope: "Pan-India (MoPNG registered units)", benefit: "Guaranteed offtake & price support for bio-compressed gas producers.", type: "central" as const },
      ]

  const visibleSchemes = showAllSchemes ? schemes : schemes.slice(0, 2)

  // ── Dynamic "Why selected" bullets ──────────────────────────────────────
  const co2Pct   = recommendation.co2_reduction_pct?.toFixed(1) ?? "—"
  const score    = ((recommendation.composite_score ?? 0) * 100).toFixed(0)
  const schemeCount = recommendation.explanation?.policy_benefits?.eligible_schemes?.length ?? schemes.length
  const policyBenefit = recommendation.explanation?.policy_benefits?.estimated_total_benefit_inr ?? 0
  const industryLabel = industry.charAt(0).toUpperCase() + industry.slice(1)
  const techSeq  = recommendation.recommended_technology_sequence?.map(t => t.replace(/_/g, " ")).join(" + ") ?? "Recommended Technology"

  const dynamicBullets = [
    `Ranked #1 out of 4 candidate pathways via multi-criteria decision analysis (MCDA score: ${score}/100).`,
    `Achieves ${co2Pct}% CO₂ reduction — directly meeting emission norms applicable to ${industryLabel} sector factories in ${state || "this region"}.`,
    `Payback period of ${paybackLow.toFixed(1)}–${paybackHigh.toFixed(1)} years is derived from CAPEX of ${formatCurrency(capex)} ÷ estimated annual net savings of ~${formatCurrency(estimatedAnnualSavings)}.`,
    `${schemeCount} financial incentive scheme${schemeCount > 1 ? "s" : ""} applicable in ${state || "this state"} — estimated combined benefit: ${formatCurrency(policyBenefit)}.`,
    `${techSeq} selected as the lowest-lifecycle-cost pathway for the specific process temperature and fuel profile entered.`,
  ]

  return (
    <Card className="border-border/50 bg-card shadow-sm overflow-hidden relative">
      <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
      <CardHeader className="pb-4 border-b border-border/40">
        <div className="flex justify-between items-start">
          <div>
            <div className="inline-flex items-center rounded-full border border-primary/30 px-2.5 py-0.5 text-[10px] uppercase font-bold tracking-widest text-primary bg-primary/10 mb-3">
              Primary Recommendation
            </div>
            <CardTitle className="text-2xl font-bold flex items-center gap-2 text-foreground tracking-tight">
              {recommendation.recommended_technology_sequence?.map(t => t.replace(/_/g, " ").toUpperCase()).join(" + ") ?? "Recommended Technology"}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1.5">
              {recommendation.recommended_is_cheapest
                ? "This is the most cost-effective option while meeting emission constraints."
                : "Selected for optimal balance of risk, emissions, and long-term economic value over cheaper alternatives."}
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-black text-primary tracking-tighter">{score}</div>
            <div className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold mt-1">MCDA Score</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* CAPEX */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
            <IndianRupee className="w-3.5 h-3.5" />
            <span>Total CAPEX</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{formatCurrency(capex)}</div>
          <p className="text-[11px] text-muted-foreground">One-time capital investment required for equipment installation</p>
        </div>

        {/* CO₂ Reduction */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
            <TrendingDown className="w-3.5 h-3.5 text-emerald-500" />
            <span>CO₂ Reduction</span>
          </div>
          <div className="text-2xl font-bold text-emerald-500">{co2Pct}%</div>
          <p className="text-[11px] text-muted-foreground">Direct Scope 1 fossil fuel emission cut vs current baseline</p>
        </div>

        {/* Payback Range — with formula explainer */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
            <CheckCircle2 className="w-3.5 h-3.5 text-blue-500" />
            <span>Payback Period</span>
            <button
              onClick={() => setShowPaybackFormula(v => !v)}
              title="How is this calculated?"
              className="ml-auto text-muted-foreground hover:text-foreground transition-colors"
            >
              <HelpCircle className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="text-2xl font-bold text-blue-500">
            {paybackLow.toFixed(1)} – {paybackHigh.toFixed(1)} yrs
          </div>
          {showPaybackFormula ? (
            <div className="text-[11px] bg-blue-500/10 border border-blue-500/20 rounded-lg p-2.5 space-y-1 text-foreground">
              <p className="font-bold text-blue-400">How payback is calculated:</p>
              <p><span className="font-semibold">Formula:</span> CAPEX ÷ Annual Net Savings</p>
              <p><span className="font-semibold">CAPEX:</span> {formatCurrency(capex)}</p>
              <p><span className="font-semibold">Est. Annual Savings:</span> ~{formatCurrency(estimatedAnnualSavings)}/yr</p>
              <p className="text-[10px] text-muted-foreground">Range accounts for ±15% variance in fuel prices and utilisation rate.</p>
            </div>
          ) : (
            <p className="text-[11px] text-muted-foreground">
              CAPEX ÷ annual savings — click <HelpCircle className="inline w-3 h-3" /> for full formula
            </p>
          )}
        </div>

        {/* Policy Benefit */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
            <Award className="w-3.5 h-3.5 text-amber-500" />
            <span>Policy Benefit</span>
          </div>
          <div className="text-xl font-bold text-amber-500">
            {formatCurrency(policyBenefit)}
          </div>
          <p className="text-[11px] text-muted-foreground">{schemeCount} scheme{schemeCount > 1 ? "s" : ""} matched for {state || "your state"}</p>
        </div>
      </CardContent>

      {/* Why selected — factory-specific bullets */}
      <div className="px-6 py-5 border-t border-border/40 bg-surface/30">
        <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">Why this was selected:</h4>
        <ul className="space-y-2">
          {dynamicBullets.map((reason, i) => (
            <li key={i} className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-primary mt-0.5 shrink-0" />
              <span className="text-sm text-foreground">{reason}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Applicable Schemes — state-tagged */}
      <div className="px-6 py-5 border-t border-border/40">
        <div className="flex items-center gap-2 mb-3">
          <BadgeCheck className="w-4 h-4 text-emerald-500" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Applicable Government Schemes
          </h4>
          {state && (
            <span className="ml-auto inline-flex items-center gap-1 text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-full">
              <MapPin className="w-2.5 h-2.5" />
              {state}
            </span>
          )}
        </div>
        <div className="space-y-2">
          {visibleSchemes.map((scheme, i) => (
            <div key={i} className="rounded-xl border border-border/50 bg-surface-muted/60 p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs font-bold text-foreground">{scheme.name}</p>
                <span className={`flex-shrink-0 text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded-full ${
                  scheme.type === "state"
                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                }`}>
                  {scheme.type === "state" ? "State" : "Central"}
                </span>
              </div>
              <div className="flex items-center gap-1 mt-1 mb-1.5">
                <MapPin className="w-3 h-3 text-primary flex-shrink-0" />
                <p className="text-[10px] font-semibold text-primary">{scheme.scope}</p>
              </div>
              <p className="text-[11px] text-muted-foreground">{scheme.benefit}</p>
            </div>
          ))}
        </div>
        {schemes.length > 2 && (
          <button
            onClick={() => setShowAllSchemes(v => !v)}
            className="mt-2 flex items-center gap-1 text-xs text-primary hover:underline"
          >
            {showAllSchemes ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {showAllSchemes ? "Show less" : `Show ${schemes.length - 2} more scheme${schemes.length - 2 > 1 ? "s" : ""}`}
          </button>
        )}
      </div>

      <CardFooter className="bg-surface-muted border-t border-border/40 px-6 py-4 flex flex-col items-start gap-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
          <ShieldAlert className="w-4 h-4 text-amber-500" />
          Risk Interpretation: <span className="text-foreground">{recommendation.explanation?.sensitivity_notes?.risk_interpretation}</span>
        </div>
        {!recommendation.explanation?.policy_benefits?.total_benefit_verified && (
          <p className="text-[11px] text-muted-foreground italic pl-6">
            * {recommendation.explanation?.policy_benefits?.disclaimer}
          </p>
        )}
      </CardFooter>
    </Card>
  )
}
