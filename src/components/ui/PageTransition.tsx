"use client";

import React, { useEffect, useRef, ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { gsap } from 'gsap';

interface PageTransitionProps {
  children: ReactNode;
  className?: string;
}

export default function PageTransition({ children, className = '' }: PageTransitionProps) {
  const pathname = usePathname();
  const contentRef = useRef<HTMLDivElement>(null);
  const prevPathnameRef = useRef<string | null>(null);
  const isInitialMountRef = useRef(true);

  useEffect(() => {
    // Skip animation on initial mount
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      prevPathnameRef.current = pathname;
      return;
    }

    const content = contentRef.current;
    if (!content) return;

    // Only animate if pathname actually changed
    if (prevPathnameRef.current && prevPathnameRef.current !== pathname) {
      // Check if navigating between dashboard routes - make it instant
      const isDashboardRoute = pathname?.startsWith('/dashboard');
      const wasDashboardRoute = prevPathnameRef.current?.startsWith('/dashboard');
      
      // For dashboard-to-dashboard navigation, skip transition for instant feel
      if (isDashboardRoute && wasDashboardRoute) {
        prevPathnameRef.current = pathname;
        return;
      }

      // Quick, subtle fade transition for other routes
      const tl = gsap.timeline();
      tl.to(content, {
        opacity: 0.8,
        duration: 0.08,
        ease: 'power2.in',
      })
      .to(content, {
        opacity: 1,
        duration: 0.12,
        ease: 'power2.out',
      });
    }

    prevPathnameRef.current = pathname;
  }, [pathname]);

  return (
    <div ref={contentRef} className={`flex flex-col flex-1 min-h-0 ${className}`} style={{ opacity: 1 }}>
      {children}
    </div>
  );
}

