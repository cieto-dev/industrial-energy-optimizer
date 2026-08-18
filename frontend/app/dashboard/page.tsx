"use client"
import React, { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import { Sidebar } from "@/components/layout/Sidebar"
import { Navbar } from "@/components/layout/Navbar"
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
  const router = useRouter()

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true)
        // Check if there is an optimization result in local storage
        const savedResult = localStorage.getItem("last_optimization")
        let recId = "mock-id"
        if (savedResult) {
          const parsed = JSON.parse(savedResult)
          if (parsed.recommended_scenario_id) {
            recId = parsed.recommended_scenario_id
          }
        }
        
        // Fetch the recommendation object from backend
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
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Navbar />
          <main className="flex-1 overflow-y-auto bg-background p-6 flex items-center justify-center">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-muted-foreground text-sm">Loading recommendation...</p>
            </div>
          </main>
        </div>
      </div>
    )
  }

  if (error || !recommendation) {
    return (
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Navbar />
          <main className="flex-1 overflow-y-auto bg-background p-6">
            <div className="mx-auto max-w-5xl">
              <div className="bg-destructive/15 text-destructive p-4 rounded-md">
                {error || "Unknown error occurred."}
              </div>
            </div>
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="mx-auto max-w-6xl space-y-8">
            
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Recommendation Dashboard</h1>
                <p className="text-muted-foreground mt-1">
                  Factory: <span className="font-medium text-foreground">{recommendation.factory_name}</span> 
                  {" • "}{recommendation.industry.charAt(0).toUpperCase() + recommendation.industry.slice(1)} 
                  {" • "}{recommendation.state}
                </p>
              </div>
            </div>

            <RecommendationCard recommendation={recommendation} />

            <ScenarioComparison scenarios={recommendation.explanation.why_others_rejected} recommended={recommendation} />

            <RejectionLog rejections={recommendation.explanation.why_others_rejected} />

          </div>
        </main>
      </div>
    </div>
  )
}
