"use client"

import React, { useRef, useState, useEffect } from "react"
import { motion, useScroll, useTransform, useInView, AnimatePresence } from "framer-motion"
import { LandingNavbar } from "@/components/layout/LandingNavbar"
import Link from "next/link"
import { ArrowRight, FileText, Globe, Network, Factory, Zap } from "lucide-react"

export default function StoryPage() {
  return (
    <div className="bg-black text-white min-h-screen selection:bg-white/20 font-sans overflow-x-hidden">
      <LandingNavbar />
      <main>
        <Chapter1 />
        <Chapter2 />
        <Chapter3 />
        <Chapter4 />
        <Chapter5 />
        <Chapter6 />
        <Chapter7 />
        <Chapter8 />
        <Chapter9 />
        <FinalChapter />
      </main>
    </div>
  )
}

/* ── CHAPTER 01: The Turning Point ────────────────────────────────────────── */
function Chapter1() {
  const { scrollY } = useScroll()
  const y1 = useTransform(scrollY, [0, 1000], [0, 200])
  const opacity = useTransform(scrollY, [0, 500], [1, 0])

  return (
    <section className="relative h-[120vh] flex items-center justify-center overflow-hidden bg-black">
      {/* High-Fidelity Cinematic Industrial Background */}
      <motion.div 
        style={{ y: y1 }} 
        className="absolute inset-0 z-0 w-full h-[150%] pointer-events-none"
      >
        <motion.div 
          className="absolute inset-0 bg-cover bg-center opacity-80"
          style={{ backgroundImage: "url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop')" }}
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
        />
        {/* Lighter gradient so the photo is clearly visible */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-black/20" />
      </motion.div>

      <div className="absolute inset-0 z-10 bg-gradient-to-b from-black/60 via-transparent to-black" />

      <motion.div style={{ opacity }} className="relative z-20 max-w-[90rem] mx-auto px-6 text-center mt-20">
        <motion.h1 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          className="text-[clamp(3rem,8vw,8rem)] font-black leading-[0.95] tracking-tight mb-8 drop-shadow-2xl"
        >
          The Next Industrial Revolution <br/>
          <span className="text-white/80">Will Be Measured in Carbon.</span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.5, delay: 0.8 }}
          className="text-xl md:text-3xl text-white/70 max-w-3xl mx-auto font-medium drop-shadow-md"
        >
          Industrial energy is entering the largest transformation in over a century.
        </motion.p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2, duration: 2 }}
        className="absolute bottom-20 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-4 opacity-60"
      >
        <span className="text-[10px] font-bold uppercase tracking-widest text-white drop-shadow-md">Begin the Story</span>
        <div className="w-[1px] h-12 bg-gradient-to-b from-white/80 to-transparent" />
      </motion.div>
    </section>
  )
}

