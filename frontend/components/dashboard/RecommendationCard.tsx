import React from "react"
import { Recommendation } from "@/types/recommendation"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/reports/common/Card"
import { CheckCircle2, TrendingDown, IndianRupee, ShieldAlert, Award } from "lucide-react"

interface Props {
  recommendation: Recommendation
}

export function RecommendationCard({ recommendation }: Props) {
  const formatCurrency = (val: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val)
  
  return (
    <Card className="border-primary/20 bg-primary/5 shadow-md overflow-hidden relative">
      <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
      <CardHeader className="pb-3 border-b border-primary/10 bg-primary/5">
        <div className="flex justify-between items-start">
          <div>
            <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-primary text-primary-foreground hover:bg-primary/80 mb-2">
              Primary Recommendation
            </div>
            <CardTitle className="text-2xl font-bold flex items-center gap-2">
              {recommendation.recommended_technology_sequence.map(t => t.replace(/_/g, ' ').toUpperCase()).join(" + ")}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {recommendation.recommended_is_cheapest 
                ? "This is the most cost-effective option while meeting emission constraints."
                : "Selected for optimal balance of risk, emissions, and long-term economic value over cheaper alternatives."}
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-black text-primary">{(recommendation.composite_score * 100).toFixed(0)}</div>
            <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">MCDA Score</div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <IndianRupee className="w-4 h-4" />
            <span>Total CAPEX</span>
          </div>
          <div className="text-2xl font-semibold">{formatCurrency(recommendation.capex_total_inr)}</div>
        </div>
        
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <TrendingDown className="w-4 h-4 text-green-500" />
            <span>CO2 Reduction</span>
          </div>
          <div className="text-2xl font-semibold text-green-600">{recommendation.co2_reduction_pct.toFixed(1)}%</div>
        </div>

        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle2 className="w-4 h-4 text-blue-500" />
            <span>Payback Range</span>
          </div>
          <div className="text-2xl font-semibold text-blue-600">
            {recommendation.payback_range_years[0].toFixed(1)} - {recommendation.payback_range_years[1].toFixed(1)} yrs
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Award className="w-4 h-4 text-amber-500" />
            <span>Policy Benefit</span>
          </div>
          <div className="text-xl font-semibold text-amber-600">
            {formatCurrency(recommendation.explanation.policy_benefits.estimated_total_benefit_inr)}
          </div>
          <div className="text-xs text-muted-foreground line-clamp-1" title={recommendation.explanation.policy_benefits.eligible_schemes.join(", ")}>
            {recommendation.explanation.policy_benefits.eligible_schemes.length} schemes matched
          </div>
        </div>
      </CardContent>
      
      <div className="px-6 py-4 bg-card border-t text-sm">
        <h4 className="font-semibold mb-2">Why this was selected:</h4>
        <ul className="space-y-1">
          {recommendation.explanation.why_selected.map((reason, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-primary mt-0.5">•</span>
              <span className="text-muted-foreground">{reason}</span>
            </li>
          ))}
        </ul>
      </div>

      <CardFooter className="bg-muted/50 border-t px-6 py-3 flex flex-col items-start gap-1">
        <div className="flex items-center gap-2 text-sm font-medium">
          <ShieldAlert className="w-4 h-4 text-orange-500" />
          Risk Interpretation: {recommendation.explanation.sensitivity_notes.risk_interpretation}
        </div>
        {!recommendation.explanation.policy_benefits.total_benefit_verified && (
          <p className="text-xs text-muted-foreground italic mt-2 border-l-2 pl-2">
            * {recommendation.explanation.policy_benefits.disclaimer}
          </p>
        )}
      </CardFooter>
    </Card>
  )
}
