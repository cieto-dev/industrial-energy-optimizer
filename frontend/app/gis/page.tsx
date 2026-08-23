"use client"

import React from "react"
import { Compass, MapPin, Zap, Flame, Award, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { GisMapComponent } from "@/components/gis/GisMapComponent"

export default function GisPage() {
  return (
    <main className="min-h-full bg-background p-4 text-foreground sm:p-6">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <section className="flex flex-col gap-4 border-b border-border/40 pb-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-500">
              <Compass className="h-3.5 w-3.5" />
              Geographic Intelligence System
            </div>

            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
              GIS & Industrial Cluster Mapping
            </h1>

            <p className="mt-2 text-sm text-muted-foreground sm:text-base">
              Explore biomass residue atlas, solar DNI irradiance, DISCOM power tariffs, and decarbonization pathways across Indian industrial clusters.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/assessment"
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
            >
              Assess My Factory Location
            </Link>
          </div>
        </section>

        {/* GIS Map and Cluster Explorer */}
        <GisMapComponent />
      </div>
    </main>
  )
}
