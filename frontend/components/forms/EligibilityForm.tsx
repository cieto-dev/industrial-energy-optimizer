"use client"
import { useFormContext } from "react-hook-form"
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/reports/common/form"
import { Input } from "@/components/reports/common/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/reports/common/select"

import { FactoryProfileType } from "@/utils/validators"

export function EligibilityForm() {
  const { control, watch } = useFormContext<FactoryProfileType>()
  const udyamRegistered = watch("udyam_registered")

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Corporate & Regulatory Status</h3>
        <p className="text-xs text-muted-foreground -mt-2">Classification and registration status determines exact subsidy eligibility across schemes.</p>
        
        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="msme_classification"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">MSME Classification</FormLabel>
                <Select onValueChange={field.onChange} value={field.value ?? ""}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select classification" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="micro">Micro</SelectItem>
                    <SelectItem value="small">Small</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="udyam_registered"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Udyam Registered?</FormLabel>
                <Select onValueChange={(val) => field.onChange(val === "yes")} value={field.value ? "yes" : "no"}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="yes">Yes</SelectItem>
                    <SelectItem value="no">No</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {udyamRegistered && (
          <FormField
            control={control}
            name="udyam_number"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Udyam Registration Number</FormLabel>
                <FormControl>
                  <Input placeholder="E.g. UDYAM-XX-00-0000000" {...field} value={field.value || ""} />
                </FormControl>
                <FormDescription>Format required for state grant verification.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        )}
      </div>

      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Financial Benchmarks</h3>
        
        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="annual_turnover_inr"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Annual Turnover (INR)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="plant_and_machinery_or_equipment_investment_inr"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">P&M Investment (INR)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </div>

      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Proposed Project Parameters</h3>
        
        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="project_type"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Project Category</FormLabel>
                <Select onValueChange={field.onChange} value={field.value ?? ""}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="energy_efficiency">Energy Efficiency</SelectItem>
                    <SelectItem value="electrification">Electrification</SelectItem>
                    <SelectItem value="renewable_energy">Renewable Energy</SelectItem>
                    <SelectItem value="alternative_fuel">Alternative Fuel</SelectItem>
                    <SelectItem value="biomass">Biomass</SelectItem>
                    <SelectItem value="waste_heat_recovery">Waste Heat Recovery</SelectItem>
                    <SelectItem value="energy_storage">Energy Storage</SelectItem>
                    <SelectItem value="waste_management">Waste Management</SelectItem>
                    <SelectItem value="circular_economy">Circular Economy</SelectItem>
                    <SelectItem value="clean_transport">Clean Transport</SelectItem>
                    <SelectItem value="pollution_control">Pollution Control</SelectItem>
                    <SelectItem value="green_infrastructure">Green Infrastructure</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="existing_or_new_project"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Project Stage</FormLabel>
                <Select onValueChange={field.onChange} value={field.value ?? ""}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select stage" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="existing">Existing Project</SelectItem>
                    <SelectItem value="new">New Project</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="project_cost_inr"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Proposed Project Cost (INR)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="loan_amount_inr"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Expected Loan (INR)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} value={field.value ?? ""} onChange={e => field.onChange(e.target.value ? parseFloat(e.target.value) : null)} />
                </FormControl>
                <FormDescription>Optional.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </div>

      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Special Categories & Clusters</h3>
        
        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="cluster_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Industrial Cluster Name</FormLabel>
                <FormControl>
                  <Input placeholder="E.g. Tirupur Textile Cluster" {...field} value={field.value || ""} />
                </FormControl>
                <FormDescription>Optional. Useful for cluster-specific grants.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="cluster_is_adeetie_identified"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">ADEETIE Identified?</FormLabel>
                <Select onValueChange={(val) => field.onChange(val === "yes")} defaultValue={field.value === true ? "yes" : field.value === false ? "no" : undefined}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="yes">Yes</SelectItem>
                    <SelectItem value="no">No</SelectItem>
                  </SelectContent>
                </Select>
                <FormDescription>Optional.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="pt-4 mt-4 border-t border-border/40">
          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-4">Ownership Categories (Optional)</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {[
              { id: "women_owned", label: "Women Owned" },
              { id: "sc_st_owned", label: "SC/ST Owned" },
              { id: "pwd_owned", label: "PwD Owned" },
              { id: "agniveer_owned", label: "Agniveer Owned" },
              { id: "transgender_owned", label: "Transgender Owned" },
              { id: "north_east_region", label: "North East Region" },
              { id: "jammu_kashmir", label: "Jammu & Kashmir" },
              { id: "ladakh", label: "Ladakh" },
              { id: "aspirational_district", label: "Aspirational District" },
              { id: "identified_credit_deficient_district", label: "Credit Deficient" },
            ].map((cat) => (
              <FormField
                key={cat.id}
                control={control}
                name={`special_category.${cat.id}` as any}
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center space-x-3 space-y-0 p-3 rounded-lg border border-border/50 bg-background hover:bg-surface-muted transition-colors cursor-pointer">
                    <FormControl>
                      <input type="checkbox" checked={field.value} onChange={field.onChange} className="h-4 w-4 rounded border-border accent-primary focus:ring-primary" />
                    </FormControl>
                    <FormLabel className="font-medium text-sm cursor-pointer !mt-0">
                      {cat.label}
                    </FormLabel>
                  </FormItem>
                )}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
