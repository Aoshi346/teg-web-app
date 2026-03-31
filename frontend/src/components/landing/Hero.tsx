// src/components/landing/Hero.tsx

"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import SplitType from "split-type";
import { LogIn, ChevronDown, ArrowRight } from "lucide-react";

export default function Hero() {
  const heroRef = useRef<HTMLElement>(null);
  const backgroundRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const gradientRef = useRef<HTMLSpanElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const secondaryRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const arrowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (
      !heroRef.current ||
      !backgroundRef.current ||
      !contentRef.current ||
      !titleRef.current ||
      !subtitleRef.current ||
      !secondaryRef.current ||
      !ctaRef.current ||
      !arrowRef.current
    ) {
      return undefined;
    }

    const splitInstances: SplitType[] = [];

    const ctx = gsap.context(() => {
      // Split title into lines
      const titleSplit = new SplitType(titleRef.current!, { types: "lines" });
      const subtitleSplit = new SplitType(subtitleRef.current!, {
        types: "lines",
      });

      splitInstances.push(titleSplit, subtitleSplit);

      // initial states
      gsap.set(arrowRef.current, { autoAlpha: 0, y: 24 });
      gsap.set(secondaryRef.current, { autoAlpha: 0, y: 20 });
      gsap.set(ctaRef.current, { autoAlpha: 0, y: 20 });
      gsap.set(titleRef.current, {
        autoAlpha: 0,
        y: 20,
        scale: 0.98,
      });
      gsap.set(titleSplit.lines, { opacity: 0, y: 40 });
      gsap.set(subtitleSplit.lines, { opacity: 0, y: 32 });

      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      tl.to(titleRef.current, {
        autoAlpha: 1,
        y: 0,
        scale: 1,
        duration: 0.9,
        ease: "power3.out",
      })
        // Reveal title lines to add rhythm
        .to(
          titleSplit.lines,
          {
            opacity: 1,
            y: 0,
            duration: 0.9,
            stagger: 0.1,
          },
          "-=0.6",
        )
        .to(
          subtitleSplit.lines,
          {
            opacity: 1,
            y: 0,
            duration: 0.9,
            stagger: 0.15,
          },
          "-=0.6",
        )
        .to(
          secondaryRef.current,
          {
            autoAlpha: 1,
            y: 0,
            duration: 1.0,
            ease: "power2.out",
          },
          "-=0.6",
        )
        .to(
          ctaRef.current,
          {
            autoAlpha: 1,
            y: 0,
            duration: 0.8,
            ease: "power2.out",
          },
          "-=0.5",
        )
        .to(
          arrowRef.current,
          {
            autoAlpha: 1,
            y: 0,
            duration: 0.8,
            ease: "power2.out",
          },
          "-=0.4",
        )
        .add(() => {
          gsap.fromTo(
            arrowRef.current,
            { y: -8 },
            {
              y: 8,
              duration: 1.2,
              ease: "power2.inOut",
              repeat: -1,
              yoyo: true,
            },
          );
          
          // Add subtle floating motion to the title banners after they enter
          if (gradientRef.current) {
            gsap.fromTo(
              gradientRef.current,
              { y: 0, rotation: -2 },
              {
                y: -8,
                rotation: -2.5,
                duration: 4,
                ease: "power1.inOut",
                repeat: -1,
                yoyo: true,
                delay: 1,
              },
            );
          }
          
          // Add gentle glow pulse to the blue banner
          const blueBanner = titleRef.current?.querySelector('.bg-usm-blue') as HTMLElement;
          if (blueBanner) {
            gsap.fromTo(
              blueBanner,
              { boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)" },
              {
                boxShadow: "0 20px 25px -5px rgba(0, 102, 255, 0.3), 0 8px 10px -6px rgba(0, 102, 255, 0.2)",
                duration: 2,
                ease: "power1.inOut",
                repeat: -1,
                yoyo: true,
                delay: 1.5,
              },
            );
          }
        });
    }, heroRef);
    return () => {
      splitInstances.forEach((instance) => instance.revert());
      ctx.revert();
    };
  }, []);

  const handleScrollToFeatures = () => {
    const el = document.getElementById("features");
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <section
      ref={heroRef}
      className="relative w-full flex items-center justify-center text-white overflow-hidden hero-gradient"
      style={{
        // Use 100svh to avoid layout shifts when mobile browser UI shows/hides while scrolling.
        // Keep a responsive top gap so the badge isn't cramped under the header.
        minHeight:
          "calc(100svh - var(--header-height, 88px) - clamp(16px, 2.8vh, 56px))",
        paddingTop:
          "calc(var(--header-height, 88px) + clamp(16px, 2.8vh, 56px))",
        boxSizing: "border-box",
      }}
    >
      {/* Background Effects */}
      <div ref={backgroundRef} className="absolute inset-0 mesh-gradient opacity-60" />
      <div className="absolute inset-0 dot-grid opacity-30" />
      
      {/* Animated Orbs */}
      <div className="absolute top-20 left-10 w-72 h-72 bg-usm-blue/20 rounded-full blur-3xl floating" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-usm-orange/20 rounded-full blur-3xl floating" style={{ animationDelay: '3s' }} />
      
      {/* Content Container */}
      <div
        ref={contentRef}
        className="relative z-20 flex flex-col items-center max-w-screen-xl px-4 text-center mt-4 md:mt-10"
      >
        <div className="relative inline-block mb-4 mt-4">
          <h1
            ref={titleRef}
            className="text-4xl font-extrabold leading-tight text-white md:text-6xl break-words relative z-20 flex flex-col items-center sm:items-start sm:pl-12"
            style={{ textShadow: "0px 4px 12px rgba(0, 0, 0, 0.2)" }}
          >
            {/* Top Light Blue Box */}
            <span className="text-white px-6 py-3 bg-usm-blue inline-block transform -rotate-2 shadow-2xl z-20 relative -mb-3 self-center sm:self-start sm:pl-12 backdrop-blur-sm border border-white/20 pulse-glow">
              Gestiona tu
            </span>
            {/* Main Orange Box */}
            <span
              ref={gradientRef}
              className="text-white px-7 py-4 bg-gradient-to-r from-usm-orange to-orange-500 inline-block transform -rotate-2 shadow-2xl z-10 relative self-center sm:self-start sm:ml-8 backdrop-blur-sm border border-white/20 hover:shadow-orange-500/30 transition-all duration-300"
            >
              Trabajo Especial de Grado
            </span>
            {/* Stroked Text */}
            <span
              className="inline-block mt-6 font-extrabold uppercase tracking-wide self-center"
              style={{
                WebkitTextStroke: "12px #0066ff",
                WebkitTextFillColor: "white",
                paintOrder: "stroke fill",
                filter: "drop-shadow(0px 4px 8px rgba(0,0,0,0.3))",
                fontSize: "inherit",
              }}
            >
              con total claridad
            </span>
          </h1>
        </div>

        <div className="mt-8 relative inline-block">
          <p
            ref={subtitleRef}
            className="max-w-3xl text-lg text-slate-100 md:text-xl font-medium px-8 py-4 relative z-10 bg-usm-navy/80 backdrop-blur-md border border-white/20 shadow-xl rounded-2xl"
            style={{ textShadow: "0px 2px 8px rgba(0, 0, 0, 0.3)" }}
          >
            Centraliza entregas, evaluaciones y aprobaciones en un flujo seguro
            con recordatorios automáticos y reportes listos para tus comités.
          </p>
        </div>

        <p
          ref={secondaryRef}
          className="mt-6 font-semibold max-w-2xl text-base text-usm-navy bg-white px-8 py-3 rounded-full shadow-xl md:text-lg inline-block"
        >
          Coordina a estudiantes, tutores y jurados con comunicación fluida.
        </p>

        {/* CTA Buttons */}
        <div
          ref={ctaRef}
          className="mt-8 flex flex-col sm:flex-row items-center gap-4"
        >
          <button
            onClick={() => {
              const modal = document.querySelector('[aria-label="Ingresar"]') as HTMLButtonElement;
              if (modal) modal.click();
            }}
            className="inline-flex items-center gap-2.5 px-8 py-3.5 text-base font-bold text-white
                       bg-gradient-to-r from-usm-orange to-orange-500
                       rounded-full shadow-lg shadow-orange-500/25
                       hover:shadow-xl hover:shadow-orange-500/30 hover:-translate-y-0.5
                       active:translate-y-0 active:shadow-md
                       transition-all duration-200 ease-out"
          >
            <LogIn className="h-5 w-5" />
            Comenzar ahora
          </button>
          <button
            onClick={handleScrollToFeatures}
            className="inline-flex items-center gap-2 px-7 py-3.5 text-base font-semibold text-white
                       bg-white/10 backdrop-blur-sm border border-white/30
                       rounded-full shadow-lg
                       hover:bg-white/20 hover:-translate-y-0.5
                       active:translate-y-0
                       transition-all duration-200 ease-out"
          >
            Ver funciones
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        {/* Scroll-down arrow */}
        <div ref={arrowRef} className="mt-10 mb-4">
          <button
            onClick={handleScrollToFeatures}
            className="p-2 rounded-full text-white/60 hover:text-white transition-colors duration-200"
            aria-label="Scroll down"
          >
            <ChevronDown className="h-8 w-8" />
          </button>
        </div>
      </div>
    </section>
  );
}
