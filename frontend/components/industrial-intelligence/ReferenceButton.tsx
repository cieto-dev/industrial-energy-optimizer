"use client"

import React from "react"
import { BookOpen } from "lucide-react"
import { useCredibility } from "./CredibilityPanel"
import { Reference } from "../../data/industrial-intelligence"

interface ReferenceButtonProps {
  reference: Reference;
  label?: string;
  type?: 'source' | 'evidence' | 'methodology' | 'reference';
}

export const ReferenceButton: React.FC<ReferenceButtonProps> = ({ 
  reference, 
  label, 
  type = 'reference' 
}) => {
  const { openReference } = useCredibility();

  const getLabel = () => {
    if (label) return label;
    switch (type) {
      case 'source': return 'View Source';
      case 'evidence': return 'View Evidence';
      case 'methodology': return 'Methodology';
      default: return 'Reference';
    }
  };

  return (
    <button
      onClick={() => openReference(reference)}
      className="inline-flex items-center gap-1.5 px-2 py-1 text-[10px] font-medium tracking-wider uppercase bg-neutral-800/50 hover:bg-neutral-700 text-neutral-400 hover:text-white border border-neutral-700 rounded transition-colors ml-2 align-middle group"
      title={`Source: ${reference.organization}`}
    >
      <BookOpen size={10} className="group-hover:text-emerald-400 transition-colors" />
      {getLabel()}
    </button>
  );
};