/* ── CHAPTER 02: Why Now (Timeline) ────────────────────────────────────────── */
function Chapter2() {
  const containerRef = useRef(null)
  
  const [activeIndex, setActiveIndex] = useState(0)

  const milestones = [
    { title: "Paris Agreement", type: "paris" },
    { title: "UN SDGs", type: "paris" },
    { title: "COP26", type: "cop" },
    { title: "Global Stocktake", type: "stocktake" },
    { title: "Net Zero Commitments", type: "netzero" },
    { title: "India's Panchamrit", type: "india" },
    { title: "Carbon Credit Trading", type: "india" },
    { title: "Mission LiFE", type: "india" },
    { title: "2030 Targets", type: "india" },
    { title: "2070 India Net Zero", type: "netzero" }
  ]

  return (
    <section ref={containerRef} className="relative py-40 bg-black overflow-hidden border-t border-white/10">
      
      {/* Dynamic Cinematic Background Layer */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        
        <AnimatePresence mode="wait">
          {milestones[activeIndex]?.type === "paris" && (
            <motion.div key="paris" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 1 }} className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop')] bg-cover bg-center">
              <div className="absolute inset-0 bg-black/40" /> {/* Brighter overlay */}
            </motion.div>
          )}
          {milestones[activeIndex]?.type === "cop" && (
            <motion.div key="cop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 1 }} className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1540575467063-178a50c2df87?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center">
              <div className="absolute inset-0 bg-black/50" />
            </motion.div>
          )}
          {milestones[activeIndex]?.type === "stocktake" && (
            <motion.div key="stocktake" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 1 }} className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop')] bg-cover bg-center">
              <div className="absolute inset-0 bg-black/50" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] border border-white/20 rounded-full animate-[spin_40s_linear_infinite]" />
            </motion.div>
          )}
          {milestones[activeIndex]?.type === "netzero" && (
            <motion.div key="netzero" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 1 }} className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1466611653911-95081537e5b7?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center">
              <div className="absolute inset-0 bg-black/40" />
            </motion.div>
          )}
          {milestones[activeIndex]?.type === "india" && (
            <motion.div key="india" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 1 }} className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center">
               <div className="absolute inset-0 bg-black/40" />
               <div className="absolute inset-0 bg-orange-900/20 mix-blend-multiply" />
            </motion.div>
          )}
        </AnimatePresence>
        {/* Global vignette/fade to blend section edges */}
        <div className="absolute inset-0 bg-gradient-to-b from-black via-transparent to-black" />
      </div>
      
      <div className="max-w-[90rem] mx-auto px-6 relative z-10">
        <h2 className="text-4xl md:text-6xl font-black mb-32 opacity-90 drop-shadow-md">History is unfolding.</h2>
        
        <div className="relative border-l border-white/20 ml-4 md:ml-10 space-y-32">
          {milestones.map((m, i) => (
            <MilestoneItem key={i} title={m.title} index={i} onInView={() => setActiveIndex(i)} />
          ))}
        </div>
      </div>
    </section>
  )
}

function MilestoneItem({ title, index, onInView }: { title: string, index: number, onInView: () => void }) {
  const ref = useRef(null)
  // Wider margin to ensure at least one is always active and rhythm doesn't drop to 0
  const isInView = useInView(ref, { margin: "-30% 0px -30% 0px" })
  
  useEffect(() => {
    if (isInView) {
      onInView()
    }
  }, [isInView, onInView])
  
  return (
    <div ref={ref} className="relative pl-12 md:pl-20 group py-4 transition-opacity duration-500">
      <motion.div 
        className="absolute left-[-5px] top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-white transition-all duration-500"
        animate={{
          scale: isInView ? 1.5 : 1,
          opacity: isInView ? 1 : 0.4,
          boxShadow: isInView ? "0 0 20px 4px rgba(255,255,255,0.6)" : "none"
        }}
      />
      <motion.div
        animate={{ opacity: isInView ? 1 : 0.4, x: isInView ? 0 : -10 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <h3 className={`text-3xl md:text-5xl font-bold tracking-tight drop-shadow-md transition-colors duration-500 ${isInView ? "text-white" : "text-white/60"}`}>
          {title}
        </h3>
      </motion.div>
    </div>
  )
}

/* ── CHAPTER 03: The Scale of the Challenge ────────────────────────────────────────── */
function Chapter3() {
  const ref = useRef(null)
  const isInView = useInView(ref, { margin: "-40% 0px -40% 0px" })

  return (
    <section ref={ref} className="min-h-screen bg-black flex flex-col justify-center items-center py-40 border-t border-white/10 relative overflow-hidden">
      {/* Background image to remove the plain black feeling */}
      <div className="absolute inset-0 pointer-events-none opacity-40">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center" />
        <div className="absolute inset-0 bg-black/70" />
      </div>

      <div className="space-y-32 text-center max-w-5xl mx-auto px-6 relative z-10">
        <StatBlock value="45%" label="Industrial energy consumption" active={isInView} delay={0} />
        <StatBlock value="Millions" label="of manufacturing decisions every year" active={isInView} delay={0.2} />
        <StatBlock value="Thousands" label="of industrial clusters" active={isInView} delay={0.4} />
        <StatBlock value="Millions" label="of tonnes of avoidable emissions" active={isInView} delay={0.6} />
        
        <motion.h3 
          initial={{ opacity: 0 }}
          animate={{ opacity: isInView ? 1 : 0 }}
          transition={{ duration: 1, delay: 1 }}
          className="text-5xl md:text-7xl font-black mt-32 text-white drop-shadow-xl"
        >
          Every decision matters.
        </motion.h3>
      </div>
    </section>
  )
}

function StatBlock({ value, label, active, delay }: { value: string, label: string, active: boolean, delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: active ? 1 : 0, y: active ? 0 : 40 }}
      transition={{ duration: 0.8, delay, ease: "easeOut" }}
    >
      <h2 className="text-7xl md:text-[8rem] font-black tracking-tighter leading-none mb-4 drop-shadow-lg">{value}</h2>
      <p className="text-xl md:text-3xl text-white/80 font-medium drop-shadow-md">{label}</p>
    </motion.div>
  )
}

