import React from 'react';

export const UrjivaLogo = ({ className = "w-8 h-8" }: { className?: string }) => {
  return (
    <svg 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <g strokeWidth="16" strokeLinecap="round" strokeLinejoin="round">
        {/* Deep Emerald: The curved base of the 'U' representing continuous energy flow */}
        <path 
          d="M25 25 V 60 C 25 76.5 38.5 90 55 90 C 71.5 90 85 76.5 85 60 V 50" 
          stroke="#065F46" 
        />
        {/* Dark Navy / Light Slate: The structural backbone representing optimization */}
        <path 
          d="M25 60 V 25 L 55 55" 
          stroke="currentColor"
          className="text-[#0F172A] dark:text-slate-100"
        />
        {/* Electric Cyan: The upward arrow representing transition and growth */}
        <path 
          d="M85 50 V 25 L 55 55" 
          stroke="#06B6D4" 
        />
        <path 
          d="M65 25 H 85 V 45" 
          stroke="#06B6D4" 
        />
      </g>
    </svg>
  );
};
