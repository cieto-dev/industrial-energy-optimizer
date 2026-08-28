"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Flame, Zap, Sun, Factory, Cpu, Battery, Settings2, Wind, CheckCircle2, XCircle, ChevronRight, Activity, ArrowRight, ShieldCheck } from "lucide-react"
import { LandingNavbar } from "@/components/layout/LandingNavbar"
import Link from "next/link"

const technologies = [
  {
    id: "electric-boiler",
    name: "Electric Boiler",
    icon: Zap,
    shortDesc: "High-efficiency resistive and electrode heating.",
    suitable: ["Grid tariff < ₹7/kWh", "Steam demand below 15 TPH", "Low maintenance priority"],
    avoid: ["Coal cost is heavily subsidized", "Weak electrical infrastructure"],
    emissionReduction: 82,
    payback: "2.8 Years",
    capex: "₹45L - ₹1.2Cr",
    efficiency: "99%",
    temp: "Up to 180°C",
    compatible: ["Thermal Storage", "Solar Rooftop"],
    badge: "High Reliability",
    color: "var(--accent)"
  },
  {
    id: "biomass-gasifier",
    name: "Biomass Gasifier",
    icon: Flame,
    shortDesc: "Thermochemical conversion of agricultural residue.",
    suitable: ["Proximity to agro-waste clusters", "High thermal load (>10 TPH)", "Space for fuel storage"],
    avoid: ["Urban zones with strict PM2.5 rules", "Volatile local pellet pricing"],
    emissionReduction: 94,
    payback: "1.5 Years",
    capex: "₹85L - ₹3.5Cr",
    efficiency: "78%",
    temp: "Up to 300°C",
    compatible: ["Waste Heat Recovery", "Baghouse Filters"],
    badge: "Lowest OPEX",
    color: "#e85d04" // Orange
  },
  {
    id: "heat-pump",
    name: "High-Temp Heat Pump",
    icon: Settings2,
    shortDesc: "Thermodynamic heat upgrading using refrigerants.",
    suitable: ["Abundant low-grade waste heat", "Process temp < 160°C", "Simultaneous cooling demand"],
    avoid: ["Process temp > 200°C", "No waste heat source"],
    emissionReduction: 75,
    payback: "3.2 Years",
    capex: "₹1.5Cr - ₹4Cr",
    efficiency: "COP 3.5",
    temp: "Up to 160°C",
    compatible: ["Chillers", "Thermal Storage"],
    badge: "Highest Efficiency",
    color: "#2a9d8f" // Teal
  },
  {
    id: "cst",
    name: "Solar Thermal (CST)",
    icon: Sun,
    shortDesc: "Concentrated solar tracking via parabolic troughs.",
    suitable: ["High DNI region (>5.5 kWh/m2/day)", "Large flat roof/land", "Daytime-heavy load"],
    avoid: ["Cloudy coastal zones", "Space constrained factories"],
    emissionReduction: 40,
    payback: "4.5 Years",
    capex: "₹2Cr - ₹5Cr",
    efficiency: "65%",
    temp: "Up to 250°C",
    compatible: ["Electric Boilers", "Thermal Storage"],
    badge: "Zero Fuel Cost",
    color: "#e9c46a" // Yellow
  },
  {
    id: "thermal-storage",
    name: "Thermal Storage",
    icon: Battery,
    shortDesc: "Stores and supplies heat for delayed industrial processes.",
    suitable: ["Intermittent heat sources", "Variable heat demand", "Solar thermal integration"],
    avoid: ["Continuous baseload heat", "Space constrained factories"],
    emissionReduction: 35,
    payback: "4.0 Years",
    capex: "₹10K - ₹40K/kWh",
    efficiency: "90%",
    temp: "Up to 300°C",
    compatible: ["Solar Thermal (CST)", "Electric Boilers"],
    badge: "Load Shifting",
    color: "#6c757d"
  },
  {
    id: "waste-heat-recovery",
    name: "Waste Heat Recovery",
    icon: Factory,
    shortDesc: "Captures and reuses exhaust heat for pre-heating.",
    suitable: ["High-temp exhaust > 400°C", "Continuous boiler operation", "Existing steam systems"],
    avoid: ["Low-temp exhaust < 150°C", "Corrosive flue gases"],
    emissionReduction: 15,
    payback: "1.5 Years",
    capex: "₹3.5L - ₹25L",
    efficiency: "80%",
    temp: "Up to 500°C",
    compatible: ["Biomass Gasifier", "Cogeneration (CHP)"],
    badge: "Lowest Risk",
    color: "#4361ee"
  },
  {
    id: "cogeneration-chp",
    name: "Cogeneration (CHP)",
    icon: Cpu,
    shortDesc: "Simultaneous production of electricity and useful heat.",
    suitable: ["High power & heat demand", "Stable baseload profiles", "Access to piped natural gas/biogas"],
    avoid: ["Highly fluctuating loads", "Low heat-to-power ratio"],
    emissionReduction: 25,
    payback: "3.5 Years",
    capex: "₹5Cr - ₹15Cr",
    efficiency: "85%",
    temp: "Up to 400°C",
    compatible: ["Waste Heat Recovery", "Thermal Storage"],
    badge: "Max Resource Use",
    color: "#7209b7"
  },
  {
    id: "h2-ready-burners",
    name: "H2-Ready Burners",
    icon: Wind,
    shortDesc: "Blended firing capable burners for natural gas and hydrogen.",
    suitable: ["Future-proofing assets", "Access to green hydrogen", "High-temp direct firing"],
    avoid: ["No hydrogen supply chain", "Low-budget retrofits"],
    emissionReduction: 99,
    payback: "5.0 Years",
    capex: "₹50L - ₹2Cr",
    efficiency: "95%",
    temp: "Up to 1200°C",
    compatible: ["Electric Boilers", "Waste Heat Recovery"],
    badge: "Future Proof",
    color: "#4cc9f0"
  }
]

