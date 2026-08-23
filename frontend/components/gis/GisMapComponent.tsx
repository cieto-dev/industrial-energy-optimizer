"use client"

import React, { useState, useMemo } from "react"
import Link from "next/link"
import {
  MapPin,
  Layers,
  Flame,
  Zap,
  Factory,
  Search,
  Filter,
  Info,
  TrendingUp,
  IndianRupee,
  Compass,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize
} from "lucide-react"
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch"

export interface IndustrialCluster {
  id: string
  name: string
  state: string
  district: string
  industry: string
  unitsCount: number
  primaryFuel: string
  annualEnergySpendCr: number
  annualCo2Tonnes: number
  recommendedTech: string[]
  biomassSurplusMT: number
  solarDNI: number // kWh/m2/day
  discomTariff: number // INR/kWh
  lat: number
  lng: number
  keySubsidies: string[]
}

const CLUSTERS_DATA: IndustrialCluster[] = [
  {
    id: "tirupur-textiles",
    name: "Tirupur Textile & Dyeing Cluster",
    state: "Tamil Nadu",
    district: "Tiruppur",
    industry: "Textiles & Garments",
    unitsCount: 1400,
    primaryFuel: "Firewood & Coal Boilers",
    annualEnergySpendCr: 840,
    annualCo2Tonnes: 320000,
    recommendedTech: ["Biomass Gasifier", "Solar Thermal (CST)", "Effluent Heat Exchanger"],
    biomassSurplusMT: 450000,
    solarDNI: 5.6,
    discomTariff: 8.25,
    lat: 11.1085,
    lng: 77.3411,
    keySubsidies: ["TANGEDCO Green Open Access", "ADEETIE Energy Audit Grant"],
  },
  {
    id: "morbi-ceramics",
    name: "Morbi Ceramic & Tiles Hub",
    state: "Gujarat",
    district: "Morbi",
    industry: "Ceramics & Sanitaryware",
    unitsCount: 850,
    primaryFuel: "Natural Gas & Coal Gasifiers",
    annualEnergySpendCr: 3200,
    annualCo2Tonnes: 1250000,
    recommendedTech: ["Bio-CNG / CBG Injection", "Oxy-Fuel Combustion", "Kiln Waste Heat ORC"],
    biomassSurplusMT: 620000,
    solarDNI: 5.8,
    discomTariff: 7.90,
    lat: 22.8125,
    lng: 70.8384,
    keySubsidies: ["Gujarat Industrial Green Incentive", "SATAT Bio-CBG Offtake"],
  },
  {
    id: "surat-synthetic-textiles",
    name: "Surat Synthetic Textiles & Weaving",
    state: "Gujarat",
    district: "Surat",
    industry: "Textiles & Chemical Processing",
    unitsCount: 2200,
    primaryFuel: "Lignite & Imported Coal",
    annualEnergySpendCr: 1850,
    annualCo2Tonnes: 780000,
    recommendedTech: ["Biomass Briquette Boiler", "High-Temp Industrial Heat Pump", "Solar Rooftop"],
    biomassSurplusMT: 380000,
    solarDNI: 5.4,
    discomTariff: 7.75,
    lat: 21.1702,
    lng: 72.8311,
    keySubsidies: ["MSME Textile Modernization Scheme (TUF)", "Accelerated Depreciation"],
  },
  {
    id: "panipat-shoddy-yarn",
    name: "Panipat Handloom & Recycling Cluster",
    state: "Haryana",
    district: "Panipat",
    industry: "Textiles & Woolen Blankets",
    unitsCount: 950,
    primaryFuel: "Paddy Straw Pellets & Coal",
    annualEnergySpendCr: 620,
    annualCo2Tonnes: 290000,
    recommendedTech: ["Paddy Straw Biomass Boilers", "Condensate Heat Recovery"],
    biomassSurplusMT: 1200000,
    solarDNI: 5.1,
    discomTariff: 7.60,
    lat: 29.3909,
    lng: 76.9635,
    keySubsidies: ["Haryana Bioenergy Policy Incentive", "CAQM Clean Fuel Subsidy"],
  },
  {
    id: "ludhiana-forging",
    name: "Ludhiana Auto Components & Forging",
    state: "Punjab",
    district: "Ludhiana",
    industry: "Forging, Metal & Engineering",
    unitsCount: 1100,
    primaryFuel: "Furnace Oil & High Sulfur Diesel",
    annualEnergySpendCr: 1150,
    annualCo2Tonnes: 450000,
    recommendedTech: ["Induction Billet Heating (Electrification)", "Waste Heat Recuperators"],
    biomassSurplusMT: 1800000,
    solarDNI: 4.9,
    discomTariff: 6.85,
    lat: 30.9010,
    lng: 75.8573,
    keySubsidies: ["Punjab Industrial Power Subsidy", "BEE MSME Foundry Scheme"],
  },
  {
    id: "coimbatore-foundries",
    name: "Coimbatore Pumps & Foundry Cluster",
    state: "Tamil Nadu",
    district: "Coimbatore",
    industry: "Foundry & Precision Engineering",
    unitsCount: 700,
    primaryFuel: "Coke / Cupola Furnaces & Grid Power",
    annualEnergySpendCr: 540,
    annualCo2Tonnes: 210000,
    recommendedTech: ["Medium-Frequency Induction Furnaces", "Solar PV + Battery Storage"],
    biomassSurplusMT: 310000,
    solarDNI: 5.5,
    discomTariff: 8.35,
    lat: 11.0168,
    lng: 76.9558,
    keySubsidies: ["Tamil Nadu Energy Efficiency Capital Subsidy", "SIDBI 4E Financing"],
  },
  {
    id: "rajkot-casting",
    name: "Rajkot Diesel Engines & Engineering",
    state: "Gujarat",
    district: "Rajkot",
    industry: "Foundry & Machining",
    unitsCount: 620,
    primaryFuel: "Coke & Furnace Oil",
    annualEnergySpendCr: 480,
    annualCo2Tonnes: 195000,
    recommendedTech: ["Electric Induction Melting", "Solar Thermal Core Drying"],
    biomassSurplusMT: 410000,
    solarDNI: 5.7,
    discomTariff: 7.80,
    lat: 22.3039,
    lng: 70.8022,
    keySubsidies: ["Gujarat MSME Clean Tech Grant", "BEE Foundry Cluster Upgrade"],
  },
  {
    id: "baddi-pharma",
    name: "Baddi Pharmaceutical Cluster",
    state: "Himachal Pradesh",
    district: "Solan",
    industry: "Pharmaceuticals & Chemicals",
    unitsCount: 1200,
    primaryFuel: "Coal & Furnace Oil Boilers",
    annualEnergySpendCr: 1550,
    annualCo2Tonnes: 480000,
    recommendedTech: ["Biomass Briquette Boiler", "Electric Heat Pumps (Low Temp)", "Solar Rooftop PV"],
    biomassSurplusMT: 280000,
    solarDNI: 4.8,
    discomTariff: 5.95,
    lat: 30.9578,
    lng: 76.7914,
    keySubsidies: ["Himachal Industrial Investment Policy", "Central Capital Investment Subsidy"],
  },
  {
    id: "kanpur-leather",
    name: "Kanpur Leather & Tanning",
    state: "Uttar Pradesh",
    district: "Kanpur",
    industry: "Leather & Tanning",
    unitsCount: 850,
    primaryFuel: "Coal & Wood Fired Boilers",
    annualEnergySpendCr: 920,
    annualCo2Tonnes: 340000,
    recommendedTech: ["Biomass Gasification", "Effluent Heat Recovery", "Solar Thermal Drying"],
    biomassSurplusMT: 850000,
    solarDNI: 5.2,
    discomTariff: 7.30,
    lat: 26.4499,
    lng: 80.3319,
    keySubsidies: ["UP MSME Promotion Policy", "Leather Sector Modernization Scheme"],
  },
  {
    id: "kathua-industrial",
    name: "Kathua Industrial Estate",
    state: "Jammu & Kashmir",
    district: "Kathua",
    industry: "Cement, Textiles & Packaging",
    unitsCount: 450,
    primaryFuel: "Coal & Petcoke",
    annualEnergySpendCr: 780,
    annualCo2Tonnes: 260000,
    recommendedTech: ["Biomass Co-firing", "Waste Heat Recovery System (WHRS)"],
    biomassSurplusMT: 150000,
    solarDNI: 4.9,
    discomTariff: 6.50,
    lat: 32.3716,
    lng: 75.5233,
    keySubsidies: ["J&K New Industrial Policy (NCSS)", "Freight Subsidy Scheme"],
  },
]

