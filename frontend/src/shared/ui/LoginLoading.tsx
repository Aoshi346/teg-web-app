"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";

interface LoginLoadingProps {
  visible: boolean;
  message?: string;
}

/**
 * Lightweight transition overlay that bridges login → dashboard.
 * Uses a fast GSAP timeline to mask network latency with a branded
 * skeleton pulse + progress bar. No heavy SVGs or canvas.
 */
export default function LoginLoading({
  visible,
  message = "Cargando...",
}: LoginLoadingProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!visible || !overlayRef.current || !progressRef.current || !contentRef.current) return;

    const ctx = gsap.context(() => {
      // Fade in overlay
      gsap.fromTo(
        overlayRef.current,
        { autoAlpha: 0 },
        { autoAlpha: 1, duration: 0.2, ease: "power2.out" }
      );

      // Content entrance
      gsap.fromTo(
        contentRef.current,
        { y: 10, autoAlpha: 0 },
        { y: 0, autoAlpha: 1, duration: 0.3, delay: 0.1, ease: "power3.out" }
      );

      // Progress bar — fills to 90% fast, then crawls
      const tl = gsap.timeline();
      tl.to(progressRef.current, {
        width: "70%",
        duration: 0.6,
        ease: "power2.out",
      }).to(progressRef.current, {
        width: "92%",
        duration: 2.5,
        ease: "power1.out",
      });
    });

    return () => ctx.revert();
  }, [visible]);

  if (!visible) return null;

  return (
    <div
      ref={overlayRef}
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-[60] flex flex-col items-center justify-center bg-usm-navy/90 backdrop-blur-sm"
      style={{ visibility: "hidden" }}
    >
      {/* Top progress bar */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-white/10">
        <div
          ref={progressRef}
          className="h-full bg-gradient-to-r from-usm-blue via-usm-blue to-usm-orange rounded-r-full"
          style={{ width: "0%" }}
        />
      </div>

      <div ref={contentRef} className="flex flex-col items-center gap-5" style={{ visibility: "hidden" }}>
        {/* Pulsing brand mark */}
        <div className="relative">
          <div className="w-14 h-14 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center">
            <span className="text-2xl font-extrabold text-white tracking-tight">T</span>
          </div>
          {/* Pulse ring */}
          <div className="absolute inset-0 rounded-2xl border-2 border-usm-blue/50 animate-ping" style={{ animationDuration: "1.5s" }} />
        </div>

        {/* Skeleton dashboard preview */}
        <div className="w-64 sm:w-72 space-y-3 opacity-40">
          <div className="h-3 bg-white/20 rounded-full w-3/4 mx-auto animate-pulse" />
          <div className="flex gap-2 justify-center">
            <div className="h-16 flex-1 bg-white/10 rounded-xl animate-pulse" style={{ animationDelay: "0.1s" }} />
            <div className="h-16 flex-1 bg-white/10 rounded-xl animate-pulse" style={{ animationDelay: "0.2s" }} />
          </div>
          <div className="h-3 bg-white/15 rounded-full w-1/2 mx-auto animate-pulse" style={{ animationDelay: "0.3s" }} />
        </div>

        {/* Message */}
        <p className="text-white/70 text-sm font-medium tracking-wide">{message}</p>
      </div>
    </div>
  );
}
