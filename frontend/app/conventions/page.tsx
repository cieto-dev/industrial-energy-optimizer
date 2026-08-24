"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { LandingNavbar } from "@/components/layout/LandingNavbar"
import { Globe, MapPin, ChevronDown, CheckCircle2 } from "lucide-react"

const milestones = [
  { year: "1992", title: "UNFCCC", type: "global", desc: "The foundational global environmental treaty establishing the framework to combat dangerous human interference with the climate system." },
  { year: "1997", title: "Kyoto Protocol", type: "global", desc: "The first international treaty that operationalized the UNFCCC by committing industrialized countries to limit and reduce greenhouse gases." },
  { year: "2015", title: "Paris Agreement", type: "global", desc: "A legally binding international treaty on climate change adopted by 196 Parties, aiming to limit global warming to well below 2°C." },
  { year: "2015", title: "Sustainable Development Goals", type: "global", desc: "17 global goals designed to be a blueprint for a better and more sustainable future, heavily influencing ESG reporting." },
  { year: "2018", title: "ISO 50001", type: "global", desc: "The international standard specifying requirements for establishing, implementing, maintaining and improving an energy management system." },
  { year: "2021", title: "India Net Zero 2070", type: "indian", desc: "India's historic commitment at COP26 to achieve Net Zero emissions by 2070, triggering massive domestic policy shifts." },
  { year: "2022", title: "Energy Conservation (Amendment) Act", type: "indian", desc: "The legal foundation for the Indian Carbon Market, empowering the government to specify carbon credit trading schemes." },
  { year: "2023", title: "Indian Carbon Market (ICM)", type: "indian", desc: "The national framework for trading carbon credit certificates to incentivize emission reductions across industrial sectors." },
  { year: "2024", title: "National Green Hydrogen Mission", type: "indian", desc: "A comprehensive policy framework and financial outlay to make India a global hub for production, usage, and export of Green Hydrogen." },
]

export default function ConventionsPage() {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  return (
    <div className="min-h-screen bg-background font-sans">
      <LandingNavbar />
      
      <main className="pt-32 pb-24 max-w-4xl mx-auto px-6">
        <div className="text-center mb-24">
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent mb-6 block">
            Regulatory Intelligence
          </span>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight text-foreground leading-[1.1] mb-6">
            The Timeline of Decarbonization.
          </h1>
          <p className="text-xl text-foreground-muted font-medium max-w-2xl mx-auto">
            From the 1992 Earth Summit to the Indian Carbon Market, see how global treaties translate into direct operational mandates for your factory.
          </p>
        </div>

        <div className="relative">
          {/* Vertical Line */}
          <div className="absolute left-[39px] md:left-1/2 top-0 bottom-0 w-px bg-border -translate-x-1/2" />
          
          <div className="space-y-12">
            {milestones.map((milestone, i) => {
              const isGlobal = milestone.type === "global"
              const isExpanded = expandedId === i

              return (
                <div key={i} className={`relative flex items-start md:items-center ${isGlobal ? 'md:flex-row-reverse' : ''}`}>
                  {/* Timeline Dot */}
                  <div className="absolute left-[39px] md:left-1/2 -translate-x-1/2 w-12 h-12 rounded-full bg-background border-2 flex items-center justify-center z-10"
                       style={{ borderColor: isGlobal ? '#0077b6' : '#e85d04' }}>
                    {isGlobal ? <Globe className="w-5 h-5" style={{ color: '#0077b6' }} /> : <MapPin className="w-5 h-5" style={{ color: '#e85d04' }} />}
                  </div>
                  
                  {/* Content Container */}
                  <div className={`ml-24 md:ml-0 md:w-1/2 ${isGlobal ? 'md:pl-16' : 'md:pr-16 text-left md:text-right'}`}>
                    <div 
                      onClick={() => setExpandedId(isExpanded ? null : i)}
                      className={`group cursor-pointer p-6 rounded-2xl border transition-all duration-300 ${isExpanded ? 'bg-surface border-accent shadow-md' : 'bg-background border-border hover:border-foreground/20'}`}
                    >
                      <span className="text-[10px] font-mono font-bold tracking-widest text-foreground-muted mb-2 block">
                        {milestone.year}
                      </span>
                      <h3 className="text-2xl font-bold text-foreground mb-2 flex items-center gap-2 justify-start md:justify-end">
                        {milestone.title}
                        <ChevronDown className={`w-5 h-5 transition-transform duration-300 ${isExpanded ? 'rotate-180 text-accent' : 'text-border'}`} />
                      </h3>

                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="overflow-hidden text-left"
                          >
                            <p className="text-foreground-muted font-medium mt-4 pt-4 border-t border-border">
                              {milestone.desc}
                            </p>
                            
                            <div className="mt-6 bg-background rounded-lg p-4 border border-border">
                              <h4 className="text-[10px] font-bold uppercase tracking-widest text-foreground mb-2">How CIETO Incorporates This</h4>
                              <p className="text-sm text-foreground-muted font-medium flex items-start gap-2">
                                <CheckCircle2 className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                                Our optimizer mathematically binds these policy constraints into the objective function, ensuring that recommended pathways automatically comply with or financially benefit from this regulation.
                              </p>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </main>
    </div>
  )
}
