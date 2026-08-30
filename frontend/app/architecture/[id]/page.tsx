import React from "react";
import Link from "next/link";
import { ArrowRight, Quote } from "lucide-react";
import { UrjivaLogo } from "@/components/ui/UrjivaLogo";

// Mock data for the detailed pages
const architectureData: Record<string, any> = {
  mcda: {
    hero: {
      bg: "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2560&auto=format&fit=crop",
      subtitleLeft: "OPTIMIZING",
      subtitleCenter: "INDUSTRIAL",
      subtitleRight: "DECARBONIZATION",
      title: "MCDA OS",
    },
    intro: {
      bannerImg: "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=2560&auto=format&fit=crop",
      heading: "Industrial operators should get the maximum return on every decarbonization investment. The MCDA engine brings mathematical rigor to the energy transition.",
      quote: "For decades, industries have watched billions in capital poured into inefficient decarbonization pathways plagued by fragmented data and chronic shortfalls. Today, we are finally delivering real change for the industrial sector, for our workforce, and for the climate goals they keep in focus. MCDA OS is not just new software; it is a new paradigm.",
    },
    integrations: {
      title: "SUPPORTED TECHNOLOGIES",
      items: [
        { name: "Electric Boilers", desc: "Up to 50MW capacity" },
        { name: "Biomass Gasifiers", desc: "High efficiency thermal" },
        { name: "Heat Pumps", desc: "Industrial scale recovery" },
      ],
    },
    impact: {
      bg: "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2560&auto=format&fit=crop",
      subtitle: "IMPACT",
      title1: "BUILDING",
      title2: "ON TIME",
    },
  },
  atlas: {
    hero: {
      bg: "https://images.unsplash.com/photo-1526628953301-3e589a6a8b74?q=80&w=2560&auto=format&fit=crop",
      subtitleLeft: "MAPPING",
      subtitleCenter: "THE ENERGY",
      subtitleRight: "LANDSCAPE",
      title: "ATLAS OS",
    },
    intro: {
      bannerImg: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2560&auto=format&fit=crop",
      heading: "Regional intelligence should drive supply chain certainty. Atlas OS maps biomass availability across the entire subcontinent.",
      quote: "Geographic data has long been trapped in static reports and outdated census figures. We bring dynamic, district-level spatial intelligence directly to the decision-maker. Predict supply, optimize logistics, and guarantee uptime.",
    },
    integrations: {
      title: "DATA SOURCES",
      items: [
        { name: "ISRO Satellite", desc: "Crop residue mapping" },
        { name: "Govt Census", desc: "District yields" },
        { name: "Market APIs", desc: "Live pricing" },
      ],
    },
    impact: {
      bg: "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?q=80&w=2560&auto=format&fit=crop",
      subtitle: "IMPACT",
      title1: "SECURING",
      title2: "SUPPLY",
    },
  },
  policy: {
    hero: {
      bg: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2560&auto=format&fit=crop",
      subtitleLeft: "NAVIGATING",
      subtitleCenter: "REGULATORY",
      subtitleRight: "FRAMEWORKS",
      title: "VECTOR OS",
    },
    intro: {
      bannerImg: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2560&auto=format&fit=crop",
      heading: "Compliance and subsidies shouldn't be a black box. Vector OS matches your exact technical specs with active capital grants.",
      quote: "Millions in available government subsidies go unclaimed every year due to bureaucratic friction. By indexing policies through advanced vector search, we ensure your projects always secure maximum possible financial support.",
    },
    integrations: {
      title: "INDEXED BODIES",
      items: [
        { name: "BEE India", desc: "Energy efficiency" },
        { name: "MNRE", desc: "Renewable grants" },
        { name: "State Nodal Agencies", desc: "Local subsidies" },
      ],
    },
    impact: {
      bg: "https://images.unsplash.com/photo-1526628953301-3e589a6a8b74?q=80&w=2560&auto=format&fit=crop",
      subtitle: "IMPACT",
      title1: "MAXIMIZING",
      title2: "CAPITAL",
    },
  },
  montecarlo: {
    hero: {
      bg: "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=2560&auto=format&fit=crop",
      subtitleLeft: "SIMULATING",
      subtitleCenter: "FINANCIAL",
      subtitleRight: "RESILIENCE",
      title: "RISK OS",
    },
    intro: {
      bannerImg: "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2560&auto=format&fit=crop",
      heading: "Uncertainty is the enemy of capital allocation. Risk OS runs thousands of market scenarios to guarantee your ROI.",
      quote: "A transition plan is only as good as its worst-case scenario. By applying stochastic modeling to fuel and grid price volatility, we provide P50 and P90 confidence bands that bank committees and boards can trust.",
    },
    integrations: {
      title: "RISK VECTORS",
      items: [
        { name: "Grid Tariffs", desc: "10-year projection" },
        { name: "Biomass Inflation", desc: "Seasonal modeling" },
        { name: "Carbon Pricing", desc: "ICM forecast" },
      ],
    },
    impact: {
      bg: "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?q=80&w=2560&auto=format&fit=crop",
      subtitle: "IMPACT",
      title1: "ENSURING",
      title2: "PAYBACK",
    },
  },
};

