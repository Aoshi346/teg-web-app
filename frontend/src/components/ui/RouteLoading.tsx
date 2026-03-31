"use client";

import React, { useEffect, useState, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { gsap } from 'gsap';

export default function RouteLoading() {
  const pathname = usePathname();
  const [isLoading, setIsLoading] = useState(false);
  const progressRef = React.useRef<HTMLDivElement>(null);
  const prevPathnameRef = useRef<string | null>(null);
  const isInitialMountRef = useRef(true);
  const skipNextRef = useRef(false);

  useEffect(() => {
    // Skip on initial mount - only show on actual route changes
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      prevPathnameRef.current = pathname;
      return;
    }

    // Only show loading if pathname actually changed
    if (prevPathnameRef.current === pathname) {
      return;
    }

    // Skip if we just logged in (handled by LoginLoading)
    try {
      const justLoggedIn = sessionStorage.getItem("justLoggedIn");
      if (justLoggedIn) {
        prevPathnameRef.current = pathname;
        skipNextRef.current = true;
        return;
      }
    } catch {}

    // Skip if navigating between dashboard pages entirely
    const isDashboardRoute = pathname?.startsWith('/dashboard');
    const wasDashboardRoute = prevPathnameRef.current?.startsWith('/dashboard');
    
    // If navigating between dashboard pages, ALWAYS skip loading for instant feel
    if (isDashboardRoute && wasDashboardRoute) {
      prevPathnameRef.current = pathname;
      setIsLoading(false);
      return;
    }

    skipNextRef.current = false;
    setIsLoading(true);
    
    if (progressRef.current) {
      gsap.set(progressRef.current, { width: '0%' });
      gsap.to(progressRef.current, {
        width: '90%',
        duration: 0.2, // normal duration for external routes
        ease: 'power2.out',
      });
    }

    const timer = setTimeout(() => {
      if (progressRef.current) {
        gsap.to(progressRef.current, {
          width: '100%',
          duration: 0.08,
          ease: 'power2.in',
          onComplete: () => {
             // Use setTimeout to ensure the React state update doesn't block painting
            setTimeout(() => {
               setIsLoading(false);
               prevPathnameRef.current = pathname;
            }, 0);
          },
        });
      } else {
        setIsLoading(false);
        prevPathnameRef.current = pathname;
      }
    }, 100);

    return () => clearTimeout(timer);
  }, [pathname]);

  if (!isLoading) return null;

  return (
    <div className="fixed top-0 left-0 right-0 h-0.5 bg-gray-200/50 z-[60]">
      <div
        ref={progressRef}
        className="h-full bg-gradient-to-r from-blue-600 to-blue-500 shadow-lg shadow-blue-500/50"
        style={{ width: '0%' }}
      />
    </div>
  );
}

