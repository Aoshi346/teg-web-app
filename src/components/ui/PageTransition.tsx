"use client";

import React, { ReactNode } from 'react';

interface PageTransitionProps {
  children: ReactNode;
  className?: string;
}

export default function PageTransition({ children, className = '' }: PageTransitionProps) {
  // We removed animations to make transitions instant as requested.
  // The component is kept for structural consistency and future extensibility.
  return (
    <div className={`flex flex-col flex-1 min-h-0 ${className}`}>
      {children}
    </div>
  );
}

