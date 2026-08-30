"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

export const CoalVsBiomassParticle = () => {
  const [activeFuel, setActiveFuel] = useState<string | null>(null);

  const fuels = [
    { 
      id: "coal", 
      name: "Coal", 
      color: "#555555", 
      emissions: "High", 
      energy: "High",
      particles: 40,
      speed: 1.5,
      description: "High energy density but massive carbon footprint and particulate matter emissions."
    },
    { 
      id: "biomass", 
      name: "Biomass", 
      color: "#8b5a2b", 
      emissions: "Medium (Biogenic)", 
      energy: "Medium",
      particles: 25,
      speed: 1,
      description: "Carbon neutral over its lifecycle, but lower calorific value requires larger volumes."
    },
    { 
      id: "gas", 
      name: "Natural Gas", 
      color: "#3399ff", 
      emissions: "Medium", 
      energy: "High",
      particles: 20,
      speed: 2,
      description: "Cleanest fossil fuel, highly efficient combustion, but still a source of Scope 1 emissions."
    },
    { 
      id: "elec", 
      name: "Electricity", 
      color: "#00e676", 
      emissions: "Zero (Scope 1)", 
      energy: "Very High",
      particles: 15,
      speed: 3,
      description: "100% efficient at point of use. Zero direct emissions. Requires high CAPEX for heat pumps/electric boilers."
    }
  ];

  return (
    <div className="w-full h-full bg-muted/10 relative p-8 flex flex-col justify-end">
      
      {/* Background Grid */}
      <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{
        backgroundImage: `linear-gradient(currentColor 1px, transparent 1px), linear-gradient(90deg, currentColor 1px, transparent 1px)`,
        backgroundSize: '2rem 2rem',
      }}></div>

      {/* Info Panel */}
      <div className="absolute top-8 left-8 max-w-sm">
        <AnimatePresence mode="wait">
          {activeFuel ? (
            <motion.div 
              key={activeFuel}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-background/90 backdrop-blur border border-border p-5 shadow-xl"
            >
              <h3 className="font-medium text-lg mb-2" style={{ color: fuels.find(f => f.id === activeFuel)?.color }}>
                {fuels.find(f => f.id === activeFuel)?.name}
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {fuels.find(f => f.id === activeFuel)?.description}
              </p>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-muted-foreground uppercase tracking-wider block mb-1 text-[10px]">Scope 1 Emissions</span>
                  <span className="font-mono text-foreground">{fuels.find(f => f.id === activeFuel)?.emissions}</span>
                </div>
                <div>
                  <span className="text-muted-foreground uppercase tracking-wider block mb-1 text-[10px]">Energy Density</span>
                  <span className="font-mono text-foreground">{fuels.find(f => f.id === activeFuel)?.energy}</span>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div 
              key="default"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="bg-background/50 backdrop-blur border border-border p-4 text-sm text-muted-foreground"
            >
              Hover over a fuel stream to compare thermodynamic and emission profiles.
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Particle Streams */}
      <div className="flex justify-around items-end h-[60%] relative z-10 w-full max-w-4xl mx-auto border-b-2 border-border pb-4">
        {fuels.map(fuel => (
          <div 
            key={fuel.id}
            className="relative flex flex-col items-center group cursor-pointer w-24 h-full"
            onMouseEnter={() => setActiveFuel(fuel.id)}
            onMouseLeave={() => setActiveFuel(null)}
          >
            {/* Particles container */}
            <div className="absolute bottom-0 w-full h-full overflow-hidden flex justify-center">
              {[...Array(fuel.particles)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute bottom-0 w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: fuel.color }}
                  initial={{ 
                    y: 0, 
                    x: (Math.random() - 0.5) * 40,
                    opacity: 0
                  }}
                  animate={{ 
                    y: -300 - Math.random() * 200, 
                    x: (Math.random() - 0.5) * 60,
                    opacity: [0, 1, 1, 0] 
                  }}
                  transition={{ 
                    duration: (2 + Math.random() * 2) / fuel.speed, 
                    repeat: Infinity,
                    delay: Math.random() * 2,
                    ease: "linear"
                  }}
                />
              ))}
            </div>

            {/* Base platform */}
            <div className={`h-2 w-16 rounded mt-auto transition-colors duration-300 ${activeFuel === fuel.id ? 'bg-foreground' : 'bg-muted-foreground/30'}`} style={{ backgroundColor: activeFuel === fuel.id ? fuel.color : undefined }}></div>
            <span className={`mt-4 text-xs font-bold uppercase tracking-wider transition-colors duration-300 ${activeFuel === fuel.id ? 'text-foreground' : 'text-muted-foreground'}`}>
              {fuel.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
