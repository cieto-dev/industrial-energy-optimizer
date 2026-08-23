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
    id: "proj-tn-textile-01",
    name: "Coimbatore Textile Dyeing Unit #4",
    industry: "Textile",
    state: "Tamil Nadu",
    district: "Coimbatore",
    createdAt: "2026-08-10T10:30:00Z",
    updatedAt: "2026-08-20T14:15:00Z",
    capexInr: 12000000,
    annualSavingsInr: 4700000,
    co2ReductionPct: 68.5,
    paybackYears: 3.2,
    status: "Completed",
    technologies: ["Biomass Gasifier", "Solar Thermal (CST)", "Economizer"],
  },
  {
    id: "proj-morbi-ceramic-02",
    name: "Morbi Tiles Vitrified Kiln #2",
    industry: "Ceramics",
    state: "Gujarat",
    district: "Morbi",
    createdAt: "2026-08-15T09:00:00Z",
    updatedAt: "2026-08-21T11:45:00Z",
    capexInr: 28000000,
    annualSavingsInr: 9200000,
    co2ReductionPct: 54.0,
    paybackYears: 3.8,
    status: "Completed",
    technologies: ["Bio-CNG Burner Upgrade", "Waste Heat Recovery (ORC)"],
  },
  {
    id: "proj-ludhiana-forging-03",
    name: "Ludhiana Auto Forging Plant A",
    industry: "Forging & Metal",
    state: "Punjab",
    district: "Ludhiana",
    createdAt: "2026-08-18T16:20:00Z",
    updatedAt: "2026-08-22T08:10:00Z",
    capexInr: 18500000,
    annualSavingsInr: 6100000,
    co2ReductionPct: 72.0,
    paybackYears: 2.9,
    status: "Completed",
    technologies: ["Induction Billet Heating", "Solar PV Rooftop"],
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
        if (Array.isArray(parsed) && parsed.length > 0) return parsed
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
