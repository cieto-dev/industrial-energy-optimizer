export interface Reference {
  source: string;
  publication?: string;
  authors?: string;
  year?: string;
  organization: string;
  relevantFigure?: string;
  keyFindings?: string;
  directQuotation?: string;
  doi?: string;
  link?: string;
}

export interface IntelligenceModule {
  id: string;
  title: string;
  description: string;
  visualType: 'three' | 'svg' | 'lottie' | 'particle';
  tags: string[];
  references: Reference[];
  implemented: boolean;
}

export const industrialModules: IntelligenceModule[] = [
  {
    id: "factory-energy-flow",
    title: "How Energy Flows Inside a Factory",
    description: "An interactive visualization of thermal and electrical energy streams across a typical manufacturing facility.",
    visualType: "three",
    tags: ["Energy Balance", "Overview", "Thermodynamics"],
    implemented: true,
    references: [
      {
        source: "Industrial Energy Systems Assessment",
        organization: "International Energy Agency (IEA)",
        year: "2023",
        keyFindings: "Manufacturing accounts for 24% of global emissions, primarily driven by industrial heat requirements.",
        link: "https://www.iea.org/"
      }
    ]
  },
  {
    id: "boiler-internals",
    title: "What Actually Happens Inside a Boiler",
    description: "Explore the internal dynamics, heat transfer, and combustion chemistry inside an industrial boiler.",
    visualType: "svg",
    tags: ["Thermal", "Equipment", "Boilers"],
    implemented: true,
    references: [
      {
        source: "Boiler Efficiency Guide",
        organization: "Bureau of Energy Efficiency (BEE)",
        year: "2022",
        keyFindings: "Every 22°C reduction in flue gas temperature increases boiler efficiency by 1%.",
        link: "https://beeindia.gov.in/"
      }
    ]
  },
  {
    id: "coal-vs-biomass",
    title: "Coal vs Biomass vs Natural Gas vs Electricity",
    description: "Thermodynamic and economic comparison of industrial fuels and their real-world application contexts.",
    visualType: "particle",
    tags: ["Fuels", "Decarbonization", "Economics"],
    implemented: true,
    references: []
  },
  {
    id: "waste-heat-recovery",
    title: "How Waste Heat Recovery Works",
    description: "Tracing exhaust streams and capturing lost thermal energy through economizers and heat exchangers.",
    visualType: "three",
    tags: ["Efficiency", "Thermal"],
    implemented: true,
    references: []
  },
  {
    id: "msme-energy-loss",
    title: "Why MSMEs Lose Energy",
    description: "The compounding effect of uninsulated valves, steam leaks, and oversized equipment.",
    visualType: "svg",
    tags: ["MSME", "Audit"],
    implemented: true,
    references: []
  }
];
