"use client"

import React, { useRef } from "react"
import { motion, useScroll, useTransform } from "framer-motion"
import { LandingNavbar } from "@/components/layout/LandingNavbar"
import { FileText, CheckCircle2, Search, ArrowDown, Map as MapIcon, Landmark } from "lucide-react"

const schemes = [
  { id: "pat", name: "PAT Scheme", ministry: "BEE", amount: "₹450 Cr" },
  { id: "nghm", name: "National Green Hydrogen", ministry: "MNRE", amount: "₹19,744 Cr" },
  { id: "zed", name: "MSME ZED", ministry: "MSME", amount: "₹500 Cr" },
  { id: "bio", name: "National Bioenergy", ministry: "MNRE", amount: "₹858 Cr" },
  { id: "state", name: "State Capital Subsidy", ministry: "State Govt", amount: "Variable" },
]

export default function SubsidiesPage() {
  const containerRef = useRef<HTMLDivElement>(null)
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  // Scattering to convergence transforms
  const scatterY = useTransform(scrollYProgress, [0, 0.4], [0, 400])
  const opacity = useTransform(scrollYProgress, [0, 0.3, 0.6], [1, 0, 0])
  const engineOpacity = useTransform(scrollYProgress, [0.4, 0.6], [0, 1])
  const engineScale = useTransform(scrollYProgress, [0.4, 0.6], [0.8, 1])
  
  return (
    <div className="min-h-screen bg-background font-sans" ref={containerRef}>
      <LandingNavbar />
      
      {/* Scroll Container */}
      <div className="h-[300vh] relative">
        
        {/* Sticky Viewport */}
        <div className="sticky top-0 h-screen overflow-hidden flex flex-col items-center justify-center pt-16">
          
          {/* Phase 1: The Scattered Problem */}
          <motion.div 
            style={{ opacity }}
            className="absolute inset-0 flex flex-col items-center justify-center z-10 pointer-events-none"
          >
            <h1 className="text-[clamp(4rem,8vw,10rem)] font-black tracking-tighter text-foreground leading-none text-center">
              ₹14,000+ <br/><span className="text-foreground-muted">Crores.</span>
            </h1>
            <p className="text-2xl text-foreground mt-8 font-medium">Available for industrial transition.</p>
            <p className="text-xl text-foreground-muted mt-2 font-medium">But scattered across dozens of schemes.</p>
            
            {/* Scattered Cards */}
            <div className="absolute inset-0 max-w-[90rem] mx-auto hidden md:block">
              {schemes.map((scheme, i) => {
                // Generate random-looking deterministic positions for scattering
                const left = `${15 + (i * 15)}%`
                const top = `${20 + (i % 2 === 0 ? 10 : 60)}%`
                const rotation = (i % 2 === 0 ? 1 : -1) * (10 + i * 2)
                
                return (
                  <motion.div
                    key={scheme.id}
                    className="absolute bg-surface border border-border p-4 rounded-lg shadow-xl w-64"
                    style={{ left, top, rotate: rotation, y: scatterY }}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Landmark className="w-4 h-4 text-accent" />
                      <span className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted">{scheme.ministry}</span>
                    </div>
                    <h3 className="text-lg font-bold text-foreground">{scheme.name}</h3>
                    <p className="text-sm font-mono text-accent mt-2">{scheme.amount}</p>
                  </motion.div>
                )
              })}
            </div>

            <div className="absolute bottom-12 flex flex-col items-center animate-bounce text-foreground-muted">
              <span className="text-[10px] font-bold uppercase tracking-widest mb-2">Scroll to discover</span>
              <ArrowDown className="w-5 h-5" />
            </div>
          </motion.div>

          {/* Phase 2: Urjiva Eligibility Engine */}
          <motion.div 
            style={{ opacity: engineOpacity, scale: engineScale }}
            className="absolute inset-0 flex flex-col items-center justify-center z-20 bg-background/90 backdrop-blur-sm"
          >
            <div className="max-w-4xl w-full px-6">
              <div className="text-center mb-16">
                <span className="w-16 h-16 rounded-2xl bg-surface border border-border flex items-center justify-center mx-auto mb-6 shadow-sm">
                  <Search className="w-8 h-8 text-accent" />
                </span>
                <h2 className="text-5xl font-black tracking-tight text-foreground mb-4">
                  Eligibility Computed.
                </h2>
                <p className="text-xl text-foreground-muted font-medium">
                  Urjiva's semantic engine automatically indexes policies against your factory's telemetry.
                </p>
              </div>

              {/* Financial Dashboard */}
              <div className="bg-surface border border-border rounded-2xl p-1 shadow-2xl relative overflow-hidden">
                {/* Scanning line animation */}
                <div className="absolute top-0 left-0 w-full h-1 bg-accent/50 blur-[2px] animate-scan" />
                
                <div className="bg-background rounded-xl p-8 border border-border/50">
                  <div className="grid md:grid-cols-2 gap-12">
                    <div>
                      <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-foreground-muted mb-8">Verified Matches</h3>
                      <div className="space-y-4">
                        {[
                          { name: "National Bioenergy Programme", status: "Eligible", amount: "₹1.2 Cr", badge: "bg-status-online/20 text-status-online border-status-online/30" },
                          { name: "PAT Scheme Cycle VII", status: "Conditional", amount: "ESCerts", badge: "bg-amber-500/20 text-amber-500 border-amber-500/30" },
                          { name: "State Capital Subsidy", status: "Under Review", amount: "₹2.5 Cr", badge: "bg-blue-500/20 text-blue-500 border-blue-500/30" }
                        ].map((match, i) => (
                          <div key={i} className="flex items-center justify-between p-4 border border-border rounded-lg bg-surface/50">
                            <div className="flex items-center gap-3">
                              <CheckCircle2 className={`w-5 h-5 ${match.status === 'Eligible' ? 'text-status-online' : 'text-foreground-muted'}`} />
                              <div>
                                <p className="text-sm font-bold text-foreground">{match.name}</p>
                                <span className={`inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest border ${match.badge}`}>
                                  {match.status}
                                </span>
                              </div>
                            </div>
                            <span className="font-mono font-bold text-foreground">{match.amount}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="flex flex-col justify-center border-l border-border pl-12">
                      <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-foreground-muted mb-2">Estimated Support</h3>
                      <p className="text-6xl font-black text-foreground mb-4 font-mono tracking-tighter">₹3.7<span className="text-3xl text-foreground-muted">Cr</span></p>
                      
                      <div className="space-y-3 mt-8">
                        <div className="flex justify-between text-sm font-medium">
                          <span className="text-foreground-muted">Total Estimated CAPEX</span>
                          <span className="font-mono">₹12.5 Cr</span>
                        </div>
                        <div className="flex justify-between text-sm font-medium text-accent">
                          <span>Total Grant Support</span>
                          <span className="font-mono">- ₹3.7 Cr</span>
                        </div>
                        <div className="h-px bg-border my-2" />
                        <div className="flex justify-between text-sm font-bold">
                          <span>Net Factory CAPEX</span>
                          <span className="font-mono">₹8.8 Cr</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

        </div>
      </div>
    </div>
  )
}
