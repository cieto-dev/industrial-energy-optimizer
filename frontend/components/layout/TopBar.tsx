"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Menu, Home, ChevronRight, User, LogIn, LogOut, Sparkles, Zap } from "lucide-react"
import { ThemeToggle } from "@/components/theme/ThemeToggle"

import { AuthModal } from "@/components/auth/AuthModal"

export function TopBar() {
  const pathname = usePathname()

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
      <header className="flex h-14 items-center justify-between border-b border-border/50 bg-background/90 backdrop-blur-md px-4 flex-shrink-0 z-30 shadow-sm">
        {/* Left side: hamburger + home + breadcrumbs */}
        <div className="flex items-center gap-3">
          {/* Home button — only show when NOT on home page */}
          {!isHome && (
            <Link
              href="/"
              className="flex h-9 items-center gap-1.5 rounded-lg px-3 text-sm font-medium text-foreground-muted hover:bg-surface hover:text-accent transition-colors"
              aria-label="Go to home"
            >
              <Home className="h-4 w-4" />
              <span className="hidden sm:inline">Home</span>
            </Link>
          )}

          {/* Divider */}
          {!isHome && <div className="h-4 w-px bg-border" />}

          {/* Breadcrumbs */}
          {breadcrumbs.length > 0 && (
            <nav className="flex items-center gap-1 text-sm">
              {breadcrumbs.map((crumb, idx) => (
                <div key={crumb.href} className="flex items-center gap-1">
                  {idx > 0 && <ChevronRight className="h-3.5 w-3.5 text-foreground-muted opacity-50" />}
                  <span className={crumb.isLast ? "font-bold text-foreground" : "font-medium text-foreground-muted hover:text-foreground transition-colors cursor-default"}>
                    {crumb.label}
                  </span>
                </div>
              ))}
            </nav>
          )}

          {isHome && (
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-foreground shadow-md">
                <Zap className="h-3.5 w-3.5 text-background" />
              </div>
              <span className="text-sm font-bold text-foreground tracking-tight">CIETO</span>
            </div>
          )}
        </div>

        {/* Right side: Auth, Status pill, Theme */}
        <div className="flex items-center gap-3">
          {/* User Auth state */}
          {currentUser ? (
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-bold text-foreground line-clamp-1">{currentUser.name}</span>
                <span className="text-[10px] text-accent font-medium">{currentUser.role}</span>
              </div>
              <button
                onClick={handleLogout}
                title="Sign out"
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface border border-border text-foreground-muted hover:text-red-500 hover:border-red-200 hover:bg-red-50 transition-colors"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsAuthOpen(true)}
              className="flex items-center gap-1.5 rounded-xl border border-accent/20 bg-accent/5 px-3 py-1.5 text-xs font-bold text-accent hover:bg-accent/10 transition"
            >
              <LogIn className="h-3.5 w-3.5" />
              <span>Login</span>
            </button>
          )}

          {/* Live Status pill */}
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 shadow-sm">
            <div className="h-1.5 w-1.5 rounded-full bg-status-online shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse" />
            <span className="text-[10px] font-bold tracking-widest uppercase text-foreground-muted">Live</span>
          </div>

          <div className="pl-2 border-l border-border">
            <ThemeToggle />
          </div>
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
