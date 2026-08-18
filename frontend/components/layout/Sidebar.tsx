"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/utils"
import { LayoutDashboard, FileText, FileBarChart, ChevronRight } from "lucide-react"

const routes = [
  {
    label: "Input Assessment",
    icon: FileText,
    href: "/assessment",
    desc: "Profile your factory",
  },
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    href: "/dashboard",
    desc: "View recommendations",
  },
  {
    label: "Reports",
    icon: FileBarChart,
    href: "/reports",
    desc: "Export analysis",
  }
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="relative flex h-full w-72 flex-col overflow-hidden border-r border-zinc-800">
      {/* Background image with overlay */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: "url('/assessment_bg.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />
      {/* Dark overlay gradient */}
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-zinc-950/95 via-zinc-950/85 to-zinc-950/95" />

      {/* Content */}
      <div className="relative z-10 flex flex-col h-full py-6">

        {/* Brand logo area */}
        <div className="px-5 mb-8">
          <div className="flex items-center gap-3 mb-1">
            {/* Custom SVG leaf-circuit logo instead of Zap icon */}
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500 shadow-lg shadow-emerald-500/30 flex-shrink-0">
              <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5 text-zinc-950" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 22 C2 22 8 16 12 12 C16 8 22 2 22 2" />
                <path d="M22 2 C22 2 22 10 18 14 C14 18 6 22 2 22" />
                <circle cx="12" cy="12" r="2" fill="currentColor" stroke="none"/>
              </svg>
            </div>
            <div>
              <p className="text-sm font-black text-white leading-none tracking-tight">CIETO</p>
              <p className="text-[10px] text-emerald-400 font-semibold tracking-widest uppercase">Energy Platform</p>
            </div>
          </div>
        </div>

        {/* Nav label */}
        <p className="px-5 mb-3 text-[10px] font-bold uppercase tracking-widest text-zinc-500">Navigation</p>

        {/* Nav routes */}
        <div className="flex flex-col gap-1 px-3">
          {routes.map((route) => {
            const isActive = pathname === route.href
            return (
              <Link
                key={route.href}
                href={route.href}
                className={cn(
                  "group relative flex w-full items-center justify-between rounded-xl px-4 py-3.5 transition-all duration-300",
                  isActive
                    ? "bg-emerald-500 text-zinc-950 shadow-lg shadow-emerald-500/25"
                    : "text-zinc-400 hover:bg-white/5 hover:text-white"
                )}
              >
                <div className="flex items-center gap-3">
                  <route.icon className={cn("h-[18px] w-[18px] flex-shrink-0", isActive ? "text-zinc-950" : "text-zinc-500 group-hover:text-emerald-400 transition-colors")} />
                  <div>
                    <p className={cn("text-sm font-semibold leading-tight", isActive ? "text-zinc-950" : "text-white")}>{route.label}</p>
                    <p className={cn("text-[11px] leading-tight mt-0.5", isActive ? "text-zinc-700" : "text-zinc-500")}>{route.desc}</p>
                  </div>
                </div>
                {isActive && <ChevronRight className="h-4 w-4 text-zinc-950 flex-shrink-0" />}
              </Link>
            )
          })}
        </div>

        {/* Divider with mission statement */}
        <div className="mt-auto mx-4 pt-6 border-t border-zinc-800/60">
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 backdrop-blur-sm p-4">
            {/* Custom leaf SVG instead of Zap */}
            <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5 text-emerald-400 mb-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 22 C6 18 14 10 22 2" />
              <path d="M22 2 C22 14 12 22 2 22" fill="hsl(152,76%,46%)" fillOpacity="0.2"/>
            </svg>
            <p className="text-xs font-bold text-white mb-1">Mission Zero</p>
            <p className="text-[11px] text-zinc-400 leading-relaxed">Decarbonizing Indian industry, one MSME at a time.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
