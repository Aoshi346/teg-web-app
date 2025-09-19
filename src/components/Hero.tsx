// src/app/Hero.tsx

"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ArrowDown } from "lucide-react";

export default function Hero() {
  const heroRef = useRef<HTMLElement>(null);
  const backgroundRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const arrowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (heroRef.current && backgroundRef.current && contentRef.current && titleRef.current && subtitleRef.current && arrowRef.current) {
      // Set initial states
      gsap.set([titleRef.current, subtitleRef.current], { opacity: 0, y: 60 });
      gsap.set(arrowRef.current, { opacity: 0, y: 20 });
      
      // Create entrance timeline
      const tl = gsap.timeline();
      
      // Animate content in
      tl.to(titleRef.current, {
        opacity: 1,
        y: 0,
        duration: 1.2,
        ease: "power3.out"
      })
      .to(subtitleRef.current, {
        opacity: 1,
        y: 0,
        duration: 1.2,
        ease: "power3.out"
      }, "-=0.8")
      .to(arrowRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.8,
        ease: "power2.out"
      }, "-=0.4");

      // Continuous background animation
      gsap.to(backgroundRef.current, {
        scale: 1.05,
        duration: 20,
        ease: "none",
        repeat: -1,
        yoyo: true
      });

      // Continuous arrow bounce
      gsap.to(arrowRef.current, {
        y: -15,
        duration: 1.5,
        ease: "power2.inOut",
        repeat: -1,
        yoyo: true
      });
    }
  }, []);
  return (
    <section ref={heroRef} className="relative h-[90vh] w-full flex items-center justify-center text-white overflow-hidden">
      {/* Background Image with Ken Burns Effect */}
      <div
        ref={backgroundRef}
        className="absolute inset-0 pointer-events-none"
        aria-hidden
        style={{
          zIndex: 0,
          backgroundImage: "url('/usm_hero.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />

      {/* Darkening Overlay */}
      <div
        className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/50 to-black/70 pointer-events-none"
        style={{ zIndex: 1 }}
      />

      {/* Content Container */}
      <div
        ref={contentRef}
        className="relative z-20 flex flex-col items-center px-4 text-center"
      >
        <h1
          ref={titleRef}
          className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight text-white"
          style={{ textShadow: "0px 4px 12px rgba(0, 0, 0, 0.5)" }}
        >
          Sistema de evaluación para el{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-700">
            Trabajo Especial de Grado (TEG)
          </span>
        </h1>

        <p
          ref={subtitleRef}
          className="mt-6 max-w-3xl text-lg md:text-xl text-slate-200"
          style={{ textShadow: "0px 2px 8px rgba(0, 0, 0, 0.5)" }}
        >
          Gestiona, entrega y evalúa los proyectos de grado de forma segura y
          colaborativa. Facilita la comunicación entre estudiantes, tutores y
          jurados, y centraliza calificaciones y comentarios.
        </p>
      </div>

      {/* Bouncing Arrow Indicator */}
      <div
        ref={arrowRef}
        className="absolute bottom-10 z-20"
        aria-hidden
      >
        <ArrowDown className="h-10 w-10 text-white/70" />
      </div>
    </section>
  );
}