/* ── CHAPTER 04: The Invisible Complexity (The Problem) ────────────────────────────────────────── */
function Chapter4() {
  const containerRef = useRef(null)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start center", "end center"]
  })

  const leftX = useTransform(scrollYProgress, [0, 0.5], ["-50%", "0%"])
  const rightX = useTransform(scrollYProgress, [0, 0.5], ["50%", "0%"])
  const opacity = useTransform(scrollYProgress, [0.4, 0.6], [0, 1])

  return (
    <section ref={containerRef} className="min-h-[150vh] bg-black relative border-t border-white/10">
      <div className="sticky top-0 h-screen flex flex-col justify-center overflow-hidden">
        
        {/* Split Cinematic Background */}
        <div className="absolute inset-0 z-0 flex pointer-events-none">
          {/* Left: Dark Haze / Pollution (Industrial Image) */}
          <div className="w-1/2 h-full bg-black relative overflow-hidden">
             <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1611273426858-450d8e3c9eeb?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center opacity-40" />
             <div className="absolute inset-0 bg-gradient-to-r from-black via-black/50 to-transparent" />
          </div>
          {/* Right: Clean Digital Grid */}
          <div className="w-1/2 h-full bg-[#000a14] relative overflow-hidden border-l border-white/10">
             <div className="absolute inset-0 bg-[linear-gradient(rgba(0,150,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(0,150,255,0.1)_1px,transparent_1px)] bg-[size:30px_30px] animate-pan-slow opacity-30" />
             <div className="absolute top-0 left-0 w-96 h-96 bg-blue-500/20 blur-[100px] animate-float-slow" />
             <div className="absolute inset-0 bg-gradient-to-l from-black via-transparent to-black/50" />
          </div>
        </div>

        <div className="flex w-full max-w-[90rem] mx-auto px-6 h-full items-center relative z-10">
          <motion.div style={{ x: leftX }} className="w-1/2 flex flex-col items-end pr-8 md:pr-16 text-right">
            <h3 className="text-3xl font-bold mb-8 text-white/70">Factory Owner</h3>
            <ul className="space-y-4 text-xl md:text-2xl font-semibold text-white/90 drop-shadow-md">
              <li>Coal prices</li>
              <li>Electricity tariffs</li>
              <li>Subsidy confusion</li>
              <li>Technology uncertainty</li>
              <li>Capital constraints</li>
            </ul>
          </motion.div>

          <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-gradient-to-b from-transparent via-white/30 to-transparent -translate-x-1/2" />

          <motion.div style={{ x: rightX }} className="w-1/2 flex flex-col items-start pl-8 md:pl-16">
            <h3 className="text-3xl font-bold mb-8 text-blue-300/80">Climate Targets</h3>
            <ul className="space-y-4 text-xl md:text-2xl font-semibold text-white/90 drop-shadow-md">
              <li>Government schemes</li>
              <li>Global regulations</li>
              <li>Carbon accounting</li>
              <li>Energy transition</li>
              <li>Supply chain rules</li>
            </ul>
          </motion.div>
        </div>

        <motion.div 
          style={{ opacity }}
          className="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-md z-20"
        >
          <h2 className="text-4xl md:text-6xl font-black text-center px-6 leading-tight drop-shadow-xl text-white">
            These worlds rarely <br/> speak the same language.
          </h2>
        </motion.div>
      </div>
    </section>
  )
}

