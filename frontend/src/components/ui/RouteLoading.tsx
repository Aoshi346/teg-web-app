"use client";

import React, { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { gsap } from "gsap";

/**
 * Ultra-lightweight, non-blocking route progress indicator.
 * Renders a thin gradient bar at the top of the viewport during external route changes.
 * Dashboard-to-dashboard navigation is instant (no indicator shown).
 * Only animates `transform: scaleX()` — zero layout thrash, GPU-composited.
 */
export default function RouteLoading() {
  const pathname = usePathname();
  const [isLoading, setIsLoading] = useState(false);
  const barRef = useRef<HTMLDivElement>(null);
  const prevPathRef = useRef<string | null>(null);
  const isFirstMount = useRef(true);
  const tweenRef = useRef<gsap.core.Tween | null>(null);

  useEffect(() => {
    if (isFirstMount.current) {
      isFirstMount.current = false;
      prevPathRef.current = pathname;
      return;
    }

    if (prevPathRef.current === pathname) return;

    const prev = prevPathRef.current;
    prevPathRef.current = pathname;

    // Skip for dashboard internal navigation — PageTransition handles it
    if (prev?.startsWith("/dashboard") && pathname?.startsWith("/dashboard")) return;

    // Skip post-login
    try {
      if (sessionStorage.getItem("justLoggedIn")) return;
    } catch {}

    setIsLoading(true);

    if (barRef.current) {
      tweenRef.current?.kill();

      // Fast fill to 90%, then complete
      gsap.set(barRef.current, { scaleX: 0, transformOrigin: "left" });
      tweenRef.current = gsap.to(barRef.current, {
        scaleX: 0.9,
        duration: 0.3,
        ease: "power2.out",
        onComplete: () => {
          if (!barRef.current) return;
          gsap.to(barRef.current, {
            scaleX: 1,
            duration: 0.15,
            ease: "power2.in",
            onComplete: () => {
              gsap.to(barRef.current!, {
                opacity: 0,
                duration: 0.2,
                onComplete: () => {
                  setIsLoading(false);
                  if (barRef.current) gsap.set(barRef.current, { opacity: 1 });
                },
              });
            },
          });
        },
      });
    }
  }, [pathname]);

  if (!isLoading) return null;

  return (
    <div className="fixed top-0 left-0 right-0 h-[2px] z-[60]">
      <div
        ref={barRef}
        className="h-full bg-gradient-to-r from-usm-blue via-usm-blue to-usm-orange"
        style={{ transform: "scaleX(0)", transformOrigin: "left" }}
      />
    </div>
  );
}
