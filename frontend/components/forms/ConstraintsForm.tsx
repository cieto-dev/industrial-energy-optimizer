"use client"
import { useFormContext } from "react-hook-form"
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/reports/common/form"
import { Input } from "@/components/reports/common/input"
import { FactoryProfileType } from "@/utils/validators"

export function ConstraintsForm() {
  const { control } = useFormContext<FactoryProfileType>()

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Spatial Constraints</h3>
        <p className="text-xs text-muted-foreground -mt-2">Available area dictates the capacity of solar PV or biomass boiler installations.</p>
        
        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="roof_area_sqm"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Roof Area (sq. m)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
                </FormControl>
                <FormDescription>Calculates maximum rooftop solar potential.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="available_land_sqm"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Land Area (sq. m)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} value={field.value ?? ""} onChange={e => field.onChange(e.target.value ? parseFloat(e.target.value) : null)} />
                </FormControl>
                <FormDescription>Optional. Used for ground-mounted solar or biomass storage.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </div>

      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Financial & Grid Constraints</h3>
        
        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="budget_inr"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">CAPEX Budget (₹)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
                </FormControl>
                <FormDescription>Used to filter out non-viable pathways.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="grid_reliability_pct"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Grid Reliability (%)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value) || 0)} />
                </FormControl>
                <FormDescription>100% means zero power cuts. Impacts thermal storage needs.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </div>
    </div>
  )
}
