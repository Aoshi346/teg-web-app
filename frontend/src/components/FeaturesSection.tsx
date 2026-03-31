// src/components/FeaturesSection.tsx

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
        if (studentsSectionRef.current && studentsHeaderRef.current && studentsCardsRef.current) {
          const studentsCards = studentsCardsRef.current.children;
          // header elements
          const studentsH2 = studentsHeaderRef.current.querySelector('h2') as HTMLElement | null;
          const studentsP = studentsHeaderRef.current.querySelector('p') as HTMLElement | null;

          // keep the header container visible; we'll animate the title/paragraph children
          gsap.set(studentsHeaderRef.current, { opacity: 1 });
          gsap.set(studentsCards, { opacity: 0, x: -140, scale: 0.94, rotate: -1 });
          const tl = gsap.timeline({
            scrollTrigger: {
              trigger: studentsSectionRef.current,
              start: 'top 85%',
              toggleActions: 'play none none none'
            }
          });

          // Character-based reveal using SplitType
          if (studentsH2) {
            // split by characters to create a per-char stagger
            const titleSplit = new SplitType(studentsH2, { types: 'chars', tagName: 'span' });
            splitInstances.push(titleSplit);
            const chars = titleSplit.chars as HTMLElement[];
            gsap.set(chars, { autoAlpha: 0, y: 14, display: 'inline-block' });
            tl.to(chars, { autoAlpha: 1, y: 0, duration: 0.7, stagger: 0.02, ease: 'power3.out' }, 0);
          } else {
            tl.to(studentsHeaderRef.current, { opacity: 1, y: 0, scale: 1, duration: 1.0, ease: 'power3.out' }, 0);
          }

          // reveal paragraph slightly after
          if (studentsP) tl.to(studentsP, { autoAlpha: 1, y: 0, duration: 0.6, ease: 'power2.out' }, '+=0.05');

          tl.to(studentsCards, { opacity: 1, x: 0, scale: 1, rotate: 0, duration: 0.9, stagger: 0.16, ease: 'power3.out' }, '-=0.4');
        }

        if (teachersSectionRef.current && teachersHeaderRef.current && teachersCardsRef.current) {
          const teachersCards = teachersCardsRef.current.children;
          const teachersH2 = teachersHeaderRef.current.querySelector('h2') as HTMLElement | null;
          const teachersP = teachersHeaderRef.current.querySelector('p') as HTMLElement | null;

          // keep the header container visible; animate title/paragraph children instead
          gsap.set(teachersHeaderRef.current, { opacity: 1 });
          gsap.set(teachersCards, { opacity: 0, x: 140, scale: 0.94, rotate: 1 });

          const tl2 = gsap.timeline({
            scrollTrigger: {
              trigger: teachersSectionRef.current,
              start: 'top 85%',
              toggleActions: 'play none none none'
            }
          });

          if (teachersH2) {
            const titleSplit = new SplitType(teachersH2, { types: 'chars', tagName: 'span' });
            splitInstances.push(titleSplit);
            const chars = titleSplit.chars as HTMLElement[];
            gsap.set(chars, { autoAlpha: 0, y: 14, display: 'inline-block' });
            tl2.to(chars, { autoAlpha: 1, y: 0, duration: 0.7, stagger: 0.02, ease: 'power3.out' }, 0);
          } else {
            tl2.to(teachersHeaderRef.current, { opacity: 1, y: 0, scale: 1, duration: 1.0, ease: 'power3.out' }, 0);
          }

          if (teachersP) tl2.to(teachersP, { autoAlpha: 1, y: 0, duration: 0.6, ease: 'power2.out' }, '+=0.05');

          tl2.to(teachersCards, { opacity: 1, x: 0, scale: 1, rotate: 0, duration: 0.9, stagger: 0.16, ease: 'power3.out' }, '-=0.4');
        }
      });

      // Mobile: cards slide up from bottom with gentler motion
      mm.add("(max-width: 767px)", () => {
        if (studentsSectionRef.current && studentsHeaderRef.current && studentsCardsRef.current) {
          const studentsCards = studentsCardsRef.current.children;
          // keep the header container visible for scramble reveal; animate children
          gsap.set(studentsHeaderRef.current, { opacity: 1 });
          gsap.set(studentsCards, { opacity: 0, y: 40, scale: 0.98 });

          gsap.timeline({
            scrollTrigger: {
              trigger: studentsSectionRef.current,
              start: 'top 90%',
              toggleActions: 'play none none none'
            }
          })
          .to(studentsHeaderRef.current, { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' })
          .to(studentsCards, { opacity: 1, y: 0, scale: 1, duration: 0.8, stagger: 0.14, ease: 'power3.out' }, '-=0.4');
        }

        if (teachersSectionRef.current && teachersHeaderRef.current && teachersCardsRef.current) {
          const teachersCards = teachersCardsRef.current.children;
          // keep the header container visible for scramble reveal; animate children
          gsap.set(teachersHeaderRef.current, { opacity: 1 });
          gsap.set(teachersCards, { opacity: 0, y: 40, scale: 0.98 });

          gsap.timeline({
            scrollTrigger: {
              trigger: teachersSectionRef.current,
              start: 'top 90%',
              toggleActions: 'play none none none'
            }
          })
          .to(teachersHeaderRef.current, { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' })
          .to(teachersCards, { opacity: 1, y: 0, scale: 1, duration: 0.8, stagger: 0.14, ease: 'power3.out' }, '-=0.4');
        }
      });

      // Return mm cleanup
      return () => mm.revert();
    }, studentsSectionRef);

    return () => {
      // revert SplitType instances
      try {
        splitInstances.forEach((s) => s && typeof s.revert === 'function' && s.revert());
      } catch {
        // ignore
      }
      ctx.revert();
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    };
  }, []);

  return (
    <>
      {/* Students Section */}
      <section
        id="features"
        ref={studentsSectionRef}
        className="container mx-auto py-24 md:py-32 px-4"
      >
        <div
          ref={studentsHeaderRef}
          className="mb-16 text-center max-w-3xl mx-auto"
        >
          <h2 className="text-4xl font-extrabold tracking-tight text-gray-900 md:text-5xl">
            Funcionalidades para Estudiantes
          </h2>
          <p className="mt-5 text-lg text-gray-600">
            Herramientas pensadas para la gestión y evaluación del Trabajo
            Especial de Grado.
          </p>
        </div>
        <div ref={studentsCardsRef} className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3 items-stretch">
          <FeatureCard
            title="Entregas y Plazos"
            icon={<ClipboardCheck size={32} />}
          >
            Mantén un registro de entregas y plazos del TEG. Visualiza fechas
            límite y el estado de tus entregas.
          </FeatureCard>
          <FeatureCard
            title="Colaboración Fluida"
            icon={<Users size={32} />}
          >
            Comunícate con tutores y compañeros, comparte archivos y coordina
            revisiones de forma centralizada.
          </FeatureCard>
          <FeatureCard
            title="Recursos Centralizados"
            icon={<BookOpen size={32} />}
          >
            Accede a guías, plantillas y material de soporte para la elaboración
            y defensa del TEG en un solo lugar.
          </FeatureCard>
        </div>
      </section>

      {/* Teachers Section Wrapper */}
      <div className="bg-slate-50/70 border-t border-slate-200">
        <section
          ref={teachersSectionRef}
          className="container mx-auto py-24 md:py-32 px-4"
          aria-labelledby="teachers-heading"
        >
          <div
            ref={teachersHeaderRef}
            className="mb-16 text-center max-w-3xl mx-auto"
          >
            <h2
              id="teachers-heading"
              className="text-4xl font-extrabold tracking-tight text-gray-900 md:text-5xl"
            >
              Funcionalidades para Docentes
            </h2>
            <p className="mt-5 text-lg text-gray-600">
              Herramientas para la evaluación, gestión de jurados y coordinación
              de defensas.
            </p>
          </div>

          <div ref={teachersCardsRef} className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3 items-stretch">
            <FeatureCard
              title="Gestión de Jurados"
              icon={<UserCheck size={32} />}
            >
              Organiza jurados, asigna evaluadores y gestiona convocatorias de
              defensa de manera sencilla y eficiente.
            </FeatureCard>

            <FeatureCard
              title="Evaluación con Rúbricas"
              icon={<FileText size={32} />}
            >
              Define rúbricas personalizadas, registra calificaciones y
              proporciona retroalimentación estructurada.
            </FeatureCard>

            <FeatureCard
              title="Calendario de Defensas"
              icon={<Calendar size={32} />}
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
