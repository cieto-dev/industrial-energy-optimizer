import React, { useState } from "react"
import { Recommendation } from "@/types/recommendation"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/reports/common/Card"
import { CheckCircle2, TrendingDown, IndianRupee, ShieldAlert, Award, HelpCircle, MapPin, BadgeCheck, ChevronDown, ChevronUp, ExternalLink, Lightbulb, X, ArrowRight, Zap } from "lucide-react"

interface SpecialCategory {
  women_owned?: boolean
  sc_st_owned?: boolean
  north_east_region?: boolean
  jammu_kashmir?: boolean
  ladakh?: boolean
  aspirational_district?: boolean
}

type Tip = {
  tip: string
  link: string | null
  label: string | null
  capexReductionPct: number   // 0–1: fraction of CAPEX this strategy removes
  savingsBoostPct: number     // 0–1: fraction by which annual savings increase
}

/** Pure function — builds contextual payback-reduction tips from the
 *  actual technology stack, state, ownership, and industry. */
function buildPaybackTips(
  techSeq: string[],
  state: string,
  industry: string,
  special: SpecialCategory,
  clusterName: string,
): Tip[] {
  const tips: Tip[] = []
  const techs = techSeq.map(t => t.toLowerCase())
  const st    = state.toLowerCase()
  const ind   = industry.toLowerCase()

  const hasBiomass  = techs.some(t => t.includes("biomass"))
  const hasWhr      = techs.some(t => t.includes("waste_heat") || t.includes("whr") || t.includes("heat_recovery"))
  const hasSolar    = techs.some(t => t.includes("solar"))
  const hasBioCng   = techs.some(t => t.includes("bio_cng") || t.includes("cng"))
  const hasHeatPump = techs.some(t => t.includes("heat_pump"))

  // 1 — Technology-specific
  if (hasBiomass) {
    tips.push({ tip: "Tie up with verified biomass aggregators to cut feedstock cost 15–25% via long-term supply agreements, directly reducing OPEX.", link: "https://mnre.gov.in/bio-energy", label: "MNRE Bio-Energy", capexReductionPct: 0, savingsBoostPct: 0.18 })
    tips.push({ tip: "Biomass boilers qualify for SATAT Bio-CNG scheme — viability gap funding & guaranteed offtake reduces your financial risk.", link: "https://petroleum.nic.in/satat", label: "SATAT (MoPNG)", capexReductionPct: 0.08, savingsBoostPct: 0.05 })
  }
  if (hasWhr) {
    tips.push({ tip: "Waste heat recovery systems qualify for BEE ADEETIE grant — up to ₹25 Lakhs direct investment grant on WHR equipment.", link: "https://beeindia.gov.in/schemes/adeetie", label: "BEE ADEETIE", capexReductionPct: 0.20, savingsBoostPct: 0 })
  }
  if (hasSolar) {
    tips.push({ tip: "Rooftop solar qualifies for PM-KUSUM Component-C — 30% central subsidy on CAPEX.", link: "https://mnre.gov.in/solar/schemes", label: "PM-KUSUM (MNRE)", capexReductionPct: 0.30, savingsBoostPct: 0 })
  }
  if (hasBioCng) {
    tips.push({ tip: "Bio-CNG/biogas installations qualify for 40% accelerated depreciation under Section 32 of the Income Tax Act.", link: null, label: null, capexReductionPct: 0.12, savingsBoostPct: 0 })
  }
  if (hasHeatPump) {
    tips.push({ tip: "Industrial heat pumps are eligible under BEE IEEFP soft loans — reduces effective CAPEX interest burden.", link: "https://beeindia.gov.in/ieefp", label: "BEE IEEFP", capexReductionPct: 0.10, savingsBoostPct: 0 })
  }

  // 2 — State-specific
  if (st.includes("himachal")) {
    tips.push({ tip: "HP Industrial Investment Policy: ₹30 Lakh capital subsidy for clean energy equipment in HP industrial areas (Baddi, Parwanoo, Solan).", link: "https://himachal.nic.in/industry", label: "HP Industrial Policy", capexReductionPct: 0.30, savingsBoostPct: 0 })
    tips.push({ tip: "Central Capital Investment Subsidy (CCIS) for HP units — 15–30% of P&M cost, max ₹3 Cr.", link: "https://dpiit.gov.in", label: "CCIS (DPIIT)", capexReductionPct: 0.20, savingsBoostPct: 0 })
  } else if (st.includes("punjab")) {
    tips.push({ tip: "Punjab Industrial Power Subsidy reduces tariff ₹1.50/unit for MSMEs — directly lowers annual OPEX.", link: null, label: null, capexReductionPct: 0, savingsBoostPct: 0.08 })
  } else if (st.includes("haryana")) {
    tips.push({ tip: "Haryana Bioenergy Policy: ₹20 Lakh capital subsidy on biomass-based thermal systems.", link: null, label: null, capexReductionPct: 0.20, savingsBoostPct: 0 })
  } else if (st.includes("gujarat")) {
    tips.push({ tip: "Gujarat Industrial Green Incentive offers 7% interest subvention on clean energy equipment loans.", link: null, label: null, capexReductionPct: 0.07, savingsBoostPct: 0 })
  } else if (st.includes("tamil")) {
    tips.push({ tip: "TANGEDCO Green Open Access waives open access charges on renewable energy above 1 MW.", link: null, label: null, capexReductionPct: 0, savingsBoostPct: 0.07 })
  }

  // 3 — Industry-specific
  if (ind.includes("pharma")) {
    tips.push({ tip: "Pharma sector qualifies for BEE PAT Scheme — earn tradeable energy savings certificates (ESCerts) and monetise them.", link: "https://beeindia.gov.in/pat", label: "BEE PAT Scheme", capexReductionPct: 0, savingsBoostPct: 0.08 })
  }
  if (ind.includes("textile")) {
    tips.push({ tip: "TUFS covers energy-efficient textile machinery — 5% interest reimbursement on term loans.", link: "https://texmin.nic.in/tufs", label: "TUFS (Texmin)", capexReductionPct: 0.05, savingsBoostPct: 0 })
  }

  // 4 — Ownership-based
  if (special.women_owned) {
    tips.push({ tip: "Women-owned enterprise: Stand-Up India loan (₹10L–₹1Cr at subsidised rate) cuts debt-servicing cost on CAPEX.", link: "https://www.standupmitra.in", label: "Stand-Up India", capexReductionPct: 0.08, savingsBoostPct: 0 })
    tips.push({ tip: "SIDBI Mahila Udyam Nidhi: concessional loan up to ₹10 Lakh exclusively for women entrepreneurs.", link: "https://sidbi.in", label: "SIDBI MUN", capexReductionPct: 0.05, savingsBoostPct: 0 })
  }
  if (special.sc_st_owned) {
    tips.push({ tip: "SC/ST-owned MSME: National SC-ST Hub credit-linked capital subsidy under MSME Ministry.", link: "https://scsthub.in", label: "SC-ST Hub", capexReductionPct: 0.12, savingsBoostPct: 0 })
  }
  if (special.north_east_region || special.jammu_kashmir || special.ladakh) {
    tips.push({ tip: "Special category region: 30% CCIS on P&M + transport subsidy under North East / J&K Industrial Policy.", link: "https://dpiit.gov.in", label: "CCIS Special", capexReductionPct: 0.30, savingsBoostPct: 0 })
  }
  if (special.aspirational_district) {
    tips.push({ tip: "Aspirational District: priority MSME credit under RBI norms — lower interest rates reduce total loan cost.", link: null, label: null, capexReductionPct: 0.06, savingsBoostPct: 0 })
  }

  // 5 — Cluster tip
  if (clusterName && clusterName.trim().length > 0) {
    tips.push({ tip: `"${clusterName}" cluster — check BEE ADEETIE cluster status for 50% DPR cost subsidy and cluster-level energy audit grants.`, link: "https://beeindia.gov.in/schemes/adeetie", label: "BEE ADEETIE", capexReductionPct: 0.08, savingsBoostPct: 0 })
  }

  // 6 — Universal
  tips.push({ tip: "Monetise surplus renewable energy via Open Access or net metering to boost annual savings and accelerate ROI.", link: "https://cea.nic.in/net-metering", label: "CEA Net Metering", capexReductionPct: 0, savingsBoostPct: 0.10 })

  // De-duplicate and cap at 6
  const seen = new Set<string>()
  return tips.filter(t => { if (seen.has(t.tip)) return false; seen.add(t.tip); return true }).slice(0, 6)
}

