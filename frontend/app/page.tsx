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
import { ShowcaseGallery } from "@/components/landing/ShowcaseGallery"

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
      <section className="relative h-[100svh] min-h-[600px] flex items-center justify-center overflow-hidden bg-black text-white">

        {/* Full-bleed Cinematic Industrial Background (Palantir Style) */}
        <div className="absolute inset-0 z-0 pointer-events-none">
          {/* Using a dark, atmospheric transmission tower/industrial fog image */}
          <div
            className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?q=80&w=2560&auto=format&fit=crop')] bg-cover bg-center animate-zoom-slow opacity-60 mix-blend-luminosity"
          />
          {/* Subtle dark gradient for top nav and bottom blending */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/20 to-black/80" />
        </div>

        <div className="relative z-10 text-center px-6 max-w-5xl mx-auto flex flex-col items-center justify-center w-full h-full pb-12">
          
          <motion.h1
            initial={{ opacity: 0, filter: "blur(10px)" }}
            animate={{ opacity: 1, filter: "blur(0px)" }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            className="text-[clamp(2.5rem,5vw,5.5rem)] font-normal tracking-tight leading-[1.05] text-white mb-6 drop-shadow-2xl"
          >
            Industrial Intelligence<br />for Every Decision
          </motion.h1>

        </div>

        {/* Disclaimer Text */}
        <div className="absolute bottom-12 left-0 right-0 z-10 text-center px-6">
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.5, delay: 0.5 }}
            className="text-[13px] text-white/50 font-medium tracking-wide max-w-2xl mx-auto"
          >
            The appearance of industrial emission visualizations<br />does not imply or constitute regulatory endorsement.
          </motion.p>
        </div>
      </section>



      {/* ── CORE CAPABILITIES (Interactive Showcase) ─────────────────────────── */}
      <div id="features">
        <ShowcaseGallery />
      </div>

      {/* ── MASSIVE DATA VISUALIZATION SECTION ──────────────────────── */}
      <section className="relative py-40 bg-background overflow-hidden border-b border-border">
        {/* Clean, Premium Geometric Background */}
        <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none opacity-50">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--foreground)/0.05)_0%,transparent_70%)]" />
          <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(to right, hsl(var(--foreground)/0.03) 1px, transparent 1px), linear-gradient(to bottom, hsl(var(--foreground)/0.03) 1px, transparent 1px)', backgroundSize: '64px 64px' }} />
          <div className="absolute inset-0 bg-gradient-to-b from-background via-transparent to-background" />
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
            <div className="border border-border/60 bg-surface/60 backdrop-blur-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)] p-8 lg:p-12 rounded-[2rem] relative group transition-transform duration-500 hover:-translate-y-1">
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
            <div className="border border-border/60 bg-surface/60 backdrop-blur-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)] p-8 lg:p-12 rounded-[2rem] relative group transition-transform duration-500 hover:-translate-y-1">
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

      {/* ── TECHNOLOGY LIBRARY ────────────────────────────────────────────── */}
      <section id="technology" className="relative py-32 bg-surface-muted overflow-hidden border-b border-border">
        {/* Subtle Background Elements */}
        <div className="absolute inset-0 z-0 pointer-events-none opacity-40">
           <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[100px]" />
           <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-foreground/5 rounded-full blur-[120px]" />
        </div>

        <div className="max-w-[90rem] mx-auto px-6 relative z-10">
          <div className="mb-16">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent mb-6 block">Hardware Matrix</span>
            <h2 className="text-4xl md:text-5xl font-black tracking-tight text-foreground leading-[1.1]">
              Industrial Technology Library.
            </h2>
            <p className="text-xl text-foreground-muted font-medium max-w-2xl mt-6">
              Our optimizer simulates the thermodynamic and financial performance of 40+ OEM-agnostic abatement technologies.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
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
              <div key={i} className="group p-8 bg-surface/60 backdrop-blur-xl border border-border/60 hover:border-accent/40 rounded-[1.5rem] transition-all duration-500 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] dark:hover:shadow-[0_8px_30px_rgb(0,0,0,0.2)] flex flex-col relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                <div className="w-12 h-12 rounded-xl bg-background border border-border/50 flex items-center justify-center text-foreground mb-8 shadow-sm group-hover:scale-110 transition-transform duration-500">
                  <tech.icon className="w-6 h-6" strokeWidth={1.5} />
                </div>
                <h3 className="text-xl font-bold text-foreground mb-4 tracking-tight">{tech.title}</h3>
                <div className="mt-auto pt-6 border-t border-border/40">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted flex justify-between items-center">
                    <span>Spec</span>
                    <span className="text-accent bg-accent/10 px-2 py-1 rounded-sm">{tech.spec}</span>
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
          <div className="flex flex-col justify-center sticky top-32">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent mb-6">Policy Intelligence</span>
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight text-foreground leading-[1.05] mb-6">
              Pan-India Incentive Schemes.
            </h2>
            <p className="text-xl text-foreground-muted font-medium mb-8 leading-relaxed max-w-lg">
              The Indian government has deployed billions in capital subsidies for decarbonisation. Urjiva tracks, indexes, and computes eligibility for every scheme in real-time.
            </p>
          </div>
          <div className="flex flex-col gap-4">
            {[
              { name: "Perform, Achieve and Trade (PAT) Scheme", desc: "A regulatory instrument to reduce specific energy consumption in energy-intensive industries." },
              { name: "Indian Carbon Market (ICM)", desc: "The national framework for trading carbon credit certificates (CCCs)." },
              { name: "National Green Hydrogen Mission", desc: "Massive financial outlay (₹19,744 Cr) aiming to make India a global hub for Green Hydrogen." },
              { name: "National Bioenergy Programme", desc: "Capital subsidy grants for setting up biomass briquette/pellet manufacturing plants." },
              { name: "MSME ZED Certification", desc: "Financial assistance for MSMEs adopting Zero Defect Zero Effect manufacturing practices." }
            ].map((scheme, i) => (
              <div key={i} className="group relative p-8 bg-surface/40 backdrop-blur-md border border-border/50 rounded-2xl transition-all duration-300 hover:bg-surface hover:shadow-sm">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-accent/0 group-hover:bg-accent transition-colors duration-300 rounded-l-2xl" />
                <h4 className="text-xl font-bold text-foreground mb-3 tracking-tight group-hover:text-accent transition-colors">{scheme.name}</h4>
                <p className="text-foreground-muted font-medium text-base leading-relaxed">{scheme.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── KNOWLEDGE BASE (Protocols & Frameworks) ────────────────────────── */}
      <section id="knowledge-base" className="relative py-32 bg-surface overflow-hidden border-b border-border">
        {/* Subtle dot matrix background */}
        <div className="absolute inset-0 z-0 pointer-events-none opacity-20" style={{ backgroundImage: 'radial-gradient(hsl(var(--foreground)/0.2) 1px, transparent 1px)', backgroundSize: '24px 24px' }} />

        <div className="max-w-[90rem] mx-auto px-6 relative z-10">
          <div className="text-center max-w-3xl mx-auto mb-20">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent mb-6 block">Regulatory Compliance</span>
            <h2 className="text-4xl md:text-5xl font-black tracking-tight text-foreground leading-[1.1]">
              Conventions, Protocols & Treaties.
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8 md:gap-12">
            <div className="bg-surface/80 backdrop-blur-2xl border border-border/60 rounded-[2rem] p-10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)]">
              <div className="flex items-center gap-6 mb-10">
                <div className="w-16 h-16 rounded-2xl bg-background border border-border/50 flex items-center justify-center text-foreground shadow-sm">
                  <Globe className="w-8 h-8" strokeWidth={1.5} />
                </div>
                <h3 className="text-3xl font-bold tracking-tight text-foreground">Global Frameworks</h3>
              </div>
              <ul className="grid grid-cols-1 gap-4">
                {["Paris Agreement & UNFCCC", "Sustainable Development Goals (SDGs)", "ISO 50001 (Energy Management)", "Science Based Targets initiative (SBTi)"].map((fw, i) => (
                  <li key={i} className="flex items-center gap-4 group p-4 rounded-xl hover:bg-background/50 transition-colors border border-transparent hover:border-border/30">
                    <CheckCircle2 className="w-5 h-5 text-accent opacity-70 group-hover:opacity-100 transition-opacity shrink-0" />
                    <span className="text-base font-semibold text-foreground-muted group-hover:text-foreground transition-colors">{fw}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="bg-surface/80 backdrop-blur-2xl border border-border/60 rounded-[2rem] p-10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)]">
              <div className="flex items-center gap-6 mb-10">
                <div className="w-16 h-16 rounded-2xl bg-background border border-border/50 flex items-center justify-center text-foreground shadow-sm">
                  <MapPin className="w-8 h-8" strokeWidth={1.5} />
                </div>
                <h3 className="text-3xl font-bold tracking-tight text-foreground">Indian Policies</h3>
              </div>
              <ul className="grid grid-cols-1 gap-4">
                {["Energy Conservation Act", "National Electricity Plan", "MNRE & BEE Guidelines", "State Captive Power Regulations"].map((fw, i) => (
                  <li key={i} className="flex items-center gap-4 group p-4 rounded-xl hover:bg-background/50 transition-colors border border-transparent hover:border-border/30">
                    <CheckCircle2 className="w-5 h-5 text-accent opacity-70 group-hover:opacity-100 transition-opacity shrink-0" />
                    <span className="text-base font-semibold text-foreground-muted group-hover:text-foreground transition-colors">{fw}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── BOTTOM CTA (Cinematic Bookend) ─────────────────────────────────── */}
      <section className="relative py-40 bg-black text-white border-b border-white/10 overflow-hidden">
        {/* Deep Cinematic Background */}
        <div className="absolute inset-0 z-0 pointer-events-none">
          <div
            className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1581092795360-fd1ca04f0952?q=80&w=2560&auto=format&fit=crop')] bg-cover bg-center opacity-40 mix-blend-luminosity"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-black/30" />
        </div>

        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <h2 className="text-4xl md:text-6xl font-black tracking-tight leading-[1.1] mb-8 drop-shadow-2xl">
            Deploy industrial intelligence.
          </h2>
          <p className="text-xl text-white/70 mb-12 font-medium max-w-2xl mx-auto">
            Join the vanguard of manufacturers using deterministic mathematics to reach Net Zero.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/assessment"
              className="inline-flex h-16 items-center justify-center bg-white px-12 text-sm font-bold uppercase tracking-widest text-black transition-transform hover:scale-[1.02] shadow-[0_0_40px_rgba(255,255,255,0.2)] rounded-sm"
            >
              Initiate Assessment Engine
            </Link>
            <Link
              href="/story"
              className="inline-flex h-16 items-center justify-center bg-white/5 backdrop-blur-md border border-white/20 px-12 text-sm font-bold uppercase tracking-widest text-white transition-colors hover:bg-white/10 rounded-sm"
            >
              Read the Urjiva Story
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ─────────────────────────────────────────────────── */}
      <footer className="bg-surface-muted py-16 text-foreground border-t border-border relative z-20">
        <div className="max-w-[90rem] mx-auto px-6 grid md:grid-cols-4 gap-12 mb-16">
          <div className="col-span-1 md:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-6">
              <span className="font-black text-xl tracking-tighter">Urjiva</span>
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
          <p>© {new Date().getFullYear()} Urjiva. Built for Smart India Hackathon 2025.</p>
          <div className="flex items-center gap-2 mt-4 md:mt-0">
            <span className="h-2 w-2 rounded-full bg-status-online" />
            <span className="uppercase tracking-widest">All Systems Operational</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
