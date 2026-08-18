"use client"
import React from "react"
import { Recommendation } from "@/types/recommendation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/reports/common/Card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/reports/common/Table"
import { TrendingDown, IndianRupee, Calendar, Award } from "lucide-react"

interface ReportPreviewProps {
  recommendation: Recommendation
}

export function ReportPreview({ recommendation }: ReportPreviewProps) {
  const formatCurrency = (v: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v)

  return (
    <div className="space-y-6">
      {/* Header summary */}
      <Card>
        <CardHeader className="border-b pb-3">
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-xl">{recommendation.factory_name}</CardTitle>
              <p className="text-sm text-muted-foreground mt-0.5">
                {recommendation.industry.charAt(0).toUpperCase() + recommendation.industry.slice(1)} &bull; {recommendation.state}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Generated</p>
              <p className="text-sm font-medium">
                {new Date(recommendation.generated_at).toLocaleDateString("en-IN", {
                  day: "numeric", month: "short", year: "numeric"
                })}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-muted-foreground flex items-center gap-1"><IndianRupee className="w-3 h-3" /> CAPEX</p>
            <p className="font-semibold text-sm">{formatCurrency(recommendation.capex_total_inr)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground flex items-center gap-1"><TrendingDown className="w-3 h-3" /> CO2 Cut</p>
            <p className="font-semibold text-sm text-green-600">{recommendation.co2_reduction_pct.toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground flex items-center gap-1"><Calendar className="w-3 h-3" /> Payback</p>
            <p className="font-semibold text-sm">
              {recommendation.payback_range_years[0].toFixed(1)}–{recommendation.payback_range_years[1].toFixed(1)} yrs
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground flex items-center gap-1"><Award className="w-3 h-3" /> MCDA Score</p>
            <p className="font-semibold text-sm">{(recommendation.composite_score * 100).toFixed(0)} / 100</p>
          </div>
        </CardContent>
      </Card>

      {/* Recommended pathway */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Recommended Pathway</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-lg font-bold capitalize mb-2">
            {recommendation.recommended_technology_sequence.join(" + ").replace(/_/g, " ")}
          </p>
          <ul className="space-y-1">
            {recommendation.explanation.why_selected.map((r, i) => (
              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="text-primary mt-0.5 shrink-0">•</span> {r}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Scenario comparison mini-table */}
      {recommendation.explanation.why_others_rejected.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Scenario Ranking</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/40">
                    <TableHead className="w-16 text-center">Rank</TableHead>
                    <TableHead>Pathway</TableHead>
                    <TableHead className="text-right">Score</TableHead>
                    <TableHead>Key Weakness</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow className="bg-primary/5 font-medium">
                    <TableCell className="text-center text-primary font-bold">1</TableCell>
                    <TableCell className="capitalize">
                      {recommendation.recommended_technology_sequence.join(" + ").replace(/_/g, " ")}
                    </TableCell>
                    <TableCell className="text-right text-primary">
                      {(recommendation.composite_score * 100).toFixed(0)}
                    </TableCell>
                    <TableCell>
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800 dark:bg-green-900 dark:text-green-300">
                        Recommended
                      </span>
                    </TableCell>
                  </TableRow>
                  {recommendation.explanation.why_others_rejected
                    .sort((a, b) => a.rank - b.rank)
                    .map((s) => (
                      <TableRow key={s.scenario_id}>
                        <TableCell className="text-center">{s.rank}</TableCell>
                        <TableCell className="capitalize">
                          {s.technology_sequence.join(" + ").replace(/_/g, " ")}
                        </TableCell>
                        <TableCell className="text-right">{(s.composite_score * 100).toFixed(0)}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">{s.key_weakness}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Policy */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Policy & Financing</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Eligible schemes</span>
            <span className="font-medium">
              {recommendation.explanation.policy_benefits.eligible_schemes.join(", ") || "None matched"}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Estimated benefit</span>
            <span className="font-medium">
              {formatCurrency(recommendation.explanation.policy_benefits.estimated_total_benefit_inr)}
            </span>
          </div>
          {!recommendation.explanation.policy_benefits.total_benefit_verified && (
            <p className="text-xs text-muted-foreground italic border-l-2 pl-2 mt-2">
              * {recommendation.explanation.policy_benefits.disclaimer}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
