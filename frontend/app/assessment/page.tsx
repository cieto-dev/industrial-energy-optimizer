"use client"
import React, { useState } from "react"
import { useForm, FormProvider } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useRouter } from "next/navigation"
import { Factory, Cpu, Network } from "lucide-react"

import { Button } from "@/components/reports/common/Button"

import { FactoryProfileSchema, FactoryProfileType } from "@/utils/validators"
import { apiService } from "@/services/api"

import { IndustryForm } from "@/components/forms/IndustryForm"
import { EnergyInputForm } from "@/components/forms/EnergyInputForm"
import { ProcessForm } from "@/components/forms/ProcessForm"
import { ConstraintsForm } from "@/components/forms/ConstraintsForm"
import { EligibilityForm } from "@/components/forms/EligibilityForm"
import { LiveInsightsPanel } from "@/components/assessment/LiveInsightsPanel"

const STEPS = [
  { id: "industry", title: "General", component: IndustryForm, fields: ["name", "industry", "state", "district"] },
  { id: "energy", title: "Production", component: EnergyInputForm, fields: ["production_per_day.value", "production_per_day.unit", "operating_hours_per_day", "operating_days_per_year", "current_fuel", "fuel_consumption.value", "fuel_consumption.unit"] },
  { id: "process", title: "Technical", component: ProcessForm, fields: ["required_process_temperature_c", "electricity_consumption_kwh_day"] },
  { id: "constraints", title: "Constraints", component: ConstraintsForm, fields: ["roof_area_sqm", "available_land_sqm", "budget_inr", "grid_reliability_pct"] },
  { id: "eligibility", title: "Eligibility", component: EligibilityForm, fields: ["msme_classification", "udyam_registered", "udyam_number", "annual_turnover_inr", "plant_and_machinery_or_equipment_investment_inr", "project_type", "project_cost_inr", "loan_amount_inr", "existing_or_new_project", "brownfield_or_greenfield", "cluster_name", "cluster_is_adeetie_identified", "annual_energy_savings_percent", "special_category"] }
]

