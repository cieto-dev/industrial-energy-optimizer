"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { industrialModules } from "../../data/industrial-intelligence"
import { ArrowRight, Hexagon, Zap, Thermometer, Factory, Layers } from "lucide-react"

export default function IndustrialIntelligencePage() {
  return (
    <div className="min-h-screen bg-background text-foreground pt-24 pb-32">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-b from-background via-background to-background"></div>
        {/* Abstract grid */}
        <div className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]" style={{
            backgroundImage: `linear-gradient(currentColor 1px, transparent 1px), linear-gradient(90deg, currentColor 1px, transparent 1px)`,
            backgroundSize: '4rem 4rem',
            transform: 'perspective(500px) rotateX(60deg) translateY(-100px) translateZ(-200px)',
          }}></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 md:px-12">
        {/* Header Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="max-w-4xl mb-24 pt-12"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="h-[1px] w-8 bg-emerald-500"></div>
            <span className="uppercase tracking-[0.2em] text-[10px] font-bold text-emerald-500">Interactive Knowledge System</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-medium tracking-tight mb-8 leading-[1.1] text-foreground">
            Industrial <br /> Intelligence
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground font-light max-w-2xl leading-relaxed">
            An immersive exploration of thermodynamic realities, energy flows, and operational truths. We don't just calculate emissions—we engineer decarbonization.
          </p>
        </motion.div>

        {/* Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {industrialModules.map((mod, index) => (
            <motion.div
              key={mod.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Link href={`/industrial-intelligence/${mod.id}`}>
                <div className="group relative h-full bg-card/50 backdrop-blur-md border border-border/50 p-8 hover:bg-accent/50 hover:border-border transition-all duration-500 flex flex-col justify-between overflow-hidden shadow-sm hover:shadow-md">
                  
                  {/* Hover gradient effect */}
                  <div className="absolute inset-0 bg-gradient-to-br from-foreground/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

                  <div className="relative z-10 mb-12">
                    <div className="flex justify-between items-start mb-6">
                      <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground group-hover:text-foreground group-hover:bg-secondary/80 transition-all duration-300">
                        {mod.visualType === 'three' ? <Hexagon size={18} /> : 
                         mod.visualType === 'svg' ? <Layers size={18} /> : 
                         mod.visualType === 'particle' ? <Zap size={18} /> : <Factory size={18} />}
                      </div>
                      {!mod.implemented && (
                        <span className="text-[9px] uppercase tracking-wider bg-secondary text-muted-foreground px-2 py-1 rounded">Coming Soon</span>
                      )}
                    </div>
                    
                    <h3 className="text-2xl font-medium mb-4 group-hover:text-emerald-500 transition-colors duration-300">
                      {mod.title}
                    </h3>
                    <p className="text-sm text-muted-foreground leading-relaxed font-light transition-colors duration-300">
                      {mod.description}
                    </p>
                  </div>
                  
                  <div className="relative z-10 flex items-center justify-between border-t border-border/50 pt-6 transition-colors duration-300">
                    <div className="flex gap-2">
                      {mod.tags.slice(0, 2).map(tag => (
                        <span key={tag} className="text-[10px] text-muted-foreground uppercase tracking-wider">{tag}</span>
                      ))}
                    </div>
                    <ArrowRight className="text-muted-foreground group-hover:text-foreground transition-colors duration-300 transform group-hover:translate-x-1" size={16} />
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
