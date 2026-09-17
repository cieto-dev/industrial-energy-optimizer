"use client";

import React, { useState, useEffect } from "react";
import { useForm, Controller, FormProvider, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import {
  Factory,
  ChevronRight,
  ArrowLeft,
  Info,
  CheckCircle2,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { FactoryProfileSchema, FactoryProfileType } from "@/utils/validators";
import { apiService } from "@/services/api";

// ---------------------------------------------------------------------------
// Smart Defaults Logic
// ---------------------------------------------------------------------------

function getSmartDefaults(industry: string): Partial<FactoryProfileType> {
  const ind = industry.toLowerCase();
  if (ind.includes("textile")) {
    return {
      current_fuel: "coal",
      required_process_temperature_c: 160,
      operating_hours_per_day: 16,
      operating_days_per_year: 300,
      grid_reliability_pct: 95,
      roof_area_sqm: 1500,
      production_per_day: { value: 1000, unit: "kg" },
      fuel_consumption: { value: 4000, unit: "kg" },
      electricity_consumption_kwh_day: 8000,
    };
  }
  if (ind.includes("pharma") || ind.includes("chemical")) {
    return {
      current_fuel: "natural_gas",
      required_process_temperature_c: 120,
      operating_hours_per_day: 24,
      operating_days_per_year: 330,
      grid_reliability_pct: 99,
      roof_area_sqm: 1000,
      production_per_day: { value: 500, unit: "kg" },
      fuel_consumption: { value: 2000, unit: "scm" },
      electricity_consumption_kwh_day: 12000,
    };
  }
  return {
    current_fuel: "diesel",
    required_process_temperature_c: 90,
    operating_hours_per_day: 12,
    operating_days_per_year: 250,
    grid_reliability_pct: 90,
    roof_area_sqm: 500,
    production_per_day: { value: 100, unit: "units" },
    fuel_consumption: { value: 500, unit: "liters" },
    electricity_consumption_kwh_day: 2000,
  };
}

// ---------------------------------------------------------------------------
// Helper Components
// ---------------------------------------------------------------------------

interface FormFieldProps {
  label: string;
  name: string;
  type?: string;
  placeholder?: string;
  isDefault?: boolean;
  tooltip?: string;
  softWarning?: string;
}

function FormInput({
  label,
  name,
  type = "text",
  placeholder,
  isDefault,
  tooltip,
  softWarning,
}: FormFieldProps) {
  const { register, formState: { errors } } = useFormContext();
  const error = (errors as any)[name]?.message || (errors as any)[name]?.value?.message;

  // Split name for nested fields like "production_per_day.value"
  const isNested = name.includes(".");

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground flex items-center gap-1.5">
          {label}
          {tooltip && (
            <span title={tooltip} className="cursor-help text-foreground-muted">
              <Info className="h-3.5 w-3.5" />
            </span>
          )}
        </label>
        {isDefault && (
          <span className="text-[10px] font-medium uppercase tracking-wider text-accent bg-accent/10 px-1.5 py-0.5 rounded-sm">
            Default
          </span>
        )}
      </div>
      <input
        {...register(name, { valueAsNumber: type === "number" })}
        type={type}
        step={type === "number" ? "any" : undefined}
        placeholder={placeholder}
        className={`flex h-11 w-full rounded-md border bg-background px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary ${
          error ? "border-destructive focus-visible:ring-destructive" : "border-input"
        }`}
      />
      {error && <p className="text-xs text-destructive">{error}</p>}
      {!error && softWarning && (
        <p className="text-xs text-amber-600 dark:text-amber-400 flex items-start gap-1">
          <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
          <span>{softWarning}</span>
        </p>
      )}
    </div>
  );
}

function FormSelect({
  label,
  name,
  options,
  isDefault,
}: FormFieldProps & { options: { label: string; value: string }[] }) {
  const { register, formState: { errors } } = useFormContext();
  const error = (errors as any)[name]?.message;

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">{label}</label>
        {isDefault && (
          <span className="text-[10px] font-medium uppercase tracking-wider text-accent bg-accent/10 px-1.5 py-0.5 rounded-sm">
            Default
          </span>
        )}
      </div>
      <select
        {...register(name)}
        className={`flex h-11 w-full rounded-md border bg-background px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary ${
          error ? "border-destructive focus-visible:ring-destructive" : "border-input"
        }`}
      >
        <option value="">Select an option</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

import { useFormContext } from "react-hook-form";

// ---------------------------------------------------------------------------
// Main Wizard Component
// ---------------------------------------------------------------------------

const STEPS = [
  { id: "basics", title: "Site Basics", subtitle: "Where and what do you produce?" },
  { id: "energy", title: "Energy Baseline", subtitle: "Current fuel and electricity usage." },
  { id: "constraints", title: "Operational Constraints", subtitle: "Limits on CAPEX, space, and grid." },
];

export default function AssessmentWizard() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [appliedDefaults, setAppliedDefaults] = useState<Set<string>>(new Set());

  const router = useRouter();

  const methods = useForm<FactoryProfileType>({
    resolver: zodResolver(FactoryProfileSchema),
    mode: "onChange", // Validate on change so next button state is accurate
    defaultValues: {
      msme_classification: "small",
      udyam_registered: true,
      project_type: "energy_efficiency",
      existing_or_new_project: "existing",
      budget_inr: null,
    },
  });

  const { trigger, handleSubmit, watch, setValue } = methods;

  // Watch fields to trigger smart defaults and show warnings
  const industry = watch("industry");
  const budgetInr = watch("budget_inr");
  const fuelValue = watch("fuel_consumption.value");

  // Apply smart defaults when moving from Step 1 to Step 2
  const handleNextStep = async () => {
    let fieldsToValidate: any[] = [];
    if (currentStep === 0) {
      fieldsToValidate = [
        "name",
        "industry",
        "state",
        "district",
        "production_per_day.value",
        "production_per_day.unit",
        "operating_hours_per_day",
        "operating_days_per_year",
      ];
    } else if (currentStep === 1) {
      fieldsToValidate = [
        "current_fuel",
        "fuel_consumption.value",
        "fuel_consumption.unit",
        "electricity_consumption_kwh_day",
        "required_process_temperature_c",
      ];
    }

    const isValid = await trigger(fieldsToValidate);
    if (!isValid) return;

    if (currentStep === 0 && industry) {
      // Apply defaults for fields not yet touched
      const defaults = getSmartDefaults(industry);
      const newDefaults = new Set(appliedDefaults);

      Object.entries(defaults).forEach(([key, val]) => {
        const currentVal = methods.getValues(key as any);
        // Only override if it's empty/undefined, or if we previously defaulted it
        if (currentVal == null || currentVal === "" || appliedDefaults.has(key)) {
          setValue(key as any, val);
          newDefaults.add(key);
        }
      });
      setAppliedDefaults(newDefaults);
    }

    setCurrentStep((p) => Math.min(p + 1, STEPS.length - 1));
  };

  const handlePrevStep = () => {
    setCurrentStep((p) => Math.max(p - 1, 0));
  };

  // Remove field from appliedDefaults if user edits it
  useEffect(() => {
    const subscription = methods.watch((value, { name, type }) => {
      if (name && appliedDefaults.has(name)) {
        const newSet = new Set(appliedDefaults);
        newSet.delete(name);
        setAppliedDefaults(newSet);
      }
    });
    return () => subscription.unsubscribe();
  }, [methods, appliedDefaults]);

  const onSubmit = async (data: FactoryProfileType) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      // Clean up empty strings or nulls to match API expectations if needed
      const payload = {
        ...data,
        factory_id: data.factory_id || `fac_${Math.random().toString(36).substr(2, 9)}`,
      };
      
      // We use optimizeV2 which correctly stores the raw result for /results to read
      await apiService.optimizeV2(payload);
      
      router.push("/results");
    } catch (error: any) {
      console.error("Submission failed", error);
      setSubmitError(error?.message ?? "Failed to run optimization. Check inputs.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-full bg-background flex flex-col font-sans">
      <div className="flex-1 max-w-3xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12 flex flex-col">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Factory className="h-6 w-6 text-foreground-muted" />
            Guided Factory Assessment
          </h1>
          <p className="mt-2 text-sm text-foreground-muted">
            Provide operational details to generate a decarbonization roadmap. Leave fields blank if unsure; the engine will attempt to estimate them.
          </p>
        </div>

        {/* Progress bar */}
        <div className="flex items-center justify-between mb-8 relative">
          <div className="absolute left-0 top-1/2 w-full h-0.5 bg-border -z-10 -translate-y-1/2" />
          {STEPS.map((step, idx) => (
            <div
              key={step.id}
              className={`flex flex-col items-center gap-2 bg-background px-2 ${
                idx <= currentStep ? "opacity-100" : "opacity-50"
              }`}
            >
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold border-2 ${
                  idx < currentStep
                    ? "bg-foreground border-foreground text-background"
                    : idx === currentStep
                    ? "bg-background border-foreground text-foreground"
                    : "bg-background border-border text-foreground-muted"
                }`}
              >
                {idx < currentStep ? <CheckCircle2 className="h-5 w-5" /> : idx + 1}
              </div>
              <span className="text-xs font-medium uppercase tracking-wider hidden sm:block">
                {step.title}
              </span>
            </div>
          ))}
        </div>

        {/* Form Container */}
        <div className="flex-1 bg-surface border border-border rounded-xl shadow-sm overflow-hidden flex flex-col">
          <FormProvider {...methods}>
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col h-full">
              {/* Form Body */}
              <div className="p-6 sm:p-8 flex-1 overflow-y-auto">
                <div className="mb-8">
                  <h2 className="text-xl font-semibold text-foreground">
                    {STEPS[currentStep].title}
                  </h2>
                  <p className="text-sm text-foreground-muted mt-1">
                    {STEPS[currentStep].subtitle}
                  </p>
                </div>

                {submitError && (
                  <div className="mb-6 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                    <span>{submitError}</span>
                  </div>
                )}

                <div className="space-y-6">
                  {/* STEP 1: Site Basics */}
                  {currentStep === 0 && (
                    <>
                      <FormInput label="Factory Name" name="name" placeholder="e.g. Surat Unit 1" />
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <FormSelect
                          label="Industry"
                          name="industry"
                          options={[
                            { label: "Textile", value: "textile" },
                            { label: "Pharmaceutical", value: "pharmaceuticals" },
                            { label: "Chemical", value: "chemical" },
                            { label: "Ceramics", value: "ceramics" },
                            { label: "Metal & Forging", value: "metal" },
                            { label: "Cement", value: "cement" },
                            { label: "Other", value: "other" },
                          ]}
                        />
                        <div className="grid grid-cols-2 gap-4">
                          <FormInput label="State" name="state" placeholder="e.g. Gujarat" />
                          <FormInput label="District" name="district" placeholder="e.g. Surat" />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="flex gap-2">
                          <div className="flex-1">
                            <FormInput
                              label="Production/Capacity"
                              name="production_per_day.value"
                              type="number"
                              isDefault={appliedDefaults.has("production_per_day")}
                            />
                          </div>
                          <div className="w-24">
                            <FormInput
                              label="Unit"
                              name="production_per_day.unit"
                              isDefault={appliedDefaults.has("production_per_day")}
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <FormInput
                            label="Hours/Day"
                            name="operating_hours_per_day"
                            type="number"
                            isDefault={appliedDefaults.has("operating_hours_per_day")}
                          />
                          <FormInput
                            label="Days/Year"
                            name="operating_days_per_year"
                            type="number"
                            isDefault={appliedDefaults.has("operating_days_per_year")}
                          />
                        </div>
                      </div>
                    </>
                  )}

                  {/* STEP 2: Energy Baseline */}
                  {currentStep === 1 && (
                    <>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <FormSelect
                          label="Primary Fuel"
                          name="current_fuel"
                          isDefault={appliedDefaults.has("current_fuel")}
                          options={[
                            { label: "Coal", value: "coal" },
                            { label: "Natural Gas (PNG)", value: "natural_gas" },
                            { label: "Diesel / LDO", value: "diesel" },
                            { label: "Furnace Oil (FO)", value: "furnace_oil" },
                            { label: "Biomass / Briquettes", value: "biomass" },
                          ]}
                        />
                        <div className="flex gap-2">
                          <div className="flex-1">
                            <FormInput
                              label="Fuel Consumption / Day"
                              name="fuel_consumption.value"
                              type="number"
                              isDefault={appliedDefaults.has("fuel_consumption")}
                              softWarning={
                                !fuelValue || fuelValue === 0
                                  ? "Missing fuel data will block firm recommendations."
                                  : undefined
                              }
                            />
                          </div>
                          <div className="w-24">
                            <FormInput
                              label="Unit"
                              name="fuel_consumption.unit"
                              isDefault={appliedDefaults.has("fuel_consumption")}
                            />
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <FormInput
                          label="Electricity Consumption (kWh/day)"
                          name="electricity_consumption_kwh_day"
                          type="number"
                          isDefault={appliedDefaults.has("electricity_consumption_kwh_day")}
                        />
                        <FormInput
                          label="Process Temperature (°C)"
                          name="required_process_temperature_c"
                          type="number"
                          isDefault={appliedDefaults.has("required_process_temperature_c")}
                        />
                      </div>
                    </>
                  )}

                  {/* STEP 3: Constraints */}
                  {currentStep === 2 && (
                    <>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <FormInput
                          label="CAPEX Budget (INR)"
                          name="budget_inr"
                          type="number"
                          placeholder="Leave blank if unknown"
                          softWarning={
                            !budgetInr
                              ? "Without a CAPEX limit, the engine will recommend the optimal tech regardless of cost. Note: technology-specific CAPEX estimates will still be required later for ROI calculations."
                              : undefined
                          }
                        />
                        <FormInput
                          label="Grid Reliability (%)"
                          name="grid_reliability_pct"
                          type="number"
                          isDefault={appliedDefaults.has("grid_reliability_pct")}
                        />
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <FormInput
                          label="Available Roof Area (sqm)"
                          name="roof_area_sqm"
                          type="number"
                          isDefault={appliedDefaults.has("roof_area_sqm")}
                          tooltip="Required for solar PV viability"
                        />
                        <FormInput
                          label="Available Land (sqm)"
                          name="available_land_sqm"
                          type="number"
                          placeholder="Optional"
                        />
                      </div>
                      
                      {/* Hidden defaults to pass validation without overwhelming UI */}
                      <input type="hidden" {...methods.register("annual_turnover_inr", { valueAsNumber: true })} value="0" />
                      <input type="hidden" {...methods.register("plant_and_machinery_or_equipment_investment_inr", { valueAsNumber: true })} value="0" />
                      <input type="hidden" {...methods.register("project_cost_inr", { valueAsNumber: true })} value="0" />
                    </>
                  )}
                </div>
              </div>

              {/* Form Footer */}
              <div className="p-6 bg-surface-muted border-t border-border flex items-center justify-between">
                <button
                  type="button"
                  onClick={handlePrevStep}
                  disabled={currentStep === 0 || isSubmitting}
                  className="inline-flex items-center gap-2 h-11 px-4 text-sm font-medium text-foreground hover:bg-surface border border-border rounded-md transition-colors disabled:opacity-50"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </button>
                
                {currentStep < STEPS.length - 1 ? (
                  <button
                    type="button"
                    onClick={handleNextStep}
                    className="inline-flex items-center gap-2 h-11 px-6 text-sm font-medium bg-foreground text-background hover:bg-foreground/90 rounded-md transition-colors"
                  >
                    Next Step
                    <ChevronRight className="h-4 w-4" />
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="inline-flex items-center gap-2 h-11 px-6 text-sm font-medium bg-foreground text-background hover:bg-foreground/90 rounded-md transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Running Analysis...
                      </>
                    ) : (
                      <>
                        Run Engine
                        <ChevronRight className="h-4 w-4" />
                      </>
                    )}
                  </button>
                )}
              </div>
            </form>
          </FormProvider>
        </div>
      </div>
    </div>
  );
}
