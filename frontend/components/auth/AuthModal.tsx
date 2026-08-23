"use client"

import React, { useState } from "react"
import {
  X,
  User,
  Lock,
  Mail,
  CheckCircle2,
  ShieldAlert,
  Loader2,
  Sparkles,
  Building2,
} from "lucide-react"

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  onLoginSuccess: (user: { name: string; email: string; role: string }) => void
}

const DEMO_ACCOUNTS = [
  {
    name: "Ramesh Sundaram",
    email: "ramesh@textiles-coimbatore.in",
    role: "Plant Manager (Textile MSME)",
    factory: "TN Dyeing Unit #4",
  },
  {
    name: "Priya Patel",
    email: "priya@morbi-ceramics.com",
    role: "Sustainability Director (Ceramics)",
    factory: "Morbi Vitrified Tiles Hub",
  },
  {
    name: "Gurpreet Singh",
    email: "gurpreet@ludhiana-forging.in",
    role: "Energy Auditor (Metal & Forging)",
    factory: "Ludhiana Engineering Works",
  },
]

export function AuthModal({ isOpen, onClose, onLoginSuccess }: AuthModalProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [mode, setMode] = useState<"login" | "signup">("login")

  if (!isOpen) return null

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    // Simulate login or call backend auth
    setTimeout(() => {
      setIsLoading(false)
      const user = {
        name: email.split("@")[0] || "MSME Plant Owner",
        email: email || "user@cieto.in",
        role: "Industrial MSME Owner",
      }
      localStorage.setItem("auth_token", "demo_jwt_token_" + Date.now())
      localStorage.setItem("auth_user", JSON.stringify(user))
      onLoginSuccess(user)
      onClose()
    }, 600)
  }

  const handleDemoSelect = (demo: typeof DEMO_ACCOUNTS[0]) => {
    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
      const user = {
        name: demo.name,
        email: demo.email,
        role: demo.role,
      }
      localStorage.setItem("auth_token", "demo_jwt_token_" + Date.now())
      localStorage.setItem("auth_user", JSON.stringify(user))
      onLoginSuccess(user)
      onClose()
    }, 400)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-md rounded-2xl border border-white/10 bg-zinc-900 p-6 shadow-2xl">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1.5 text-zinc-400 hover:bg-white/10 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="mb-5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500 text-zinc-950 font-black text-xs">
              CI
            </div>
            <span className="text-sm font-bold tracking-tight text-white">CIETO Industrial Access</span>
          </div>
          <h3 className="text-xl font-bold text-white mt-3">
            {mode === "login" ? "Sign in to your account" : "Create an account"}
          </h3>
          <p className="text-xs text-zinc-400 mt-1">
            Access saved factory assessments, decarbonization benchmarks, and PDF reports.
          </p>
        </div>

        {/* Demo Accounts Quick Login */}
        <div className="mb-5 rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-3.5">
          <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 mb-2">
            <Sparkles className="h-3.5 w-3.5" />
            Quick Demo Login (One-Click)
          </div>
          <div className="space-y-1.5">
            {DEMO_ACCOUNTS.map((demo) => (
              <button
                key={demo.email}
                type="button"
                onClick={() => handleDemoSelect(demo)}
                className="w-full flex items-center justify-between rounded-lg bg-zinc-950/80 hover:bg-emerald-500/10 border border-white/5 hover:border-emerald-500/30 p-2 text-left transition-all group"
              >
                <div>
                  <p className="text-xs font-bold text-white group-hover:text-emerald-300">{demo.name}</p>
                  <p className="text-[10px] text-zinc-400">{demo.role}</p>
                </div>
                <span className="text-[10px] font-semibold text-emerald-400 opacity-0 group-hover:opacity-100 transition">
                  Login &rarr;
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Traditional Form */}
        <form onSubmit={handleLogin} className="space-y-3.5">
          <div>
            <label className="block text-xs font-semibold text-zinc-300 mb-1">Work Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="plant.manager@factory.in"
                className="h-10 w-full rounded-xl border border-white/10 bg-zinc-950/80 pl-9 pr-3 text-xs text-white placeholder-zinc-500 focus:border-emerald-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="h-10 w-full rounded-xl border border-white/10 bg-zinc-950/80 pl-9 pr-3 text-xs text-white placeholder-zinc-500 focus:border-emerald-500 focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 h-10 rounded-xl bg-emerald-500 text-zinc-950 font-bold text-xs shadow-lg shadow-emerald-500/25 hover:bg-emerald-400 transition-all disabled:opacity-50 mt-2"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : mode === "login" ? "Sign In" : "Register"}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => setMode(mode === "login" ? "signup" : "login")}
            className="text-xs text-zinc-400 hover:text-emerald-400 transition"
          >
            {mode === "login" ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  )
}