export default async function ArchitectureDetail({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  // Default to mcda if not found
  const data = architectureData[resolvedParams.id] || architectureData.mcda;

  return (
    <div className="min-h-screen bg-[#111111] text-[#f4f4f4] font-sans selection:bg-white/30 overflow-x-hidden">
      
      {/* ── 1. HERO SECTION ──────────────────────────────────────────────── */}
      <section className="relative h-[100svh] min-h-[600px] w-full flex flex-col justify-between overflow-hidden pt-8 pb-16">
        {/* Background Image */}
        <div className="absolute inset-0 z-0">
          <div
            className="absolute inset-0 bg-cover bg-center transition-transform duration-10000 hover:scale-105 opacity-80 mix-blend-luminosity"
            style={{ backgroundImage: `url(${data.hero.bg})` }}
          />
          {/* Subtle gradient overlay to ensure text readability */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/90" />
        </div>

        {/* Minimal Nav (Palantir style) */}
        <header className="relative z-10 px-8 flex justify-between items-center w-full max-w-[120rem] mx-auto">
          <Link href="/" className="flex items-center gap-2 text-white hover:opacity-80 transition-opacity">
            <UrjivaLogo className="w-6 h-6 text-white" />
            <span className="font-semibold tracking-wide text-lg">Urjiva</span>
          </Link>
          <Link href="/assessment" className="text-white text-xs font-bold tracking-widest uppercase hover:opacity-80 transition-opacity">
            Get Started
          </Link>
        </header>

        {/* Hero Content */}
        <div className="relative z-10 flex-1 flex flex-col justify-center max-w-[120rem] mx-auto w-full px-8 mt-20">
          
          {/* Middle Subtitles */}
          <div className="flex justify-between w-full text-white/90 text-sm md:text-xl lg:text-3xl font-light tracking-[0.2em] md:tracking-[0.3em] uppercase mb-16 md:mb-32">
            <span>{data.hero.subtitleLeft}</span>
            <span>{data.hero.subtitleCenter}</span>
            <span>{data.hero.subtitleRight}</span>
          </div>

          {/* Massive Title */}
          <div className="mt-auto flex justify-center w-full">
            <h1 className="text-[18vw] leading-[0.8] font-medium tracking-tighter text-white drop-shadow-2xl">
              {data.hero.title}
            </h1>
          </div>
        </div>
      </section>

      {/* ── 2. INTRODUCTION SECTION ──────────────────────────────────────── */}
      <section className="relative bg-[#1a1a1a] pb-32">
        {/* Top Banner Sliver */}
        <div className="h-24 md:h-32 w-full overflow-hidden">
          <div 
            className="w-full h-full bg-cover bg-center opacity-60 mix-blend-luminosity"
            style={{ backgroundImage: `url(${data.intro.bannerImg})` }}
          />
        </div>

        <div className="max-w-6xl mx-auto px-8 pt-20">
          <div className="border-t border-white/20 pt-4 mb-16 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 bg-white/50" />
              <span className="text-xs font-bold tracking-widest uppercase text-white/70">Introduction</span>
            </div>
            <span className="text-xs font-bold text-white/50">01</span>
          </div>

          {/* Main Statement */}
          <h2 className="text-3xl md:text-5xl lg:text-[3.5rem] font-medium leading-[1.1] tracking-tight text-white mb-32 max-w-5xl">
            {data.intro.heading}
          </h2>

          {/* Quote Block */}
          <div className="flex flex-col md:flex-row gap-8 md:gap-16 border-t border-white/20 pt-16">
            <div className="hidden md:block">
              <Quote className="w-16 h-16 text-white/40 rotate-180" strokeWidth={1} />
            </div>
            <p className="text-lg md:text-2xl font-light leading-relaxed text-white/90 max-w-3xl">
              {data.intro.quote}
            </p>
          </div>
        </div>
      </section>

      {/* ── 3. INTEGRATIONS / SUPPLIERS ──────────────────────────────────── */}
      <section className="bg-[#111111] py-32 border-t border-white/10">
        <div className="max-w-6xl mx-auto px-8">
          <div className="flex justify-between items-center border-b border-white/20 pb-4 mb-16">
            <h3 className="text-lg tracking-wide uppercase text-white/80">{data.integrations.title}</h3>
            <div className="flex gap-4 text-white/40">
              <ArrowRight className="w-6 h-6 rotate-180 cursor-pointer hover:text-white transition-colors" strokeWidth={1} />
              <ArrowRight className="w-6 h-6 cursor-pointer hover:text-white transition-colors" strokeWidth={1} />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {data.integrations.items.map((item: any, i: number) => (
              <div 
                key={i} 
                className="group relative h-40 border border-white/20 bg-white/5 flex flex-col items-center justify-center p-6 hover:bg-white/10 transition-colors cursor-pointer clip-path-angled"
                style={{
                  clipPath: "polygon(0 0, 85% 0, 100% 15%, 100% 100%, 0 100%)"
                }}
              >
                <h4 className="text-2xl font-bold tracking-tighter mb-2 text-white">{item.name}</h4>
                <p className="text-xs uppercase tracking-widest text-white/50">{item.desc}</p>
                {/* Decorative bottom dashes */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPjxyZWN0IHdpZHRoPSIyIiBoZWlnaHQ9IjIiIGZpbGw9IiM1NTUiLz48L3N2Zz4=')] opacity-50" />
              </div>
            ))}
          </div>

          <button className="w-full md:w-auto px-6 py-4 border border-white/20 bg-white/5 hover:bg-white/10 transition-colors flex justify-between items-center text-xs font-bold tracking-widest uppercase">
            <span>Expand List</span>
            <span className="ml-8 text-white/50">▼</span>
          </button>
        </div>
      </section>

      {/* ── 4. IMPACT SECTION ────────────────────────────────────────────── */}
      <section className="relative h-[80svh] min-h-[600px] flex items-center border-t border-white/20 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <div
            className="absolute inset-0 bg-cover bg-center opacity-80 mix-blend-luminosity"
            style={{ backgroundImage: `url(${data.impact.bg})` }}
          />
          {/* Subtle gradient to make text readable */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#111] via-[#111]/70 to-transparent" />
        </div>

        <div className="relative z-10 w-full max-w-6xl mx-auto px-8">
          <div className="border-t border-black/40 pt-4 mb-16 flex justify-between items-center max-w-xl">
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 bg-white" />
              <span className="text-xs font-bold tracking-widest uppercase text-white">{data.impact.subtitle}</span>
            </div>
            <span className="text-xs font-bold text-white">02</span>
          </div>

          <div className="flex flex-col">
            <h2 className="text-[12vw] md:text-[8rem] leading-[0.85] font-medium tracking-tighter text-white drop-shadow-lg">
              {data.impact.title1}<br />
              {data.impact.title2}
            </h2>
          </div>
        </div>
      </section>
      
      {/* ── 5. FOOTER (Minimal) ──────────────────────────────────────────── */}
      <footer className="bg-black py-12 border-t border-white/10 text-white/50 text-xs font-bold tracking-widest uppercase text-center">
        © {new Date().getFullYear()} Urjiva Systems. Confidential & Proprietary.
      </footer>
    </div>
  );
}
