"use client"

import React, { useState } from "react"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import { 
  FileText, 
  LayoutDashboard, 
  Compass, 
  Sliders, 
  ArrowRightLeft, 
  FolderKanban, 
  FileBarChart,
  ChevronRight,
  Network
} from "lucide-react"

const products = [
  {
    id: "assessment",
    title: "Input Assessment",
    description: "Profile your factory's baseline energy consumption, operational constraints, and existing infrastructure to initialize the Urjiva engine.",
    icon: FileText,
    href: "/assessment",
    color: "bg-emerald-500/10 text-emerald-500",
    border: "border-emerald-500/20 hover:border-emerald-500/50"
  },
  {
    id: "report",
    title: "Factory Dashboard",
    description: "View the synthesized decarbonization recommendations, ranked technology pathways, and detailed financial payback analysis.",
    icon: LayoutDashboard,
    href: "/report",
    color: "bg-blue-500/10 text-blue-500",
    border: "border-blue-500/20 hover:border-blue-500/50"
  },
  {
    id: "gis",
    title: "GIS & Maps",
    description: "Explore the interactive spatial atlas. Map your factory against nearby biomass availability, logistics corridors, and industrial clusters.",
    icon: Compass,
    href: "/gis",
    color: "bg-purple-500/10 text-purple-500",
    border: "border-purple-500/20 hover:border-purple-500/50"
  },
  {
    id: "scenario",
    title: "Scenario Playground",
    description: "Run Monte Carlo simulations and test 'what-if' pathways against fluctuating fuel prices, carbon taxes, and CAPEX constraints.",
    icon: Sliders,
    href: "/scenario-playground",
    color: "bg-amber-500/10 text-amber-500",
    border: "border-amber-500/20 hover:border-amber-500/50"
  },
  {
    id: "comparison",
    title: "State Comparison",
    description: "Compare state-level policies, grid emission factors, and subsidies to determine the optimal geographical deployment strategy.",
    icon: ArrowRightLeft,
    href: "/comparison",
    color: "bg-rose-500/10 text-rose-500",
    border: "border-rose-500/20 hover:border-rose-500/50"
  }
]

const secondaryTools = [
  {
    id: "projects",
    title: "Saved Projects",
    description: "Access your portfolio of saved assessments and multi-factory analyses.",
    icon: FolderKanban,
    href: "/projects",
  },
  {
    id: "reports",
    title: "PDF Reports",
    description: "Download bank-grade, fully auditable Decarbonization Roadmaps ready for board approval.",
    icon: FileBarChart,
    href: "/reports",
  }
]

export default function PlatformHubPage() {
  const [activeTab, setActiveTab] = useState("products")

  return (
    <div className="min-h-full bg-background relative font-sans">
      {/* Premium Background Elements */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `linear-gradient(currentColor 1px, transparent 1px), linear-gradient(90deg, currentColor 1px, transparent 1px)`,
          backgroundSize: '2rem 2rem',
        }}></div>
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[100px]"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-[100px]"></div>
      </div>

      <div className="relative z-10 p-6 md:p-12">
        {/* Header section */}
        <div className="max-w-6xl mx-auto mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-accent/10 rounded-lg">
              <Network className="w-6 h-6 text-accent" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
              Platform Hub
            </h1>
          </div>
          <p className="text-lg text-foreground-muted max-w-2xl">
            Welcome to the Urjiva Intelligence Layer. Select an engine to begin your industrial decarbonization analysis.
          </p>
        </div>

      {/* Tabs */}
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-6 border-b border-border mb-8">
          <button
            onClick={() => setActiveTab("products")}
            className={`pb-4 text-sm font-medium transition-colors relative ${activeTab === "products" ? "text-foreground" : "text-foreground-muted hover:text-foreground"}`}
          >
            Products We Offer
            {activeTab === "products" && (
              <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
            )}
          </button>
          <button
            onClick={() => setActiveTab("tools")}
            className={`pb-4 text-sm font-medium transition-colors relative ${activeTab === "tools" ? "text-foreground" : "text-foreground-muted hover:text-foreground"}`}
          >
            Saved & Reports
            {activeTab === "tools" && (
              <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
            )}
          </button>
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {activeTab === "products" && (
            <motion.div
              key="products"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {products.map((product) => (
                <Link key={product.id} href={product.href}>
                  <div className={`group flex flex-col h-full bg-surface border rounded-xl p-6 transition-all duration-300 hover:shadow-xl hover:shadow-black/5 cursor-pointer ${product.border}`}>
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-6 ${product.color}`}>
                      <product.icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-bold text-foreground mb-3 group-hover:text-accent transition-colors">
                      {product.title}
                    </h3>
                    <p className="text-sm text-foreground-muted leading-relaxed flex-grow">
                      {product.description}
                    </p>
                    <div className="mt-6 flex items-center text-sm font-medium text-foreground-muted group-hover:text-accent transition-colors">
                      Launch Engine
                      <ChevronRight className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1" />
                    </div>
                  </div>
                </Link>
              ))}
            </motion.div>
          )}

          {activeTab === "tools" && (
            <motion.div
              key="tools"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl"
            >
              {secondaryTools.map((tool) => (
                <Link key={tool.id} href={tool.href}>
                  <div className="group flex items-start gap-4 bg-surface border border-border rounded-xl p-6 transition-all duration-300 hover:border-foreground/30 hover:shadow-lg cursor-pointer">
                    <div className="w-10 h-10 shrink-0 rounded-lg bg-foreground/5 flex items-center justify-center">
                      <tool.icon className="w-5 h-5 text-foreground" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-foreground mb-1 group-hover:text-accent transition-colors">
                        {tool.title}
                      </h3>
                      <p className="text-sm text-foreground-muted leading-relaxed">
                        {tool.description}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      </div>
    </div>
  )
}
