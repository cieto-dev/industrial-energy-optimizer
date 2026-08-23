"use client"

import React, { useState, useMemo } from "react"
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
} from "lucide-react"

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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-2xl border border-white/10 bg-zinc-900/70 p-4 backdrop-blur-md">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              placeholder="Search cluster, district, or industry..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 w-72 rounded-xl border border-white/10 bg-zinc-950/80 pl-10 pr-4 text-xs text-white placeholder-zinc-500 focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <select
            value={selectedStateFilter}
            onChange={(e) => setSelectedStateFilter(e.target.value)}
            className="h-10 rounded-xl border border-white/10 bg-zinc-950/80 px-3 text-xs text-zinc-300 focus:border-emerald-500 focus:outline-none"
          >
            <option value="all">All States</option>
            <option value="Tamil Nadu">Tamil Nadu</option>
            <option value="Gujarat">Gujarat</option>
            <option value="Haryana">Haryana</option>
            <option value="Punjab">Punjab</option>
          </select>
        </div>

        {/* Layer Switcher */}
        <div className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-zinc-950/80 p-1">
          <button
            onClick={() => setActiveLayer("clusters")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
              activeLayer === "clusters"
                ? "bg-emerald-500 text-zinc-950 shadow-md shadow-emerald-500/30"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            <Factory className="h-3.5 w-3.5" />
            Industrial Clusters
          </button>
          <button
            onClick={() => setActiveLayer("biomass")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
              activeLayer === "biomass"
                ? "bg-emerald-500 text-zinc-950 shadow-md shadow-emerald-500/30"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            <Flame className="h-3.5 w-3.5" />
            Biomass Atlas
          </button>
          <button
            onClick={() => setActiveLayer("discom")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
              activeLayer === "discom"
                ? "bg-emerald-500 text-zinc-950 shadow-md shadow-emerald-500/30"
                : "text-zinc-400 hover:text-white"
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
        <div className="lg:col-span-7 rounded-2xl border border-white/10 bg-zinc-900/80 p-6 backdrop-blur-md relative overflow-hidden flex flex-col justify-between min-h-[460px]">
          {/* Map Title & Legend */}
          <div className="flex items-start justify-between z-10">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Compass className="h-5 w-5 text-emerald-400" />
                India Industrial Decarbonization GIS Atlas
              </h3>
              <p className="text-xs text-zinc-400 mt-0.5">
                {activeLayer === "clusters" && "Select any industrial MSME cluster to inspect resource signals & pathways"}
                {activeLayer === "biomass" && "District-level agricultural residue surplus & agro-pellet supply density"}
                {activeLayer === "discom" && "State electricity grid tariffs & green power open access regulations"}
              </p>
            </div>
            <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full">
              {filteredClusters.length} Clusters Found
            </span>
          </div>

          {/* Interactive Geographic Representation */}
          <div className="relative my-6 py-6 px-4 bg-zinc-950/60 rounded-xl border border-white/5 flex flex-col items-center justify-center">
            {/* Schematic India Map Canvas with District Points */}
            <div className="w-full max-w-[500px] h-[300px] relative border border-emerald-500/10 rounded-2xl bg-gradient-to-b from-zinc-900/80 to-zinc-950/90 p-4 flex items-center justify-center">
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
                          ? "bg-emerald-400 text-zinc-950 ring-4 ring-emerald-500/40"
                          : "bg-zinc-800 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500 hover:text-zinc-950"
                      }`}
                    >
                      <MapPin className="h-4 w-4" />
                    </div>
                    {/* Tooltip on hover */}
                    <div className="absolute left-8 top-1/2 -translate-y-1/2 hidden group-hover:flex whitespace-nowrap bg-zinc-900 border border-white/20 px-2.5 py-1 rounded-lg text-[10px] font-semibold text-white shadow-xl z-30">
                      {cluster.name}
                    </div>
                  </button>
                )
              })}

              {/* Map watermark / compass */}
              <div className="absolute right-4 bottom-4 text-[11px] text-zinc-600 font-mono">
                GIS Layer • WGS84 Coords
              </div>
            </div>
          </div>

          {/* Quick Stats Footer */}
          <div className="grid grid-cols-3 gap-3 pt-3 border-t border-white/10 text-center">
            <div className="bg-white/[0.02] p-2.5 rounded-xl border border-white/5">
              <p className="text-[10px] uppercase font-bold text-zinc-500">Total MSME Units</p>
              <p className="text-sm font-bold text-white mt-0.5">8,820+ Registered</p>
            </div>
            <div className="bg-white/[0.02] p-2.5 rounded-xl border border-white/5">
              <p className="text-[10px] uppercase font-bold text-zinc-500">Biomass Surplus</p>
              <p className="text-sm font-bold text-emerald-400 mt-0.5">5.17 Million MT</p>
            </div>
            <div className="bg-white/[0.02] p-2.5 rounded-xl border border-white/5">
              <p className="text-[10px] uppercase font-bold text-zinc-500">CO₂ Abatement Potential</p>
              <p className="text-sm font-bold text-teal-300 mt-0.5">3.48 Mt CO₂/yr</p>
            </div>
          </div>
        </div>

        {/* Selected Cluster Detailed Inspection Drawer */}
        <div className="lg:col-span-5 rounded-2xl border border-white/10 bg-zinc-900/80 p-6 backdrop-blur-md flex flex-col justify-between space-y-5">
          <div>
            <div className="flex items-start justify-between mb-2">
              <div>
                <span className="text-[10px] uppercase font-extrabold tracking-widest text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
                  {selectedCluster.state} • {selectedCluster.district}
                </span>
                <h4 className="text-lg font-bold text-white mt-2 leading-snug">
                  {selectedCluster.name}
                </h4>
                <p className="text-xs text-zinc-400 mt-0.5">{selectedCluster.industry}</p>
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-3 mt-4">
              <div className="rounded-xl border border-white/5 bg-zinc-950/70 p-3">
                <p className="text-[10px] uppercase font-semibold text-zinc-500">Current Primary Fuel</p>
                <p className="text-xs font-bold text-red-400 mt-0.5">{selectedCluster.primaryFuel}</p>
              </div>
              <div className="rounded-xl border border-white/5 bg-zinc-950/70 p-3">
                <p className="text-[10px] uppercase font-semibold text-zinc-500">Annual Energy Bill</p>
                <p className="text-xs font-bold text-white mt-0.5">₹{selectedCluster.annualEnergySpendCr} Cr / year</p>
              </div>
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-3">
                <p className="text-[10px] uppercase font-semibold text-emerald-400">Biomass Availability</p>
                <p className="text-xs font-bold text-emerald-300 mt-0.5">
                  {(selectedCluster.biomassSurplusMT / 1000).toFixed(0)}k MT/yr surplus
                </p>
              </div>
              <div className="rounded-xl border border-sky-500/20 bg-sky-950/20 p-3">
                <p className="text-[10px] uppercase font-semibold text-sky-400">Solar DNI Resource</p>
                <p className="text-xs font-bold text-sky-300 mt-0.5">{selectedCluster.solarDNI} kWh/m²/day</p>
              </div>
            </div>

            {/* Recommended Transition Pathways */}
            <div className="mt-4">
              <p className="text-xs font-bold text-white uppercase tracking-wider mb-2">
                Recommended Decarbonization Pathways
              </p>
              <div className="space-y-1.5">
                {selectedCluster.recommendedTech.map((tech, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-zinc-300 bg-white/[0.02] border border-white/5 rounded-lg px-3 py-2">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                    <span className="font-semibold text-white">{tech}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Applicable Subsidies & Policies */}
            <div className="mt-4">
              <p className="text-xs font-bold text-white uppercase tracking-wider mb-2">
                State & Central Scheme Incentives
              </p>
              <div className="space-y-1.5">
                {selectedCluster.keySubsidies.map((sub, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px] text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-1.5">
                    <Info className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                    <span>{sub}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-white/10">
            <div className="flex items-center justify-between text-xs">
              <span className="text-zinc-500">DISCOM Industrial Tariff:</span>
              <span className="font-bold text-white">₹{selectedCluster.discomTariff.toFixed(2)} / kWh</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
