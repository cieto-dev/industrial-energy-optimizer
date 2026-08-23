"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Zap, Menu, X, ArrowRight } from "lucide-react"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { motion, AnimatePresence } from "framer-motion"

const navLinks = [
  { name: "Features", href: "/#features" },
  { name: "Technology", href: "/#technology" },
  { name: "Story", href: "/story" },
  { name: "Subsidies", href: "/#subsidies" },
  { name: "Knowledge Base", href: "/#knowledge-base" },
]

export function LandingNavbar() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const pathname = usePathname()

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${pathname === '/story' ? 'dark' : ''} ${
        isScrolled
          ? pathname === '/story'
            ? "bg-black/50 backdrop-blur-md border-b border-white/10 text-white"
            : "bg-background/70 backdrop-blur-md border-b border-border shadow-sm"
          : pathname === '/story' 
            ? "bg-transparent border-transparent text-white"
            : "bg-transparent border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/30 transition-transform group-hover:scale-105">
            <Zap size={22} className="fill-current" />
          </div>
          <div className="flex flex-col">
            <span className={`font-bold text-xl tracking-tight leading-none ${pathname === '/story' ? 'text-white' : 'text-foreground'}`}>
              CIETO
            </span>
            <span className="text-[10px] font-semibold text-primary uppercase tracking-widest mt-0.5">
              Energy Platform
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className={`text-sm font-medium transition-colors ${
                pathname === '/story' 
                  ? 'text-white/70 hover:text-white' 
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {link.name}
            </Link>
          ))}
        </nav>

        {/* Actions */}
        <div className="hidden md:flex items-center gap-4">
          <ThemeToggle />
          <Link
            href="/dashboard"
            className="group inline-flex h-10 items-center justify-center rounded-lg bg-primary px-6 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/90 hover:scale-105"
          >
            Dashboard
            <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>

        {/* Mobile Menu Toggle */}
        <div className="md:hidden flex items-center gap-4">
          <ThemeToggle />
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className={`p-2 ${pathname === '/story' ? 'text-white' : 'text-foreground'}`}
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-20 left-0 right-0 bg-background border-b border-border shadow-lg p-6 flex flex-col gap-4 md:hidden"
          >
            {navLinks.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-base font-medium text-foreground py-2 border-b border-border/50"
              >
                {link.name}
              </Link>
            ))}
            <Link
              href="/dashboard"
              onClick={() => setIsMobileMenuOpen(false)}
              className="mt-4 flex h-12 items-center justify-center rounded-lg bg-primary px-6 text-base font-semibold text-primary-foreground"
            >
              Dashboard
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
