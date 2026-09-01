import React, { useState } from "react"
import { Recommendation, RejectedScenarioExplanation } from "@/types/recommendation"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/reports/common/Card"
import { AlertCircle, CheckCircle2 } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface Props {
  rejections: RejectedScenarioExplanation[]
  recommendation?: Recommendation
}

export function RejectionLog({ rejections, recommendation }: Props) {
  const recommendedTech = recommendation?.recommended_technology_sequence?.join(" + ").replace(/_/g, " ") ?? "Recommended Pathway";
  
  const allScenarios = [
    {
      id: "recommended",
      rank: 1,
      title: recommendedTech,
      isRecommended: true,
      score: recommendation?.composite_score ? Math.round(recommendation.composite_score * 100) : 100,
      reason: recommendation?.explanation?.why_selected?.join(" ") || "This pathway was selected because it offers the best balance of cost, emissions reduction, and reliability.",
      key_weakness: "None (Optimal)",
    },
    ...rejections.map(r => ({
      id: r.scenario_id,
      rank: r.rank,
      title: r.technology_sequence.join(" + ").replace(/_/g, " "),
      isRecommended: false,
      score: Math.round(r.composite_score * 100),
      reason: r.reason,
      key_weakness: r.key_weakness,
    }))
  ];

  const [activeTabId, setActiveTabId] = useState(allScenarios[0]?.id);

  if (allScenarios.length === 0 || (allScenarios.length === 1 && !allScenarios[0].isRecommended)) return null;

  const activeScenario = allScenarios.find(s => s.id === activeTabId) || allScenarios[0];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scenario Analysis & Decision Log</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Tabs Sidebar */}
          <div className="lg:w-1/3 flex flex-col gap-2">
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
                <div className={`mt-0.5 p-1 rounded-full shrink-0 ${scenario.isRecommended ? 'bg-emerald-500/20 text-emerald-500' : 'bg-destructive/10 text-destructive'}`}>
                  {scenario.isRecommended ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                </div>
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-widest opacity-80 mb-0.5">Rank #{scenario.rank}</p>
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
                      <span className={`text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded-full border ${activeScenario.isRecommended ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-destructive/10 text-destructive border-destructive/20'}`}>
                        {activeScenario.isRecommended ? 'Recommended Selection' : 'Rejected Alternative'}
                      </span>
                      <span className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground bg-surface px-2.5 py-0.5 rounded-full border border-border/50">
                        Rank #{activeScenario.rank}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold capitalize text-foreground leading-tight">
                      {activeScenario.title}
                    </h3>
                  </div>
                  
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">MCDA Score</p>
                    <div className="flex items-center gap-2">
                      <span className={`text-2xl font-black ${activeScenario.isRecommended ? 'text-emerald-500' : 'text-foreground'}`}>
                        {activeScenario.score}
                      </span>
                      <span className="text-sm text-muted-foreground font-medium">/ 100</span>
                    </div>
                  </div>
                </div>

                <div className="flex-1 space-y-6">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
                      {activeScenario.isRecommended ? 'Why this was selected' : 'Why this was rejected'}
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
