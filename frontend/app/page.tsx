"use client"

import Link from "next/link"
import { ArrowRight, Leaf, Zap, Factory, TrendingDown, Wind, Sun } from "lucide-react"
import { Sidebar } from "@/components/layout/Sidebar"
import { Navbar } from "@/components/layout/Navbar"

const stats = [
  { value: "9", label: "Industries Covered", sub: "Cement to Textile" },
  { value: "65%", label: "Avg. CO₂ Reduction", sub: "Per optimized factory" },
  { value: "₹2.1L Cr", label: "Subsidy Potential", sub: "Central + State schemes" },
  { value: "3.4 Yr", label: "Avg. Payback Period", sub: "Across all scenarios" },
]

const bento = [
  {
    col: "md:col-span-2",
    bg: "bg-emerald-950/90",
    tag: "AI Decision Engine",
    title: "Zero fossil fuel. Real numbers.",
    body: "Our multi-criteria engine evaluates solar thermal, biomass, electrification, heat pumps and more — then ranks them against your exact factory constraints.",
    icon: <Zap className="h-7 w-7 text-emerald-400" />,
    accent: "text-emerald-400",
    badge: "MCDA Ranked",
  },
  {
    col: "md:col-span-1",
    bg: "bg-green-900/90",
    tag: "Policy Matching",
    title: "Find subsidies you didn't know existed.",
    body: "Vector-search across central + state schemes to surface exact grants for your Udyam category, region & project type.",
    icon: <Leaf className="h-7 w-7 text-green-300" />,
    accent: "text-green-300",
    badge: "Live KB",
  },
  {
    col: "md:col-span-1",
    bg: "bg-slate-800/90",
    tag: "Emissions Engine",
    title: "Track every tonne of CO₂ saved.",
    body: "IPCC-based emission factors with grid-specific calculations for all Indian states.",
    icon: <TrendingDown className="h-7 w-7 text-sky-400" />,
    accent: "text-sky-400",
    badge: "IPCC Aligned",
  },
  {
    col: "md:col-span-2",
    bg: "bg-zinc-900/90",
    tag: "Financial Sensitivity",
    title: "Payback ranges, not guesses.",
    body: "Monte Carlo simulations on fuel price volatility give MSMEs bankable [low, high] payback bands — not a single optimistic number.",
    icon: <Sun className="h-7 w-7 text-amber-400" />,
    accent: "text-amber-400",
    badge: "Monte Carlo",
  },
]

