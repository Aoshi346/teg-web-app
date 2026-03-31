// src/components/landing/FeaturesSection.tsx

"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import FeatureCard from "@/components/landing/FeatureCard";
import {
  ClipboardCheck,
  Users,
  BookOpen,
  UserCheck,
  FileText,
  Calendar,
  GraduationCap,
  Briefcase,
} from "lucide-react";

gsap.registerPlugin(ScrollTrigger);

export default function FeaturesSection() {
  const studentsSectionRef = useRef<HTMLElement>(null);
  const studentsHeaderRef = useRef<HTMLDivElement>(null);
  const studentsCardsRef = useRef<HTMLDivElement>(null);
  const teachersSectionRef = useRef<HTMLElement>(null);
  const teachersHeaderRef = useRef<HTMLDivElement>(null);
  const teachersCardsRef = useRef<HTMLDivElement>(null);
  const dividerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Divider line expand
      if (dividerRef.current) {
        gsap.set(dividerRef.current, { scaleX: 0 });
        ScrollTrigger.create({
          trigger: dividerRef.current,
          start: "top 90%",
          once: true,
          onEnter: () => {
            gsap.to(dividerRef.current, { scaleX: 1, duration: 1, ease: "power3.inOut" });
          },
        });
      }

      // Reusable section animator — no SplitType (perf), simple fade + slide
      const animateSection = (
        sectionEl: HTMLElement | null,
        headerEl: HTMLDivElement | null,
        cardsEl: HTMLDivElement | null,
        direction: "left" | "right"
      ) => {
        if (!sectionEl || !headerEl || !cardsEl) return;

        const badge = headerEl.querySelector(".section-badge") as HTMLElement | null;
        const h2 = headerEl.querySelector("h2") as HTMLElement | null;
        const p = headerEl.querySelector("p") as HTMLElement | null;
        const cards = cardsEl.children;

        // Set initial hidden states
        if (badge) gsap.set(badge, { autoAlpha: 0, y: 10, scale: 0.9 });
        if (h2) gsap.set(h2, { autoAlpha: 0, y: 20 });
        if (p) gsap.set(p, { autoAlpha: 0, y: 16 });

        const xOffset = direction === "left" ? -60 : 60;
        gsap.set(cards, { opacity: 0, x: xOffset, scale: 0.96 });

        // Mobile: simpler slide-up
        const isMobile = window.innerWidth < 768;
        if (isMobile) {
          gsap.set(cards, { opacity: 0, x: 0, y: 30, scale: 0.98 });
        }

        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: sectionEl,
            start: isMobile ? "top 88%" : "top 80%",
            once: true,
          },
        });

        if (badge) {
          tl.to(badge, { autoAlpha: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(1.5)" }, 0);
        }
        if (h2) {
          tl.to(h2, { autoAlpha: 1, y: 0, duration: 0.5, ease: "power3.out" }, 0.1);
        }
        if (p) {
          tl.to(p, { autoAlpha: 1, y: 0, duration: 0.5, ease: "power2.out" }, 0.25);
        }

        tl.to(
          cards,
          {
            opacity: 1,
            x: 0,
            y: 0,
            scale: 1,
            duration: 0.6,
            stagger: 0.1,
            ease: "power3.out",
          },
          0.3
        );
      };

      animateSection(
        studentsSectionRef.current,
        studentsHeaderRef.current,
        studentsCardsRef.current,
        "left"
      );
      animateSection(
        teachersSectionRef.current,
        teachersHeaderRef.current,
        teachersCardsRef.current,
        "right"
      );
    });

    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach((t) => t.kill());
    };
  }, []);

  return (
    <>
      {/* Students Section */}
      <section
        id="features"
        ref={studentsSectionRef}
        className="relative w-full bg-gradient-to-b from-slate-50 via-white to-slate-50 py-20 md:py-28 px-4 overflow-hidden"
      >
        {/* Subtle background washes — CSS only */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute top-0 right-0 w-full h-[60%] bg-gradient-to-bl from-usm-blue/[0.05] via-transparent to-transparent" />
          <div className="absolute bottom-0 left-0 w-full h-[50%] bg-gradient-to-tr from-usm-orange/[0.04] via-transparent to-transparent" />
          <div className="hidden md:block absolute top-[10%] right-[5%] w-[350px] h-[350px] rounded-full border border-dashed border-usm-blue/[0.08]" />
          <div className="hidden md:block absolute bottom-[8%] left-[3%] w-[400px] h-[400px] rounded-full border border-dashed border-usm-orange/[0.07]" />
        </div>

        <div className="container mx-auto max-w-6xl relative z-10">
          <div ref={studentsHeaderRef} className="mb-14 text-center max-w-3xl mx-auto">
            <div className="mb-5 flex justify-center">
              <span className="section-badge bg-usm-blue/10 text-usm-blue border border-usm-blue/20">
                <GraduationCap className="h-4 w-4" />
                Para Estudiantes
              </span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-usm-navy md:text-5xl gradient-underline">
              Funcionalidades para Estudiantes
            </h2>
            <p className="mt-6 text-base sm:text-lg text-gray-500 leading-relaxed">
              Herramientas pensadas para la gestión y evaluación del Trabajo
              Especial de Grado.
            </p>
          </div>
          <div
            ref={studentsCardsRef}
            className="grid grid-cols-1 gap-6 sm:gap-8 md:grid-cols-2 lg:grid-cols-3 items-stretch"
          >
            <FeatureCard
              title="Entregas y Plazos"
              icon={<ClipboardCheck size={24} />}
              accentColor="usm-blue"
            >
              Mantén un registro de entregas y plazos del TEG. Visualiza fechas
              límite y el estado de tus entregas.
            </FeatureCard>
            <FeatureCard
              title="Colaboración Fluida"
              icon={<Users size={24} />}
              accentColor="usm-blue"
            >
              Comunícate con tutores y compañeros, comparte archivos y coordina
              revisiones de forma centralizada.
            </FeatureCard>
            <FeatureCard
              title="Recursos Centralizados"
              icon={<BookOpen size={24} />}
              accentColor="usm-blue"
            >
              Accede a guías, plantillas y material de soporte para la
              elaboración y defensa del TEG en un solo lugar.
            </FeatureCard>
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="relative w-full px-4">
        <div className="container mx-auto max-w-4xl">
          <div
            ref={dividerRef}
            className="h-px bg-gradient-to-r from-transparent via-slate-300 to-transparent"
            style={{ transformOrigin: "center" }}
          />
        </div>
      </div>

      {/* Teachers Section */}
      <div className="relative bg-gradient-to-b from-slate-50 via-white to-slate-100 overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute top-0 left-0 w-full h-[60%] bg-gradient-to-br from-usm-orange/[0.05] via-transparent to-transparent" />
          <div className="absolute bottom-0 right-0 w-full h-[50%] bg-gradient-to-tl from-usm-blue/[0.04] via-transparent to-transparent" />
          <div className="hidden md:block absolute top-[10%] left-[5%] w-[350px] h-[350px] rounded-full border border-dashed border-usm-orange/[0.08]" />
          <div className="hidden md:block absolute bottom-[8%] right-[5%] w-[380px] h-[380px] rounded-full border border-dashed border-usm-blue/[0.07]" />
        </div>

        <section
          ref={teachersSectionRef}
          className="relative container mx-auto max-w-6xl py-20 md:py-28 px-4"
          aria-labelledby="teachers-heading"
        >
          <div ref={teachersHeaderRef} className="mb-14 text-center max-w-3xl mx-auto">
            <div className="mb-5 flex justify-center">
              <span className="section-badge bg-usm-orange/10 text-usm-orange border border-usm-orange/20">
                <Briefcase className="h-4 w-4" />
                Para Docentes
              </span>
            </div>
            <h2
              id="teachers-heading"
              className="text-3xl sm:text-4xl font-extrabold tracking-tight text-usm-navy md:text-5xl gradient-underline"
            >
              Funcionalidades para Docentes
            </h2>
            <p className="mt-6 text-base sm:text-lg text-gray-500 leading-relaxed">
              Herramientas para la evaluación, gestión de jurados y coordinación
              de defensas.
            </p>
          </div>

          <div
            ref={teachersCardsRef}
            className="grid grid-cols-1 gap-6 sm:gap-8 md:grid-cols-2 lg:grid-cols-3 items-stretch"
          >
            <FeatureCard
              title="Gestión de Jurados"
              icon={<UserCheck size={24} />}
              accentColor="usm-orange"
            >
              Organiza jurados, asigna evaluadores y gestiona convocatorias de
              defensa de manera sencilla y eficiente.
            </FeatureCard>
            <FeatureCard
              title="Evaluación con Rúbricas"
              icon={<FileText size={24} />}
              accentColor="usm-orange"
            >
              Define rúbricas personalizadas, registra calificaciones y
              proporciona retroalimentación estructurada.
            </FeatureCard>
            <FeatureCard
              title="Calendario de Defensas"
              icon={<Calendar size={24} />}
              accentColor="usm-orange"
            >
              Programa fechas de defensa, sincroniza eventos y notifica a
              estudiantes y jurados automáticamente.
            </FeatureCard>
          </div>
        </section>
      </div>
    </>
  );
}
