"use client"
import { useFormContext } from "react-hook-form"
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/reports/common/form"
import { Input } from "@/components/reports/common/input"
import { FactoryProfileType } from "@/utils/validators"

export function ProcessForm() {
  const { control } = useFormContext<FactoryProfileType>()

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Process Parameters</h3>
        <p className="text-xs text-muted-foreground -mt-2">These technical parameters define the viability of specific technologies like heat pumps.</p>
        
        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="required_process_temperature_c"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Required Temperature (°C)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
                </FormControl>
                <FormDescription>Critical for technology matching.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="electricity_consumption_kwh_day"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Electricity (kWh/day)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
                </FormControl>
                <FormDescription>Used to calculate baseline electrical load.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </div>
    </div>
  )
}
