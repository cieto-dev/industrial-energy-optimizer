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
    <div className="space-y-4">
      <h2 className="text-xl font-semibold mb-4">5. MSME Eligibility & Policy Data</h2>
      
      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={control}
          name="msme_classification"
          render={({ field }) => (
            <FormItem>
              <FormLabel>MSME Classification</FormLabel>
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
              <FormLabel>Udyam Registered?</FormLabel>
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
              <FormLabel>Udyam Registration Number</FormLabel>
              <FormControl>
                <Input placeholder="E.g. UDYAM-XX-00-0000000" {...field} value={field.value || ""} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      )}

      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={control}
          name="annual_turnover_inr"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Annual Turnover (INR)</FormLabel>
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
              <FormLabel>P&M Investment (INR)</FormLabel>
              <FormControl>
                <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={control}
          name="project_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project Type</FormLabel>
              <Select onValueChange={field.onChange} value={field.value ?? ""}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
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
              <FormLabel>Project Stage</FormLabel>
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

      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={control}
          name="project_cost_inr"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Proposed Project Cost (INR)</FormLabel>
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
              <FormLabel>Expected Loan Amount (INR) (Optional)</FormLabel>
              <FormControl>
                <Input type="number" {...field} value={field.value ?? ""} onChange={e => field.onChange(e.target.value ? parseFloat(e.target.value) : null)} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={control}
          name="brownfield_or_greenfield"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project Site Status</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value || undefined}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select status (Optional)" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="brownfield">Brownfield</SelectItem>
                  <SelectItem value="greenfield">Greenfield</SelectItem>
                  <SelectItem value="not_applicable">Not Applicable</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={control}
          name="annual_energy_savings_percent"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Expected Energy Savings % (Optional)</FormLabel>
              <FormControl>
                <Input type="number" {...field} value={field.value ?? ""} onChange={e => field.onChange(e.target.value ? parseFloat(e.target.value) : null)} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={control}
          name="cluster_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Industrial Cluster Name (Optional)</FormLabel>
              <FormControl>
                <Input placeholder="E.g. Tirupur Textile Cluster" {...field} value={field.value || ""} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={control}
          name="cluster_is_adeetie_identified"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Is ADEETIE Identified Cluster?</FormLabel>
              <Select onValueChange={(val) => field.onChange(val === "yes")} defaultValue={field.value === true ? "yes" : field.value === false ? "no" : undefined}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select (Optional)" />
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
      
      <div className="space-y-3 pt-4 border-t">
        <h3 className="text-md font-medium">Special Category Status (Optional)</h3>
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
                <FormItem className="flex flex-row items-start space-x-3 space-y-0 p-2 rounded border">
                  <FormControl>
                    <input type="checkbox" checked={field.value} onChange={field.onChange} className="h-4 w-4 rounded border-gray-300" />
                  </FormControl>
                  <FormLabel className="font-normal cursor-pointer text-sm">
                    {cat.label}
                  </FormLabel>
                </FormItem>
              )}
            />
          ))}
        </div>
      </div>

    </div>
  )
}
