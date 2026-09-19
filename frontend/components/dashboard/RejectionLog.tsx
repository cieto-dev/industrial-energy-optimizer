import React, { useState } from "react"
import type { ScenarioPathwayEnriched } from "@/types/optimization"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/reports/common/Card"
import { AlertCircle, CheckCircle2, ShieldAlert } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface Props {
  pathways: ScenarioPathwayEnriched[]
  rejectedTechs: Array<Record<string, unknown>>
}

export function RejectionLog({ pathways, rejectedTechs }: Props) {
  const recommendedTech = pathways[0]?.technology_sequence?.join(" + ").replace(/_/g, " ") ?? "Recommended Pathway"
  
  const allScenarios: any[] = []

  // Add feasible pathways (ranked)
  pathways.forEach((p, index) => {
    const isRecommended = index === 0
    const title = p.technology_sequence?.join(" + ").replace(/_/g, " ") ?? "Unknown Pathway"
    const score = p.reliability_score_pct ? Math.round(p.reliability_score_pct) : 0
    
    const reason = isRecommended 
       ? "This pathway was selected because it can be integrated without stopping your production lines, matches your exact temperature needs, and has the highest validated reliability score."
       : "This alternative is structurally feasible, but was ranked lower because it may introduce supply-chain complexities or require more invasive modifications to your existing lines."

    const key_weakness = isRecommended ? "None (Optimal Operational Fit)" : "Lower operational integration score"

    allScenarios.push({
      id: `feasible-${index}`,
      rank: index + 1,
      title,
      isRecommended,
      isFeasible: true,
      score,
      reason,
      key_weakness
    })
  })

  // Add rejected technologies
  rejectedTechs.forEach((r, index) => {
    const title = (r.technology as string)?.replace(/_/g, " ") || "Rejected Technology"
    
    // Translate raw technical reasons into operational language
    const rawReason = ((r.reason as string) || "Did not pass technical constraints").toLowerCase()
    let reason = rawReason
    if (rawReason.includes("temperature")) {
       reason = "Cannot reach your required process temperature. Attempting to use this would require installing an additional booster boiler, defeating the purpose."
    } else if (rawReason.includes("capacity") || rawReason.includes("throughput")) {
       reason = "Cannot reliably match your current production throughput. Risk of process bottlenecks."
    } else if (rawReason.includes("fuel") || rawReason.includes("biomass")) {
       reason = "Local supply chain for this fuel is not reliable enough to guarantee uninterrupted production."
    } else {
       reason = "Rejected to protect production continuity. Integration would likely require a full line shutdown or significant structural modifications."
    }

    const rawRule = ((r.rule_failed as string) || "Technical constraint failure").toLowerCase()
    let key_weakness = "Operational Disruption Risk"
    if (rawRule.includes("temp")) key_weakness = "Insufficient Temperature"
    else if (rawRule.includes("space") || rawRule.includes("footprint")) key_weakness = "Space Constraints"
    else if (rawRule.includes("cost") || rawRule.includes("capex")) key_weakness = "Prohibitive Capital Requirement"
    else if (rawRule.includes("grid")) key_weakness = "Grid Unreliability"

    allScenarios.push({
      id: `rejected-${index}`,
      rank: null,
      title,
      isRecommended: false,
      isFeasible: false,
      score: 0,
      reason,
      key_weakness
    })
  })

  const [activeTabId, setActiveTabId] = useState(allScenarios[0]?.id)

  if (allScenarios.length === 0 || (allScenarios.length === 1 && !allScenarios[0].isRecommended)) return null

  const activeScenario = allScenarios.find(s => s.id === activeTabId) || allScenarios[0]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scenario Analysis & Decision Log</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Tabs Sidebar */}
          <div className="lg:w-1/3 flex flex-col gap-2 max-h-[500px] overflow-y-auto pr-2">
            {allScenarios.map((scenario) => (
              <button
                key={scenario.id}
                onClick={() => setActiveTabId(scenario.id)}
                className={`flex items-start gap-3 p-3 rounded-xl border text-left transition-all ${
                  activeTabId === scenario.id
                    ? "bg-primary/10 border-primary shadow-sm"
                    : "bg-surface-muted border-border/40 hover:bg-surface hover:border-border text-muted-foreground"
                }`}
              >
                <div className={`mt-0.5 p-1 rounded-full shrink-0 ${
                  scenario.isRecommended ? 'bg-emerald-500/20 text-emerald-500' :
                  scenario.isFeasible ? 'bg-blue-500/20 text-blue-500' :
                  'bg-destructive/10 text-destructive'
                }`}>
                  {scenario.isRecommended ? <CheckCircle2 className="w-4 h-4" /> : 
                   scenario.isFeasible ? <ShieldAlert className="w-4 h-4" /> : 
                   <AlertCircle className="w-4 h-4" />}
                </div>
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-widest opacity-80 mb-0.5">
                    {scenario.rank ? `Rank #${scenario.rank}` : "Rejected early"}
                  </p>
                  <p className={`text-sm font-semibold capitalize leading-tight ${activeTabId === scenario.id ? 'text-primary' : ''}`}>
                    {scenario.title}
                  </p>
                </div>
              </button>
            ))}
          </div>

          {/* Content Pane */}
          <div className="lg:w-2/3 bg-surface-muted/30 border border-border/50 rounded-xl p-6 relative overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeScenario.id}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
                className="h-full flex flex-col"
              >
                <div className="flex items-start justify-between border-b border-border/40 pb-5 mb-5">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded-full border ${
                        activeScenario.isRecommended ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 
                        activeScenario.isFeasible ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' :
                        'bg-destructive/10 text-destructive border-destructive/20'
                      }`}>
                        {activeScenario.isRecommended ? 'Recommended Selection' : 
                         activeScenario.isFeasible ? 'Alternative Pathway' :
                         'Rejected Filter'}
                      </span>
                      {activeScenario.rank && (
                        <span className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground bg-surface px-2.5 py-0.5 rounded-full border border-border/50">
                          Rank #{activeScenario.rank}
                        </span>
                      )}
                    </div>
                    <h3 className="text-xl font-bold capitalize text-foreground leading-tight">
                      {activeScenario.title}
                    </h3>
                  </div>
                  
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Match Score</p>
                    <div className="flex items-center gap-2">
                      <span className={`text-2xl font-black ${
                        activeScenario.isRecommended ? 'text-emerald-500' : 
                        activeScenario.isFeasible ? 'text-blue-500' :
                        'text-foreground'
                      }`}>
                        {activeScenario.score}
                      </span>
                      <span className="text-sm text-muted-foreground font-medium">%</span>
                    </div>
                  </div>
                </div>

                <div className="flex-1 space-y-6">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
                      {activeScenario.isRecommended ? 'Why this was selected' : 'Why this was rejected or ranked lower'}
                    </h4>
                    <p className="text-foreground/90 text-sm leading-relaxed">
                      {activeScenario.reason}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Key Weakness / Limitation</h4>
                    <div className="inline-flex items-center rounded-lg border border-border/50 bg-background px-3 py-2 text-xs font-semibold text-muted-foreground capitalize">
                      {activeScenario.key_weakness}
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