/* ── CHAPTER 05: Why Traditional Decision Making Breaks ────────────────────────────────────────── */
function Chapter5() {
  const ref = useRef(null)
  const isInView = useInView(ref, { margin: "-30% 0px -30% 0px" })

  return (
    <section ref={ref} className="py-40 bg-black border-t border-white/10 relative overflow-hidden">
      {/* Cinematic Office/Blueprint Background */}
      <div className="absolute inset-0 pointer-events-none opacity-30">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1497215728101-856f4ea42174?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center" />
        <div className="absolute inset-0 bg-black/80" />
      </div>

      <div className="max-w-5xl mx-auto px-6 relative z-10">
        <div className="mb-32">
          <h3 className="text-xl font-bold text-white/50 uppercase tracking-widest mb-12">Traditional</h3>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
            {["Excel", "Consultants", "PDF Reports", "Static Audits", "Manual Calculations", "Isolated Datasets"].map((item, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: isInView ? 0.3 : 0, scale: isInView ? 1 : 0.95 }}
                transition={{ delay: i * 0.1, duration: 1 }}
                className="p-6 border border-white/20 rounded-lg line-through decoration-white/50 decoration-2 text-white bg-black/50 backdrop-blur-sm"
              >
                {item}
              </motion.div>
            ))}
          </div>
          <motion.p 
            animate={{ opacity: isInView ? 1 : 0 }}
            className="mt-8 text-xl text-red-400 font-medium drop-shadow-md"
          >
            Outdated immediately.
          </motion.p>
        </div>

        <div>
          <h3 className="text-xl font-bold text-white uppercase tracking-widest mb-12 flex items-center gap-4 drop-shadow-md">
            <Zap className="text-white w-5 h-5" /> Modern
          </h3>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
            {["Live Policy Engine", "Engineering Simulation", "GIS Intelligence", "Financial Modelling", "Emission Analytics", "Continuous Optimization"].map((item, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: isInView ? 1 : 0, y: isInView ? 0 : 20 }}
                transition={{ delay: 0.5 + (i * 0.1), duration: 0.8 }}
                className="p-6 border border-white/20 bg-white/10 rounded-lg font-semibold flex items-center gap-3 shadow-xl backdrop-blur-md"
              >
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-slow shadow-[0_0_10px_rgba(52,211,153,0.8)]" />
                <span className="text-white text-lg">{item}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

/* ── CHAPTER 06: The Missing Intelligence Layer ────────────────────────────────────────── */
function Chapter6() {
  return (
    <section className="py-60 bg-black relative flex flex-col items-center justify-center text-center px-6 overflow-hidden">
      {/* Code-driven Blueprint Animation Background */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-40">
        <svg width="100%" height="100%" className="absolute inset-0">
          <defs>
            <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
              <rect width="60" height="60" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" className="animate-pan-slow" />
          
          {/* Animated Intelligence Lines */}
          <g className="stroke-white/50" strokeWidth="2" fill="none">
            <motion.path 
              d="M100,500 Q300,200 600,400 T1200,300" 
              initial={{ pathLength: 0, opacity: 0 }}
              whileInView={{ pathLength: 1, opacity: 1 }}
              viewport={{ margin: "-20%" }}
              transition={{ duration: 4, ease: "easeInOut" }}
            />
            <motion.path 
              d="M200,800 Q500,600 800,700 T1400,500" 
              initial={{ pathLength: 0, opacity: 0 }}
              whileInView={{ pathLength: 1, opacity: 1 }}
              viewport={{ margin: "-20%" }}
              transition={{ duration: 5, ease: "easeInOut", delay: 1 }}
            />
          </g>
          {/* Glowing Nodes */}
          <motion.circle cx="600" cy="400" r="6" className="fill-white shadow-[0_0_20px_white]" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ delay: 2 }} />
          <motion.circle cx="800" cy="700" r="6" className="fill-white shadow-[0_0_20px_white]" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ delay: 3 }} />
        </svg>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_20%,black_80%)]" />
      </div>
      
      <div className="relative z-10 max-w-4xl">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: false, margin: "-20%" }}
          transition={{ duration: 1.5 }}
          className="space-y-6 text-3xl md:text-5xl font-bold text-white/50 mb-20 drop-shadow-md"
        >
          <p>Industry has ERP.</p>
          <p>Industry has SCADA.</p>
          <p>Industry has Sensors.</p>
          <p>Industry has Machines.</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: false, margin: "-20%" }}
          transition={{ duration: 1.5, delay: 0.8 }}
        >
          <p className="text-4xl md:text-6xl font-black mb-10 leading-tight text-white drop-shadow-xl">
            What industry never had... <br/>
            was intelligence connecting them all.
          </p>
          <div className="w-16 h-2 bg-white mx-auto rounded-full shadow-[0_0_10px_white]" />
        </motion.div>
      </div>
    </section>
  )
}

