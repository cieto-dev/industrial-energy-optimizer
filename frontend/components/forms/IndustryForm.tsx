"use client"
import { useFormContext } from "react-hook-form"
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/reports/common/form"
import { Input } from "@/components/reports/common/input"
import { FactoryProfileType } from "@/utils/validators"

export function IndustryForm() {
  const { control } = useFormContext<FactoryProfileType>()

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Basic Information</h3>
        
        <FormField
          control={control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Factory Name</FormLabel>
              <FormControl>
                <Input placeholder="E.g. XYZ Textiles Pvt Ltd" {...field} />
              </FormControl>
              <FormDescription>The legal name of the manufacturing entity.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={control}
          name="industry"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Industry Profile</FormLabel>
              <FormControl>
                <Input placeholder="E.g. Textile, Cement, Steel" {...field} />
              </FormControl>
              <FormDescription>Your core industry sector determines base emission heuristics.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="p-6 rounded-xl border border-border/50 bg-card shadow-sm space-y-6">
        <h3 className="text-sm font-semibold text-foreground border-b border-border/40 pb-4">Location Data</h3>
        <p className="text-xs text-muted-foreground -mt-2">Geospatial location is required to calculate grid emission factors and match state-specific subsidies.</p>
        
        <div className="grid grid-cols-2 gap-6">
          <FormField
            control={control}
            name="state"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">State</FormLabel>
                <FormControl>
                  <Input placeholder="E.g. Tamil Nadu" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          
          <FormField
            control={control}
            name="district"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-bold uppercase tracking-wider text-muted-foreground">District</FormLabel>
                <FormControl>
                  <Input placeholder="E.g. Coimbatore" {...field} />
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