export default function AssessmentPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const lastStepChangeTime = React.useRef(0)
  const router = useRouter()

  const methods = useForm<FactoryProfileType>({
    resolver: zodResolver(FactoryProfileSchema),
    mode: "onTouched",
    defaultValues: {
      name: "Surat Textile Mill Factory",
      industry: "textile",
      state: "Gujarat",
      district: "Surat",
      production_per_day: { value: 500, unit: "kg" },
      operating_hours_per_day: 16,
      operating_days_per_year: 300,
      current_fuel: "coal",
      fuel_consumption: { value: 2000, unit: "kg" },
      electricity_consumption_kwh_day: 5000,
      required_process_temperature_c: 150,
      roof_area_sqm: 2000,
      available_land_sqm: 500,
      budget_inr: 20000000,
      grid_reliability_pct: 95,
      annual_turnover_inr: 50000000,
      plant_and_machinery_or_equipment_investment_inr: 25000000,
      project_cost_inr: 15000000,
      project_type: "energy_efficiency",
      existing_or_new_project: "existing",
      msme_classification: "small",
      udyam_registered: true,
      special_category: {
        women_owned: false,
        sc_st_owned: false,
        pwd_owned: false,
        agniveer_owned: false,
        transgender_owned: false,
        north_east_region: false,
        jammu_kashmir: false,
        ladakh: false,
        aspirational_district: false,
        identified_credit_deficient_district: false
      }
    }
  })

  const { trigger, handleSubmit } = methods

  const nextStep = async () => {
    const fieldsToValidate = STEPS[currentStep].fields as any
    const isStepValid = await trigger(fieldsToValidate)
    
    if (isStepValid) {
      setCurrentStep(prev => {
        lastStepChangeTime.current = Date.now()
        return Math.min(prev + 1, STEPS.length - 1)
      })
    }
  }

  const prevStep = () => {
    setCurrentStep(prev => {
      lastStepChangeTime.current = Date.now()
      return Math.max(prev - 1, 0)
    })
  }

  const onSubmit = async (data: FactoryProfileType) => {
    setIsSubmitting(true)
    setIsAnalyzing(true)
    setSubmitError(null)
    try {
      const payload = {
        ...data,
        factory_id: data.factory_id || `fac_${Math.random().toString(36).substr(2, 9)}`,
      }
      const response = await apiService.optimize(payload as any)
      
      const enrichedResponse = {
        ...response,
        factory_name: data.name,
        industry: data.industry,
        state: data.state,
        district: data.district,
        cluster_name: data.cluster_name ?? "",
        special_category: data.special_category ?? {},
      }
      localStorage.setItem("last_optimization", JSON.stringify(enrichedResponse))
      
      setTimeout(() => {
        router.push("/report")
      }, 3500)
    } catch (error: any) {
      console.error("Submission failed", error)
      setSubmitError(error?.message ?? "Failed to submit assessment. Please check your inputs and try again.")
      setIsSubmitting(false)
      setIsAnalyzing(false)
    }
  }

  // Called when form has validation errors — show them clearly
  const onInvalid = (errors: any) => {
    console.error("Form validation errors:", errors)
    const firstError = Object.values(errors)[0] as any
    setSubmitError(`Please fix: ${firstError?.message ?? "some fields have errors"}`)
  }

  const CurrentComponent = STEPS[currentStep].component

  if (isAnalyzing) {
    return (
      <div className="flex flex-col h-[calc(100vh-56px)] bg-background text-foreground items-center justify-center">
        <div className="max-w-md w-full space-y-8 text-center p-8">
          <div className="relative mx-auto h-24 w-24">
            <div className="absolute inset-0 rounded-full border-t-2 border-primary animate-spin" />
            <div className="absolute inset-2 rounded-full border-r-2 border-emerald-500 animate-spin flex items-center justify-center delay-150">
               <svg viewBox="0 0 24 24" fill="none" className="h-8 w-8 text-primary" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 22 C6 18 14 10 22 2" />
                <path d="M22 2 C22 14 12 22 2 22" fill="currentColor" fillOpacity="0.3"/>
              </svg>
            </div>
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight mb-2">Analyzing Factory Profile</h2>
            <p className="text-muted-foreground text-sm">Cross-referencing parameters with IPCC emission factors and state policies...</p>
          </div>
          <div className="space-y-4 text-left bg-surface-muted/50 p-6 rounded-xl border border-border/50 text-sm font-medium">
             <div className="flex items-center gap-3 text-emerald-500"><span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"/> Evaluating thermodynamic constraints</div>
             <div className="flex items-center gap-3 text-primary"><span className="h-2 w-2 rounded-full bg-primary animate-pulse" style={{ animationDelay: '0.5s' }}/> Simulating decarbonization pathways</div>
             <div className="flex items-center gap-3 text-sky-500"><span className="h-2 w-2 rounded-full bg-sky-500 animate-pulse" style={{ animationDelay: '1s' }}/> Matching financial subsidies</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-56px)] bg-background text-foreground overflow-hidden relative">
      
      {/* Premium Background Elements */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `linear-gradient(currentColor 1px, transparent 1px), linear-gradient(90deg, currentColor 1px, transparent 1px)`,
          backgroundSize: '2rem 2rem',
        }}></div>
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px]"></div>
      </div>

      <div className="relative z-10 flex flex-col h-full w-full">
        {/* Top Bar for Assessment */}
        <div className="flex items-center justify-between px-8 py-4 border-b border-border/40 bg-card/50 flex-shrink-0 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary shadow-sm">
              <Factory className="h-4 w-4 text-primary-foreground" />
            </div>
          <div>
            <h1 className="text-sm font-bold text-foreground leading-none tracking-tight">Factory Assessment</h1>
            <p className="text-xs text-muted-foreground mt-1">Configure your industrial profile</p>
          </div>
        </div>
        
        {/* Progress Tracker in Header */}
        <div className="flex items-center gap-2">
          {STEPS.map((step, index) => (
            <div key={step.id} className="flex items-center gap-2">
              <div
                className={`flex items-center justify-center h-6 w-6 rounded-full text-[10px] font-bold transition-colors ${
                  index < currentStep ? "bg-primary text-primary-foreground"
                  : index === currentStep ? "bg-primary/20 text-primary border border-primary/30"
                  : "bg-surface-muted text-muted-foreground border border-border/50"
                }`}
              >
                {index < currentStep ? "✓" : index + 1}
              </div>
              {index < STEPS.length - 1 && (
                <div className={`h-px w-4 ${index < currentStep ? "bg-primary" : "bg-border"}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      <FormProvider {...methods}>
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            if (currentStep === STEPS.length - 1) {
              if (Date.now() - lastStepChangeTime.current < 500) {
                return; // Prevent accidental double-click / rapid Enter submission
              }
              handleSubmit(onSubmit, onInvalid)(e);
            } else {
              nextStep();
            }
          }}
          className="flex flex-1 overflow-hidden"
        >
          
          {/* LEFT WORKSPACE (Stepper + Form) */}
          <div className="flex flex-1 overflow-hidden bg-background">
            
            {/* Stepper Sidebar */}
            <div className="hidden md:flex flex-col w-64 border-r border-border/40 bg-surface/30 p-6 overflow-y-auto">
              <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-6">Configuration Steps</h3>
              <div className="space-y-1">
                {STEPS.map((step, index) => (
                  <button
                    key={step.id}
                    type="button"
                    onClick={() => {
                      // Optional: allow skipping back but not forward without validation
                      if (index < currentStep) setCurrentStep(index)
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-all text-left ${
                      index === currentStep 
                        ? "bg-primary/10 text-primary" 
                        : index < currentStep 
                        ? "text-foreground hover:bg-surface-muted" 
                        : "text-muted-foreground opacity-60 cursor-not-allowed"
                    }`}
                  >
                    <div className={`h-2 w-2 rounded-full ${index === currentStep ? "bg-primary animate-pulse" : index < currentStep ? "bg-primary" : "bg-border"}`} />
                    {step.title}
                  </button>
                ))}
              </div>
            </div>

            {/* Main Form Area */}
            <main className="flex-1 overflow-y-auto p-8 relative">
              <div className="mx-auto max-w-2xl">
                
                <div className="mb-8">
                  <h2 className="text-2xl font-semibold tracking-tight text-foreground">{STEPS[currentStep].title}</h2>
                  <p className="text-sm text-muted-foreground mt-1">Please provide accurate information to improve AI insights.</p>
                </div>

                {submitError && (
                  <div className="mb-8 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive flex items-start gap-2">
                    <span className="mt-0.5 flex-shrink-0 text-destructive">⚠</span>
                    <span>{submitError}</span>
                  </div>
                )}

                {/* The Form Component */}
                <div className="mb-10">
                  <CurrentComponent />
                </div>

                {/* Navigation Footer */}
                <div className="flex items-center justify-between pt-6 border-t border-border/40 pb-10">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={prevStep}
                    disabled={currentStep === 0 || isSubmitting}
                    className="text-foreground border-border hover:bg-surface-muted"
                  >
                    ← Previous
                  </Button>

                  {currentStep < STEPS.length - 1 ? (
                    <button
                      type="button"
                      onClick={nextStep}
                      className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary shadow-sm"
                    >
                      Next Step →
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSubmitting ? (
                        <><span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" /> Analyzing...</>
                      ) : (
                        <>Run Analysis →</>
                      )}
                    </button>
                  )}
                </div>

              </div>
            </main>
          </div>

          {/* RIGHT PANEL: Live AI Insights */}
          <div className="hidden lg:block w-[360px] flex-shrink-0 bg-card border-l border-border/40">
            {/* The LiveInsightsPanel will automatically consume the FormProvider context */}
            <LiveInsightsPanel />
          </div>

        </form>
      </FormProvider>
      </div>
    </div>
  )
}
