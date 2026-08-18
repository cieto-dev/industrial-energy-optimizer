import { z } from "zod";

export const QuantitySchema = z.object({
  value: z.number().min(0, "Value must be non-negative"),
  unit: z.string().min(1, "Unit is required"),
});

export const SpecialCategorySchema = z.object({
  women_owned: z.boolean(),
  sc_st_owned: z.boolean(),
  pwd_owned: z.boolean(),
  agniveer_owned: z.boolean(),
  transgender_owned: z.boolean(),
  north_east_region: z.boolean(),
  jammu_kashmir: z.boolean(),
  ladakh: z.boolean(),
  aspirational_district: z.boolean(),
  identified_credit_deficient_district: z.boolean(),
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
  operating_days_per_year: z.number().min(1).max(366),
  
  current_fuel: z.string().min(1, "Current fuel is required"),
  fuel_consumption: QuantitySchema,
  electricity_consumption_kwh_day: z.number().min(0, "Cannot be negative"),
  required_process_temperature_c: z.number().min(0, "Cannot be negative"),
  
  // Constraints
  roof_area_sqm: z.number().min(0, "Cannot be negative"),
  available_land_sqm: z.number().min(0, "Cannot be negative").nullable().optional(),
  budget_inr: z.number().min(0, "Cannot be negative"),
  grid_reliability_pct: z.number().min(0).max(100, "Cannot exceed 100%"),
  
  // MSME & Eligibility (Module 4a)
  msme_classification: z.enum(["micro", "small", "medium"]),
  udyam_registered: z.boolean(),
  udyam_number: z.string().nullable().optional(),
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
  loan_amount_inr: z.number().min(0, "Loan amount cannot be negative").nullable().optional(),
  existing_or_new_project: z.enum(["existing", "new"]),
  brownfield_or_greenfield: z.enum(["brownfield", "greenfield", "not_applicable"]).nullable().optional(),
  cluster_name: z.string().nullable().optional(),
  cluster_is_adeetie_identified: z.boolean().nullable().optional(),
  annual_energy_savings_percent: z.number().min(0).max(100).nullable().optional(),
  special_category: SpecialCategorySchema.nullable().optional(),
});

export type FactoryProfileType = z.infer<typeof FactoryProfileSchema>;
export type SpecialCategoryType = z.infer<typeof SpecialCategorySchema>;
