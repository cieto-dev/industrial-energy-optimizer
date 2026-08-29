"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ArrowRight } from "lucide-react"

const features = [
  {
    id: "mcda",
    tabName: "MCDA Engine",
    massiveTitle: "Optimization",
    subtitle: "Multi-Criteria Decision Analysis",
    description: "Evaluates dozens of technologies against specific thermal loads, capex limits, and operational hours to find the mathematically optimal pathway.",
    bgImage: "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=2560&auto=format&fit=crop", // Abstract nodes/tech
  },
  {
    id: "atlas",
    tabName: "Spatial Atlas",
    massiveTitle: "Intelligence",
    subtitle: "Geographic Biomass Mapping",
    description: "District-level spatial intelligence mapping agricultural residue surplus and agro-pellet pricing across the subcontinent.",
    bgImage: "https://images.unsplash.com/photo-1526628953301-3e589a6a8b74?q=80&w=2560&auto=format&fit=crop", // Data visualization/mapping
  },
  {
    id: "policy",
    tabName: "Vector Search",
    massiveTitle: "Subsidies",
    subtitle: "Real-time Semantic Matching",
    description: "Instantly locates exact capital grants against a vast index of BEE, MNRE, and state-level industrial policies using RAG.",
    bgImage: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2560&auto=format&fit=crop", // Code/Data streams
  },
  {
    id: "montecarlo",
    tabName: "Risk Simulator",
    massiveTitle: "Confidence",
    subtitle: "Monte Carlo Stochastic Modeling",
    description: "Runs 10,000+ localized fuel and grid price scenarios to calculate highly accurate P50 payback confidence bands.",
    bgImage: "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2560&auto=format&fit=crop", // Hardware/processing
  }
];

export function ShowcaseGallery() {
  const [activeTab, setActiveTab] = useState(features[0].id)

  const activeFeature = features.find(f => f.id === activeTab) || features[0]

  return (
    <div className="w-full bg-background text-foreground py-24 overflow-hidden border-y border-border">
      <div className="max-w-[90rem] mx-auto px-6 mb-12">
        <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-8">System Architecture</h2>
        
        {/* Horizontal Scrollable Tabs */}
        <div className="flex overflow-x-auto hide-scrollbar gap-2 pb-4 border-b border-border">
          {features.map((feature) => (
            <button
              key={feature.id}
              onClick={() => setActiveTab(feature.id)}
              className={`whitespace-nowrap px-6 py-3 text-sm font-semibold tracking-wide uppercase transition-colors rounded-sm ${
                activeTab === feature.id
                  ? "bg-foreground text-background"
                  : "bg-surface text-foreground-muted hover:text-foreground hover:bg-surface-muted"
              }`}
            >
              {feature.tabName}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-[90rem] mx-auto px-6">
        <div className="relative w-full h-[600px] md:h-[700px] bg-surface rounded-xl overflow-hidden border border-border group">
          
          <AnimatePresence mode="wait">
            <motion.div
              key={activeFeature.id}
              initial={{ opacity: 0, scale: 1.05 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="absolute inset-0 z-0"
            >
              {/* Image Background */}
              <div 
                className="absolute inset-0 bg-cover bg-center opacity-30 mix-blend-luminosity dark:opacity-40"
                style={{ backgroundImage: `url(${activeFeature.bgImage})` }}
              />
              {/* Gradient Overlays */}
              <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent" />
              <div className="absolute inset-0 bg-gradient-to-r from-background/90 via-background/50 to-transparent" />
              
              {/* Content Overlay */}
              <div className="absolute inset-0 z-10 flex flex-col justify-between p-8 md:p-16">
                
                {/* Top Section: Details */}
                <div className="max-w-xl">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2, duration: 0.5 }}
                  >
                    <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-foreground-muted mb-4 block">
                      Core Component // {activeFeature.id.toUpperCase()}
                    </span>
                    <h3 className="text-3xl md:text-4xl font-bold tracking-tight mb-6 text-foreground">
                      {activeFeature.subtitle}
                    </h3>
                    <p className="text-lg text-foreground-muted leading-relaxed font-medium">
                      {activeFeature.description}
                    </p>
                  </motion.div>
                </div>

                {/* Bottom Section: Massive Typography & Action */}
                <div className="flex flex-col md:flex-row items-end justify-between w-full gap-8">
                  <motion.div
                    initial={{ opacity: 0, x: -40 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3, duration: 0.7, ease: "easeOut" }}
                    className="overflow-hidden"
                  >
                    <h2 className="text-[clamp(4rem,12vw,14rem)] font-black tracking-tighter leading-[0.8] text-foreground opacity-90 drop-shadow-sm">
                      {activeFeature.massiveTitle}
                    </h2>
                  </motion.div>
                  
                  <motion.button
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5, duration: 0.4 }}
                    className="shrink-0 w-16 h-16 bg-foreground/5 hover:bg-foreground text-foreground hover:text-background backdrop-blur-md flex items-center justify-center rounded-full transition-all duration-300 group-hover:scale-110 border border-border"
                  >
                    <ArrowRight strokeWidth={1.5} className="w-8 h-8" />
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>
          
        </div>
      </div>
    </div>
  )
}
