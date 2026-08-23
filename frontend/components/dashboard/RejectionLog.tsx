import React from "react"
import { RejectedScenarioExplanation } from "@/types/recommendation"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/reports/common/Card"
import { AlertCircle } from "lucide-react"
import { motion } from "framer-motion"
interface Props {
  rejections: RejectedScenarioExplanation[]
}

export function RejectionLog({ rejections }: Props) {
  if (rejections.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Why other technologies were not selected</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rejections.map((rejection, i) => {
            const scorePct = Math.round(rejection.composite_score * 100)
            return (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1, duration: 0.4 }}
                key={rejection.scenario_id} 
                className="group p-5 rounded-xl border border-border bg-card hover:bg-surface-muted hover:border-border/80 transition-all cursor-pointer flex flex-col gap-4 shadow-sm hover:shadow-md"
              >
                {/* Header & Score Visual */}
                <div className="flex items-start justify-between border-b border-border/40 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="bg-destructive/10 p-2 rounded-full shrink-0 group-hover:scale-110 transition-transform">
                      <AlertCircle className="w-5 h-5 text-destructive" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-0.5">Rank #{rejection.rank}</p>
                      <h4 className="font-semibold text-base capitalize group-hover:text-primary transition-colors leading-tight">
                        {rejection.technology_sequence.join(" + ").replace(/_/g, " ")}
                      </h4>
                    </div>
                  </div>
                  
                  {/* Score Visualization */}
                  <div className="flex flex-col items-end gap-1">
                    <span className="text-xl font-black text-foreground">{scorePct}</span>
                    <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-destructive/60" style={{ width: `${scorePct}%` }} />
                    </div>
                  </div>
                </div>

                {/* Explanation */}
                <div className="flex-1">
                  <p className="text-muted-foreground text-sm leading-relaxed mb-4">
                    {rejection.reason}
                  </p>
                  <div className="inline-flex items-center rounded-md border border-border px-2.5 py-1 text-[11px] font-semibold text-muted-foreground bg-background group-hover:bg-primary/5 group-hover:text-foreground transition-colors uppercase tracking-wider">
                    Weakness: {rejection.key_weakness}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
