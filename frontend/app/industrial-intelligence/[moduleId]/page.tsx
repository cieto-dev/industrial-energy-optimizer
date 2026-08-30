"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowLeft, ArrowRight, Play, Pause, Maximize2, Settings2, Info } from "lucide-react"
import { industrialModules } from "../../../data/industrial-intelligence"
import { ReferenceButton } from "../../../components/industrial-intelligence/ReferenceButton"
import { FactoryEnergyFlow3D } from "../../../components/industrial-intelligence/visualizations/FactoryEnergyFlow3D"
import { BoilerInternalsSVG } from "../../../components/industrial-intelligence/visualizations/BoilerInternalsSVG"
import { CoalVsBiomassParticle } from "../../../components/industrial-intelligence/visualizations/CoalVsBiomassParticle"
import { WasteHeatRecovery3D } from "../../../components/industrial-intelligence/visualizations/WasteHeatRecovery3D"
import { MsmeEnergyLossSVG } from "../../../components/industrial-intelligence/visualizations/MsmeEnergyLossSVG"

export default function ModulePage() {
  const params = useParams()
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const [isPlaying, setIsPlaying] = useState(true)

  const moduleId = typeof params.moduleId === 'string' ? params.moduleId : ''
  const moduleData = industrialModules.find(m => m.id === moduleId)

  if (!moduleData) {
    return (
      <div className="min-h-screen bg-background text-foreground pt-32 px-12 flex flex-col items-center">
        <h1 className="text-2xl mb-4 text-foreground">Module not found</h1>
        <button onClick={() => router.push('/industrial-intelligence')} className="text-emerald-500 hover:underline">
          Return to Intelligence System
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col selection:bg-foreground/20 selection:text-foreground overflow-hidden">
      
      {/* Top Navigation Bar specific to the module */}
      <div className="h-14 border-b border-border flex items-center justify-between px-6 bg-background/80 backdrop-blur-md z-50 fixed top-0 w-full">
        <div className="flex items-center gap-4">
          <Link href="/industrial-intelligence" className="text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft size={18} />
          </Link>
          <div className="h-4 w-[1px] bg-border"></div>
          <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-500">Urjiva Intelligence</span>
          <span className="text-muted-foreground">/</span>
          <span className="text-xs font-mono text-muted-foreground">{moduleData.id}</span>
        </div>
        <div className="flex items-center gap-4">
           {moduleData.references.length > 0 && (
             <ReferenceButton reference={moduleData.references[0]} label="Primary Source" />
           )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex mt-14">
        
        {/* Visualization Area */}
        <div className="flex-1 relative bg-muted/20 overflow-hidden border-r border-border">
          
          {/* Main Visualization component */}
          {moduleData.id === 'factory-energy-flow' ? (
            <FactoryEnergyFlow3D />
          ) : moduleData.id === 'boiler-internals' ? (
            <BoilerInternalsSVG />
          ) : moduleData.id === 'coal-vs-biomass' ? (
            <CoalVsBiomassParticle />
          ) : moduleData.id === 'waste-heat-recovery' ? (
            <WasteHeatRecovery3D />
          ) : moduleData.id === 'msme-energy-loss' ? (
            <MsmeEnergyLossSVG />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-muted-foreground flex-col gap-4">
               <div className="w-24 h-24 border border-border rounded-full flex items-center justify-center bg-muted/30">
                 <Settings2 size={32} className="opacity-50" />
               </div>
               <p className="font-mono text-sm tracking-widest uppercase mt-4 text-foreground/70">Visualization Module Pending</p>
               <p className="text-xs text-muted-foreground max-w-md text-center">
                 The {moduleData.visualType.toUpperCase()} interactive engine for this module is scheduled for future release.
               </p>
            </div>
          )}
        </div>

        {/* Sidebar / Narrative Area */}
        <div className="w-[400px] bg-background overflow-y-auto flex flex-col shrink-0 border-l border-border">
          <div className="p-8 pb-12 flex-1">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="flex gap-2 mb-6 flex-wrap">
                {moduleData.tags.map(tag => (
                  <span key={tag} className="text-[9px] font-bold uppercase tracking-widest border border-border text-muted-foreground px-2 py-1">
                    {tag}
                  </span>
                ))}
              </div>
              
              <h1 className="text-3xl font-medium mb-6 leading-tight text-foreground">{moduleData.title}</h1>
              
              <p className="text-sm text-muted-foreground leading-relaxed mb-8">
                {moduleData.description}
              </p>

              <div className="h-[1px] w-full bg-border mb-8"></div>

              <h3 className="text-[10px] font-bold uppercase tracking-widest text-emerald-500 mb-4">Engineering Notes</h3>
              
              <div className="space-y-6">
                <div className="group">
                  <h4 className="text-foreground text-sm font-medium mb-2">Thermodynamic Inefficiency</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Most manufacturing facilities lose up to 30% of input energy through uninsulated surfaces, flue gases, and inefficient steam distribution. 
                    <ReferenceButton reference={{
                      source: "Industrial Heat Recovery Analysis",
                      organization: "US DOE",
                      keyFindings: "30% of energy is lost as waste heat in industrial processes.",
                      year: "2021"
                    }} type="evidence" />
                  </p>
                </div>
                
                <div className="group">
                  <h4 className="text-foreground text-sm font-medium mb-2">Decarbonization Potential</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Electrification of low-temperature heat using industrial heat pumps can yield COPs of 3.0 or higher, drastically cutting scope 1 emissions.
                    <ReferenceButton reference={{
                      source: "Heat Pumps in Industry",
                      organization: "IEA",
                      keyFindings: "Heat pumps can supply up to 30% of industrial heat demand.",
                      year: "2023"
                    }} />
                  </p>
                </div>
              </div>

            </motion.div>
          </div>
          
          {/* Action Footer */}
          <div className="p-6 border-t border-border bg-muted/30 shrink-0">
             <button 
               onClick={() => router.push('/dashboard')}
               className="w-full bg-foreground text-background font-medium py-3 text-sm hover:bg-foreground/90 transition-colors flex justify-center items-center gap-2 rounded-sm shadow-sm"
             >
               Apply to My Facility <ArrowRight size={16} />
             </button>
          </div>
        </div>

      </div>
    </div>
  )
}
