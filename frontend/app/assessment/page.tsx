"use client"
import React, { useState } from "react"
import { useForm, FormProvider } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useRouter } from "next/navigation"

import { Sidebar } from "@/components/layout/Sidebar"
import { Navbar } from "@/components/layout/Navbar"
import { Button } from "@/components/reports/common/Button"
import { Card, CardContent, CardFooter } from "@/components/reports/common/Card"

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
  const router = useRouter()

  const methods = useForm<FactoryProfileType>({
    resolver: zodResolver(FactoryProfileSchema),
    mode: "onTouched",
    defaultValues: {
      name: "",
      industry: "",
      state: "",
      district: "",
      production_per_day: { value: 0, unit: "" },
      operating_hours_per_day: 0,
      operating_days_per_year: 300,
      current_fuel: "",
      fuel_consumption: { value: 0, unit: "" },
      electricity_consumption_kwh_day: 0,
      required_process_temperature_c: 0,
      roof_area_sqm: 0,
      budget_inr: 0,
      grid_reliability_pct: 0,
      annual_turnover_inr: 0,
      plant_and_machinery_or_equipment_investment_inr: 0,
      project_cost_inr: 0,
      udyam_registered: false,
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
      setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1))
    }
  }

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0))
  }

  const onSubmit = async (data: FactoryProfileType) => {
    setIsSubmitting(true)
    try {
      const payload = {
        ...data,
        factory_id: data.factory_id || `fac_${Math.random().toString(36).substr(2, 9)}`,
      }
      
      const response = await apiService.optimize(payload as any)
      localStorage.setItem("last_optimization", JSON.stringify(response))
      router.push("/dashboard")
    } catch (error) {
      console.error("Submission failed", error)
      alert("Failed to submit assessment. Please check your inputs.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const CurrentComponent = STEPS[currentStep].component

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="mx-auto max-w-4xl space-y-4">
            
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-3xl font-bold tracking-tight">Factory Assessment</h1>
              <div className="text-sm text-muted-foreground">
                Step {currentStep + 1} of {STEPS.length}
              </div>
            </div>

            <div className="flex gap-2 mb-8">
              {STEPS.map((step, index) => (
                <div 
                  key={step.id} 
                  className={`h-2 flex-1 rounded-full ${index <= currentStep ? 'bg-primary' : 'bg-muted'}`}
                />
              ))}
            </div>

            <FormProvider {...methods}>
              <form onSubmit={handleSubmit(onSubmit)}>
                <Card className="border-border">
                  <CardContent className="pt-6">
                    <CurrentComponent />
                  </CardContent>
                  <CardFooter className="flex justify-between border-t pt-6">
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={prevStep}
                      disabled={currentStep === 0 || isSubmitting}
                    >
                      Previous
                    </Button>
                    
                    {currentStep < STEPS.length - 1 ? (
                      <Button type="button" onClick={nextStep}>
                        Next
                      </Button>
                    ) : (
                      <Button type="submit" disabled={isSubmitting}>
                        {isSubmitting ? "Submitting..." : "Submit Assessment"}
                      </Button>
                    )}
                  </CardFooter>
                </Card>
              </form>
            </FormProvider>

          </div>
        </main>
      </div>
    </div>
  )
}
