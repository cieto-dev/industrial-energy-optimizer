"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Zap, Menu, X, Search, ArrowRight, Activity } from "lucide-react"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { UrjivaLogo } from "@/components/ui/UrjivaLogo"
import { motion, AnimatePresence } from "framer-motion"
import { useTheme } from "next-themes"

const navLinks = [
  { name: "Industrial Intelligence", href: "/industrial-intelligence" },
  { name: "Features", href: "/features" },
  { name: "Technology", href: "/technology" },
  { name: "Story", href: "/story" },
  { name: "Subsidies", href: "/subsidies" },
  { name: "Knowledge Base", href: "/knowledge-base" },
  { name: "Conventions", href: "/conventions" },
]

export function LandingNavbar() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isFullScreenMenuOpen, setIsFullScreenMenuOpen] = useState(false)
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(false)
  const [isBannerVisible, setIsBannerVisible] = useState(true)
  const [mounted, setMounted] = useState(false)
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  // Lock body scroll when menus are open
  useEffect(() => {
    if (isFullScreenMenuOpen || isRightSidebarOpen) {
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = "unset"
    }
    return () => {
      document.body.style.overflow = "unset"
    }
  }, [isFullScreenMenuOpen, isRightSidebarOpen])

  const isDarkHeader = isFullScreenMenuOpen || (!isScrolled && pathname === '/') || pathname === '/story';

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 flex flex-col ${
          isFullScreenMenuOpen
            ? "bg-[#181a1b] text-white border-transparent"
            : isRightSidebarOpen
            ? "bg-background text-foreground"
            : isScrolled
            ? "bg-background/20 backdrop-blur-md text-foreground shadow-[0_1px_2px_rgba(0,0,0,0.05)] border-b border-border/20"
            : "bg-transparent text-white"
        }`}
      >
        <AnimatePresence>
          {isBannerVisible && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className={`text-xs py-2.5 px-6 md:px-8 flex justify-between items-center overflow-hidden shrink-0 transition-colors ${
                isFullScreenMenuOpen
                  ? "bg-[#181a1b] text-white/90 border-b border-transparent"
                  : !isScrolled && !isRightSidebarOpen
                  ? "bg-white/10 backdrop-blur-sm text-white/90 border-b border-white/10"
                  : "bg-transparent text-foreground/90 border-b border-border/20"
              }`}
            >
              <p>
                Read CEO's <Link href="/story" className="underline underline-offset-2 opacity-90 hover:opacity-100 transition-opacity font-medium">Letter on Industrial Net-Zero</Link>
              </p>
              <button onClick={() => setIsBannerVisible(false)} className="opacity-60 hover:opacity-100 transition-opacity ml-4 shrink-0">
                <X size={14} strokeWidth={2} />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="w-full px-6 md:px-8 h-16 shrink-0 flex items-center justify-between border-b border-transparent">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 z-50 group">
            <UrjivaLogo className="w-6 h-6 opacity-90 group-hover:opacity-100 transition-opacity" />
            <span className="font-medium text-lg tracking-wide opacity-90 group-hover:opacity-100 transition-opacity">
              Urjiva
            </span>
          </Link>

          {/* Actions */}
          <div className="flex items-center gap-3 z-[60]">
            <button 
              onClick={() => { setIsRightSidebarOpen(true); setIsFullScreenMenuOpen(false); }}
              className={`hidden md:inline-flex h-9 items-center justify-center px-6 text-[13px] font-medium transition-colors border ${
                isFullScreenMenuOpen
                  ? "bg-transparent text-white hover:bg-white/10 border-white/20"
                  : !isScrolled && !isRightSidebarOpen
                  ? "bg-white text-black hover:bg-white/90 border-transparent"
                  : "bg-background text-foreground hover:bg-surface-muted border-border"
              }`}
            >
              Get Started
            </button>
            
            <div className={`flex items-center rounded-sm overflow-hidden h-9 border transition-colors ${
              isFullScreenMenuOpen
                ? "bg-transparent text-white border-white/20"
                : !isScrolled && !isRightSidebarOpen
                ? "bg-white text-black border-transparent"
                : "bg-background text-foreground border-border"
            }`}>
              <button className={`px-3 h-full flex items-center justify-center transition-colors border-r ${
                isFullScreenMenuOpen
                  ? "hover:bg-white/10 border-white/20"
                  : !isScrolled && !isRightSidebarOpen
                  ? "hover:bg-black/5 border-black/10"
                  : "hover:bg-surface-muted border-border"
              }`}>
                <Search size={16} strokeWidth={2} />
              </button>
              <button
                onClick={() => {
                  if (isRightSidebarOpen) {
                    setIsRightSidebarOpen(false);
                  } else {
                    setIsFullScreenMenuOpen(!isFullScreenMenuOpen);
                  }
                }}
                className={`px-3 h-full flex items-center justify-center transition-colors ${
                  isFullScreenMenuOpen
                    ? "hover:bg-white/10"
                    : !isScrolled && !isRightSidebarOpen
                    ? "hover:bg-black/5"
                    : "hover:bg-surface-muted"
                }`}
              >
                {isFullScreenMenuOpen || isRightSidebarOpen ? (
                  <X size={18} strokeWidth={2} />
                ) : (
                  <Menu size={18} strokeWidth={2} />
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Full Screen Menu */}
      <AnimatePresence>
        {isFullScreenMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-[#181a1b] text-white pt-24 px-6 md:px-12 overflow-y-auto"
          >
            <div className="max-w-[90rem] mx-auto grid grid-cols-1 md:grid-cols-12 gap-12 pb-24 border-t border-white/10 pt-12">
              
              {/* Column 1: Navigation Tabs */}
              <div className="md:col-span-3 border-r border-white/10 pr-8">
                <h3 className="text-[10px] font-semibold text-white/50 tracking-widest mb-8 uppercase">Navigation</h3>
                <div className="flex flex-col gap-6">
                  {navLinks.map((link) => (
                    <Link
                      key={link.name}
                      href={link.href}
                      onClick={() => setIsFullScreenMenuOpen(false)}
                      className="text-2xl font-normal text-white hover:text-white/80 transition-colors flex items-center gap-2 group w-fit"
                    >
                      <span className="opacity-0 group-hover:opacity-100 transition-opacity text-xl text-white/50">↳</span>
                      <span className="-ml-6 group-hover:ml-0 transition-all">{link.name}</span>
                    </Link>
                  ))}
                </div>
              </div>

              {/* Column 2: MCDA Explainer (Interactive) */}
              <div className="md:col-span-4 border-r border-white/10 pr-8">
                <div className="flex justify-between items-center mb-8">
                  <h3 className="text-[10px] font-semibold text-white/50 tracking-widest uppercase">Platform Intelligence</h3>
                  <span className="text-[10px] font-semibold text-white/30 tracking-widest uppercase hover:text-white transition-colors cursor-pointer flex items-center gap-1">Read Whitepaper <ArrowRight className="w-3 h-3" /></span>
                </div>
                
                <div className="group relative overflow-hidden rounded-lg bg-white/5 border border-white/10 transition-all hover:bg-white/10 hover:border-white/20 p-6 h-[400px] flex flex-col justify-end">
                  <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=800&auto=format&fit=crop')] bg-cover bg-center opacity-20 mix-blend-overlay group-hover:scale-105 group-hover:opacity-40 transition-all duration-700" />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#181a1b] via-[#181a1b]/80 to-transparent" />
                  
                  <div className="relative z-10">
                    <div className="w-10 h-10 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                      <Zap className="w-5 h-5 text-white" />
                    </div>
                    <h4 className="text-xl font-medium mb-3">Understanding MCDA Scores</h4>
                    <p className="text-sm text-white/70 leading-relaxed mb-4">
                      Our Multi-Criteria Decision Analysis (MCDA) engine ranks technologies by simultaneously weighing CAPEX, emissions impact, reliability, and thermodynamic feasibility. No single metric rules them all.
                    </p>
                    <button className="text-xs font-medium border-b border-white pb-0.5 hover:text-white/70 transition-colors">
                      Interactive Walkthrough
                    </button>
                  </div>
                </div>
              </div>

              {/* Column 3: Payback Explainer */}
              <div className="md:col-span-3 border-r border-white/10 pr-8">
                <div className="flex justify-between items-center mb-8">
                  <h3 className="text-[10px] font-semibold text-white/50 tracking-widest uppercase">Financial Models</h3>
                </div>

                <div className="group relative overflow-hidden rounded-lg bg-white/5 border border-white/10 transition-all hover:bg-white/10 hover:border-white/20 p-6 h-[400px] flex flex-col justify-end">
                  <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=800&auto=format&fit=crop')] bg-cover bg-center opacity-20 mix-blend-overlay group-hover:scale-105 group-hover:opacity-40 transition-all duration-700" />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#181a1b] via-[#181a1b]/80 to-transparent" />
                  
                  <div className="relative z-10">
                    <div className="w-10 h-10 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                      <Activity className="w-5 h-5 text-white" />
                    </div>
                    <h4 className="text-xl font-medium mb-3">Accelerating Payback</h4>
                    <p className="text-sm text-white/70 leading-relaxed mb-4">
                      Payback periods aren't static. Learn how leveraging state subsidies, carbon credits, and optimizing operational hours can cut your ROI timeframe by up to 40%.
                    </p>
                    <button className="text-xs font-medium border-b border-white pb-0.5 hover:text-white/70 transition-colors">
                      Explore Scenarios
                    </button>
                  </div>
                </div>
              </div>

              {/* Column 4: Quick Links */}
              <div className="md:col-span-2">
                <h3 className="text-[10px] font-semibold text-white/50 tracking-widest mb-8 uppercase">Quick Links</h3>
                <ul className="flex flex-col gap-4">
                  {[
                    "About Urjiva",
                    "Engineering Blog",
                    "Investor Relations",
                    "Letters from the CEO",
                    "Data Privacy",
                    "Security Center",
                    "Grid Partners",
                    "Learning Hub",
                    "Customer Success",
                    "Contact Us"
                  ].map((item) => (
                    <li key={item}>
                      <Link href="#" className="text-sm text-white/70 hover:text-white transition-colors">
                        {item}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>

            </div>

            {/* System Preferences / Theme Toggle footer inside the menu */}
            <div className="max-w-[90rem] mx-auto mt-12 pt-8 border-t border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div className="flex items-center gap-6">
                 <span className="text-[10px] font-semibold text-white/50 tracking-widest uppercase">System Interface Theme</span>
                 {mounted && (
                   <div className="flex bg-white/5 rounded-sm p-1 border border-white/10">
                     <button 
                       onClick={() => setTheme("dark")} 
                       className={`px-6 py-1.5 text-[11px] font-bold uppercase tracking-wider transition-colors ${theme === 'dark' ? 'bg-white text-black shadow-sm' : 'text-white/60 hover:text-white'}`}
                     >
                       Dark
                     </button>
                     <button 
                       onClick={() => setTheme("light")} 
                       className={`px-6 py-1.5 text-[11px] font-bold uppercase tracking-wider transition-colors ${theme === 'light' ? 'bg-white text-black shadow-sm' : 'text-white/60 hover:text-white'}`}
                     >
                       Light
                     </button>
                   </div>
                 )}
              </div>
              
              <div className="flex items-center gap-3">
                 <span className="flex items-center justify-center h-2 w-2 relative">
                   <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75 animate-ping"></span>
                   <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                 </span>
                 <span className="text-[10px] font-semibold text-white/50 tracking-widest uppercase">All Systems Nominal</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Right Sidebar - Get Started */}
      <AnimatePresence>
        {isRightSidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
              onClick={() => setIsRightSidebarOpen(false)}
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 bottom-0 z-50 w-full max-w-lg bg-white overflow-y-auto"
            >
              <div className="p-6 md:p-12 min-h-full flex flex-col pt-24">
                <button 
                  onClick={() => setIsRightSidebarOpen(false)}
                  className="absolute top-6 left-6 p-2 text-black/50 hover:text-black transition-colors"
                >
                  <X size={24} strokeWidth={1} />
                </button>
                
                <div className="mb-16"></div>
                
                <h2 className="text-3xl md:text-4xl font-medium text-black mb-4 leading-tight">
                  Demo Environment Login
                </h2>
                
                <p className="text-sm text-black/60 mb-12">
                  Access the Urjiva interactive platform. Use the demo credentials below to explore our features.
                </p>
                
                <form className="flex flex-col gap-8 flex-grow" onSubmit={(e) => { e.preventDefault(); window.location.href = '/dashboard'; }}>
                  {[
                    { label: 'Email Address', type: 'email' },
                    { label: 'Password', type: 'password' },
                  ].map((field) => (
                    <div key={field.label} className="relative group">
                      <label className="absolute left-0 top-0 text-[10px] font-semibold tracking-widest uppercase text-black/50 group-focus-within:text-black transition-colors">
                        {field.label}: <span className="text-red-500">*</span>
                      </label>
                      <input 
                        type={field.type} 
                        className="w-full bg-transparent border-b border-black/20 pt-6 pb-2 text-black focus:outline-none focus:border-black transition-colors"
                        required
                      />
                    </div>
                  ))}
                  
                  <div className="mt-2 p-5 bg-black/5 rounded-sm">
                    <p className="text-[10px] font-bold text-black/50 mb-2 uppercase tracking-widest">Demo Credentials</p>
                    <div className="flex flex-col gap-1">
                      <p className="text-sm text-black/80 font-medium">Email: <span className="font-mono bg-white px-1.5 py-0.5 rounded text-black border border-black/10 ml-2">demo@cieto.com</span></p>
                      <p className="text-sm text-black/80 font-medium">Password: <span className="font-mono bg-white px-1.5 py-0.5 rounded text-black border border-black/10 ml-2">demo123</span></p>
                    </div>
                  </div>
                  
                  <button type="submit" className="mt-8 bg-black text-white py-4 px-12 font-medium hover:bg-black/90 transition-colors w-fit self-end">
                    Login
                  </button>
                </form>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