export default function Home() {
  return (
    <div className="flex h-screen overflow-hidden bg-zinc-950">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto">

          {/* ── CINEMATIC HERO — full bleed photo background ─────── */}
          <section
            className="relative min-h-[90vh] flex flex-col justify-end overflow-hidden"
            style={{
              backgroundImage: "url('/hero_bg.jpg')",
              backgroundSize: "cover",
              backgroundPosition: "center 40%",
            }}
          >
            {/* Multi-layer dark overlay — strong at bottom for text legibility */}
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/60 to-zinc-950/10" />
            <div className="absolute inset-0 bg-gradient-to-r from-zinc-950/80 via-transparent to-transparent" />

            {/* Content — positioned at the bottom-left like AirCompany */}
            <div className="relative z-10 max-w-6xl mx-auto w-full px-8 md:px-16 pb-20">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/10 backdrop-blur-sm px-4 py-1.5 text-sm font-medium text-emerald-400">
                <span className="flex h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
                Decarbonization Platform for Indian MSMEs
              </div>

              <h1 className="text-6xl md:text-8xl font-black tracking-tight leading-none text-white mb-6 max-w-4xl">
                Powering India's<br />
                <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
                  green transition.
                </span>
              </h1>

              <p className="text-lg md:text-xl text-zinc-300 max-w-2xl leading-relaxed mb-10">
                The AI engine that tells every industrial MSME <strong className="text-white">exactly</strong> how to move from coal and fossil fuels to clean energy — with CAPEX, payback, CO₂ impact, and government subsidies calculated instantly.
              </p>

              <div className="flex flex-wrap gap-4">
                <Link
                  href="/assessment"
                  className="inline-flex h-14 items-center gap-2 rounded-2xl bg-emerald-500 px-8 text-base font-bold text-zinc-950 shadow-2xl shadow-emerald-500/30 transition-all hover:scale-105 hover:bg-emerald-400"
                >
                  Start Factory Assessment
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link
                  href="/dashboard"
                  className="inline-flex h-14 items-center gap-2 rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md px-8 text-base font-semibold text-white transition-all hover:bg-white/20"
                >
                  View Demo Dashboard
                </Link>
              </div>

              {/* Stats row at the very bottom of hero */}
              <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-px bg-white/10 rounded-2xl overflow-hidden border border-white/10 backdrop-blur-sm">
                {stats.map((s) => (
                  <div key={s.label} className="bg-zinc-950/60 backdrop-blur-md px-6 py-5">
                    <p className="text-3xl font-black text-emerald-400">{s.value}</p>
                    <p className="text-sm font-semibold text-white mt-1">{s.label}</p>
                    <p className="text-xs text-zinc-400 mt-0.5">{s.sub}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ── BENTO CAPABILITIES ─────────────────────────────────── */}
          <section className="bg-zinc-950 px-8 md:px-16 py-20">
            <div className="max-w-6xl mx-auto">
              <p className="text-xs font-bold uppercase tracking-widest text-emerald-500 mb-3">How It Works</p>
              <h2 className="text-4xl md:text-5xl font-black text-white mb-12 leading-tight">
                From fossil fuel to <br />clean energy — in minutes.
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {bento.map((card) => (
                  <div
                    key={card.title}
                    className={`${card.col} ${card.bg} border border-white/5 rounded-3xl p-8 flex flex-col justify-between min-h-[220px] group hover:scale-[1.015] transition-transform duration-300`}
                  >
                    <div>
                      <div className="flex items-start justify-between mb-4">
                        <div className="h-12 w-12 rounded-2xl bg-black/30 flex items-center justify-center">
                          {card.icon}
                        </div>
                        <span className={`text-xs font-bold uppercase tracking-wider ${card.accent} opacity-70`}>{card.badge}</span>
                      </div>
                      <p className="text-xs uppercase tracking-widest text-zinc-400 mb-2">{card.tag}</p>
                      <h3 className="text-xl md:text-2xl font-bold text-white leading-snug mb-3">{card.title}</h3>
                      <p className="text-sm text-zinc-400 leading-relaxed">{card.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ── MISSION STRIP ─────────────────────────────────────── */}
          <section className="bg-emerald-500 px-8 md:px-16 py-16">
            <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-8">
              <div>
                <h2 className="text-3xl md:text-4xl font-black text-zinc-950 leading-tight">
                  India's MSMEs emit <span className="underline decoration-wavy decoration-zinc-700/50">25% of industrial CO₂.</span>
                  <br />We're changing that.
                </h2>
                <p className="mt-4 text-zinc-800 max-w-xl leading-relaxed">
                  Every assessment run on this platform is a step toward a decarbonized industrial sector. We make clean energy transitions economically rational — not just aspirational.
                </p>
              </div>
              <Link href="/assessment" className="flex-shrink-0 inline-flex h-14 items-center gap-2 rounded-2xl bg-zinc-950 px-8 text-base font-bold text-emerald-400 transition-all hover:bg-zinc-800 hover:scale-105">
                Run Your Assessment
                <ArrowRight className="h-5 w-5" />
              </Link>
            </div>
          </section>

          {/* ── TECHNOLOGY TAGS ─────────────────────────────────────── */}
          <section className="bg-zinc-900 px-8 md:px-16 py-14 border-t border-zinc-800">
            <div className="max-w-6xl mx-auto">
              <p className="text-center text-sm text-zinc-500 mb-8 uppercase tracking-widest">Technologies Evaluated by the Engine</p>
              <div className="flex flex-wrap justify-center gap-4">
                {["Solar Thermal", "Biomass Boiler", "Heat Pump", "Waste Heat Recovery", "Biogas", "Electrification", "Thermal Storage"].map((tech) => (
                  <span key={tech} className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-5 py-2 text-sm font-medium text-emerald-400">
                    <Wind className="h-3.5 w-3.5" />
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          </section>

        </main>
      </div>
    </div>
  )
}