const TechCard = ({ tech }: { tech: any }) => {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <motion.div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="relative group bg-surface border border-border rounded-2xl overflow-hidden transition-all duration-500 hover:border-accent hover:shadow-[0_0_40px_rgba(var(--accent-rgb),0.1)]"
      layout
    >
      {/* Dynamic Background Effects on Hover */}
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-0 pointer-events-none overflow-hidden"
          >
            {/* Glowing Aura */}
            <div 
              className="absolute top-1/4 -right-20 w-64 h-64 rounded-full blur-3xl opacity-20"
              style={{ backgroundColor: tech.color }}
            />
            {/* Animated Grid / Particles Simulation */}
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjIiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiLz48L3N2Zz4=')] opacity-50 animate-pan-slow" />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative z-10 p-8 flex flex-col h-full">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-background border border-border flex items-center justify-center transition-colors group-hover:border-transparent" style={{ color: isHovered ? tech.color : 'var(--foreground)' }}>
              <tech.icon className="w-7 h-7" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-foreground tracking-tight">{tech.name}</h3>
              <p className="text-sm text-foreground-muted font-medium">{tech.shortDesc}</p>
            </div>
          </div>
          <div className="px-3 py-1 rounded-full bg-background border border-border text-[10px] font-bold uppercase tracking-widest flex items-center gap-2">
            <ShieldCheck className="w-3 h-3" style={{ color: tech.color }} />
            {tech.badge}
          </div>
        </div>

        {/* Dynamic Content (Expands on Hover) */}
        <div className="flex-1 grid md:grid-cols-2 gap-8">
          {/* Left Col: Specs */}
          <div className="flex flex-col gap-6">
            <div className="grid grid-cols-2 gap-4 border-b border-border/50 pb-6">
              <div>
                <p className="text-[10px] font-mono text-foreground-muted uppercase tracking-widest mb-1">CAPEX Range</p>
                <p className="text-lg font-bold text-foreground">{tech.capex}</p>
              </div>
              <div>
                <p className="text-[10px] font-mono text-foreground-muted uppercase tracking-widest mb-1">Payback</p>
                <p className="text-lg font-bold text-foreground">{tech.payback}</p>
              </div>
              <div>
                <p className="text-[10px] font-mono text-foreground-muted uppercase tracking-widest mb-1">Efficiency</p>
                <p className="text-lg font-bold text-foreground">{tech.efficiency}</p>
              </div>
              <div>
                <p className="text-[10px] font-mono text-foreground-muted uppercase tracking-widest mb-1">Max Temp</p>
                <p className="text-lg font-bold text-foreground">{tech.temp}</p>
              </div>
            </div>

            <div>
              <p className="text-[10px] font-mono text-foreground-muted uppercase tracking-widest mb-3">Emission Reduction</p>
              <div className="flex items-center gap-4">
                <div className="flex-1 h-2 bg-surface-muted rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full rounded-full"
                    style={{ backgroundColor: tech.color }}
                    initial={{ width: '0%' }}
                    animate={{ width: isHovered ? `${tech.emissionReduction}%` : '10%' }}
                    transition={{ duration: 1, ease: "easeOut" }}
                  />
                </div>
                <span className="font-mono text-sm font-bold">{tech.emissionReduction}%</span>
              </div>
            </div>
          </div>

          {/* Right Col: Suitability */}
          <div className="flex flex-col gap-6">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-status-online mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" /> Suitable When
              </p>
              <ul className="space-y-2">
                {tech.suitable.map((item: string, i: number) => (
                  <li key={i} className="text-sm font-medium text-foreground-muted flex items-start gap-2">
                    <span className="text-status-online opacity-50 mt-0.5">✓</span> {item}
                  </li>
                ))}
              </ul>
            </div>
            
            <AnimatePresence>
              {isHovered && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="overflow-hidden"
                >
                  <p className="text-xs font-bold uppercase tracking-widest text-destructive mb-3 flex items-center gap-2 pt-2 border-t border-border/50">
                    <XCircle className="w-4 h-4" /> Avoid If
                  </p>
                  <ul className="space-y-2">
                    {tech.avoid.map((item: string, i: number) => (
                      <li key={i} className="text-sm font-medium text-foreground-muted flex items-start gap-2">
                        <span className="text-destructive opacity-50 mt-0.5">✕</span> {item}
                      </li>
                    ))}
                  </ul>

                  <div className="mt-6 p-4 bg-background border border-border rounded-lg flex items-center justify-between">
                    <div>
                      <p className="text-[10px] font-mono text-foreground-muted uppercase tracking-widest mb-1">Works best with</p>
                      <p className="text-sm font-bold text-foreground">{tech.compatible.join(" + ")}</p>
                    </div>
                    <Activity className="w-5 h-5 text-accent opacity-50" />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Call to action */}
        <AnimatePresence>
          {isHovered && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="mt-8 flex justify-end"
            >
              <span className="text-xs font-bold text-foreground uppercase tracking-widest flex items-center gap-2 group-hover:text-accent transition-colors">
                Run Simulation in Urjiva <ArrowRight className="w-4 h-4" />
              </span>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </motion.div>
  )
}

export default function TechnologyPage() {
  return (
    <div className="min-h-screen bg-background font-sans">
      <LandingNavbar />
      
      <main className="pt-32 pb-24">
        {/* Header */}
        <div className="max-w-[90rem] mx-auto px-6 mb-16 text-center">
          <motion.span 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent mb-6 block"
          >
            Hardware Matrix
          </motion.span>
          <motion.h1 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-[clamp(3rem,5vw,6rem)] font-black tracking-tight text-foreground leading-[1.1] mb-6 max-w-5xl mx-auto"
          >
            Industrial Technology Library.
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-xl text-foreground-muted font-medium max-w-3xl mx-auto leading-relaxed"
          >
            Urjiva does not just list equipment. We dynamically model the thermodynamics, CAPEX, and local grid constraints of over 40 distinct abatement technologies to mathematically prove the optimal transition.
          </motion.p>
        </div>

        {/* Grid */}
        <div className="max-w-[90rem] mx-auto px-6 grid xl:grid-cols-2 gap-8">
          {technologies.map((tech) => (
            <TechCard key={tech.id} tech={tech} />
          ))}
        </div>
      </main>
    </div>
  )
}
