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
      {/* Wave Separator */}
      <div className="relative w-full h-24 overflow-hidden bg-usm-navy">
        <svg className="absolute bottom-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 1200 120" xmlns="http://www.w3.org/2000/svg">
          <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z" 
                fill="currentColor" className="text-slate-50" />
        </svg>
      </div>
      
      {/* Students Section */}
      <section
        id="features"
        ref={studentsSectionRef}
        className="relative w-full bg-gradient-to-b from-slate-50 to-white py-24 md:py-32 px-4"
      >
        <div className="container mx-auto max-w-6xl">
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
      <div className="relative bg-gradient-to-b from-white via-slate-50 to-slate-100">
        {/* Subtle pattern overlay */}
        <div className="absolute inset-0 opacity-[0.03]">
          <div className="dot-grid" />
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
