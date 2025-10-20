// src/app/Hero.tsx

"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrambleTextPlugin } from "gsap/ScrambleTextPlugin";
import SplitType from "split-type";

export default function Hero() {
  const heroRef = useRef<HTMLElement>(null);
  const backgroundRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const badgeRef = useRef<HTMLSpanElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const gradientRef = useRef<HTMLSpanElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const secondaryRef = useRef<HTMLParagraphElement>(null);
  const arrowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (
      !heroRef.current ||
      !backgroundRef.current ||
      !contentRef.current ||
      !badgeRef.current ||
      !titleRef.current ||
      !subtitleRef.current ||
      !secondaryRef.current ||
      !arrowRef.current
    ) {
      return undefined;
    }

    gsap.registerPlugin(ScrambleTextPlugin);

    const splitInstances: SplitType[] = [];

    const ctx = gsap.context(() => {
      // Split title into lines (avoid double-splitting the gradient words)
      const titleSplit = new SplitType(titleRef.current!, { types: "lines" });
      // Split only the gradient phrase so we can style its generated word elements
      const gradientSplit = gradientRef.current
        ? new SplitType(gradientRef.current, { types: "words" })
        : null;
      const subtitleSplit = new SplitType(subtitleRef.current!, { types: "lines" });

  if (gradientSplit) splitInstances.push(titleSplit, subtitleSplit, gradientSplit);
  else splitInstances.push(titleSplit, subtitleSplit);

      const finalSecondaryText = secondaryRef.current!.textContent ?? "";

      // initial states
      gsap.set([badgeRef.current, arrowRef.current], { autoAlpha: 0, y: 24 });
      gsap.set(titleRef.current, { autoAlpha: 0, y: 20, scale: 0.98, skewX: 6 });
      gsap.set(titleSplit.lines, { opacity: 0, y: 40 });
      // Ensure the generated gradient words inherit the gradient coloring and start hidden (3D rotated)
      if (gradientSplit && gradientSplit.words) {
        gsap.set(gradientSplit.words, { opacity: 0, y: 40, rotationX: -75, transformOrigin: "50% 50%" });
        gradientSplit.words.forEach((w) => {
          const el = w as HTMLElement;
          el.style.backgroundImage = "linear-gradient(90deg,#67e8f9,#3b82f6)";
          el.style.setProperty("-webkit-background-clip", "text");
          el.style.setProperty("background-clip", "text");
          el.style.setProperty("-webkit-text-fill-color", "transparent");
          el.style.color = "transparent";
          el.style.display = "inline-block";
          el.style.backfaceVisibility = "hidden";
        });
      }
      gsap.set(subtitleSplit.lines, { opacity: 0, y: 32 });
      gsap.set(secondaryRef.current, { autoAlpha: 0 });

      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      tl.to(badgeRef.current, {
        autoAlpha: 1,
        y: 0,
        duration: 0.6
      })
        // Pop/tilt the whole heading
        .to(
          titleRef.current,
          {
            autoAlpha: 1,
            y: 0,
            scale: 1,
            skewX: 0,
            duration: 0.9,
            ease: "power3.out"
          },
          "-=0.2"
        )
        // Reveal title lines to add rhythm
        .to(
          titleSplit.lines,
          {
            opacity: 1,
            y: 0,
            duration: 0.9,
            stagger: 0.06
          },
          "-=0.6"
        )
        // Flip-in gradient words with a bouncy 3D animation
        .to(
          gradientSplit ? gradientSplit.words : [],
          {
            opacity: 1,
            y: 0,
            rotationX: 0,
            duration: 0.9,
            stagger: 0.08,
            ease: "elastic.out(1, 0.6)",
            transformOrigin: "50% 50%"
          },
          "-=0.8"
        )
        .to(
          subtitleSplit.lines,
          {
            opacity: 1,
            y: 0,
            duration: 0.9,
            stagger: 0.3
          },
          "-=0.4"
        )
        .fromTo(
          secondaryRef.current,
          { autoAlpha: 0 },
          {
            autoAlpha: 1,
            duration: 1.4,
            ease: "power2.out",
            scrambleText: {
              text: finalSecondaryText,
              chars: "upperAndLowerCase",
              revealDelay: 0.2
            }
          },
          "-=0.6"
        )
        .to(
          arrowRef.current,
          {
            autoAlpha: 1,
            y: 0,
            duration: 0.8,
            ease: "power2.out"
          },
          "-=0.4"
        )
        .add(() => {
          gsap.fromTo(
            arrowRef.current,
            { y: -16 },
            {
              y: 16,
              duration: 1.2,
              ease: "power2.inOut",
              repeat: -1,
              yoyo: true,
            },
          );
        });

      gsap.to(backgroundRef.current, {
        scale: 1.06,
        duration: 24,
        ease: "none",
        repeat: -1,
        yoyo: true
      });
    }, heroRef);

    return () => {
      splitInstances.forEach((instance) => instance.revert());
      ctx.revert();
    };
  }, []);
  return (
    <section ref={heroRef} className="relative h-[90vh] w-full flex items-center justify-center text-white overflow-x-hidden overflow-hidden">
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
        className="relative z-20 flex flex-col items-center max-w-screen-xl px-4 text-center"
      >
        <span
          ref={badgeRef}
          className="inline-flex items-center rounded-full bg-white/10 px-5 py-1 text-xs font-semibold uppercase tracking-[0.4em] text-slate-100 backdrop-blur-sm md:text-sm"
        >
          Plataforma Tesisfar
        </span>

        <h1
          ref={titleRef}
          className="mt-6 max-w-4xl text-4xl font-extrabold leading-tight text-white md:text-6xl break-words"
          style={{ textShadow: "0px 4px 12px rgba(0, 0, 0, 0.5)" }}
        >
          Gestiona tu
          <span ref={gradientRef} className="text-transparent bg-clip-text bg-gradient-to-r from-sky-300 to-blue-500">
            {" "}
            Trabajo Especial de Grado
            {" "}
          </span>
          con total claridad
        </h1>

        <p
          ref={subtitleRef}
          className="mt-6 max-w-3xl text-lg text-slate-200 md:text-xl"
          style={{ textShadow: "0px 2px 8px rgba(0, 0, 0, 0.5)" }}
        >
          Centraliza entregas, evaluaciones y aprobaciones en un flujo seguro con
          recordatorios automáticos y reportes listos para tus comités.
        </p>

        <p
          ref={secondaryRef}
          className="mt-4 max-w-2xl text-base text-slate-100/90 md:text-lg"
        >
          Coordina a estudiantes, tutores y jurados con comunicación fluida y
          seguimiento en tiempo real.
        </p>
      </div>

      {/* Bouncing Arrow Indicator */}
      <div
        ref={arrowRef}
        className="absolute bottom-10 z-20"
        aria-hidden
      >
        <svg
          className="h-12 w-12 text-white/70"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M19 14l-7 7m0 0l-7-7m7 7V3"
          />
        </svg>
      </div>
    </section>
  );
}