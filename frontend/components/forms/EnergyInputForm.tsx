"use client"
import { useFormContext } from "react-hook-form"
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/reports/common/form"
import { Input } from "@/components/reports/common/input"
import { FactoryProfileType } from "@/utils/validators"

export function EnergyInputForm() {
  const { control } = useFormContext<FactoryProfileType>()

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold mb-4">2. Production & Operations</h2>
      
      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={control}
          name="production_per_day.value"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Production Per Day</FormLabel>
              <FormControl>
                <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={control}
          name="production_per_day.unit"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Unit</FormLabel>
              <FormControl>
                <Input placeholder="E.g. tons" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <FormField
        control={control}
        name="operating_hours_per_day"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Operating Hours Per Day</FormLabel>
            <FormControl>
              <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <div className="grid grid-cols-3 gap-4">
        <FormField
          control={control}
          name="current_fuel"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Current Fuel</FormLabel>
              <FormControl>
                <Input placeholder="E.g. Coal" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={control}
          name="fuel_consumption.value"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Fuel Consumption</FormLabel>
              <FormControl>
                <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={control}
          name="fuel_consumption.unit"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Unit</FormLabel>
              <FormControl>
                <Input placeholder="E.g. tons/day" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>
    </div>
  )
}