/* ── CHAPTER 07: How Urjiva Thinks (Urjiva Vision) ────────────────────────────────────────── */
function Chapter7() {
  const steps = [
    { icon: Factory, label: "Factory Telemetry" },
    { icon: Globe, label: "GIS Biomass Atlas" },
    { icon: FileText, label: "Policy Base" },
    { icon: Network, label: "Monte Carlo" },
    { icon: Zap, label: "MCDA Engine" },
    { icon: ArrowRight, label: "Decision" },
  ]

  return (
    <section className="py-40 bg-black border-t border-white/10 relative overflow-hidden">
      {/* Abstract Neuron Network Background (Brighter) */}
      <div className="absolute inset-0 opacity-30 pointer-events-none">
         <div className="absolute top-1/2 left-0 right-0 h-40 bg-blue-500/30 blur-[100px] -translate-y-1/2 animate-pulse-slow mix-blend-screen" />
         <div className="absolute top-1/3 left-1/3 w-64 h-64 bg-emerald-500/20 blur-[100px] animate-float-slow mix-blend-screen" />
      </div>

      <div className="max-w-[90rem] mx-auto px-6 relative z-10">
        <h2 className="text-4xl md:text-6xl font-black mb-40 text-center text-white drop-shadow-lg">How Urjiva Thinks</h2>
        
        <div className="relative flex flex-col md:flex-row justify-between items-center max-w-5xl mx-auto gap-12 md:gap-0">
          {/* Subtle glowing connecting line */}
          <div className="hidden md:block absolute top-1/2 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-blue-500/50 to-transparent -translate-y-1/2 shadow-[0_0_15px_rgba(59,130,246,0.8)]" />
          
          {steps.map((step, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false, margin: "-10%" }}
              transition={{ delay: i * 0.2, duration: 1 }}
              className="relative z-10 flex flex-col items-center gap-4 bg-black px-4"
            >
              <div className="w-20 h-20 rounded-full border-2 border-white/20 bg-black flex items-center justify-center shadow-[0_0_30px_rgba(255,255,255,0.1)] transition-colors hover:border-white/50">
                <step.icon className="w-8 h-8 text-white/90" />
              </div>
              <p className="text-xs font-bold uppercase tracking-widest text-center w-28 text-white/70">
                {step.label}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ── CHAPTER 08: Every Recommendation is Evidence Based ────────────────────────────────────────── */
function Chapter8() {
  const docs = ["BEE Framework", "IPCC Guidelines", "NITI Aayog Reports", "TERI Standards", "CEEW Analysis", "MNRE Policies"]
  
  return (
    <section className="py-40 bg-black relative overflow-hidden flex items-center border-t border-white/10">
      
      {/* Background Library/Data Image */}
      <div className="absolute inset-0 pointer-events-none opacity-30">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=2034&auto=format&fit=crop')] bg-cover bg-center" />
        <div className="absolute inset-0 bg-black/80" />
      </div>

      <div className="max-w-[90rem] mx-auto px-6 w-full grid lg:grid-cols-2 gap-20 items-center relative z-10">
        
        <div>
          <h2 className="text-5xl md:text-7xl font-black mb-8 text-white drop-shadow-xl">Evidence Based.</h2>
          <p className="text-2xl text-white/80 leading-relaxed font-medium drop-shadow-md">
            Every recommendation visually traces back to its engineering standard. We don't just use AI; we root every decision in institutional policy.
          </p>
        </div>

        <div className="relative h-[500px]">
          {docs.map((doc, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 50, rotate: Math.random() * 20 - 10 }}
              whileInView={{ opacity: 1, y: 0, rotate: Math.random() * 10 - 5 }}
              viewport={{ once: false, margin: "-10%" }}
              transition={{ delay: i * 0.15, duration: 1.2, ease: "easeOut" }}
              className="absolute p-6 border border-white/20 bg-white/10 rounded-lg shadow-2xl flex items-start gap-4 w-64 backdrop-blur-xl"
              style={{
                left: `${(i % 2) * 40}%`,
                top: `${i * 15}%`,
                zIndex: i,
              }}
            >
              <FileText className="w-6 h-6 text-emerald-400 shrink-0" />
              <div>
                <p className="text-[10px] uppercase font-bold text-white/60 mb-1 tracking-wider">Source Verified</p>
                <p className="text-base font-semibold text-white">{doc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ── CHAPTER 09: The Future We Believe In ────────────────────────────────────────── */
function Chapter9() {
  return (
    <section className="min-h-screen flex items-center justify-center py-40 relative overflow-hidden">
      {/* Ending Cinematic Background (Sunrise) */}
      <div className="absolute inset-0 bg-[#000510] z-0" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-500/30 via-blue-900/20 to-transparent opacity-80 z-0 animate-pulse-slow" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/80 to-[#ffffff] z-10 transition-colors duration-1000" />
      
      {/* Slow moving fog */}
      <div className="absolute bottom-0 w-full h-[50vh] bg-[url('https://www.transparenttextures.com/patterns/black-scales.png')] opacity-20 animate-drift-slow z-0" />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: false, margin: "-20%" }}
        transition={{ duration: 2.5, ease: "easeOut" }}
        className="relative z-20 text-center max-w-5xl px-6"
      >
        <h2 className="text-4xl md:text-6xl font-black leading-[1.1] text-white mb-12 drop-shadow-2xl">
          The Future Will Not Be Built <br/> By Choosing Between <br/> Industry and Sustainability.
        </h2>
        <h2 className="text-4xl md:text-6xl font-black leading-[1.1] text-white/60 drop-shadow-xl">
          It Will Be Built <br/> By Making Better Decisions.
        </h2>
      </motion.div>
    </section>
  )
}

/* ── FINAL CHAPTER ────────────────────────────────────────── */
function FinalChapter() {
  return (
    <section className="min-h-screen bg-white text-black flex flex-col items-center justify-center text-center px-6 selection:bg-black/10 relative z-20">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-[clamp(4rem,8vw,8rem)] font-black tracking-tighter leading-[0.85] mb-12">
          The Intelligence Layer <br/>
          For Industrial <br/> Decarbonization.
        </h1>
        
        <p className="text-xl md:text-2xl text-black/60 font-medium max-w-3xl mx-auto leading-relaxed mb-16">
          Urjiva combines engineering, economics, policy intelligence, geospatial data, and scientific evidence into a single industrial decision engine built for the next generation of manufacturing.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/assessment"
            className="group flex h-14 items-center justify-center gap-3 bg-black px-10 text-sm font-bold text-white transition-all hover:bg-zinc-800"
          >
            Start Assessment
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            href="/dashboard"
            className="flex h-14 items-center justify-center gap-3 border-2 border-black/10 px-10 text-sm font-bold text-black transition-colors hover:border-black/30 hover:bg-black/5"
          >
            Explore the Platform
          </Link>
        </div>
      </div>
    </section>
  )
}
