"use client"
import React, { useState } from "react"
import { useForm, FormProvider } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useRouter } from "next/navigation"

import { Button } from "@/components/reports/common/Button"

import { FactoryProfileSchema, FactoryProfileType } from "@/utils/validators"
import { apiService } from "@/services/api"

import { IndustryForm } from "@/components/forms/IndustryForm"
import { EnergyInputForm } from "@/components/forms/EnergyInputForm"
import { ProcessForm } from "@/components/forms/ProcessForm"
import { ConstraintsForm } from "@/components/forms/ConstraintsForm"
import { EligibilityForm } from "@/components/forms/EligibilityForm"

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
  const [submitError, setSubmitError] = useState<string | null>(null)
  const router = useRouter()

  const methods = useForm<FactoryProfileType>({
    resolver: zodResolver(FactoryProfileSchema),
    mode: "onTouched",
    defaultValues: {
      name: "TN Textile MSME Demo",
      industry: "textile",
      state: "Tamil Nadu",
      district: "Coimbatore",
      production_per_day: { value: 500, unit: "kg" },
      operating_hours_per_day: 16,
      operating_days_per_year: 300,
      current_fuel: "coal",
      fuel_consumption: { value: 10, unit: "tonnes" },
      electricity_consumption_kwh_day: 5000,
      required_process_temperature_c: 200,
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
        women_owned: true,
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
      setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1))
    }
  }

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0))
  }

  const onSubmit = async (data: FactoryProfileType) => {
    setIsSubmitting(true)
    setSubmitError(null)
    try {
      const payload = {
        ...data,
        factory_id: data.factory_id || `fac_${Math.random().toString(36).substr(2, 9)}`,
      }
      const response = await apiService.optimize(payload as any)
      localStorage.setItem("last_optimization", JSON.stringify(response))
      router.push("/dashboard")
    } catch (error: any) {
      console.error("Submission failed", error)
      setSubmitError(error?.message ?? "Failed to submit assessment. Please check your inputs and try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  // Called when form has validation errors — show them clearly
  const onInvalid = (errors: any) => {
    console.error("Form validation errors:", errors)
    const firstError = Object.values(errors)[0] as any
    setSubmitError(`Please fix: ${firstError?.message ?? "some fields have errors"}`)
  }

  const CurrentComponent = STEPS[currentStep].component

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-950">

      {/* LEFT PANEL — motivational image with mission text */}
      <div
        className="hidden lg:flex relative w-[380px] flex-shrink-0 flex-col justify-end overflow-hidden"
        style={{
          backgroundImage: "url('/assessment_bg.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        {/* Dark overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/60 to-zinc-950/30" />
        {/* Mission text overlay */}
        <div className="relative z-10 p-8 pb-12">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 mb-4">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Step {currentStep + 1} of {STEPS.length}
          </div>
          <h2 className="text-3xl font-black text-white leading-tight mb-3">
            Every watt counts<br />
            <span className="text-emerald-400">toward zero.</span>
          </h2>
          <p className="text-sm text-zinc-400 leading-relaxed">
            You're building the case for a cleaner, more profitable factory. The data you enter here powers our AI engine to find the best clean energy pathway for your exact operation.
          </p>
          {/* Step names */}
          <div className="mt-8 space-y-2">
            {STEPS.map((step, index) => (
              <div key={step.id} className="flex items-center gap-3">
                <div className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                  index < currentStep ? "bg-emerald-500 text-zinc-950"
                  : index === currentStep ? "border-2 border-emerald-500 text-emerald-400"
                  : "border border-zinc-700 text-zinc-600"
                }`}>
                  {index < currentStep ? "✓" : index + 1}
                </div>
                <span className={`text-sm font-medium ${
                  index === currentStep ? "text-white" : index < currentStep ? "text-emerald-400" : "text-zinc-600"
                }`}>{step.title}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT PANEL — form area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Slim top bar */}
        <div className="flex items-center justify-between px-8 py-4 border-b border-zinc-800 bg-zinc-950 flex-shrink-0">
          <div className="flex items-center gap-3">
            {/* Inline brand mark */}
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500 shadow-md shadow-emerald-500/30">
              <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-zinc-950" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 22 C6 18 14 10 22 2" />
                <path d="M22 2 C22 14 12 22 2 22" fill="currentColor" fillOpacity="0.3"/>
              </svg>
            </div>
            <div>
              <p className="text-sm font-bold text-white leading-none">Factory Assessment</p>
              <p className="text-xs text-zinc-500 mt-0.5">{STEPS[currentStep].title}</p>
            </div>
          </div>
          {/* Step progress pills */}
          <div className="flex gap-1.5">
            {STEPS.map((_, index) => (
              <div
                key={index}
                className={`h-1.5 w-8 rounded-full transition-all duration-500 ${
                  index <= currentStep ? "bg-emerald-500" : "bg-zinc-800"
                }`}
              />
            ))}
          </div>
        </div>

        {/* Scrollable form area */}
        <main className="flex-1 overflow-y-auto bg-zinc-950 p-8">
          <div className="mx-auto max-w-xl">

            {submitError && (
              <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400 flex items-start gap-2">
                <span className="mt-0.5 flex-shrink-0">⚠</span>
                <span>{submitError}</span>
              </div>
            )}

            <FormProvider {...methods}>
              <form onSubmit={handleSubmit(onSubmit, onInvalid)}>
                {/* Form card */}
                <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 backdrop-blur-sm p-6 mb-6">
                  <CurrentComponent />
                </div>

                {/* Navigation footer */}
                <div className="flex justify-between items-center">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={prevStep}
                    disabled={currentStep === 0 || isSubmitting}
                    className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                  >
                    ← Previous
                  </Button>

                  {currentStep < STEPS.length - 1 ? (
                    <button
                      type="button"
                      onClick={nextStep}
                      className="inline-flex h-11 items-center gap-2 rounded-xl bg-emerald-500 px-6 text-sm font-bold text-zinc-950 shadow-lg shadow-emerald-500/25 transition-all hover:scale-105 hover:bg-emerald-400"
                    >
                      Next Step →
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="inline-flex h-11 items-center gap-2 rounded-xl bg-emerald-500 px-6 text-sm font-bold text-zinc-950 shadow-lg shadow-emerald-500/25 transition-all hover:scale-105 hover:bg-emerald-400 disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      {isSubmitting ? (
                        <><span className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-950 border-t-transparent" /> Analyzing...</>
                      ) : (
                        <>Run Analysis →</>
                      )}
                    </button>
                  )}
                </div>
              </form>
            </FormProvider>
          </div>
        </main>
      </div>
    </div>
  )
}
