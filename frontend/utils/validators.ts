import { z } from "zod";

export const QuantitySchema = z.object({
  value: z.number().min(0, "Value must be non-negative"),
  unit: z.string().min(1, "Unit is required"),
});

export const FactoryProfileSchema = z.object({
  factory_id: z.string().optional(),
  name: z.string().min(1, "Name is required"),

  // Location & Industry
  industry: z.string().min(1, "Industry is required"),
  state: z.string().min(1, "State is required"),
  district: z.string().min(1, "District is required"),
  
  // Production and Energy
  production_per_day: QuantitySchema,
  operating_hours_per_day: z.number().positive("Must be greater than 0"),
  
  current_fuel: z.string().min(1, "Current fuel is required"),
  fuel_consumption: QuantitySchema,
  electricity_consumption_kwh_day: z.number().min(0, "Cannot be negative"),
  required_process_temperature_c: z.number().min(0, "Cannot be negative"),
  
  // Constraints
  roof_area_sqm: z.number().min(0, "Cannot be negative"),
  budget_inr: z.number().min(0, "Cannot be negative"),
  grid_reliability_pct: z.number().min(0).max(100, "Cannot exceed 100%"),
  
  // MSME & Eligibility (Module 4a)
  msme_classification: z.enum(["micro", "small", "medium"]),
  udyam_registered: z.boolean({
    required_error: "Udyam registration status is required"
  }),
  annual_turnover_inr: z.number().min(0, "Turnover cannot be negative"),
  plant_and_machinery_or_equipment_investment_inr: z.number().min(0, "Investment cannot be negative"),
  project_type: z.enum([
    "energy_efficiency",
    "electrification",
    "renewable_energy",
    "alternative_fuel",
    "biomass",
    "waste_heat_recovery",
    "energy_storage",
    "waste_management",
    "circular_economy",
    "clean_transport",
    "pollution_control",
    "green_infrastructure",
    "other",
  ]),
  project_cost_inr: z.number().min(0, "Project cost cannot be negative"),
  existing_or_new_project: z.enum(["existing", "new"]),
});

export type FactoryProfileType = z.infer<typeof FactoryProfileSchema>;
