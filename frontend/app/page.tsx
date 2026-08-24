"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { ArrowRight, Leaf, Zap, Factory, BarChart3, Database, ShieldCheck, Map, ChevronRight, Binary, Network, Globe, CheckCircle2, Flame, Sun, Cpu, Battery, Settings2, Wind, Landmark, Building, FileText, ChevronDown, MapPin, Search } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend
} from "recharts"
import { LandingNavbar } from "@/components/layout/LandingNavbar"

// --- Mock Data for Charts ---
const emissionsData = [
  { month: "Jan", baseline: 4000, optimized: 4000 },
  { month: "Feb", baseline: 4100, optimized: 3800 },
  { month: "Mar", baseline: 3900, optimized: 3200 },
  { month: "Apr", baseline: 4200, optimized: 2800 },
  { month: "May", baseline: 4050, optimized: 2100 },
  { month: "Jun", baseline: 4300, optimized: 1500 },
  { month: "Jul", baseline: 4100, optimized: 1200 },
]

const roiData = [
  { name: "Solar Array", capex: 120, opex_saving: 45 },
  { name: "Biomass", capex: 85, opex_saving: 35 },
  { name: "Heat Pump", capex: 150, opex_saving: 60 },
]

export default function LandingPage() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])
  if (!mounted) return null

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <LandingNavbar />

      {/* ── HERO SECTION ───────────────────────────────────────────── */}
      <section className="relative min-h-[100svh] flex items-center pt-24 pb-12 overflow-hidden bg-black text-white">

        {/* Full-bleed Cinematic Industrial Background (Palantir Style) */}
        <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
          <div
            className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2560&auto=format&fit=crop')] bg-cover bg-center animate-zoom-slow opacity-60"
          />
          {/* Dark gradient to ensure text readability and blend smoothly into the next white section */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/40 to-background" />
        </div>

        <div className="max-w-[90rem] mx-auto px-6 w-full grid lg:grid-cols-12 gap-12 lg:gap-8 items-center relative z-10">

          {/* Left: Typography */}
          <div className="lg:col-span-6 flex flex-col justify-center">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="text-[clamp(2.5rem,4.5vw,5rem)] font-black tracking-[-0.04em] leading-[1.05] text-white mb-6 drop-shadow-xl"
            >
              The intelligence layer for industrial decarbonization.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
              className="text-lg md:text-xl text-white/80 mb-10 max-w-lg leading-relaxed font-medium drop-shadow-md"
            >
              Decisions engineered from physics, economics, and policy. The enterprise infrastructure for Indian MSMEs to build, deploy, and govern emission abatement roadmaps at scale.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
              className="flex items-center gap-4"
            >
              <Link
                href="/assessment"
                className="group flex h-14 items-center justify-center gap-3 bg-white px-8 text-sm font-bold text-black transition-all hover:bg-white/90 shadow-sm rounded-sm"
              >
                Deploy Engine
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link
                href="/dashboard"
                className="group flex h-14 items-center justify-center gap-3 border border-white/20 bg-black/40 backdrop-blur-md px-8 text-sm font-bold text-white transition-colors hover:bg-black/60 rounded-sm"
              >
                View Architecture
              </Link>
            </motion.div>
          </div>

          {/* Right: Glass Panel Mockup */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
            className="lg:col-span-6 relative"
          >
            {/* The Mockup Container */}
            <div className="rounded-xl border border-border bg-card shadow-2xl overflow-hidden flex flex-col h-[600px] relative z-20">

              {/* Fake Browser/App Header */}
              <div className="h-12 border-b border-border bg-surface-muted flex items-center px-4 justify-between shrink-0">
                <div className="flex items-center gap-4">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-border" />
                    <div className="w-3 h-3 rounded-full bg-border" />
                    <div className="w-3 h-3 rounded-full bg-border" />
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1 bg-background border border-border rounded-md">
                    <Binary className="h-3 w-3 text-accent" />
                    <span className="text-[10px] font-mono text-foreground-muted">cieto-studio / optimization-kernel</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-status-online">
                    <div className="w-1.5 h-1.5 rounded-full bg-status-online animate-pulse" />
                    Kernel Active
                  </span>
                </div>
              </div>

              {/* App Body - Split Pane Layout */}
              <div className="flex-1 flex overflow-hidden">
                {/* Left Sidebar */}
                <div className="w-48 border-r border-border bg-surface-muted/50 p-4 shrink-0 flex flex-col gap-6">
                  <div>
                    <p className="text-[9px] font-bold uppercase tracking-widest text-foreground-muted mb-3">Data Fusion</p>
                    <ul className="space-y-2 text-xs font-semibold text-foreground">
                      <li className="flex items-center gap-2 px-2 py-1.5 bg-background rounded border border-border shadow-sm"><Database className="h-3 w-3 text-accent" /> Telemetry</li>
                      <li className="flex items-center gap-2 px-2 py-1.5 opacity-60"><Map className="h-3 w-3" /> GIS Atlas</li>
                      <li className="flex items-center gap-2 px-2 py-1.5 opacity-60"><ShieldCheck className="h-3 w-3" /> Policy Index</li>
                    </ul>
                  </div>
                  <div>
                    <p className="text-[9px] font-bold uppercase tracking-widest text-foreground-muted mb-3">Agents</p>
                    <ul className="space-y-2 text-xs font-semibold text-foreground">
                      <li className="flex items-center gap-2 px-2 py-1.5 opacity-60"><Factory className="h-3 w-3" /> MCDA Solver</li>
                      <li className="flex items-center gap-2 px-2 py-1.5 opacity-60"><BarChart3 className="h-3 w-3" /> Monte Carlo</li>
                    </ul>
                  </div>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 bg-background p-6 overflow-hidden flex flex-col">
                  <div className="mb-6">
                    <h2 className="text-xl font-black text-foreground">Live Abatement Telemetry</h2>
                    <p className="text-xs text-foreground-muted mt-1">Real-time processing of Scope 1 & 2 emissions data against selected pathways.</p>
                  </div>

                  {/* Fake Data Visualization */}
                  <div className="grid grid-cols-3 gap-4 mb-6 shrink-0">
                    <div className="border border-border p-4 rounded-lg bg-surface shadow-sm">
                      <p className="text-[9px] font-bold uppercase tracking-widest text-foreground-muted mb-1">Status</p>
                      <p className="text-sm font-black text-status-online flex items-center gap-1.5"><CheckCircle2 className="h-3.5 w-3.5" /> Nominal</p>
                    </div>
                    <div className="border border-border p-4 rounded-lg bg-surface shadow-sm">
                      <p className="text-[9px] font-bold uppercase tracking-widest text-foreground-muted mb-1">MCDA Confidence</p>
                      <p className="text-xl font-black text-foreground">94.2%</p>
                    </div>
                    <div className="border border-border p-4 rounded-lg bg-surface shadow-sm">
                      <p className="text-[9px] font-bold uppercase tracking-widest text-foreground-muted mb-1">Active Nodes</p>
                      <p className="text-xl font-black text-foreground">1,204</p>
                    </div>
                  </div>

                  <div className="flex-1 border border-border rounded-lg bg-surface-muted/30 relative overflow-hidden">
                    {/* Abstract graph lines to look like an active chart */}
                    <svg className="absolute inset-0 w-full h-full opacity-40 stroke-accent" preserveAspectRatio="none" viewBox="0 0 100 100">
                      <path d="M0,80 Q20,20 40,60 T100,30" fill="none" strokeWidth="2" />
                      <path d="M0,90 Q30,40 50,70 T100,50" fill="none" strokeWidth="1" className="stroke-foreground-muted opacity-50" />
                    </svg>
                    <div className="absolute bottom-4 left-4 right-4 flex justify-between text-[10px] font-mono text-foreground-muted">
                      <span>t-60s</span>
                      <span>t-30s</span>
                      <span>t-0s (Live)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>



      {/* ── MASSIVE DATA VISUALIZATION SECTION ──────────────────────── */}
      <section className="relative py-40 bg-background overflow-hidden">
        {/* Transmission / Terrain Background - Highly Visible Enhanced Version */}
        <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
          <div
            className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?q=80&w=2560&auto=format&fit=crop')] bg-cover bg-center opacity-20 grayscale animate-pan-slow mix-blend-luminosity"
          />
          {/* Light gradient overlay to ensure text is readable at top/bottom while leaving center visuals highly visible */}
          <div className="absolute inset-0 bg-gradient-to-b from-background via-background/40 to-background" />
        </div>

        <div className="max-w-[90rem] mx-auto px-6 relative z-10">
          <div className="max-w-4xl mb-24">
            <h2 className="text-4xl md:text-5xl font-black tracking-tight text-foreground leading-[1.1] mb-6 drop-shadow-sm">
              Infrastructure-grade intelligence for every industrial decision.
            </h2>
            <p className="text-xl text-foreground-muted font-medium max-w-2xl">
              We process hundreds of variables—from regional biomass availability and grid tariffs to specific boiler efficiencies—to generate mathematically proven energy transitions.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Chart 1 */}
            <div className="border border-border/40 bg-white/70 backdrop-blur-xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-8 lg:p-12 rounded-xl relative">
              <div className="mb-12 relative z-10">
                <p className="text-[10px] font-bold uppercase tracking-widest text-accent mb-2">Simulated Trajectory</p>
                <h3 className="text-2xl font-black text-foreground">CO₂ Abatement Waterfall</h3>
                <p className="text-sm text-foreground-muted mt-2">12-month projection comparing baseline operation vs. optimal MCDA pathway.</p>
              </div>
              <div className="h-[300px] w-full relative z-10">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={emissionsData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                    <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v / 1000}k`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "hsl(var(--card))", borderColor: "hsl(var(--border))", borderRadius: "0px", fontSize: "12px", border: "1px solid hsl(var(--border))" }}
                      itemStyle={{ color: "hsl(var(--foreground))", fontWeight: "bold" }}
                    />
                    <Area type="step" dataKey="baseline" stroke="hsl(var(--foreground-muted))" strokeDasharray="4 4" fill="none" strokeWidth={2} name="Current Baseline" />
                    <Area type="step" dataKey="optimized" stroke="hsl(var(--accent))" fillOpacity={0.1} fill="hsl(var(--accent))" strokeWidth={3} name="Optimized Pathway" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2 */}
            <div className="border border-border/40 bg-white/70 backdrop-blur-xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-8 lg:p-12 rounded-xl relative">
              <div className="mb-12 relative z-10">
                <p className="text-[10px] font-bold uppercase tracking-widest text-accent mb-2">Financial Engineering</p>
                <h3 className="text-2xl font-black text-foreground">CAPEX Allocation & ROI</h3>
                <p className="text-sm text-foreground-muted mt-2">Capital expenditure mapped against projected annual operational savings.</p>
              </div>
              <div className="h-[300px] w-full relative z-10">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={roiData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                    <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "hsl(var(--background))", borderColor: "hsl(var(--border))", borderRadius: "0px", fontSize: "12px" }}
                      itemStyle={{ color: "hsl(var(--foreground))", fontWeight: "bold" }}
                      cursor={{ fill: "hsl(var(--surface-muted))" }}
                    />
                    <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "20px", fontWeight: "bold" }} />
                    <Bar dataKey="capex" name="CAPEX (₹ Lakhs)" fill="hsl(var(--foreground))" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="opex_saving" name="Annual OPEX Savings" fill="hsl(var(--accent))" radius={[0, 0, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ── CORE CAPABILITIES GRID (Features) ───────────────────────────────────── */}
      <section id="features" className="relative py-40 bg-foreground text-background overflow-hidden">
        {/* Factory Interior Background for Dark Section */}
        <div className="absolute inset-0 z-0 pointer-events-none">
          <div
            className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?q=80&w=2560&auto=format&fit=crop')] bg-cover bg-center opacity-[0.08] animate-zoom-slow"
          />
        </div>

        <div className="max-w-[90rem] mx-auto px-6 relative z-10">
          <div className="mb-24">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-background/50 border-b border-background/20 pb-1">
              System Architecture
            </span>
            <h2 className="text-4xl md:text-6xl font-black tracking-tight mt-6 max-w-3xl leading-[1.1]">
              The core engines powering industrial-scale transition.
            </h2>
          </div>

          <div className="grid md:grid-cols-3 border-t border-l border-background/10">
            {[
              {
                title: "MCDA Optimization Engine",
                desc: "Multi-criteria decision analysis evaluating dozens of technologies against specific thermal loads, capex limits, and operational hours.",
              },
              {
                title: "Spatial Biomass Atlas",
                desc: "District-level geographic intelligence mapping agricultural residue surplus and agro-pellet pricing across the subcontinent.",
              },
              {
                title: "Policy Vector Search",
                desc: "Real-time semantic matching against a vast index of BEE, MNRE, and state-level industrial subsidies to locate exact capital grants.",
              },
              {
                title: "Monte Carlo Risk Simulator",
                desc: "Stochastic modeling running 10,000+ localized fuel and grid price scenarios to calculate highly accurate P50 payback confidence bands.",
              },
              {
                title: "Scenario Control Playground",
                desc: "A live interface allowing engineers to manually override fuel costs, capex constraints, and schedules to compare alternative pathways.",
              },
              {
                title: "Auditable Knowledge Base",
                desc: "Fully transparent RAG pipeline referencing 200+ government circulars and IPCC emission factors to mathematically prove every recommendation.",
              }
            ].map((feature, i) => (
              <div
                key={i}
                className="p-10 border-b border-r border-background/10 hover:bg-background/5 transition-colors"
              >
                <h3 className="text-xl font-bold mb-4 tracking-tight">{feature.title}</h3>
                <p className="text-sm text-background/60 leading-relaxed font-medium">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TECHNOLOGY LIBRARY ────────────────────────────────────────────── */}
      <section id="technology" className="relative py-32 bg-surface border-y border-border overflow-hidden">
        <div className="max-w-[90rem] mx-auto px-6">
          <div className="mb-16">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent mb-6 block">Hardware Matrix</span>
            <h2 className="text-4xl md:text-5xl font-black tracking-tight text-foreground leading-[1.1]">
              Industrial Technology Library.
            </h2>
            <p className="text-xl text-foreground-muted font-medium max-w-2xl mt-6">
              Our optimizer simulates the thermodynamic and financial performance of 40+ OEM-agnostic abatement technologies.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { title: "Biomass Gasifiers", spec: "1-15 TPH Steam", icon: Flame },
              { title: "Electric Boilers", spec: "Up to 50 MW", icon: Zap },
              { title: "High-Temp Heat Pumps", spec: "Max 160°C", icon: Settings2 },
              { title: "Thermal Storage", spec: "Latent & Sensible", icon: Battery },
              { title: "Solar Thermal (CST)", spec: "Parabolic Trough", icon: Sun },
              { title: "Waste Heat Recovery", spec: "ORC Systems", icon: Factory },
              { title: "Cogeneration (CHP)", spec: "Power + Heat", icon: Cpu },
              { title: "H2-Ready Burners", spec: "Blended Firing", icon: Wind },
            ].map((tech, i) => (
              <div key={i} className="p-6 bg-background border border-border hover:border-accent/50 rounded-xl transition-all duration-300 hover:shadow-lg">
                <div className="w-10 h-10 rounded bg-surface border border-border flex items-center justify-center text-foreground mb-6">
                  <tech.icon className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-foreground mb-2">{tech.title}</h3>
                <div className="mt-auto pt-4 border-t border-border">
                  <p className="text-[10px] font-mono uppercase tracking-widest text-foreground-muted flex justify-between">
                    <span>Spec</span>
                    <span className="text-accent">{tech.spec}</span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SUBSIDIES ──────────────────────────────────────────────────────── */}
      <section id="subsidies" className="relative py-32 bg-background border-b border-border overflow-hidden">
        <div className="max-w-[90rem] mx-auto px-6 grid lg:grid-cols-2 gap-16 items-start">
          <div className="flex flex-col justify-center">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent mb-6">Policy Intelligence</span>
            <h2 className="text-4xl md:text-5xl font-black tracking-tight text-foreground leading-[1.1] mb-6">
              Pan-India Incentive Schemes.
            </h2>
            <p className="text-xl text-foreground-muted font-medium mb-8 leading-relaxed">
              The Indian government has deployed billions in capital subsidies for decarbonisation. CIETO tracks, indexes, and computes eligibility for every scheme in real-time.
            </p>
          </div>
          <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
            {[
              { name: "Perform, Achieve and Trade (PAT) Scheme", desc: "A regulatory instrument to reduce specific energy consumption in energy-intensive industries." },
              { name: "Indian Carbon Market (ICM)", desc: "The national framework for trading carbon credit certificates (CCCs)." },
              { name: "National Green Hydrogen Mission", desc: "Massive financial outlay (₹19,744 Cr) aiming to make India a global hub for Green Hydrogen." },
              { name: "National Bioenergy Programme", desc: "Capital subsidy grants for setting up biomass briquette/pellet manufacturing plants." },
              { name: "MSME ZED Certification", desc: "Financial assistance for MSMEs adopting Zero Defect Zero Effect manufacturing practices." }
            ].map((scheme, i) => (
              <div key={i} className="border-b border-border/50 last:border-0 py-6">
                <h4 className="text-lg font-bold text-foreground mb-2">{scheme.name}</h4>
                <p className="text-foreground-muted font-medium text-sm leading-relaxed">{scheme.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── KNOWLEDGE BASE (Protocols & Frameworks) ────────────────────────── */}
      <section id="knowledge-base" className="relative py-32 bg-surface-muted border-b border-border overflow-hidden">
        <div className="max-w-[90rem] mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-20">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent mb-6 block">Regulatory Compliance</span>
            <h2 className="text-4xl md:text-5xl font-black tracking-tight text-foreground leading-[1.1]">
              Conventions, Protocols & Treaties.
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-12">
            <div className="bg-surface border border-border rounded-2xl p-8 shadow-sm">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-full bg-background border border-border flex items-center justify-center text-foreground">
                  <Globe className="w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold tracking-tight text-foreground">Global Frameworks</h3>
              </div>
              <ul className="grid grid-cols-1 gap-4">
                {["Paris Agreement & UNFCCC", "Sustainable Development Goals (SDGs)", "ISO 50001 (Energy Management)", "Science Based Targets initiative (SBTi)"].map((fw, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="text-accent text-lg leading-none mt-0.5">•</span>
                    <span className="text-sm font-medium text-foreground-muted">{fw}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-surface border border-border rounded-2xl p-8 shadow-sm">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-full bg-background border border-border flex items-center justify-center text-foreground">
                  <MapPin className="w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold tracking-tight text-foreground">Indian Policies</h3>
              </div>
              <ul className="grid grid-cols-1 gap-4">
                {["Energy Conservation Act", "National Electricity Plan", "MNRE & BEE Guidelines", "State Captive Power Regulations"].map((fw, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="text-accent text-lg leading-none mt-0.5">•</span>
                    <span className="text-sm font-medium text-foreground-muted">{fw}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── BOTTOM CTA ────────────────────────────────────────────────────── */}
      <section className="relative py-40 bg-background text-foreground border-b border-border overflow-hidden">
        {/* Sunrise Factory Background */}
        <div className="absolute inset-0 z-0 pointer-events-none">
          <div
            className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1581092795360-fd1ca04f0952?q=80&w=2560&auto=format&fit=crop')] bg-cover bg-center opacity-[0.04] mix-blend-multiply"
          />
        </div>

        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <h2 className="text-4xl md:text-6xl font-black tracking-tight leading-[1.1] mb-8">
            Deploy industrial intelligence.
          </h2>
          <p className="text-xl text-foreground-muted mb-12 font-medium">
            Join the vanguard of manufacturers using deterministic mathematics to reach Net Zero.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/assessment"
              className="inline-flex h-16 items-center justify-center bg-foreground px-12 text-sm font-bold uppercase tracking-widest text-background transition-transform hover:scale-[1.02] shadow-sm rounded-sm"
            >
              Initiate Assessment Engine
            </Link>
            <Link
              href="/story"
              className="inline-flex h-16 items-center justify-center bg-surface border border-border px-12 text-sm font-bold uppercase tracking-widest text-foreground transition-colors hover:bg-surface-muted shadow-sm rounded-sm"
            >
              Read the CIETO Story
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ─────────────────────────────────────────────────── */}
      <footer className="bg-surface-muted py-16 text-foreground border-t border-border relative z-20">
        <div className="max-w-[90rem] mx-auto px-6 grid md:grid-cols-4 gap-12 mb-16">
          <div className="col-span-1 md:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-6">
              <span className="font-black text-xl tracking-tighter">CIETO</span>
            </Link>
            <p className="text-xs text-foreground-muted leading-relaxed max-w-xs font-medium">
              Enterprise Infrastructure for Industrial Decarbonization.
            </p>
          </div>
          <div>
            <h4 className="text-[10px] font-bold uppercase tracking-[0.2em] text-foreground-muted mb-6">Product</h4>
            <ul className="space-y-4 text-sm font-semibold">
              <li><Link href="/assessment" className="hover:text-accent transition-colors">Assessment Engine</Link></li>
              <li><Link href="/dashboard" className="hover:text-accent transition-colors">Intelligence Dashboard</Link></li>
              <li><Link href="/gis" className="hover:text-accent transition-colors">GIS Spatial Atlas</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-[10px] font-bold uppercase tracking-[0.2em] text-foreground-muted mb-6">Architecture</h4>
            <ul className="space-y-4 text-sm font-semibold">
              <li><span className="cursor-not-allowed">Monte Carlo Simulation</span></li>
              <li><span className="cursor-not-allowed">Subsidy Vector Search</span></li>
              <li><span className="cursor-not-allowed">MCDA Optimization</span></li>
            </ul>
          </div>
          <div>
            <h4 className="text-[10px] font-bold uppercase tracking-[0.2em] text-foreground-muted mb-6">Operations</h4>
            <ul className="space-y-4 text-sm font-semibold">
              <li><span className="cursor-not-allowed">Documentation</span></li>
              <li><span className="cursor-not-allowed">Security Compliance</span></li>
            </ul>
          </div>
        </div>
        <div className="max-w-[90rem] mx-auto px-6 flex flex-col md:flex-row items-center justify-between text-xs font-bold text-foreground-muted">
          <p>© {new Date().getFullYear()} CIETO. Built for Smart India Hackathon 2025.</p>
          <div className="flex items-center gap-2 mt-4 md:mt-0">
            <span className="h-2 w-2 rounded-full bg-status-online" />
            <span className="uppercase tracking-widest">All Systems Operational</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
