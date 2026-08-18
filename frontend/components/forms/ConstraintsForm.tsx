"use client"
import { useFormContext } from "react-hook-form"
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/reports/common/form"
import { Input } from "@/components/reports/common/input"
import { FactoryProfileType } from "@/utils/validators"

export function ConstraintsForm() {
  const { control } = useFormContext<FactoryProfileType>()

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold mb-4">4. Site & Financial Constraints</h2>
      
      <FormField
        control={control}
        name="roof_area_sqm"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Available Roof Area (sq. meters)</FormLabel>
            <FormControl>
              <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={control}
        name="budget_inr"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Total Available Budget (INR)</FormLabel>
            <FormControl>
              <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={control}
        name="grid_reliability_pct"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Grid Reliability (%)</FormLabel>
            <FormControl>
              <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  )
}
