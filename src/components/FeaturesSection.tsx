// src/components/FeaturesSection.tsx

"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import FeatureCard from "@/components/FeatureCard";
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
    // Students section animations
    if (studentsSectionRef.current && studentsHeaderRef.current && studentsCardsRef.current) {
      const studentsCards = studentsCardsRef.current.children;
      
      // Set initial states
      gsap.set(studentsHeaderRef.current, { opacity: 0, y: 60, scale: 0.95 });
      gsap.set(studentsCards, { opacity: 0, x: -120, scale: 0.9 });

      // Create scroll trigger for students section
      ScrollTrigger.create({
        trigger: studentsSectionRef.current,
        start: "top 85%",
        onEnter: () => {
          const tl = gsap.timeline();
          
          // Animate header with slower, more appealing timing
          tl.to(studentsHeaderRef.current, {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 1.2,
            ease: "power3.out"
          })
          // Animate cards from left with slower stagger
          .to(studentsCards, {
            opacity: 1,
            x: 0,
            scale: 1,
            duration: 1.0,
            stagger: 0.3,
            ease: "power3.out"
          }, "-=0.6");
        }
      });
    }

    // Teachers section animations
    if (teachersSectionRef.current && teachersHeaderRef.current && teachersCardsRef.current) {
      const teachersCards = teachersCardsRef.current.children;
      
      // Set initial states
      gsap.set(teachersHeaderRef.current, { opacity: 0, y: 60, scale: 0.95 });
      gsap.set(teachersCards, { opacity: 0, x: 120, scale: 0.9 });

      // Create scroll trigger for teachers section
      ScrollTrigger.create({
        trigger: teachersSectionRef.current,
        start: "top 85%",
        onEnter: () => {
          const tl = gsap.timeline();
          
          // Animate header with slower, more appealing timing
          tl.to(teachersHeaderRef.current, {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 1.2,
            ease: "power3.out"
          })
          // Animate cards from right with slower stagger
          .to(teachersCards, {
            opacity: 1,
            x: 0,
            scale: 1,
            duration: 1.0,
            stagger: 0.3,
            ease: "power3.out"
          }, "-=0.6");
        }
      });
    }

    // Cleanup function
    return () => {
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    };
  }, []);

  return (
    <>
      {/* Students Section */}
      <section
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
