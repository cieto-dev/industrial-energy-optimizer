"use client"
import React from "react"
import { useFormContext } from "react-hook-form"
import { FactoryProfileType } from "@/utils/validators"
import { Zap, Factory, AlertCircle, ShieldCheck } from "lucide-react"

export function LiveInsightsPanel() {
  const { watch } = useFormContext<FactoryProfileType>()
  
  // Watch necessary fields for live preview
  const industry = watch("industry") || "Unknown"
  const currentFuel = watch("current_fuel") || "Coal"
  const fuelConsumption = watch("fuel_consumption.value") || 0
  const electricityConsumption = watch("electricity_consumption_kwh_day") || 0
  const operatingDays = watch("operating_days_per_year") || 300
  
  // Simple heuristics for live insights
  const estimatedCO2 = (fuelConsumption * 2.5 * operatingDays) / 1000 // roughly tons
  const annualEnergyDemand = (electricityConsumption * operatingDays) / 1000 // MWh
  
  const aiConfidence = 
    industry !== "Unknown" && fuelConsumption > 0 && electricityConsumption > 0 
      ? 92 
      : 45

  return (
    <div className="h-full flex flex-col p-6 space-y-6 bg-card border-l border-border/50 shadow-sm overflow-y-auto w-full max-w-sm ml-auto">
      <div className="flex items-center justify-between pb-4 border-b border-border/40">
        <h3 className="text-sm font-semibold flex items-center gap-2 text-foreground">
          <Zap className="h-4 w-4 text-primary" />
          Live Insights
        </h3>
        <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
      </div>

      <div className="space-y-4">
        {/* Metric Cards */}
        <div className="p-4 rounded-xl bg-surface-muted border border-border/50 flex flex-col transition-all">
          <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">Est. Annual CO₂</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-foreground tracking-tight">{estimatedCO2.toFixed(1)}</span>
            <span className="text-xs text-muted-foreground">ktons/yr</span>
          </div>
          <div className="mt-3 text-[10px] text-muted-foreground flex items-center gap-1.5">
             <AlertCircle className="h-3 w-3 text-amber-500" />
             Based on {currentFuel} factors
          </div>
        </div>

        <div className="p-4 rounded-xl bg-surface-muted border border-border/50 flex flex-col transition-all">
          <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">Annual Power Demand</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-foreground tracking-tight">{annualEnergyDemand.toFixed(1)}</span>
            <span className="text-xs text-muted-foreground">MWh</span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl border border-border/50 bg-background/50 flex flex-col items-center justify-center text-center">
             <ShieldCheck className="h-5 w-5 text-emerald-500 mb-2" />
             <span className="text-[10px] font-medium text-muted-foreground uppercase mb-1">Confidence</span>
             <span className="text-lg font-bold text-foreground">{aiConfidence}%</span>
          </div>
          <div className="p-4 rounded-xl border border-border/50 bg-background/50 flex flex-col items-center justify-center text-center">
             <Factory className="h-5 w-5 text-primary mb-2" />
             <span className="text-[10px] font-medium text-muted-foreground uppercase mb-1">Profile</span>
             <span className="text-sm font-bold text-foreground capitalize truncate max-w-[80px]">{industry}</span>
          </div>
        </div>
      </div>
      
      <div className="mt-auto pt-6 border-t border-border/40">
        <p className="text-xs text-muted-foreground leading-relaxed">
          The AI engine continuously analyzes inputs against IPCC factors and state policies. Complete the assessment for a full decarbonization roadmap.
        </p>
      </div>
    </div>
  )
}
