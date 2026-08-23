"use client"

import React, { useState, useEffect } from "react"
import {
  FolderKanban,
  Plus,
  ArrowRight,
  TrendingDown,
  IndianRupee,
  Calendar,
  Layers,
  Trash2,
  ExternalLink,
  CheckCircle2,
  Factory,
} from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { projectService, SavedProject } from "@/services/projectService"

export default function ProjectsPage() {
  const [projects, setProjects] = useState<SavedProject[]>([])
  const router = useRouter()

  useEffect(() => {
    setProjects(projectService.getProjects())
  }, [])

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm("Are you sure you want to delete this assessment?")) {
      const updated = projectService.deleteProject(id)
      setProjects(updated)
    }
  }

  const handleOpenProject = (project: SavedProject) => {
    projectService.loadIntoSession(project)
    router.push("/dashboard")
  }

  const formatCurrency = (v: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v)

  return (
    <main className="min-h-full bg-zinc-950 p-4 text-white sm:p-6">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <section className="flex flex-col gap-4 border-b border-white/10 pb-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
              <FolderKanban className="h-3.5 w-3.5" />
              Multi-Assessment & Factory History
            </div>

            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Saved Factory Assessments
            </h1>

            <p className="mt-2 text-sm text-zinc-400 sm:text-base">
              Manage and track multiple decarbonization assessments across your industrial facilities, evaluate history, and load into dashboard.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/assessment"
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-zinc-950 shadow-lg shadow-emerald-500/25 transition hover:bg-emerald-400"
            >
              <Plus className="h-4 w-4" />
              New Factory Assessment
            </Link>
          </div>
        </section>

        {/* Project Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <div
              key={project.id}
              onClick={() => handleOpenProject(project)}
              className="group cursor-pointer rounded-2xl border border-white/10 bg-zinc-900/80 p-6 backdrop-blur-sm hover:border-emerald-500/40 hover:bg-zinc-900 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
                    {project.industry} • {project.state}
                  </span>
                  <button
                    onClick={(e) => handleDelete(project.id, e)}
                    className="text-zinc-600 hover:text-red-400 p-1 transition"
                    title="Delete assessment"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <h3 className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors line-clamp-1">
                  {project.name}
                </h3>
                <p className="text-xs text-zinc-400 mt-0.5">{project.district} District</p>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-white/5">
                  <div className="rounded-xl bg-zinc-950/60 p-2.5 border border-white/5">
                    <p className="text-[10px] uppercase font-semibold text-zinc-500">CAPEX</p>
                    <p className="text-xs font-bold text-white mt-0.5">{formatCurrency(project.capexInr)}</p>
                  </div>
                  <div className="rounded-xl bg-zinc-950/60 p-2.5 border border-white/5">
                    <p className="text-[10px] uppercase font-semibold text-zinc-500">CO₂ Cut</p>
                    <p className="text-xs font-bold text-emerald-400 mt-0.5">{project.co2ReductionPct}%</p>
                  </div>
                  <div className="rounded-xl bg-zinc-950/60 p-2.5 border border-white/5">
                    <p className="text-[10px] uppercase font-semibold text-zinc-500">Annual Savings</p>
                    <p className="text-xs font-bold text-emerald-300 mt-0.5">{formatCurrency(project.annualSavingsInr)}/yr</p>
                  </div>
                  <div className="rounded-xl bg-zinc-950/60 p-2.5 border border-white/5">
                    <p className="text-[10px] uppercase font-semibold text-zinc-500">Payback</p>
                    <p className="text-xs font-bold text-white mt-0.5">{project.paybackYears} Years</p>
                  </div>
                </div>

                {/* Tech Pills */}
                <div className="mt-4">
                  <p className="text-[10px] uppercase font-bold text-zinc-500 mb-1.5">Pathway</p>
                  <div className="flex flex-wrap gap-1.5">
                    {project.technologies.map((t, idx) => (
                      <span key={idx} className="text-[10px] font-medium bg-white/[0.04] text-zinc-300 rounded px-2 py-0.5">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Card Footer */}
              <div className="mt-6 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-zinc-400">
                <span>{new Date(project.updatedAt).toLocaleDateString()}</span>
                <span className="flex items-center gap-1 text-emerald-400 font-semibold group-hover:translate-x-0.5 transition-transform">
                  Open in Dashboard <ArrowRight className="h-3.5 w-3.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
