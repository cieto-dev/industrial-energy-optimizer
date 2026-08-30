"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

export const MsmeEnergyLossSVG = () => {
  const [activeLoss, setActiveLoss] = useState<string | null>(null);

  const losses = [
    { id: "valve", x: 200, y: 150, title: "Uninsulated Valve", loss: "5-10%", desc: "Exposed metal radiating heat directly into the ambient environment." },
    { id: "leak", x: 350, y: 220, title: "Steam Leak", loss: "10-15%", desc: "High-pressure steam escaping from a degraded pipe joint." },
    { id: "flue", x: 450, y: 80, title: "High Flue Gas Temp", loss: "15-20%", desc: "Heat escaping up the chimney instead of being recovered." },
  ];

  return (
    <div className="w-full h-full bg-muted/5 relative flex items-center justify-center p-8 overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{
        backgroundImage: `linear-gradient(currentColor 1px, transparent 1px), linear-gradient(90deg, currentColor 1px, transparent 1px)`,
        backgroundSize: '2rem 2rem',
      }}></div>

      <svg width="600" height="400" viewBox="0 0 600 400" className="max-w-full drop-shadow-xl relative z-10">
        <defs>
          <linearGradient id="pipeGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="var(--muted-foreground)" stopOpacity="0.4" />
            <stop offset="50%" stopColor="var(--muted-foreground)" stopOpacity="0.1" />
            <stop offset="100%" stopColor="var(--muted-foreground)" stopOpacity="0.5" />
          </linearGradient>
        </defs>

        {/* Main Process Pipe */}
        <path d="M 50 150 L 350 150 L 350 250 L 550 250" fill="transparent" stroke="url(#pipeGrad)" strokeWidth="40" strokeLinejoin="round" />
        
        {/* Animated Steam Flow */}
        <motion.path 
           d="M 50 150 L 350 150 L 350 250 L 550 250" 
           fill="transparent" 
           stroke="#00ccff" strokeWidth="6" strokeDasharray="15 15" strokeLinejoin="round" opacity="0.5"
           animate={{ strokeDashoffset: [-30, 0] }}
           transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
        />

        {/* Boiler Unit (Source) */}
        <rect x="30" y="100" width="80" height="100" fill="currentColor" className="text-secondary" rx="5" />
        <rect x="40" y="50" width="20" height="50" fill="currentColor" className="text-muted" /> {/* Chimney */}
        
        {/* Flue Gas Heat Loss */}
        <motion.path 
           d="M 45 40 Q 50 20 60 0 M 55 40 Q 60 20 40 0" 
           stroke="#ff4400" strokeWidth="3" fill="transparent" opacity="0.6"
           animate={{ strokeDashoffset: [20, 0], opacity: [0, 0.6, 0] }}
           transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
        />
        {/* Flue gas hotspot */}
        <circle cx="50" cy="30" r="15" fill="transparent" stroke="#ff4400" strokeWidth="2" strokeDasharray="4 4" className="animate-spin-slow cursor-pointer" 
                onMouseEnter={() => setActiveLoss('flue')} onMouseLeave={() => setActiveLoss(null)} />

        {/* Valve */}
        <circle cx="200" cy="150" r="25" fill="currentColor" className="text-border" />
        <rect x="195" y="100" width="10" height="30" fill="currentColor" className="text-muted-foreground" />
        <ellipse cx="200" cy="100" rx="15" ry="5" fill="currentColor" className="text-foreground" />
        
        {/* Valve Heat Loss (Radiant) */}
        <motion.circle cx="200" cy="150" r="35" fill="transparent" stroke="#ffaa00" strokeWidth="2"
           animate={{ r: [30, 50], opacity: [0.6, 0] }}
           transition={{ repeat: Infinity, duration: 2, ease: "easeOut" }}
        />
        {/* Valve hotspot */}
        <circle cx="200" cy="150" r="30" fill="transparent" stroke="#ffaa00" strokeWidth="2" strokeDasharray="4 4" className="animate-spin-slow cursor-pointer" 
                onMouseEnter={() => setActiveLoss('valve')} onMouseLeave={() => setActiveLoss(null)} />

        {/* Steam Leak */}
        <path d="M 330 240 L 370 240 L 370 260 L 330 260 Z" fill="currentColor" className="text-border" />
        <motion.path 
           d="M 360 230 Q 380 200 400 230 Q 370 190 350 220" 
           stroke="#ffffff" strokeWidth="4" fill="transparent" opacity="0.8"
           animate={{ opacity: [0, 0.8, 0], d: [
             "M 360 230 Q 380 200 400 230 Q 370 190 350 220",
             "M 360 220 Q 390 180 410 210 Q 380 170 340 200"
           ] }}
           transition={{ repeat: Infinity, duration: 0.8, ease: "easeOut" }}
        />
        {/* Leak hotspot */}
        <circle cx="360" cy="220" r="20" fill="transparent" stroke="#00ccff" strokeWidth="2" strokeDasharray="4 4" className="animate-spin-slow cursor-pointer" 
                onMouseEnter={() => setActiveLoss('leak')} onMouseLeave={() => setActiveLoss(null)} />

      </svg>

      {/* Info Panel Overlay */}
      <AnimatePresence>
        {activeLoss && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="absolute top-8 right-8 w-64 bg-background/90 backdrop-blur border border-border p-5 shadow-xl"
          >
            <div className="flex items-center justify-between mb-2 border-b border-border pb-2">
              <h3 className="font-medium text-sm text-foreground">{losses.find(l => l.id === activeLoss)?.title}</h3>
              <span className="text-xs font-bold text-red-500 bg-red-500/10 px-2 py-0.5 rounded">
                {losses.find(l => l.id === activeLoss)?.loss} LOSS
              </span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {losses.find(l => l.id === activeLoss)?.desc}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
      
      {!activeLoss && (
        <div className="absolute top-8 right-8 w-64 bg-background/50 backdrop-blur border border-border p-4 text-xs text-muted-foreground text-center">
          Hover over the dashed hotspots to inspect common thermal energy losses.
        </div>
      )}
    </div>
  )
}
