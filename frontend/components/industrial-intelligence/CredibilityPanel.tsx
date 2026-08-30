"use client"

import React, { createContext, useContext, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, ExternalLink, BookOpen, Download, Copy, CheckCircle } from "lucide-react"
import { Reference } from "../../data/industrial-intelligence"

interface CredibilityContextType {
  openReference: (ref: Reference) => void;
}

const CredibilityContext = createContext<CredibilityContextType | undefined>(undefined);

export const useCredibility = () => {
  const context = useContext(CredibilityContext);
  if (!context) throw new Error("useCredibility must be used within CredibilityProvider");
  return context;
};

export const CredibilityProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeRef, setActiveRef] = useState<Reference | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!activeRef) return;
    const citation = `${activeRef.authors || activeRef.organization} (${activeRef.year || 'n.d.'}). ${activeRef.source}. ${activeRef.publication || ''}`;
    navigator.clipboard.writeText(citation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <CredibilityContext.Provider value={{ openReference: setActiveRef }}>
      {children}
      
      {/* Side Panel */}
      <AnimatePresence>
        {activeRef && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm"
              onClick={() => setActiveRef(null)}
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 bottom-0 z-[70] w-full max-w-md bg-[#111] border-l border-neutral-800 shadow-2xl overflow-y-auto text-white flex flex-col"
            >
              <div className="p-6 border-b border-neutral-800 flex justify-between items-center bg-[#151515] sticky top-0 z-10">
                <div className="flex items-center gap-2 text-neutral-400">
                  <BookOpen size={16} />
                  <span className="text-xs uppercase tracking-widest font-semibold">Credibility Layer</span>
                </div>
                <button 
                  onClick={() => setActiveRef(null)}
                  className="text-neutral-500 hover:text-white transition-colors p-1"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="p-8 flex-grow">
                <div className="inline-block px-2 py-1 bg-neutral-800 text-neutral-300 text-[10px] uppercase tracking-widest rounded mb-6">
                  {activeRef.organization}
                </div>
                
                <h2 className="text-2xl font-medium mb-6 leading-snug">
                  {activeRef.source}
                </h2>

                <div className="space-y-6">
                  {activeRef.authors && (
                    <div>
                      <p className="text-[10px] text-neutral-500 uppercase tracking-wider mb-1">Authors</p>
                      <p className="text-sm text-neutral-300">{activeRef.authors}</p>
                    </div>
                  )}

                  {activeRef.year && (
                    <div>
                      <p className="text-[10px] text-neutral-500 uppercase tracking-wider mb-1">Year of Publication</p>
                      <p className="text-sm text-neutral-300">{activeRef.year}</p>
                    </div>
                  )}

                  {activeRef.keyFindings && (
                    <div className="bg-neutral-800/50 p-4 rounded-sm border border-neutral-700/50 mt-8">
                      <p className="text-[10px] text-emerald-500 uppercase tracking-wider mb-2 font-bold">Key Findings</p>
                      <p className="text-sm text-neutral-300 leading-relaxed italic">
                        "{activeRef.keyFindings}"
                      </p>
                    </div>
                  )}
                  
                  {activeRef.doi && (
                    <div>
                      <p className="text-[10px] text-neutral-500 uppercase tracking-wider mb-1">DOI</p>
                      <p className="text-sm text-blue-400 hover:underline cursor-pointer">{activeRef.doi}</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-6 border-t border-neutral-800 bg-[#151515] flex gap-3">
                {activeRef.link && (
                  <a 
                    href={activeRef.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex-1 flex items-center justify-center gap-2 bg-white text-black py-3 px-4 text-sm font-medium hover:bg-neutral-200 transition-colors rounded-sm"
                  >
                    View Original <ExternalLink size={14} />
                  </a>
                )}
                <button 
                  onClick={handleCopy}
                  className="flex items-center justify-center gap-2 border border-neutral-700 text-white py-3 px-4 text-sm font-medium hover:bg-neutral-800 transition-colors rounded-sm w-32"
                >
                  {copied ? <><CheckCircle size={14} className="text-emerald-500" /> Copied</> : <><Copy size={14} /> Citation</>}
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </CredibilityContext.Provider>
  );
};
