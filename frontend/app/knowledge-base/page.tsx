"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { LandingNavbar } from "@/components/layout/LandingNavbar"
import { Search, Flame, Leaf, Zap, BarChart3, Factory, Activity, Globe, X } from "lucide-react"

// Knowledge Graph Data
const nodes = [
  { id: "heat", x: 50, y: 30, label: "Industrial Heat", icon: Flame, color: "#e85d04", category: "Thermodynamics" },
  { id: "steam", x: 30, y: 45, label: "Steam Systems", icon: Factory, color: "#9d4edd", category: "Infrastructure" },
  { id: "biomass", x: 70, y: 45, label: "Biomass", icon: Leaf, color: "#2a9d8f", category: "Fuels" },
  { id: "markets", x: 20, y: 70, label: "Carbon Markets", icon: Globe, color: "#0077b6", category: "Finance" },
  { id: "elec", x: 50, y: 80, label: "Electrification", icon: Zap, color: "#e9c46a", category: "Technology" },
  { id: "audit", x: 80, y: 70, label: "Energy Audits", icon: Activity, color: "#ef476f", category: "Compliance" },
  { id: "finance", x: 50, y: 55, label: "Decarb Finance", icon: BarChart3, color: "#06d6a0", category: "Finance" },
]

const edges = [
  { source: "heat", target: "steam" },
  { source: "heat", target: "biomass" },
  { source: "steam", target: "markets" },
  { source: "biomass", target: "finance" },
  { source: "elec", target: "finance" },
  { source: "audit", target: "finance" },
  { source: "steam", target: "elec" },
]

export default function KnowledgeBasePage() {
  const [activeNode, setActiveNode] = useState<string | null>(null)
  
  const selectedData = nodes.find(n => n.id === activeNode)

  return (
    <div className="min-h-screen bg-background font-sans overflow-hidden">
      <LandingNavbar />
      
      <main className="pt-32 pb-24 h-screen flex flex-col relative">
        <div className="max-w-[90rem] mx-auto px-6 mb-8 w-full z-10">
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent mb-4 block">
            Ontology Explorer
          </span>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight text-foreground leading-[1.1]">
            Industrial Decarbonization Atlas.
          </h1>
        </div>

        {/* Interactive Graph Area */}
        <div className="flex-1 relative mx-6 rounded-2xl border border-border bg-surface overflow-hidden">
          {/* Background Grid */}
          <div className="absolute inset-0 opacity-[0.03] bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTAgMGg0MHY0MEgweiIgZmlsbD0ibm9uZSIvPjxwaXhlbCBmaWxsPSJ3aGl0ZSI+PC9waXhlbD48cGF0aCBkPSJNMCAwdjQwaDQwVjBIMHptMzkgMzlIMVYxSDM5djM4eiIgZmlsbD0iY3VycmVudENvbG9yIi8+PC9zdmc+')] pointer-events-none" />

          {/* SVG Edges */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            {edges.map((edge, i) => {
              const sourceNode = nodes.find(n => n.id === edge.source)
              const targetNode = nodes.find(n => n.id === edge.target)
              if (!sourceNode || !targetNode) return null

              const isActive = activeNode === edge.source || activeNode === edge.target

              return (
                <line
                  key={i}
                  x1={`${sourceNode.x}%`}
                  y1={`${sourceNode.y}%`}
                  x2={`${targetNode.x}%`}
                  y2={`${targetNode.y}%`}
                  stroke="hsl(var(--border))"
                  strokeWidth="2"
                  strokeOpacity={activeNode ? (isActive ? 1 : 0.2) : 0.5}
                  className="transition-all duration-500"
                />
              )
            })}
          </svg>

          {/* HTML Nodes */}
          {nodes.map((node) => {
            const isActive = activeNode === node.id
            const isDimmed = activeNode && !isActive

            return (
              <motion.button
                key={node.id}
                onClick={() => setActiveNode(node.id)}
                className={`absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-3 transition-all duration-500 ${isDimmed ? 'opacity-20 scale-90' : 'opacity-100 scale-100 hover:scale-110 z-20'}`}
                style={{ left: `${node.x}%`, top: `${node.y}%` }}
              >
                <div 
                  className={`w-16 h-16 rounded-2xl border flex items-center justify-center transition-all ${isActive ? 'shadow-[0_0_40px_rgba(0,0,0,0.1)]' : 'shadow-sm hover:shadow-md'}`}
                  style={{ 
                    backgroundColor: isActive ? node.color : 'hsl(var(--background))',
                    borderColor: isActive ? 'transparent' : 'hsl(var(--border))',
                    color: isActive ? '#fff' : node.color
                  }}
                >
                  <node.icon className="w-8 h-8" />
                </div>
                <div className="bg-background/80 backdrop-blur-sm px-3 py-1.5 rounded-md border border-border">
                  <span className="text-sm font-bold text-foreground whitespace-nowrap">{node.label}</span>
                </div>
              </motion.button>
            )
          })}

          {/* Explainer Overlay */}
          <AnimatePresence>
            {activeNode && selectedData && (
              <motion.div
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 50 }}
                className="absolute top-6 right-6 bottom-6 w-96 bg-background/95 backdrop-blur-xl border border-border rounded-xl shadow-2xl p-6 flex flex-col z-30"
              >
                <div className="flex justify-between items-start mb-8">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted mb-2 block">{selectedData.category}</span>
                    <h3 className="text-2xl font-bold text-foreground flex items-center gap-2">
                      <selectedData.icon className="w-6 h-6" style={{ color: selectedData.color }} />
                      {selectedData.label}
                    </h3>
                  </div>
                  <button onClick={() => setActiveNode(null)} className="p-2 hover:bg-surface rounded-md transition-colors">
                    <X className="w-5 h-5 text-foreground-muted" />
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                  <p className="text-sm text-foreground-muted leading-relaxed font-medium mb-6">
                    This is an interactive engineering explainer. In the production app, this module loads highly specific thermodynamic equations, supply chain constraints, and cost models related to {selectedData.label.toLowerCase()}.
                  </p>
                  
                  <div className="bg-surface rounded-lg p-4 border border-border mb-6">
                    <h4 className="text-xs font-bold uppercase tracking-widest text-foreground mb-3">Key Metrics</h4>
                    <ul className="space-y-3">
                      <li className="flex justify-between text-sm">
                        <span className="text-foreground-muted">System Efficiency</span>
                        <span className="font-mono font-bold">82.4%</span>
                      </li>
                      <li className="flex justify-between text-sm">
                        <span className="text-foreground-muted">Carbon Abatement</span>
                        <span className="font-mono font-bold">2.1 tCO₂/MWh</span>
                      </li>
                      <li className="flex justify-between text-sm">
                        <span className="text-foreground-muted">Capital Intensity</span>
                        <span className="font-mono font-bold text-amber-500">High</span>
                      </li>
                    </ul>
                  </div>

                  <button className="w-full py-3 bg-foreground text-background text-sm font-bold uppercase tracking-widest rounded-md hover:bg-foreground/90 transition-colors">
                    View Full Engineering Module
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  )
}
