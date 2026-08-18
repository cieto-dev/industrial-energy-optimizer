"use client"
import { useFormContext } from "react-hook-form"
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/reports/common/form"
import { Input } from "@/components/reports/common/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/reports/common/select"
import { FactoryProfileType } from "@/utils/validators"

export function EligibilityForm() {
  const { control } = useFormContext<FactoryProfileType>()

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
              <Select onValueChange={field.onChange} defaultValue={field.value}>
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
              <Select onValueChange={(val) => field.onChange(val === "yes")} defaultValue={field.value ? "yes" : "no"}>
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

      <FormField
        control={control}
        name="project_type"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Project Type</FormLabel>
            <Select onValueChange={field.onChange} defaultValue={field.value}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="energy_efficiency">Energy Efficiency</SelectItem>
                <SelectItem value="renewable_energy">Renewable Energy</SelectItem>
                <SelectItem value="waste_heat_recovery">Waste Heat Recovery</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />

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
          name="existing_or_new_project"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project Stage</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
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
    </div>
  )
}
