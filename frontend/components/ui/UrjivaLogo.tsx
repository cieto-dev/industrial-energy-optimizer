import React from 'react';

export const UrjivaLogo = ({ className = "w-8 h-8" }: { className?: string }) => {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      {/* Dark Navy / CurrentColor (Fossil Baseline) */}
      <path d="M4 2H9V12L20 23H15L4 12V2Z" fill="currentColor" className="text-[#0F172A] dark:text-slate-100" />
      {/* Deep Emerald (Sustainable Upward Arrow) */}
      <path d="M17.5 2L20 4.5V12L9 23H4L15 12V4.5L17.5 2Z" fill="#059669" />
      {/* Electric Cyan (Intelligent Optimization Nexus) */}
      <path d="M12 15L14.5 17.5L12 20L9.5 17.5Z" fill="#06B6D4" />
    </svg>
  );
};
