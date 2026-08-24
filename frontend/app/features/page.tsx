"use client"

import React from "react"
import { motion } from "framer-motion"
import { LandingNavbar } from "@/components/layout/LandingNavbar"
import { Activity, Map, Coins, Landmark, Zap, Factory, BarChart3, Database, Target, FileText } from "lucide-react"

const pipelineSteps = [
  { id: "telemetry", title: "Factory Telemetry", icon: Activity, desc: "Ingesting real-time operational data: 24/7 steam demand curves, existing boiler efficiencies, and process temperature requirements." },
  { id: "gis", title: "Spatial Biomass Atlas", icon: Map, desc: "Mapping the exact location of the factory against surrounding agricultural zones to calculate logistics costs for specific residues (e.g., Rice Husk vs. Mustard Stalk)." },
  { id: "fuel", title: "Commodity Pricing", icon: Coins, desc: "Indexing historical and projected prices for coal, natural gas, biomass pellets, and grid electricity in the specific district." },
  { id: "subsidies", title: "Policy Vector Search", icon: Landmark, desc: "Scanning 200+ central and state policies to identify applicable capital subsidies based on the factory's MSME status and sector." },
  { id: "tariffs", title: "Grid Tariff Analysis", icon: Zap, desc: "Analyzing complex Time-of-Day (ToD) electricity tariffs and open access regulations to determine the exact cost of electrification." },
  { id: "equipment", title: "Technology Library", icon: Factory, desc: "Simulating the performance of 40+ abatement technologies (Heat Pumps, Gasifiers) under the factory's specific load conditions." },
  { id: "montecarlo", title: "Monte Carlo Simulator", icon: BarChart3, desc: "Running 10,000+ stochastic scenarios to stress-test financial viability against future fuel price shocks and carbon tax risks." },
  { id: "mcda", title: "MCDA Optimization", icon: Database, desc: "Multi-Criteria Decision Analysis weighing CAPEX constraints against emission goals to find the mathematically optimal technology mix." },
  { id: "finance", title: "Financial Engineering", icon: Target, desc: "Structuring the optimal deployment roadmap, balancing upfront capital expenditure with rapid operational payback." },
  { id: "output", title: "Recommended Pathway", icon: FileText, desc: "Generating a bank-grade, fully auditable Decarbonization Roadmap ready for board approval and immediate execution." }
]

export default function FeaturesPage() {
  return (
    <div className="bg-[#0a0a0a] min-h-screen text-white font-sans selection:bg-white/30">
      <LandingNavbar />
      
      <div className="max-w-7xl mx-auto px-6 pt-32 pb-32 flex flex-col md:flex-row relative">
        
        {/* Left Column - Fixed Title (sticky on desktop) */}
        <div className="w-full md:w-1/3 mb-16 md:mb-0">
          <div className="md:sticky md:top-40">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/50 mb-6 block">
              System Architecture
            </span>
            <h1 className="text-5xl font-black tracking-tight leading-[1.1] mb-6">
              Inside the <br/>Intelligence Engine.
            </h1>
            <p className="text-lg text-white/60 font-medium">
              Watch how CIETO processes millions of data points to generate a deterministic decarbonization pathway.
            </p>
          </div>
        </div>

        {/* Right Column - Scrolling Pipeline */}
        <div className="w-full md:w-2/3 relative md:pl-16">
          
          {/* The Pipeline Track */}
          <div className="absolute left-[39px] md:left-[103px] top-0 bottom-0 w-px bg-white/10" />

          {/* Steps Container */}
          <div className="relative w-full space-y-32">
            {pipelineSteps.map((step, index) => {
              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, y: 50 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: false, margin: "-20% 0px -20% 0px" }}
                  transition={{ duration: 0.7, ease: "easeOut" }}
                  className="relative flex items-start gap-8 w-full max-w-2xl"
                >
                  {/* Node Icon */}
                  <div className="relative shrink-0 w-20 h-20 rounded-2xl bg-black border border-white/20 flex items-center justify-center z-20 shadow-[0_0_30px_rgba(59,130,246,0.15)] group">
                    <motion.div 
                      className="absolute inset-0 bg-blue-500/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                    />
                    <step.icon className="w-8 h-8 text-blue-400 relative z-10" />
                  </div>
                  
                  {/* Content */}
                  <div className="pt-2">
                    <span className="text-[10px] font-mono text-blue-500 mb-2 block uppercase tracking-widest">
                      Step {String(index + 1).padStart(2, '0')}
                    </span>
                    <h2 className="text-3xl font-bold mb-4 tracking-tight">{step.title}</h2>
                    <p className="text-xl text-white/60 leading-relaxed font-medium">
                      {step.desc}
                    </p>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
        
      </div>
    </div>
  )
}