export function GisMapComponent() {
  const [selectedCluster, setSelectedCluster] = useState<IndustrialCluster>(CLUSTERS_DATA[0])
  const [activeLayer, setActiveLayer] = useState<"clusters" | "biomass" | "discom">("clusters")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedStateFilter, setSelectedStateFilter] = useState("all")

  const filteredClusters = useMemo(() => {
    return CLUSTERS_DATA.filter((cluster) => {
      const matchQuery =
        cluster.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        cluster.district.toLowerCase().includes(searchQuery.toLowerCase()) ||
        cluster.industry.toLowerCase().includes(searchQuery.toLowerCase())
      const matchState = selectedStateFilter === "all" || cluster.state === selectedStateFilter
      return matchQuery && matchState
    })
  }, [searchQuery, selectedStateFilter])

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-xl border border-border/50 bg-card p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search cluster, district, or industry..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 w-72 rounded-md border border-border/50 bg-background pl-10 pr-4 text-xs text-foreground placeholder-muted-foreground focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-colors"
            />
          </div>

          <select
            value={selectedStateFilter}
            onChange={(e) => setSelectedStateFilter(e.target.value)}
            className="h-10 rounded-md border border-border/50 bg-background px-3 text-xs text-foreground focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-colors"
          >
            <option value="all">All States</option>
            <option value="Gujarat">Gujarat</option>
            <option value="Haryana">Haryana</option>
            <option value="Himachal Pradesh">Himachal Pradesh</option>
            <option value="Jammu & Kashmir">Jammu & Kashmir</option>
            <option value="Punjab">Punjab</option>
            <option value="Tamil Nadu">Tamil Nadu</option>
            <option value="Uttar Pradesh">Uttar Pradesh</option>
          </select>
        </div>

        {/* Layer Switcher */}
        <div className="flex items-center gap-1.5 rounded-md border border-border/50 bg-background p-1">
          <button
            onClick={() => setActiveLayer("clusters")}
            className={`flex items-center gap-1.5 rounded-sm px-3 py-1.5 text-xs font-semibold transition ${
              activeLayer === "clusters"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Factory className="h-3.5 w-3.5" />
            Industrial Clusters
          </button>
          <button
            onClick={() => setActiveLayer("biomass")}
            className={`flex items-center gap-1.5 rounded-sm px-3 py-1.5 text-xs font-semibold transition ${
              activeLayer === "biomass"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Flame className="h-3.5 w-3.5" />
            Biomass Atlas
          </button>
          <button
            onClick={() => setActiveLayer("discom")}
            className={`flex items-center gap-1.5 rounded-sm px-3 py-1.5 text-xs font-semibold transition ${
              activeLayer === "discom"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Zap className="h-3.5 w-3.5" />
            DISCOM Tariffs
          </button>
        </div>
      </div>

      {/* Main Interactive Map & Details Area */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Visual Map Canvas / Interactive District Pins */}
        <div className="lg:col-span-7 rounded-xl border border-border/50 bg-card p-6 shadow-sm relative overflow-hidden flex flex-col justify-between min-h-[460px]">
          {/* Map Title & Legend */}
          <div className="flex items-start justify-between z-10">
            <div>
              <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                <Compass className="h-5 w-5 text-primary" />
                India Industrial Decarbonization GIS Atlas
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                {activeLayer === "clusters" && "Select any industrial MSME cluster to inspect resource signals & pathways"}
                {activeLayer === "biomass" && "District-level agricultural residue surplus & agro-pellet supply density"}
                {activeLayer === "discom" && "State electricity grid tariffs & green power open access regulations"}
              </p>
            </div>
            <span className="text-[10px] uppercase font-bold tracking-widest text-primary bg-primary/10 border border-primary/20 px-2.5 py-1 rounded-full">
              {filteredClusters.length} Clusters Found
            </span>
          </div>

          {/* Interactive Geographic Representation */}
          <div className="relative my-6 py-6 px-4 bg-background rounded-xl border border-border/40 flex flex-col items-center justify-center">
            
            <TransformWrapper
              initialScale={1}
              minScale={0.5}
              maxScale={4}
              centerOnInit
            >
              {({ zoomIn, zoomOut, resetTransform }) => (
                <>
                  <div className="absolute top-2 right-2 z-50 flex flex-col gap-1.5 bg-card/80 backdrop-blur-md p-1 border border-border rounded-md shadow-sm">
                    <button onClick={() => zoomIn()} className="p-1 hover:bg-surface-muted rounded text-foreground transition-colors"><ZoomIn className="w-4 h-4" /></button>
                    <button onClick={() => zoomOut()} className="p-1 hover:bg-surface-muted rounded text-foreground transition-colors"><ZoomOut className="w-4 h-4" /></button>
                    <button onClick={() => resetTransform()} className="p-1 hover:bg-surface-muted rounded text-foreground transition-colors"><Maximize className="w-4 h-4" /></button>
                  </div>

                  <TransformComponent wrapperStyle={{ width: "100%", maxWidth: "500px", height: "300px" }}>
                    {/* Schematic India Map Canvas with District Points */}
                    <div className="w-[500px] h-[300px] relative border border-primary/10 rounded-2xl bg-gradient-to-b from-surface-muted to-background p-4 flex items-center justify-center">
                      {/* Map grid lines overlay */}
                      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] rounded-2xl" />

                      {/* District Cluster Markers positioned geographically */}
                      {filteredClusters.map((cluster) => {
                        // Map lat/lng roughly to coordinates inside the 500x300 canvas
                        // India bounds approx: Lat 8.4 to 35.5, Lng 68.7 to 97.25
                        const leftPct = ((cluster.lng - 68) / (85 - 68)) * 80 + 10
                        const topPct = ((34 - cluster.lat) / (34 - 8)) * 80 + 10
                        const isSelected = selectedCluster.id === cluster.id

                        return (
                          <button
                            key={cluster.id}
                            onClick={() => setSelectedCluster(cluster)}
                            style={{ left: `${Math.min(90, Math.max(10, leftPct))}%`, top: `${Math.min(90, Math.max(10, topPct))}%` }}
                            className={`absolute -translate-x-1/2 -translate-y-1/2 group flex items-center transition-all z-20 ${
                              isSelected ? "scale-125 z-30" : "hover:scale-110"
                            }`}
                          >
                            <div
                              className={`h-7 w-7 rounded-full flex items-center justify-center shadow-lg transition-all ${
                                isSelected
                                  ? "bg-primary text-primary-foreground ring-4 ring-primary/40"
                                  : "bg-surface-muted text-primary border border-primary/50 hover:bg-primary hover:text-primary-foreground"
                              }`}
                            >
                              <MapPin className="h-4 w-4" />
                            </div>
                            {/* Tooltip on hover */}
                            <div className="absolute left-8 top-1/2 -translate-y-1/2 hidden group-hover:flex whitespace-nowrap bg-card border border-border/50 px-2.5 py-1 rounded-md text-[10px] font-semibold text-foreground shadow-xl z-30">
                              {cluster.name}
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </TransformComponent>
                </>
              )}
            </TransformWrapper>

            {/* Map watermark / compass */}
            <div className="absolute right-4 bottom-4 text-[11px] text-muted-foreground font-mono pointer-events-none">
              GIS Layer • WGS84 Coords
            </div>
          </div>

          {/* Quick Stats Footer */}
          <div className="grid grid-cols-3 gap-3 pt-3 border-t border-border/40 text-center">
            <div className="bg-surface-muted p-2.5 rounded-xl border border-border/50">
              <p className="text-[10px] uppercase font-bold text-muted-foreground">Total MSME Units</p>
              <p className="text-sm font-bold text-foreground mt-0.5">8,820+ Registered</p>
            </div>
            <div className="bg-surface-muted p-2.5 rounded-xl border border-border/50">
              <p className="text-[10px] uppercase font-bold text-muted-foreground">Biomass Surplus</p>
              <p className="text-sm font-bold text-emerald-500 mt-0.5">5.17 Million MT</p>
            </div>
            <div className="bg-surface-muted p-2.5 rounded-xl border border-border/50">
              <p className="text-[10px] uppercase font-bold text-muted-foreground">CO₂ Abatement Potential</p>
              <p className="text-sm font-bold text-teal-500 mt-0.5">3.48 Mt CO₂/yr</p>
            </div>
          </div>
        </div>

        {/* Selected Cluster Detailed Inspection Drawer */}
        <div className="lg:col-span-5 rounded-xl border border-border/50 bg-card p-6 shadow-sm flex flex-col justify-between space-y-5">
          <div>
            <div className="flex items-start justify-between mb-2">
              <div className="flex flex-col gap-2">
                <div className="flex flex-wrap gap-2">
                  <span className="text-[10px] uppercase font-extrabold tracking-widest text-primary bg-primary/10 border border-primary/20 px-2.5 py-0.5 rounded-full">
                    {selectedCluster.state} • {selectedCluster.district}
                  </span>
                  <span className="text-[10px] uppercase font-extrabold tracking-widest text-muted-foreground bg-surface-muted border border-border/50 px-2.5 py-0.5 rounded-full">
                    {selectedCluster.unitsCount.toLocaleString()} MSME Units
                  </span>
                </div>
                <h4 className="text-lg font-bold text-foreground mt-2 leading-snug tracking-tight">
                  {selectedCluster.name}
                </h4>
                <p className="text-xs text-muted-foreground mt-0.5">{selectedCluster.industry}</p>
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-3 mt-4">
              <div className="rounded-xl border border-border/50 bg-surface-muted p-3">
                <p className="text-[10px] uppercase font-semibold text-muted-foreground">Current Primary Fuel</p>
                <p className="text-xs font-bold text-red-400 mt-0.5">{selectedCluster.primaryFuel}</p>
              </div>
              <div className="rounded-xl border border-border/50 bg-surface-muted p-3">
                <p className="text-[10px] uppercase font-semibold text-muted-foreground">Annual Energy Bill</p>
                <p className="text-xs font-bold text-foreground mt-0.5">₹{selectedCluster.annualEnergySpendCr} Cr / year</p>
              </div>
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3">
                <p className="text-[10px] uppercase font-semibold text-emerald-500">Biomass Availability</p>
                <p className="text-xs font-bold text-emerald-500 mt-0.5">
                  {(selectedCluster.biomassSurplusMT / 1000).toFixed(0)}k MT/yr surplus
                </p>
              </div>
              <div className="rounded-xl border border-sky-500/20 bg-sky-500/10 p-3">
                <p className="text-[10px] uppercase font-semibold text-sky-500">Solar DNI Resource</p>
                <p className="text-xs font-bold text-sky-500 mt-0.5">{selectedCluster.solarDNI} kWh/m²/day</p>
              </div>
            </div>

            {/* Recommended Transition Pathways */}
            <div className="mt-4">
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2">
                Recommended Decarbonization Pathways
              </p>
              <div className="space-y-1.5">
                {selectedCluster.recommendedTech.map((tech, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-foreground bg-surface-muted border border-border/50 rounded-lg px-3 py-2">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary flex-shrink-0" />
                    <span className="font-semibold text-foreground">{tech}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Applicable Subsidies & Policies */}
            <div className="mt-4">
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2">
                State & Central Scheme Incentives
              </p>
              <div className="space-y-1.5">
                {selectedCluster.keySubsidies.map((sub, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px] text-primary bg-primary/10 border border-primary/20 rounded-lg px-3 py-1.5">
                    <Info className="h-3.5 w-3.5 text-primary flex-shrink-0" />
                    <span>{sub}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-border/40 space-y-4">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">DISCOM Industrial Tariff:</span>
              <span className="font-bold text-foreground">₹{selectedCluster.discomTariff.toFixed(2)} / kWh</span>
            </div>
            <Link 
              href="/assessment" 
              className="flex w-full items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-bold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
            >
              <Factory className="h-4 w-4" />
              Assess Individual Factory in this Cluster
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
