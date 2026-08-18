"use client"
import { useFormContext } from "react-hook-form"
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/reports/common/form"
import { Input } from "@/components/reports/common/input"
import { FactoryProfileType } from "@/utils/validators"

export function ProcessForm() {
  const { control } = useFormContext<FactoryProfileType>()

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold mb-4">3. Technical Process Requirements</h2>
      
      <FormField
        control={control}
        name="required_process_temperature_c"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Required Process Temperature (°C)</FormLabel>
            <FormControl>
              <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={control}
        name="electricity_consumption_kwh_day"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Electricity Consumption (kWh/day)</FormLabel>
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