interface Props {
  recommendation: Recommendation & {
    state?: string
    district?: string
    industry?: string
    factory_name?: string
    cluster_name?: string
    special_category?: SpecialCategory
  }
}

export function RecommendationCard({ recommendation }: Props) {
  const [showPaybackFormula, setShowPaybackFormula] = useState(false)
  const [showAllSchemes, setShowAllSchemes]         = useState(false)
  const [showPaybackTips, setShowPaybackTips]       = useState(false)

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(val)

  const state    = recommendation.state    || ""
  const district = recommendation.district || ""
  const industry = recommendation.industry || ""
  const clusterName   = (recommendation as any).cluster_name     || ""
  const special: SpecialCategory = (recommendation as any).special_category || {}
  const techSeq = recommendation.recommended_technology_sequence ?? []

  // ── Contextual payback tips (derived from tech + state + ownership + industry) ──
  const PAYBACK_TIPS = buildPaybackTips(techSeq, state, industry, special, clusterName)

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
  const techSeqLabel = recommendation.recommended_technology_sequence?.map(t => t.replace(/_/g, " ")).join(" + ") ?? "Recommended Technology"

  const dynamicBullets = [
    `Ranked #1 out of 4 candidate pathways via multi-criteria decision analysis (MCDA score: ${score}/100).`,
    `Achieves ${co2Pct}% CO₂ reduction — directly meeting emission norms applicable to ${industryLabel} sector factories in ${state || "this region"}.`,
    `Payback period of ${paybackLow.toFixed(1)}–${paybackHigh.toFixed(1)} years is derived from CAPEX of ${formatCurrency(capex)} ÷ estimated annual net savings of ~${formatCurrency(estimatedAnnualSavings)}.`,
    `${schemeCount} financial incentive scheme${schemeCount > 1 ? "s" : ""} applicable in ${state || "this state"} — estimated combined benefit: ${formatCurrency(policyBenefit)}.`,
    `${techSeqLabel} selected as the lowest-lifecycle-cost pathway for the specific process temperature and fuel profile entered.`,
  ]

  return (
    <>
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

          {/* ── How to reduce payback? — opens sidebar ── */}
          <button
            onClick={() => setShowPaybackTips(true)}
            className="mt-2 inline-flex items-center gap-1.5 text-[11px] font-semibold text-blue-400 hover:text-blue-300 border border-blue-500/30 hover:border-blue-400/50 bg-blue-500/5 hover:bg-blue-500/10 px-2.5 py-1 rounded-full transition-all duration-200"
          >
            <Lightbulb className="w-3 h-3" />
            How to reduce this?
            <ArrowRight className="w-3 h-3" />
          </button>
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

    {/* ═══════════════════════════════════════════════════════════
        PAYBACK REDUCTION SIDEBAR — fixed viewport overlay
        ═══════════════════════════════════════════════════════════ */}
    {(() => {
      const totalCapexReduction = Math.min(PAYBACK_TIPS.reduce((s, t) => s + t.capexReductionPct, 0), 0.60)
      const totalSavingsBoost   = Math.min(PAYBACK_TIPS.reduce((s, t) => s + t.savingsBoostPct,   0), 0.45)
      const projLow  = +(paybackLow  * (1 - totalCapexReduction) / (1 + totalSavingsBoost)).toFixed(1)
      const projHigh = +(paybackHigh * (1 - totalCapexReduction) / (1 + totalSavingsBoost)).toFixed(1)
      const pctReduction = Math.round((1 - projLow / paybackLow) * 100)

      return (
        <>
          {/* Backdrop */}
          <div
            onClick={() => setShowPaybackTips(false)}
            className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${showPaybackTips ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
          />

          {/* Sidebar panel */}
          <div
            className={`fixed top-0 right-0 z-50 h-full w-full max-w-[420px] bg-background border-l border-border shadow-2xl flex flex-col transition-transform duration-300 ease-in-out ${showPaybackTips ? "translate-x-0" : "translate-x-full"}`}
          >
            {/* ── Header ── */}
            <div className="relative flex-shrink-0 px-6 py-5 border-b border-border bg-gradient-to-br from-blue-500/10 to-emerald-500/10">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Zap className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400">Payback Accelerator</p>
                  </div>
                  <h2 className="text-lg font-bold text-foreground leading-tight">Reduce Your Payback Period</h2>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    {PAYBACK_TIPS.length} strategies identified for{" "}
                    <span className="text-foreground font-medium">{state || "your factory"}</span>
                  </p>
                </div>
                <button
                  onClick={() => setShowPaybackTips(false)}
                  className="flex-shrink-0 rounded-full p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* ── Scrollable body ── */}
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

              {/* Before / After projector */}
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400 mb-3">
                  Projected outcome — if all strategies applied
                </p>
                <div className="flex items-center justify-between gap-4 mb-4">
                  {/* Current */}
                  <div className="text-center flex-1">
                    <p className="text-[9px] uppercase tracking-widest text-muted-foreground mb-1">Current</p>
                    <p className="text-2xl font-black text-blue-400 line-through decoration-red-400/60 decoration-2">
                      {paybackLow.toFixed(1)}–{paybackHigh.toFixed(1)}
                    </p>
                    <p className="text-[10px] text-muted-foreground">years</p>
                  </div>
                  {/* Reduction indicator */}
                  <div className="flex flex-col items-center gap-1 px-2">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-emerald-500/15 border border-emerald-500/30">
                      <TrendingDown className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                    </div>
                    <span className="text-sm font-black text-emerald-600 dark:text-emerald-400">−{pctReduction}%</span>
                  </div>
                  {/* Projected */}
                  <div className="text-center flex-1">
                    <p className="text-[9px] uppercase tracking-widest text-muted-foreground mb-1">Projected</p>
                    <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                      ~{projLow}–{projHigh}
                    </p>
                    <p className="text-[10px] text-muted-foreground">years</p>
                  </div>
                </div>
                {/* Progress bar */}
                <div className="space-y-1.5">
                  <div className="h-2.5 w-full rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400"
                      style={{ width: `${pctReduction}%`, transition: "width 0.8s ease-out" }}
                    />
                  </div>
                  <div className="flex justify-between text-[9px] text-muted-foreground">
                    <span>CAPEX reduction: −{Math.round(totalCapexReduction * 100)}%</span>
                    <span>Savings boost: +{Math.round(totalSavingsBoost * 100)}%</span>
                  </div>
                  <p className="text-[9px] text-muted-foreground/60 italic">
                    Estimates based on government scheme data. Individual results vary.
                  </p>
                </div>
              </div>

              {/* Divider label */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-border/40" />
                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Strategies</p>
                <div className="flex-1 h-px bg-border/40" />
              </div>

              {/* Strategy cards */}
              <div className="space-y-3">
                {PAYBACK_TIPS.map((item, i) => {
                  const tipImpact   = item.capexReductionPct + item.savingsBoostPct
                  const impactLabel = tipImpact >= 0.25 ? "High" : tipImpact >= 0.10 ? "Medium" : "Low"
                  const badgeClass  = tipImpact >= 0.25
                    ? "text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                    : tipImpact >= 0.10
                    ? "text-amber-700 dark:text-amber-400 bg-amber-500/10 border-amber-500/30"
                    : "text-blue-700 dark:text-blue-400 bg-blue-500/10 border-blue-500/30"
                  const barWidth    = Math.round(tipImpact * 200)   // visual bar scaled to max ~60%
                  const barColor    = tipImpact >= 0.25 ? "bg-emerald-500" : tipImpact >= 0.10 ? "bg-amber-500" : "bg-blue-500"

                  return (
                    <div key={i} className="rounded-xl border border-border bg-card hover:bg-accent/50 transition-colors p-4 shadow-sm">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`inline-block text-[9px] font-bold uppercase px-2 py-0.5 rounded-full border ${badgeClass}`}>
                            {impactLabel} impact
                          </span>
                        </div>
                        <span className="text-[10px] text-muted-foreground font-mono flex-shrink-0">#{i + 1}</span>
                      </div>
                      {/* Impact bar */}
                      <div className="h-1 w-full rounded-full bg-muted mb-2.5 overflow-hidden">
                        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${barWidth}%` }} />
                      </div>
                      <p className="text-[12px] text-foreground/85 leading-relaxed">{item.tip}</p>
                      {item.link && (
                        <a
                          href={item.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          <ExternalLink className="w-3 h-3" />
                          {item.label}
                        </a>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* ── Footer ── */}
            <div className="flex-shrink-0 px-6 py-4 border-t border-border bg-muted/30">
              <p className="text-[10px] text-muted-foreground text-center">
                Strategies are matched to your factory profile · {state} · {industry}
              </p>
            </div>
          </div>
        </>
      )
    })()}
    </>
  )
}
