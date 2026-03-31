// src/components/landing/FeaturesSection.tsx

"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import SplitType from "split-type";
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

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

export default function FeaturesSection() {
  const studentsSectionRef = useRef<HTMLElement>(null);
  const studentsHeaderRef = useRef<HTMLDivElement>(null);
  const studentsCardsRef = useRef<HTMLDivElement>(null);
  const teachersSectionRef = useRef<HTMLElement>(null);
  const teachersHeaderRef = useRef<HTMLDivElement>(null);
  const teachersCardsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // track SplitType instances so we can revert them on unmount
    const splitInstances: Array<{ revert?: () => void }> = [];
    // Use gsap.context and matchMedia so animations are scoped and responsive
    const ctx = gsap.context(() => {
      const mm = gsap.matchMedia();

      // Desktop/tablet: cards slide from sides
      mm.add("(min-width: 768px)", () => {
        if (
          studentsSectionRef.current &&
          studentsHeaderRef.current &&
          studentsCardsRef.current
        ) {
          const studentsCards = studentsCardsRef.current.children;
          // header elements
          const studentsH2 = studentsHeaderRef.current.querySelector(
            "h2",
          ) as HTMLElement | null;
          const studentsP = studentsHeaderRef.current.querySelector(
            "p",
          ) as HTMLElement | null;
          const studentsBadge = studentsHeaderRef.current.querySelector(
            ".section-badge",
          ) as HTMLElement | null;

          // keep the header container visible; we'll animate the title/paragraph children
          gsap.set(studentsHeaderRef.current, { opacity: 1 });
          gsap.set(studentsCards, {
            opacity: 0,
            x: -140,
            scale: 0.94,
            rotate: -1,
          });
          const tl = gsap.timeline({
            scrollTrigger: {
              trigger: studentsSectionRef.current,
              start: "top 85%",
              toggleActions: "play none none none",
            },
          });

          // Badge fade in
          if (studentsBadge) {
            gsap.set(studentsBadge, { autoAlpha: 0, y: 10, scale: 0.9 });
            tl.to(
              studentsBadge,
              {
                autoAlpha: 1,
                y: 0,
                scale: 1,
                duration: 0.5,
                ease: "power3.out",
              },
              0,
            );
          }

          // Word-based reveal using SplitType (switched from chars to avoid word-break bugs)
          if (studentsH2) {
            const titleSplit = new SplitType(studentsH2, {
              types: "words",
              tagName: "span",
            });
            splitInstances.push(titleSplit);
            const words = titleSplit.words as HTMLElement[];
            gsap.set(words, { autoAlpha: 0, y: 14, display: "inline-block" });
            tl.to(
              words,
              {
                autoAlpha: 1,
                y: 0,
                duration: 0.7,
                stagger: 0.04,
                ease: "power3.out",
              },
              0.15,
            );
          } else {
            tl.to(
              studentsHeaderRef.current,
              { opacity: 1, y: 0, scale: 1, duration: 1.0, ease: "power3.out" },
              0,
            );
          }

          // reveal paragraph slightly after
          if (studentsP)
            tl.to(
              studentsP,
              { autoAlpha: 1, y: 0, duration: 0.6, ease: "power2.out" },
              "+=0.05",
            );

          tl.to(
            studentsCards,
            {
              opacity: 1,
              x: 0,
              scale: 1,
              rotate: 0,
              duration: 0.9,
              stagger: 0.16,
              ease: "power4.out",
            },
            "-=0.4",
          );
        }

        if (
          teachersSectionRef.current &&
          teachersHeaderRef.current &&
          teachersCardsRef.current
        ) {
          const teachersCards = teachersCardsRef.current.children;
          const teachersH2 = teachersHeaderRef.current.querySelector(
            "h2",
          ) as HTMLElement | null;
          const teachersP = teachersHeaderRef.current.querySelector(
            "p",
          ) as HTMLElement | null;
          const teachersBadge = teachersHeaderRef.current.querySelector(
            ".section-badge",
          ) as HTMLElement | null;

          // keep the header container visible; animate title/paragraph children instead
          gsap.set(teachersHeaderRef.current, { opacity: 1 });
          gsap.set(teachersCards, {
            opacity: 0,
            x: 140,
            scale: 0.94,
            rotate: 1,
          });

          const tl2 = gsap.timeline({
            scrollTrigger: {
              trigger: teachersSectionRef.current,
              start: "top 85%",
              toggleActions: "play none none none",
            },
          });

          // Badge fade in
          if (teachersBadge) {
            gsap.set(teachersBadge, { autoAlpha: 0, y: 10, scale: 0.9 });
            tl2.to(
              teachersBadge,
              {
                autoAlpha: 1,
                y: 0,
                scale: 1,
                duration: 0.5,
                ease: "power3.out",
              },
              0,
            );
          }

          if (teachersH2) {
            const titleSplit = new SplitType(teachersH2, {
              types: "words",
              tagName: "span",
            });
            splitInstances.push(titleSplit);
            const words = titleSplit.words as HTMLElement[];
            gsap.set(words, { autoAlpha: 0, y: 14, display: "inline-block" });
            tl2.to(
              words,
              {
                autoAlpha: 1,
                y: 0,
                duration: 0.7,
                stagger: 0.04,
                ease: "power3.out",
              },
              0.15,
            );
          } else {
            tl2.to(
              teachersHeaderRef.current,
              { opacity: 1, y: 0, scale: 1, duration: 1.0, ease: "power3.out" },
              0,
            );
          }

          if (teachersP)
            tl2.to(
              teachersP,
              { autoAlpha: 1, y: 0, duration: 0.6, ease: "power2.out" },
              "+=0.05",
            );

          tl2.to(
            teachersCards,
            {
              opacity: 1,
              x: 0,
              scale: 1,
              rotate: 0,
              duration: 0.9,
              stagger: 0.14,
              ease: "power4.out",
            },
            "-=0.4",
          );
        }
      });

      // Mobile: cards slide up from bottom with gentler motion
      mm.add("(max-width: 767px)", () => {
        if (
          studentsSectionRef.current &&
          studentsHeaderRef.current &&
          studentsCardsRef.current
        ) {
          const studentsCards = studentsCardsRef.current.children;
          // keep the header container visible for scramble reveal; animate children
          gsap.set(studentsHeaderRef.current, { opacity: 1 });
          gsap.set(studentsCards, { opacity: 0, y: 40, scale: 0.98 });

          gsap
            .timeline({
              scrollTrigger: {
                trigger: studentsSectionRef.current,
                start: "top 90%",
                toggleActions: "play none none none",
              },
            })
            .to(studentsHeaderRef.current, {
              opacity: 1,
              y: 0,
              duration: 0.8,
              ease: "power3.out",
            })
            .to(
              studentsCards,
              {
                opacity: 1,
                y: 0,
                scale: 1,
                duration: 0.8,
                stagger: 0.14,
                ease: "power3.out",
              },
              "-=0.4",
            );
        }

        if (
          teachersSectionRef.current &&
          teachersHeaderRef.current &&
          teachersCardsRef.current
        ) {
          const teachersCards = teachersCardsRef.current.children;
          // keep the header container visible for scramble reveal; animate children
          gsap.set(teachersHeaderRef.current, { opacity: 1 });
          gsap.set(teachersCards, { opacity: 0, y: 40, scale: 0.98 });

          gsap
            .timeline({
              scrollTrigger: {
                trigger: teachersSectionRef.current,
                start: "top 90%",
                toggleActions: "play none none none",
              },
            })
            .to(teachersHeaderRef.current, {
              opacity: 1,
              y: 0,
              duration: 0.8,
              ease: "power3.out",
            })
            .to(
              teachersCards,
              {
                opacity: 1,
                y: 0,
                scale: 1,
                duration: 0.8,
                stagger: 0.14,
                ease: "power3.out",
              },
              "-=0.4",
            );
        }
      });

      // Return mm cleanup
      return () => mm.revert();
    }, studentsSectionRef);

    return () => {
      // revert SplitType instances
      try {
        splitInstances.forEach(
          (s) => s && typeof s.revert === "function" && s.revert(),
        );
      } catch {
        // ignore
      }
      ctx.revert();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, []);

  return (
    <>
      {/* Students Section */}
      <section
        id="features"
        ref={studentsSectionRef}
        className="relative w-full bg-gradient-to-b from-slate-50 via-white to-slate-50 py-24 md:py-32 px-4 overflow-hidden"
      >
        {/* Organic flowing background */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          {/* Large soft gradient washes */}
          <div className="absolute top-0 right-0 w-full h-[60%] bg-gradient-to-bl from-usm-blue/[0.07] via-transparent to-transparent" />
          <div className="absolute bottom-0 left-0 w-full h-[50%] bg-gradient-to-tr from-usm-orange/[0.05] via-transparent to-transparent" />
          
          {/* Organic blob shapes via SVG */}
          <svg className="absolute top-[-5%] right-[-10%] w-[500px] h-[500px] md:w-[800px] md:h-[800px] text-usm-blue/[0.06]" viewBox="0 0 200 200" fill="currentColor">
            <path d="M44.7,-76.4C58.8,-69.2,71.8,-59.1,79.6,-45.8C87.4,-32.5,90,-16.3,88.5,-0.9C87,14.5,81.4,29,72.4,40.8C63.4,52.6,51,61.7,37.5,69.2C24,76.7,9.4,82.5,-4.1,88.6C-17.6,94.7,-35.2,101.1,-48.7,96.1C-62.2,91.1,-71.6,74.7,-78.4,57.9C-85.2,41.1,-89.4,23.9,-89.8,-0.2C-90.1,-24.4,-86.6,-48.8,-73.8,-63.2C-61,-77.5,-38.9,-81.8,-21.2,-76.3C-3.5,-70.9,10.9,-55.6,24.7,-55.6C38.5,-55.6,51.7,-70.9,44.7,-76.4Z" transform="translate(100 100) scale(1.1)" />
          </svg>
          
          <svg className="absolute bottom-[-8%] left-[-8%] w-[400px] h-[400px] md:w-[700px] md:h-[700px] text-usm-orange/[0.05]" viewBox="0 0 200 200" fill="currentColor">
            <path d="M39.9,-65.7C52.8,-59.5,65,-51.2,73.4,-39.3C81.9,-27.3,86.7,-11.7,85.3,3.2C83.9,18.1,76.3,32.3,66.2,43.9C56.1,55.5,43.5,64.5,29.7,70.6C15.9,76.7,0.9,79.9,-14.6,79.1C-30.1,78.3,-46.1,73.5,-57.3,63.1C-68.5,52.7,-74.9,36.7,-79.2,20.1C-83.5,3.5,-85.7,-13.7,-81,-29.1C-76.3,-44.5,-64.7,-58.1,-50.5,-63.8C-36.3,-69.5,-19.5,-67.3,-2.8,-62.6C13.9,-57.9,27,-71.9,39.9,-65.7Z" transform="translate(100 100) scale(1.2)" />
          </svg>
          
          {/* Soft concentric dashed rings */}
          <div className="hidden md:block absolute top-[10%] right-[5%] w-[400px] h-[400px] rounded-full border border-dashed border-usm-blue/[0.12]" />
          <div className="hidden md:block absolute top-[14%] right-[8%] w-[300px] h-[300px] rounded-full border border-dashed border-usm-blue/[0.08]" />
          
          <div className="hidden md:block absolute bottom-[8%] left-[3%] w-[450px] h-[450px] rounded-full border border-dashed border-usm-orange/[0.10]" />
          <div className="hidden md:block absolute bottom-[12%] left-[7%] w-[320px] h-[320px] rounded-full border border-dashed border-usm-orange/[0.07]" />
        </div>

        <div className="container mx-auto max-w-6xl relative z-10">
          <div
            ref={studentsHeaderRef}
            className="mb-16 text-center max-w-3xl mx-auto"
          >
            {/* Section Badge */}
            <div className="mb-6 flex justify-center">
              <span className="section-badge bg-usm-blue/10 text-usm-blue border border-usm-blue/20">
                <GraduationCap className="h-4 w-4" />
                Para Estudiantes
              </span>
            </div>
            <h2 className="text-4xl font-extrabold tracking-tight text-usm-navy md:text-5xl gradient-underline" style={{ whiteSpace: "normal", wordBreak: "normal", overflowWrap: "normal" }}>
              Funcionalidades para Estudiantes
            </h2>
            <p className="mt-8 text-lg text-gray-500 leading-relaxed">
              Herramientas pensadas para la gestión y evaluación del Trabajo
              Especial de Grado.
            </p>
          </div>
          <div
            ref={studentsCardsRef}
            className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3 items-stretch"
          >
          <FeatureCard
            title="Entregas y Plazos"
            icon={<ClipboardCheck size={28} />}
            accentColor="usm-blue"
          >
            Mantén un registro de entregas y plazos del TEG. Visualiza fechas
            límite y el estado de tus entregas.
          </FeatureCard>
          <FeatureCard title="Colaboración Fluida" icon={<Users size={28} />} accentColor="usm-blue">
            Comunícate con tutores y compañeros, comparte archivos y coordina
            revisiones de forma centralizada.
          </FeatureCard>
          <FeatureCard
            title="Recursos Centralizados"
            icon={<BookOpen size={28} />}
            accentColor="usm-blue"
          >
            Accede a guías, plantillas y material de soporte para la elaboración
            y defensa del TEG en un solo lugar.
          </FeatureCard>
          </div>
        </div>
      </section>

      {/* Decorative Divider */}
      <div className="relative w-full px-4">
        <div className="container mx-auto max-w-4xl">
          <div className="h-px bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
        </div>
      </div>

      {/* Teachers Section with gradient background */}
      <div className="relative bg-gradient-to-b from-slate-50 via-white to-slate-100 overflow-hidden">
        {/* Organic flowing background */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          {/* Large soft gradient washes — mirrored */}
          <div className="absolute top-0 left-0 w-full h-[60%] bg-gradient-to-br from-usm-orange/[0.07] via-transparent to-transparent" />
          <div className="absolute bottom-0 right-0 w-full h-[50%] bg-gradient-to-tl from-usm-blue/[0.05] via-transparent to-transparent" />
          
          {/* Organic blob shapes via SVG — mirrored positions */}
          <svg className="absolute top-[-5%] left-[-10%] w-[450px] h-[450px] md:w-[750px] md:h-[750px] text-usm-orange/[0.06]" viewBox="0 0 200 200" fill="currentColor">
            <path d="M47.7,-73.2C62.1,-67.8,74.3,-56.3,81.3,-42.2C88.3,-28.1,90.1,-11.4,87.6,4.1C85.1,19.6,78.3,34,68.7,46.1C59.1,58.2,46.7,68,32.9,74.1C19.1,80.2,3.9,82.6,-11.4,81.1C-26.7,79.6,-42.1,74.2,-54.4,64.4C-66.7,54.6,-75.9,40.4,-80.5,24.8C-85.1,9.2,-85.1,-7.8,-80.2,-22.6C-75.3,-37.4,-65.5,-50,-52.8,-56.8C-40.1,-63.6,-24.5,-64.6,-9.4,-66.4C5.7,-68.2,33.3,-78.6,47.7,-73.2Z" transform="translate(100 100) scale(1.1)" />
          </svg>
          
          <svg className="absolute bottom-[-8%] right-[-8%] w-[380px] h-[380px] md:w-[650px] md:h-[650px] text-usm-blue/[0.05]" viewBox="0 0 200 200" fill="currentColor">
            <path d="M44.7,-76.4C58.8,-69.2,71.8,-59.1,79.6,-45.8C87.4,-32.5,90,-16.3,88.5,-0.9C87,14.5,81.4,29,72.4,40.8C63.4,52.6,51,61.7,37.5,69.2C24,76.7,9.4,82.5,-4.1,88.6C-17.6,94.7,-35.2,101.1,-48.7,96.1C-62.2,91.1,-71.6,74.7,-78.4,57.9C-85.2,41.1,-89.4,23.9,-89.8,-0.2C-90.1,-24.4,-86.6,-48.8,-73.8,-63.2C-61,-77.5,-38.9,-81.8,-21.2,-76.3C-3.5,-70.9,10.9,-55.6,24.7,-55.6C38.5,-55.6,51.7,-70.9,44.7,-76.4Z" transform="translate(100 100) scale(1.15)" />
          </svg>
          
          {/* Soft concentric dashed rings — mirrored */}
          <div className="hidden md:block absolute top-[10%] left-[5%] w-[380px] h-[380px] rounded-full border border-dashed border-usm-orange/[0.12]" />
          <div className="hidden md:block absolute top-[14%] left-[8%] w-[280px] h-[280px] rounded-full border border-dashed border-usm-orange/[0.08]" />
          
          <div className="hidden md:block absolute bottom-[8%] right-[5%] w-[420px] h-[420px] rounded-full border border-dashed border-usm-blue/[0.10]" />
          <div className="hidden md:block absolute bottom-[12%] right-[9%] w-[300px] h-[300px] rounded-full border border-dashed border-usm-blue/[0.07]" />
        </div>
        
        <section
          ref={teachersSectionRef}
          className="relative container mx-auto max-w-6xl py-24 md:py-32 px-4"
          aria-labelledby="teachers-heading"
        >
          <div
            ref={teachersHeaderRef}
            className="mb-16 text-center max-w-3xl mx-auto"
          >
            {/* Section Badge */}
            <div className="mb-6 flex justify-center">
              <span className="section-badge bg-usm-orange/10 text-usm-orange border border-usm-orange/20">
                <Briefcase className="h-4 w-4" />
                Para Docentes
              </span>
            </div>
            <h2
              id="teachers-heading"
              className="text-4xl font-extrabold tracking-tight text-usm-navy md:text-5xl gradient-underline"
              style={{ whiteSpace: "normal", wordBreak: "normal", overflowWrap: "normal" }}
            >
              Funcionalidades para Docentes
            </h2>
            <p className="mt-8 text-lg text-gray-500 leading-relaxed">
              Herramientas para la evaluación, gestión de jurados y coordinación
              de defensas.
            </p>
          </div>

          <div
            ref={teachersCardsRef}
            className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3 items-stretch"
          >
            <FeatureCard
              title="Gestión de Jurados"
              icon={<UserCheck size={28} />}
              accentColor="usm-orange"
            >
              Organiza jurados, asigna evaluadores y gestiona convocatorias de
              defensa de manera sencilla y eficiente.
            </FeatureCard>

            <FeatureCard
              title="Evaluación con Rúbricas"
              icon={<FileText size={28} />}
              accentColor="usm-orange"
            >
              Define rúbricas personalizadas, registra calificaciones y
              proporciona retroalimentación estructurada.
            </FeatureCard>

            <FeatureCard
              title="Calendario de Defensas"
              icon={<Calendar size={28} />}
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
