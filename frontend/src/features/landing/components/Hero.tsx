// src/components/landing/Hero.tsx

"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import SplitType from "split-type";

/**
 * Lightweight animated canvas — drifting circles and soft connecting lines
 * in brand colors. Pure CSS fallback for reduced-motion. No mouse tracking.
 */
const HeroCanvas = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let w = 0;
    let h = 0;
    const dpr = Math.min(window.devicePixelRatio, 2);

    type Orb = {
      x: number;
      y: number;
      r: number;
      vx: number;
      vy: number;
      color: string;
      alpha: number;
    };

    const orbs: Orb[] = [];
    const orbCount = 18;
    const connectDist = 150;

    const palette = [
      "0, 102, 255",
      "255, 107, 53",
      "255, 210, 63",
      "255, 255, 255",
    ];

    const resize = () => {
      const parent = canvas.parentElement!;
      w = parent.offsetWidth;
      h = parent.offsetHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const seed = () => {
      orbs.length = 0;
      for (let i = 0; i < orbCount; i++) {
        orbs.push({
          x: Math.random() * w,
          y: Math.random() * h,
          r: 2 + Math.random() * 4,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
          color: palette[Math.floor(Math.random() * palette.length)],
          alpha: 0.15 + Math.random() * 0.35,
        });
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, w, h);

      for (let i = 0; i < orbs.length; i++) {
        for (let j = i + 1; j < orbs.length; j++) {
          const dx = orbs[i].x - orbs[j].x;
          const dy = orbs[i].y - orbs[j].y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < connectDist) {
            const a = (1 - d / connectDist) * 0.08;
            ctx.strokeStyle = `rgba(255,255,255,${a})`;
            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(orbs[i].x, orbs[i].y);
            ctx.lineTo(orbs[j].x, orbs[j].y);
            ctx.stroke();
          }
        }
      }

      for (const o of orbs) {
        o.x += o.vx;
        o.y += o.vy;
        if (o.x < -10) o.x = w + 10;
        if (o.x > w + 10) o.x = -10;
        if (o.y < -10) o.y = h + 10;
        if (o.y > h + 10) o.y = -10;

        ctx.beginPath();
        ctx.arc(o.x, o.y, o.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${o.color}, ${o.alpha})`;
        ctx.fill();
      }

      animId = requestAnimationFrame(draw);
    };

    resize();
    seed();
    draw();

    const onResize = () => {
      resize();
      seed();
    };
    window.addEventListener("resize", onResize, { passive: true });
    return () => {
      window.removeEventListener("resize", onResize);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 z-[1] pointer-events-none"
      aria-hidden="true"
    />
  );
};

export default function Hero() {
  const heroRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const gradientRef = useRef<HTMLSpanElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const secondaryRef = useRef<HTMLDivElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const arrowRef = useRef<HTMLDivElement>(null);
  const cursorLightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (
      !heroRef.current ||
      !contentRef.current ||
      !titleRef.current ||
      !subtitleRef.current ||
      !secondaryRef.current ||
      !ctaRef.current ||
      !arrowRef.current
    ) {
      return undefined;
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return undefined;
    }

    const splitInstances: SplitType[] = [];

    const ctx = gsap.context(() => {
      const titleSplit = new SplitType(titleRef.current!, { types: "lines" });
      const subtitleSplit = new SplitType(subtitleRef.current!, {
        types: "lines",
      });
      splitInstances.push(titleSplit, subtitleSplit);

      gsap.set(arrowRef.current, { autoAlpha: 0, y: 20 });
      gsap.set(secondaryRef.current, { autoAlpha: 0, y: 24 });
      gsap.set(ctaRef.current, { autoAlpha: 0, y: 24 });
      gsap.set(titleRef.current, { autoAlpha: 0 });
      gsap.set(titleSplit.lines, { opacity: 0, y: 40 });
      gsap.set(subtitleSplit.lines, { opacity: 0, y: 30 });

      const banners = titleRef.current?.querySelectorAll(".hero-banner");
      if (banners) {
        gsap.set(banners, { clipPath: "inset(0 100% 0 0)", autoAlpha: 1 });
      }

      const tl = gsap.timeline({ defaults: { ease: "power3.out" }, delay: 0.15 });

      tl.to(titleRef.current, { autoAlpha: 1, duration: 0.05 })
        .to(banners ?? [], { clipPath: "inset(0 0% 0 0)", duration: 0.8, stagger: 0.12, ease: "power3.inOut" }, "-=0.15")
        .to(titleSplit.lines, { opacity: 1, y: 0, duration: 0.7, stagger: 0.08 }, "-=0.5")
        .to(subtitleSplit.lines, { opacity: 1, y: 0, duration: 0.6, stagger: 0.08 }, "-=0.35")
        .to(secondaryRef.current, { autoAlpha: 1, y: 0, duration: 0.6 }, "-=0.3")
        .to(ctaRef.current, { autoAlpha: 1, y: 0, duration: 0.5, ease: "back.out(1.2)" }, "-=0.25")
        .to(arrowRef.current, { autoAlpha: 1, y: 0, duration: 0.4 }, "-=0.2");

      tl.add(() => {
        gsap.to(arrowRef.current, { y: 6, duration: 1.4, ease: "sine.inOut", repeat: -1, yoyo: true });
        if (gradientRef.current) {
          gsap.to(gradientRef.current, { y: -5, rotation: -2.5, duration: 4, ease: "sine.inOut", repeat: -1, yoyo: true });
        }
        gsap.to(".lh-bridge-pill", { y: 4, duration: 1.2, repeat: -1, yoyo: true, ease: "sine.inOut" });
      });
    }, heroRef);

    return () => {
      splitInstances.forEach((inst) => inst.revert());
      ctx.revert();
    };
  }, []);

  // Cursor light follower — only on desktop pointer-fine, non-reduced-motion.
  useEffect(() => {
    const hero = heroRef.current;
    const light = cursorLightRef.current;
    if (!hero || !light) return undefined;

    const desktop = window.matchMedia("(min-width: 1024px) and (pointer: fine)");
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (!desktop.matches || reduced.matches) return undefined;

    const onMove = (e: MouseEvent) => {
      const rect = hero.getBoundingClientRect();
      light.style.setProperty("--lh-cx", `${e.clientX - rect.left}px`);
      light.style.setProperty("--lh-cy", `${e.clientY - rect.top}px`);
    };

    hero.addEventListener("mousemove", onMove, { passive: true });
    return () => {
      hero.removeEventListener("mousemove", onMove);
    };
  }, []);

  // Banner parallax — translate the orange b2 banner up to ~24px between
  // scrollY 0 and 600. rAF-throttled, single-token cancel-and-schedule.
  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (reduced.matches) return undefined;

    let rafId: number | null = null;
    const schedule = () => {
      if (rafId !== null) return;
      rafId = requestAnimationFrame(() => {
        rafId = null;
        const el = gradientRef.current;
        if (!el) return;
        const y = Math.min(Math.max(window.scrollY, 0), 600);
        const offset = (y / 600) * 24;
        el.classList.add("is-parallaxed");
        el.style.setProperty("--lh-parallax-y", `${-offset}px`);
        el.style.transform = `translateY(${-offset}px) rotate(-2deg)`;
      });
    };

    window.addEventListener("scroll", schedule, { passive: true });
    return () => {
      window.removeEventListener("scroll", schedule);
      if (rafId !== null) cancelAnimationFrame(rafId);
    };
  }, []);

  const handleScrollToFeatures = () => {
    const el = document.getElementById("features");
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handlePrimaryClick = () => {
    const modal = document.querySelector('[aria-label="Ingresar"]') as HTMLButtonElement | null;
    if (modal) modal.click();
  };

  return (
    <section
      ref={heroRef}
      className="relative w-full flex items-center justify-center text-white overflow-hidden hero-gradient"
      style={{
        minHeight: "calc(100svh - var(--header-height, 88px) - clamp(16px, 2.8vh, 56px))",
        paddingTop: "calc(var(--header-height, 88px) + clamp(16px, 2.8vh, 56px))",
        boxSizing: "border-box",
      }}
    >
      {/* Background layers — CSS only (no JS mouse tracking) */}
      <div className="absolute inset-0 mesh-gradient opacity-60" />
      <div className="absolute inset-0 dot-grid opacity-20" />

      {/* Animated canvas — lightweight drifting orbs */}
      <HeroCanvas />

      {/* Atmosphere layers — Landing Hero v2026 */}
      <div className="lh-aurora" aria-hidden />
      <div className="lh-grain" aria-hidden />
      <div className="lh-cursor-light" aria-hidden ref={cursorLightRef} />

      {/* Content */}
      <div
        ref={contentRef}
        className="relative z-20 flex flex-col items-center max-w-screen-xl px-4 text-center mt-4 md:mt-10"
      >
        <div className="relative inline-block mb-4">
          <h1
            ref={titleRef}
            className="text-4xl font-extrabold leading-tight text-white md:text-6xl break-words relative z-20 flex flex-col items-center sm:items-start sm:pl-12"
            style={{ textShadow: "0px 4px 16px rgba(0, 0, 0, 0.25)" }}
          >
            <span className="hero-banner text-white px-6 py-3 bg-usm-blue inline-block transform -rotate-2 shadow-2xl z-20 relative -mb-3 self-center sm:self-start sm:pl-12 border border-white/20">
              Gestiona tu
            </span>
            <span
              ref={gradientRef}
              className="hero-banner banner b2 text-white px-7 py-4 bg-gradient-to-r from-usm-orange to-orange-500 inline-block transform -rotate-2 shadow-2xl z-10 relative self-center sm:self-start sm:ml-8 border border-white/20"
            >
              Trabajo Especial de Grado
            </span>
            <span
              className="inline-block mt-6 font-extrabold uppercase tracking-wide self-center"
              style={{
                WebkitTextStroke: "12px #0066ff",
                WebkitTextFillColor: "white",
                paintOrder: "stroke fill",
                filter: "drop-shadow(0px 4px 12px rgba(0,0,0,0.35))",
                fontSize: "inherit",
              }}
            >
              con total claridad
            </span>
          </h1>
        </div>

        {/* Stacked-layered pair (Option III) */}
        <div className="lh-stack-pair" data-testid="hero-stack-pair">
          <div className="lh-stack-sub">
            <p ref={subtitleRef}>
              Centraliza <em>entregas, evaluaciones y aprobaciones</em> en un flujo seguro
              con recordatorios automáticos y reportes listos para tus comités.
            </p>
          </div>
          <div ref={secondaryRef} className="lh-stack-secondary">
            <span className="dash">—</span>&nbsp;Coordina a estudiantes, tutores y jurados con comunicación fluida.
          </div>
        </div>

        {/* CTA Buttons — stamp + ghost */}
        <div ref={ctaRef} className="mt-8 flex flex-col sm:flex-row items-center gap-4">
          <button
            type="button"
            onClick={handlePrimaryClick}
            className="lh-btn-stamp"
          >
            <span className="corner tr" aria-hidden />
            <span className="corner bl" aria-hidden />
            <span className="lh-btn-num">01</span>
            <span>Comenzar ahora</span>
            <span className="arr" aria-hidden>→</span>
          </button>
          <button
            type="button"
            onClick={handleScrollToFeatures}
            className="lh-btn-stamp-ghost"
          >
            Ver funciones
          </button>
        </div>

        {/* Bridge pill — replaces ChevronDown scroll arrow */}
        <div ref={arrowRef} className="mt-10 mb-4">
          <button
            type="button"
            className="lh-bridge-pill"
            aria-label="Cómo te ayuda Tesisfar — desplazarse"
            onClick={handleScrollToFeatures}
          >
            Cómo te ayuda Tesisfar
            <span className="arr" aria-hidden>↓</span>
          </button>
        </div>
      </div>
    </section>
  );
}
