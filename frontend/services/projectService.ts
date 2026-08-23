"use client"

export interface SavedProject {
  id: string
  name: string
  industry: string
  state: string
  district: string
  createdAt: string
  updatedAt: string
  capexInr: number
  annualSavingsInr: number
  co2ReductionPct: number
  paybackYears: number
  status: "Completed" | "Draft" | "Under Review"
  technologies: string[]
  profileData?: any
  optimizationResult?: any
}

const DEFAULT_PROJECTS: SavedProject[] = [
  {
    id: "proj-baddi-pharma-01",
    name: "Baddi Pharma Extractors Pvt. Ltd.",
    industry: "Pharmaceuticals & Chemicals",
    state: "Himachal Pradesh",
    district: "Solan",
    createdAt: "2026-08-10T10:30:00Z",
    updatedAt: "2026-08-20T14:15:00Z",
    capexInr: 12000000,
    annualSavingsInr: 4400000,
    co2ReductionPct: 62.5,
    paybackYears: 2.7,
    status: "Completed",
    technologies: ["Biomass Boiler", "Heat Pump (Air Source)"],
  },
  {
    id: "proj-kanpur-leather-02",
    name: "Kanpur Tanneries & Leather Works",
    industry: "Leather",
    state: "Uttar Pradesh",
    district: "Kanpur Nagar",
    createdAt: "2026-08-15T09:00:00Z",
    updatedAt: "2026-08-21T11:45:00Z",
    capexInr: 28000000,
    annualSavingsInr: 6200000,
    co2ReductionPct: 48.0,
    paybackYears: 4.5,
    status: "Completed",
    technologies: ["Solar Water Heater", "Waste Heat Recovery"],
  },
  {
    id: "proj-jammu-food-03",
    name: "Jammu Agro & Food Processing",
    industry: "Food & Beverage",
    state: "Jammu & Kashmir",
    district: "Jammu",
    createdAt: "2026-08-18T16:20:00Z",
    updatedAt: "2026-08-22T08:10:00Z",
    capexInr: 18500000,
    annualSavingsInr: 5100000,
    co2ReductionPct: 75.0,
    paybackYears: 3.6,
    status: "Completed",
    technologies: ["Electric Boiler", "Solar PV Rooftop"],
  },
  {
    id: "proj-tn-textile-04",
    name: "Coimbatore Textile Dyeing Unit #4",
    industry: "Textile",
    state: "Tamil Nadu",
    district: "Coimbatore",
    createdAt: "2026-08-10T10:30:00Z",
    updatedAt: "2026-08-20T14:15:00Z",
    capexInr: 32000000,
    annualSavingsInr: 10600000,
    co2ReductionPct: 68.5,
    paybackYears: 3.0,
    status: "Completed",
    technologies: ["Biomass Gasifier", "Solar Thermal (CST)", "Economizer"],
  },
]

const STORAGE_KEY = "cieto_saved_projects"

export const projectService = {
  getProjects(): SavedProject[] {
    if (typeof window === "undefined") return DEFAULT_PROJECTS
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed) && parsed.length > 0) {
          // Merge missing defaults into parsed
          let modified = false
          const currentIds = new Set(parsed.map((p: SavedProject) => p.id))
          
          DEFAULT_PROJECTS.forEach(defProj => {
            if (!currentIds.has(defProj.id)) {
              parsed.push(defProj)
              modified = true
            }
          })
          
          if (modified) {
            this.saveProjects(parsed)
          }
          
          return parsed
        }
      }
    } catch (e) {
      console.error("Failed to read saved projects from localStorage", e)
    }
    // Initialize default if not present
    this.saveProjects(DEFAULT_PROJECTS)
    return DEFAULT_PROJECTS
  },

  saveProjects(projects: SavedProject[]) {
    if (typeof window === "undefined") return
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(projects))
    } catch (e) {
      console.error("Failed to save projects to localStorage", e)
    }
  },

  addProject(project: Omit<SavedProject, "id" | "createdAt" | "updatedAt">): SavedProject {
    const existing = this.getProjects()
    const newProject: SavedProject = {
      ...project,
      id: `proj-${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    const updated = [newProject, ...existing]
    this.saveProjects(updated)
    return newProject
  },

  deleteProject(id: string): SavedProject[] {
    const existing = this.getProjects()
    const updated = existing.filter((p) => p.id !== id)
    this.saveProjects(updated)
    return updated
  },

  loadIntoSession(project: SavedProject) {
    if (typeof window === "undefined") return
    if (project.optimizationResult) {
      localStorage.setItem("last_optimization", JSON.stringify(project.optimizationResult))
    } else {
      // Create a compatible recommendation mock
      const mockResult = {
        recommended_scenario_id: project.id,
        factory_name: project.name,
        industry: project.industry.toLowerCase(),
        state: project.state,
        district: project.district,
      }
      localStorage.setItem("last_optimization", JSON.stringify(mockResult))
    }
  },
}
