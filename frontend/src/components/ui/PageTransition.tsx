"use client";

import React, { useRef, useEffect, ReactNode } from "react";
import { usePathname } from "next/navigation";
import { gsap } from "gsap";

interface PageTransitionProps {
  children: ReactNode;
  className?: string;
}

/**
 * GSAP-powered page transition wrapper.
 * Plays a fast enter animation on every route change.
 * Only animates `opacity` and `transform` (GPU-composited, 60fps safe).
 */
export default function PageTransition({ children, className = "" }: PageTransitionProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const isFirstRender = useRef(true);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    // Skip animation on first mount — let individual pages handle their own entrance
    if (isFirstRender.current) {
      isFirstRender.current = false;
      gsap.set(el, { opacity: 1, y: 0 });
      return;
    }

    // Route changed — play a fast enter transition
    const ctx = gsap.context(() => {
      gsap.fromTo(
        el,
        { opacity: 0, y: 8 },
        {
          opacity: 1,
          y: 0,
          duration: 0.3,
          ease: "power2.out",
          clearProps: "transform",
        }
      );
    });

    return () => ctx.revert();
  }, [pathname]);

  return (
    <div
      ref={containerRef}
      className={`flex flex-col flex-1 min-h-0 ${className}`}
      style={{ willChange: "opacity, transform" }}
    >
      {children}
    </div>
  );
}
