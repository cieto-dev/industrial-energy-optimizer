import React from "react"
import { Recommendation, RejectedScenarioExplanation } from "@/types/recommendation"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/reports/common/Table"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/reports/common/Card"
import { motion } from "framer-motion"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts"
interface Props {
  scenarios: RejectedScenarioExplanation[]
  recommended: Recommendation
}

export function ScenarioComparison({ scenarios, recommended }: Props) {
  // Prepare data for the chart
  const chartData = [
    {
      name: recommended.recommended_technology_sequence.join("+"),
      score: Math.round(recommended.composite_score * 100),
      isRecommended: true
    },
    ...scenarios.map(s => ({
      name: s.technology_sequence.join("+"),
      score: Math.round(s.composite_score * 100),
      isRecommended: false
    }))
  ].sort((a, b) => b.score - a.score)

  return (
    <Card className="overflow-hidden border-border/50 shadow-sm">
      <CardHeader className="bg-surface-muted border-b border-border/40 pb-4">
        <CardTitle className="text-xl flex items-center gap-2">
          Scenario Comparison Matrix
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="grid lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x border-border/40">
          
          {/* Visual Chart Section */}
          <div className="p-6 bg-surface/30 flex flex-col">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-6">MCDA Score Distribution</h4>
            <div className="flex-1 min-h-[250px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="var(--border)" opacity={0.5} />
                  <XAxis type="number" domain={[0, 100]} hide />
                  <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 10, fill: "var(--foreground)" }} tickLine={false} axisLine={false} />
                  <Tooltip 
                    cursor={{ fill: 'var(--accent)', opacity: 0.05 }}
                    contentStyle={{ backgroundColor: 'var(--card)', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '12px' }}
                  />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={24}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.isRecommended ? "var(--primary)" : "var(--muted-foreground)"} opacity={entry.isRecommended ? 1 : 0.4} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Table Section */}
          <div className="p-0 bg-card overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-surface-muted/50 hover:bg-surface-muted/50">
                  <TableHead className="w-[80px] text-center text-[10px] uppercase tracking-wider">Rank</TableHead>
                  <TableHead className="text-[10px] uppercase tracking-wider">Technology Pathway</TableHead>
                  <TableHead className="text-right text-[10px] uppercase tracking-wider">MCDA Score</TableHead>
                  <TableHead className="text-[10px] uppercase tracking-wider">Status / Weakness</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {/* Row 1: Recommended */}
                <TableRow className="bg-primary/5 font-medium group hover:bg-primary/10 transition-colors cursor-pointer border-b border-border/40">
                  <TableCell className="text-center font-bold text-primary group-hover:scale-110 transition-transform">1</TableCell>
                  <TableCell className="capitalize text-foreground font-semibold">{recommended.recommended_technology_sequence.join(" + ").replace(/_/g, " ")}</TableCell>
                  <TableCell className="text-right text-primary font-bold">{(recommended.composite_score * 100).toFixed(0)}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center rounded-full bg-primary/20 border border-primary/30 px-2.5 py-0.5 text-xs font-semibold text-primary">
                      Recommended
                    </span>
                  </TableCell>
                </TableRow>

                {/* Remaining Rows */}
                {scenarios.sort((a, b) => a.rank - b.rank).map((scenario, i) => (
                  <TableRow key={scenario.scenario_id} className="group hover:bg-surface-muted transition-colors cursor-pointer border-b border-border/40 last:border-0">
                    <TableCell className="text-center font-medium text-muted-foreground group-hover:text-foreground transition-colors">{scenario.rank}</TableCell>
                    <TableCell className="capitalize font-medium text-muted-foreground group-hover:text-foreground transition-colors">{scenario.technology_sequence.join(" + ").replace(/_/g, " ")}</TableCell>
                    <TableCell className="text-right font-medium text-muted-foreground group-hover:text-foreground transition-colors">{(scenario.composite_score * 100).toFixed(0)}</TableCell>
                    <TableCell className="text-muted-foreground text-xs group-hover:text-foreground transition-colors">
                      {scenario.key_weakness}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
