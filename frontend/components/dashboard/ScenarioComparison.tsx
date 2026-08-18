import React from "react"
import { Recommendation, RejectedScenarioExplanation } from "@/types/recommendation"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/reports/common/Table"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/reports/common/Card"


interface Props {
  scenarios: RejectedScenarioExplanation[]
  recommended: Recommendation
}

export function ScenarioComparison({ scenarios, recommended }: Props) {
  // We need to merge the recommended scenario with the rejected ones to display them all in a single table.
  // The 'Recommendation' has the details for the chosen one, while 'RejectedScenarioExplanation' has details for the others.
  
  // Note: the backend 'RejectedScenarioExplanation' contains reason, rank, composite_score, key_weakness.
  // To show CAPEX/payback for rejected scenarios, we'd need them provided by the backend. 
  // Wait, the backend model for RejectedScenarioExplanation doesn't include CAPEX or Payback directly in the log.
  // However, the `Recommendation` object doesn't include the full `scenarios` dictionary in its output schema natively, unless we added it.
  // Let's display what we have: Rank, Scenario, Score, Key Weakness.

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scenario Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="w-[80px] text-center">Rank</TableHead>
                <TableHead>Technology Pathway</TableHead>
                <TableHead className="text-right">MCDA Score</TableHead>
                <TableHead>Status / Key Weakness</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {/* Row 1: Recommended */}
              <TableRow className="bg-primary/5 font-medium">
                <TableCell className="text-center font-bold text-primary">1</TableCell>
                <TableCell className="capitalize">{recommended.recommended_technology_sequence.join(" + ").replace(/_/g, " ")}</TableCell>
                <TableCell className="text-right text-primary">{(recommended.composite_score * 100).toFixed(0)}</TableCell>
                <TableCell>
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-800 dark:bg-green-900 dark:text-green-300">
                    Recommended
                  </span>
                </TableCell>
              </TableRow>

              {/* Remaining Rows */}
              {scenarios.sort((a, b) => a.rank - b.rank).map((scenario) => (
                <TableRow key={scenario.scenario_id}>
                  <TableCell className="text-center">{scenario.rank}</TableCell>
                  <TableCell className="capitalize">{scenario.technology_sequence.join(" + ").replace(/_/g, " ")}</TableCell>
                  <TableCell className="text-right">{(scenario.composite_score * 100).toFixed(0)}</TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {scenario.key_weakness}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
