"use client"
import React, { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import { apiService } from "@/services/api"
import { Recommendation } from "@/types/recommendation"

import { RecommendationCard } from "@/components/dashboard/RecommendationCard"
import { ScenarioComparison } from "@/components/dashboard/ScenarioComparison"
import { RejectionLog } from "@/components/dashboard/RejectionLog"

export default function DashboardPage() {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true)
        const savedResult = localStorage.getItem("last_optimization")
        let recId = "mock-id"
        if (savedResult) {
          const parsed = JSON.parse(savedResult)
          if (parsed.recommended_scenario_id) recId = parsed.recommended_scenario_id
        }
        const res = await apiService.getRecommendation(recId)
        if (res.status === "success" && res.recommendation) {
          setRecommendation(res.recommendation as Recommendation)
        } else {
          setError("Failed to load recommendation data.")
        }
      } catch (err: any) {
        console.error(err)
        setError("Error communicating with backend.")
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [])

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center h-full p-6">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
          <p className="text-zinc-400 text-sm">Loading recommendation...</p>
        </div>
      </div>
    )
  }

  if (error || !recommendation) {
    return (
      <div className="p-6">
        <div className="mx-auto max-w-5xl bg-red-500/10 text-red-400 border border-red-500/20 p-4 rounded-xl">
          {error || "Unknown error occurred."}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mx-auto max-w-6xl space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Recommendation Dashboard</h1>
          <p className="text-zinc-400 mt-1">
            Factory: <span className="font-medium text-white">{recommendation.factory_name}</span>
            {" • "}{recommendation.industry.charAt(0).toUpperCase() + recommendation.industry.slice(1)}
            {" • "}{recommendation.state}
          </p>
        </div>

        <RecommendationCard recommendation={recommendation} />
        <ScenarioComparison scenarios={recommendation.explanation.why_others_rejected} recommended={recommendation} />
        <RejectionLog rejections={recommendation.explanation.why_others_rejected} />
      </div>
    </div>
  )
}
