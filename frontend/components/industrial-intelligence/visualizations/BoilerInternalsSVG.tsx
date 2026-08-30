"use client"

import React, { useState } from "react"
import { motion } from "framer-motion"

export const BoilerInternalsSVG = () => {
  const [hoveredPart, setHoveredPart] = useState<string | null>(null);

  const parts = {
    burner: { name: "Burner System", desc: "Combustion of fuel and air mixture", x: 100, y: 300, color: "#ff4400" },
    furnace: { name: "Furnace (Radiant Section)", desc: "Primary heat transfer via radiation", x: 250, y: 250, color: "#ffaa00" },
    tubes: { name: "Water Tubes", desc: "Water converting to high-pressure steam", x: 250, y: 150, color: "#00ccff" },
    drum: { name: "Steam Drum", desc: "Separates steam from boiling water", x: 250, y: 50, color: "#88ccff" },
    exhaust: { name: "Flue Gas Exhaust", desc: "Waste heat leaving the system", x: 450, y: 100, color: "#777777" },
  };

  return (
    <div className="w-full h-full bg-muted/10 relative flex items-center justify-center p-8 overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{
        backgroundImage: `linear-gradient(currentColor 1px, transparent 1px), linear-gradient(90deg, currentColor 1px, transparent 1px)`,
        backgroundSize: '2rem 2rem',
      }}></div>

      <svg width="600" height="400" viewBox="0 0 600 400" className="max-w-full drop-shadow-xl relative z-10">
        <defs>
          <linearGradient id="fireGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ff0000" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#ffaa00" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#ff8800" stopOpacity="0" />
          </linearGradient>
          
          <linearGradient id="waterGrad" x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="#0055ff" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#00ccff" stopOpacity="0.8" />
          </linearGradient>

          <pattern id="diagonalHatch" width="10" height="10" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
             <line x1="0" y1="0" x2="0" y2="10" stroke="currentColor" strokeWidth="1" className="text-muted-foreground opacity-20" />
          </pattern>
        </defs>

        {/* Boiler Outer Shell */}
        <path d="M 180 350 L 180 80 Q 180 40 250 40 Q 320 40 320 80 L 320 350 Z" 
              fill="url(#diagonalHatch)" 
              stroke="currentColor" strokeWidth="2" className="text-border" />
              
        {/* Furnace / Firebox */}
        <path d="M 100 320 L 280 320 L 280 180 L 180 180 Z" 
              fill="transparent" 
              stroke="currentColor" strokeWidth="1" className="text-border" 
              onMouseEnter={() => setHoveredPart('furnace')}
              onMouseLeave={() => setHoveredPart(null)}
              style={{ cursor: 'pointer' }}
        />
        
        {/* Animated Fire */}
        <motion.path 
           d="M 100 310 Q 150 280 200 310 Q 240 290 270 310 L 270 200 Q 230 250 180 200 Z" 
           fill="url(#fireGrad)"
           animate={{
             d: [
               "M 100 310 Q 150 280 200 310 Q 240 290 270 310 L 270 200 Q 230 250 180 200 Z",
               "M 100 310 Q 150 290 200 300 Q 240 300 270 310 L 270 210 Q 230 230 180 190 Z",
               "M 100 310 Q 150 280 200 310 Q 240 290 270 310 L 270 200 Q 230 250 180 200 Z"
             ]
           }}
           transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
        />
        
        {/* Burner Input */}
        <rect x="60" y="290" width="40" height="40" fill="currentColor" className="text-secondary" 
              onMouseEnter={() => setHoveredPart('burner')}
              onMouseLeave={() => setHoveredPart(null)}
              style={{ cursor: 'pointer' }}
        />
        <motion.line x1="40" y1="310" x2="80" y2="310" stroke="#ff4400" strokeWidth="4" strokeDasharray="4 4"
           animate={{ strokeDashoffset: [-10, 0] }}
           transition={{ repeat: Infinity, duration: 0.5, ease: "linear" }}
        />

        {/* Water Tubes (Riser) */}
        <rect x="290" y="90" width="20" height="250" fill="url(#waterGrad)" rx="5" 
              onMouseEnter={() => setHoveredPart('tubes')}
              onMouseLeave={() => setHoveredPart(null)}
              style={{ cursor: 'pointer' }}
        />
        {/* Water Tubes (Downcomer) */}
        <rect x="190" y="90" width="10" height="250" fill="#0055ff" opacity="0.6" rx="5" />
        
        {/* Steam Drum */}
        <ellipse cx="250" cy="80" rx="60" ry="30" fill="currentColor" className="text-secondary" stroke="currentColor" strokeWidth="2"
                 onMouseEnter={() => setHoveredPart('drum')}
                 onMouseLeave={() => setHoveredPart(null)}
                 style={{ stroke: 'var(--border)', cursor: 'pointer' }}
        />
        {/* Steam inside drum */}
        <path d="M 195 80 Q 250 50 305 80 L 305 80 A 60 30 0 0 1 195 80 Z" fill="#ffffff" opacity="0.4" />
        
        {/* Steam Output */}
        <motion.line x1="250" y1="50" x2="250" y2="10" stroke="#ffffff" strokeWidth="6" strokeDasharray="8 8" opacity="0.8"
           animate={{ strokeDashoffset: [16, 0] }}
           transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
        />
        
        {/* Flue Gas Path */}
        <path d="M 270 180 L 320 180 L 320 100 L 450 100" fill="transparent" stroke="#777" strokeWidth="30" opacity="0.3" 
              onMouseEnter={() => setHoveredPart('exhaust')}
              onMouseLeave={() => setHoveredPart(null)}
              style={{ cursor: 'pointer' }}
        />
        {/* Flue Gas Animation */}
        <motion.line x1="320" y1="100" x2="450" y2="100" stroke="#ff8800" strokeWidth="4" strokeDasharray="8 8" opacity="0.6"
           animate={{ strokeDashoffset: [16, 0] }}
           transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
        />

        {/* Hover Highlight Rings */}
        {hoveredPart && (
           <circle cx={parts[hoveredPart as keyof typeof parts].x} cy={parts[hoveredPart as keyof typeof parts].y} r="20" fill="transparent" stroke={parts[hoveredPart as keyof typeof parts].color} strokeWidth="2" strokeDasharray="4 4" className="animate-spin-slow" />
        )}
      </svg>

      {/* Info Panel Overlay */}
      <div className="absolute top-6 left-6 max-w-[250px]">
         {hoveredPart ? (
           <motion.div 
             initial={{ opacity: 0, y: 10 }}
             animate={{ opacity: 1, y: 0 }}
             className="bg-background/90 backdrop-blur border border-border p-4 shadow-xl"
           >
             <div className="flex items-center gap-2 mb-2">
               <div className="w-2 h-2 rounded-full" style={{ backgroundColor: parts[hoveredPart as keyof typeof parts].color }}></div>
               <h3 className="font-medium text-sm text-foreground">{parts[hoveredPart as keyof typeof parts].name}</h3>
             </div>
             <p className="text-xs text-muted-foreground leading-relaxed">
               {parts[hoveredPart as keyof typeof parts].desc}
             </p>
           </motion.div>
         ) : (
           <div className="bg-background/50 backdrop-blur border border-border p-4 text-xs text-muted-foreground">
             Hover over the components to explore the internal thermodynamics.
           </div>
         )}
      </div>
    </div>
  )
}
