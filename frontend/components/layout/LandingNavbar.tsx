"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Zap, Menu, X, Search, ArrowRight } from "lucide-react"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { motion, AnimatePresence } from "framer-motion"

const navLinks = [
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
  const pathname = usePathname()

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
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b ${
          isFullScreenMenuOpen
            ? "bg-[#181a1b] border-transparent text-white"
            : pathname === '/story'
            ? "bg-black/40 backdrop-blur-md border-white/10 text-white"
            : !isScrolled && pathname === '/'
            ? "bg-black/20 backdrop-blur-lg border-white/10 text-white"
            : "bg-background/90 backdrop-blur-md border-border/50 text-foreground shadow-sm"
        }`}
      >
        <div className="w-full px-6 md:px-12 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group z-[60]" onClick={() => { setIsFullScreenMenuOpen(false); setIsRightSidebarOpen(false); }}>
            <Zap size={22} className={isDarkHeader ? "text-white" : "text-foreground"} />
            <span className={`font-medium text-xl tracking-tight ${isDarkHeader ? 'text-white' : 'text-foreground'}`}>
              CIETO
            </span>
          </Link>

          {/* Actions */}
          <div className="flex items-center gap-4 z-[60]">
            <button 
              onClick={() => { setIsRightSidebarOpen(true); setIsFullScreenMenuOpen(false); }}
              className={`hidden md:inline-flex h-10 items-center justify-center border ${
                isDarkHeader 
                  ? 'border-white/70 text-white hover:bg-white/10' 
                  : 'border-black/20 text-black hover:bg-black/5'
              } px-6 text-sm font-medium transition-colors rounded-sm`}
            >
              Get Started
            </button>
            
            <div className={`flex items-center border ${isDarkHeader ? 'border-white/70' : 'border-black/20'} rounded-sm`}>
              <button className={`p-2.5 border-r ${isDarkHeader ? 'border-white/70 text-white hover:bg-white/10' : 'border-black/20 text-black hover:bg-black/5'} transition-colors`}>
                <Search size={18} strokeWidth={1.5} />
              </button>
              <button
                onClick={() => {
                  if (isRightSidebarOpen) {
                    setIsRightSidebarOpen(false);
                  } else {
                    setIsFullScreenMenuOpen(!isFullScreenMenuOpen);
                  }
                }}
                className={`p-2.5 ${isDarkHeader ? 'text-white hover:bg-white/10' : 'text-black hover:bg-black/5'} transition-colors ${isFullScreenMenuOpen || isRightSidebarOpen ? 'bg-white text-black hover:bg-white' : ''}`}
              >
                {isFullScreenMenuOpen || isRightSidebarOpen ? (
                  <X size={18} strokeWidth={1.5} className={isFullScreenMenuOpen || isRightSidebarOpen ? 'text-black' : ''} />
                ) : (
                  <Menu size={18} strokeWidth={1.5} />
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
            <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-12 pb-24">
              {/* Navigation Tabs */}
              <div className="md:col-span-12">
                <h3 className="text-xs font-semibold text-white/50 tracking-widest mb-6 uppercase">Navigation</h3>
                <div className="flex flex-col gap-4">
                  {navLinks.map((link) => (
                    <Link
                      key={link.name}
                      href={link.href}
                      onClick={() => setIsFullScreenMenuOpen(false)}
                      className="text-3xl md:text-4xl font-normal text-white hover:text-white/80 transition-colors flex items-center gap-2 group w-fit"
                    >
                      <span className="opacity-0 group-hover:opacity-100 transition-opacity text-xl">↳</span>
                      <span className="-ml-6 group-hover:ml-0 transition-all">{link.name}</span>
                    </Link>
                  ))}
                </div>
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
                  Access the CIETO interactive platform. Use the demo credentials below to explore our features.
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
