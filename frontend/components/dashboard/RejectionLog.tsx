import React from "react"
import { RejectedScenarioExplanation } from "@/types/recommendation"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/reports/common/Card"
import { AlertCircle } from "lucide-react"

interface Props {
  rejections: RejectedScenarioExplanation[]
}

export function RejectionLog({ rejections }: Props) {
  if (rejections.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Technology Rejection Log: "Why not X?"</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {rejections.map((rejection) => (
            <div key={rejection.scenario_id} className="p-4 rounded-lg border bg-card flex flex-col sm:flex-row gap-4 items-start">
              <div className="bg-destructive/10 p-2 rounded-full mt-1 shrink-0">
                <AlertCircle className="w-5 h-5 text-destructive" />
              </div>
              <div>
                <h4 className="font-semibold text-lg capitalize mb-1">
                  {rejection.technology_sequence.join(" + ").replace(/_/g, " ")}
                </h4>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {rejection.reason}
                </p>
                <div className="mt-3 inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold text-muted-foreground bg-muted/50">
                  Key Weakness: {rejection.key_weakness}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
