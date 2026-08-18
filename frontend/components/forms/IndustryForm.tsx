"use client"
import { useFormContext } from "react-hook-form"
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/reports/common/form"
import { Input } from "@/components/reports/common/input"
import { FactoryProfileType } from "@/utils/validators"

export function IndustryForm() {
  const { control } = useFormContext<FactoryProfileType>()

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold mb-4">1. General Information</h2>
      
      <FormField
        control={control}
        name="name"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Factory Name</FormLabel>
            <FormControl>
              <Input placeholder="E.g. XYZ Textiles Pvt Ltd" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={control}
          name="industry"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Industry</FormLabel>
              <FormControl>
                <Input placeholder="E.g. Textile" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={control}
          name="state"
          render={({ field }) => (
            <FormItem>
              <FormLabel>State</FormLabel>
              <FormControl>
                <Input placeholder="E.g. Tamil Nadu" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <FormField
        control={control}
        name="district"
        render={({ field }) => (
          <FormItem>
            <FormLabel>District</FormLabel>
            <FormControl>
              <Input placeholder="E.g. Coimbatore" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  )
}
