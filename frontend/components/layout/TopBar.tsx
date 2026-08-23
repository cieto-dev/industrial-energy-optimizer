"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Menu, Home, ChevronRight, User, LogIn, LogOut, Sparkles } from "lucide-react"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { useSidebar } from "./SidebarContext"
import { AuthModal } from "@/components/auth/AuthModal"

export function TopBar() {
  const pathname = usePathname()
  const { toggle } = useSidebar()
  const [isAuthOpen, setIsAuthOpen] = useState(false)
  const [currentUser, setCurrentUser] = useState<{ name: string; email: string; role: string } | null>(null)

  useEffect(() => {
    try {
      const stored = localStorage.getItem("auth_user")
      if (stored) {
        setCurrentUser(JSON.parse(stored))
      }
    } catch (e) {
      console.error(e)
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem("auth_token")
    localStorage.removeItem("auth_user")
    setCurrentUser(null)
  }

  // Create breadcrumbs from pathname
  const paths = pathname.split('/').filter(Boolean)
  const breadcrumbs = paths.map((path, idx) => ({
    label: path === "gis" ? "GIS & Maps" : path === "scenario-playground" ? "Scenario Playground" : path.charAt(0).toUpperCase() + path.slice(1),
    href: '/' + paths.slice(0, idx + 1).join('/'),
    isLast: idx === paths.length - 1
  }))

  const isHome = pathname === "/"

  return (
    <>
      <header className="flex h-14 items-center justify-between border-b border-zinc-800 bg-zinc-950 px-4 flex-shrink-0 z-30">
        {/* Left side: hamburger + home + breadcrumbs */}
        <div className="flex items-center gap-3">
          {/* Hamburger — always visible, opens sidebar */}
          <button
            onClick={toggle}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors"
            aria-label="Toggle menu"
            id="sidebar-toggle-btn"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Home button — only show when NOT on home page */}
          {!isHome && (
            <Link
              href="/"
              className="flex h-9 items-center gap-1.5 rounded-lg px-3 text-sm font-medium text-zinc-400 hover:bg-zinc-800 hover:text-emerald-400 transition-colors"
              aria-label="Go to home"
            >
              <Home className="h-4 w-4" />
              <span className="hidden sm:inline">Home</span>
            </Link>
          )}

          {/* Divider */}
          {!isHome && <div className="h-4 w-px bg-zinc-700" />}

          {/* Breadcrumbs */}
          {breadcrumbs.length > 0 && (
            <nav className="flex items-center gap-1 text-sm">
              {breadcrumbs.map((crumb, idx) => (
                <div key={crumb.href} className="flex items-center gap-1">
                  {idx > 0 && <ChevronRight className="h-3.5 w-3.5 text-zinc-600" />}
                  <span className={crumb.isLast ? "font-semibold text-white" : "text-zinc-500"}>
                    {crumb.label}
                  </span>
                </div>
              ))}
            </nav>
          )}

          {isHome && (
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500 shadow-md shadow-emerald-500/30">
                <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-zinc-950" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M2 22 C6 18 14 10 22 2" />
                  <path d="M22 2 C22 14 12 22 2 22" fill="currentColor" fillOpacity="0.3"/>
                </svg>
              </div>
              <span className="text-sm font-bold text-white">CIETO</span>
              <span className="text-xs text-emerald-400 font-semibold tracking-widest uppercase">Energy Platform</span>
            </div>
          )}
        </div>

        {/* Right side: Auth, Status pill, Theme */}
        <div className="flex items-center gap-3">
          {/* User Auth state */}
          {currentUser ? (
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-bold text-white line-clamp-1">{currentUser.name}</span>
                <span className="text-[10px] text-emerald-400">{currentUser.role}</span>
              </div>
              <button
                onClick={handleLogout}
                title="Sign out"
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 border border-white/10 text-zinc-400 hover:text-red-400 transition"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsAuthOpen(true)}
              className="flex items-center gap-1.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-bold text-emerald-300 hover:bg-emerald-500/20 transition"
            >
              <LogIn className="h-3.5 w-3.5" />
              <span>Login</span>
            </button>
          )}

          {/* Live Status pill */}
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-zinc-700 bg-zinc-900 px-3 py-1">
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-medium text-zinc-400">Live</span>
          </div>

          <ThemeToggle />
        </div>
      </header>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onLoginSuccess={(user) => setCurrentUser(user)}
      />
    </>
  )
}
