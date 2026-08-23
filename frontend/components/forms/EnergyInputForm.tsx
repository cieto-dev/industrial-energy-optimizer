"use client"
import { useFormContext } from "react-hook-form"
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/reports/common/form"
import { Input } from "@/components/reports/common/input"
import { FactoryProfileType } from "@/utils/validators"

export function EnergyInputForm() {
  const { control } = useFormContext<FactoryProfileType>()

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Production Profile</h3>
        <p className="text-xs text-muted-foreground -mt-2">Define your production scale to baseline energy intensity.</p>
        
        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="production_per_day.value"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Production Per Day</FormLabel>
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
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Unit</FormLabel>
                <FormControl>
                  <Input placeholder="E.g. tons, units" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="operating_hours_per_day"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Operating Hours / Day</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
                </FormControl>
                <FormDescription>Max 24 hours.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={control}
            name="operating_days_per_year"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Operating Days / Year</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 300)} />
                </FormControl>
                <FormDescription>Standard is 300 to 330 days.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </div>

      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Thermal Energy (Fuel)</h3>
        
        <div className="grid grid-cols-3 gap-6">
          <FormField
            control={control}
            name="current_fuel"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Current Fuel</FormLabel>
                <FormControl>
                  <Input placeholder="E.g. Coal, FO, LDO" {...field} />
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
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Consumption</FormLabel>
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
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Unit</FormLabel>
                <FormControl>
                  <Input placeholder="E.g. tons/day" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </div>
    </div>
  )
}
