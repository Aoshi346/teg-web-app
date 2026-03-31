"use client";

import React from 'react';

interface LoginLoadingProps {
  visible: boolean;
  message?: string;
}

export default function LoginLoading({ visible, message = 'Cargando...' }: LoginLoadingProps) {
  if (!visible) return null;

  const ekgKeyframes = `
    @keyframes ekg-pulse {
      0% {
        stroke-dashoffset: 300;
      }
      50% {
        stroke-dashoffset: 0;
      }
      100% {
        stroke-dashoffset: -300;
      }
    }
  `;

  return (
    <>
      <style>{ekgKeyframes}</style>
      <div role="status" aria-live="polite" className="fixed inset-0 z-60 flex flex-col items-center justify-center bg-black/60 backdrop-blur-md">
        <svg width="120" height="80" viewBox="0 0 120 80" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path 
            d="M0 40 H30 L40 25 L50 55 L60 35 L70 45 L80 40 H120" 
            stroke="#34d399" // emerald-400
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="150"
            style={{ animation: 'ekg-pulse 2s ease-in-out infinite' }}
          />
        </svg>
        <div className="text-white text-lg mt-4 font-light tracking-wider">{message}</div>
      </div>
    </>
  );
}
