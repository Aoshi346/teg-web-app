// src/components/FeaturesSection.tsx

"use client";

import React from "react";
import { motion, Variants } from "framer-motion";
import FeatureCard from "@/components/FeatureCard";
import {
  ClipboardCheck,
  Users,
  BookOpen,
  UserCheck,
  FileText,
  Calendar,
} from "lucide-react";

// Animation variants for the header text (h2 and p)
const headerVariants: Variants = {
  offscreen: {
    y: 30,
    opacity: 0,
  },
  onscreen: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      duration: 0.8,
    },
  },
};

export default function FeaturesSection() {
  return (
    <>
      {/* Students Section */}
      <motion.section
        className="container mx-auto py-24 md:py-32 px-4" // Increased vertical padding
        initial="offscreen"
        whileInView="onscreen"
        viewport={{ once: true, amount: 0.2 }} // Trigger animation slightly earlier
        transition={{ staggerChildren: 0.25 }} // More pronounced stagger
      >
        <motion.div
          className="mb-16 text-center max-w-3xl mx-auto" // Center and constrain width
          variants={headerVariants}
        >
          <h2 className="text-4xl font-extrabold tracking-tight text-gray-900 md:text-5xl">
            Funcionalidades para Estudiantes
          </h2>
          <p className="mt-5 text-lg text-gray-600">
            Herramientas pensadas para la gestión y evaluación del Trabajo
            Especial de Grado.
          </p>
        </motion.div>
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3 items-stretch">
          <FeatureCard
            title="Entregas y Plazos"
            icon={<ClipboardCheck size={32} />}
            delay={0.1}
          >
            Mantén un registro de entregas y plazos del TEG. Visualiza fechas
            límite y el estado de tus entregas.
          </FeatureCard>
          <FeatureCard
            title="Colaboración Fluida"
            icon={<Users size={32} />}
            delay={0.2}
          >
            Comunícate con tutores y compañeros, comparte archivos y coordina
            revisiones de forma centralizada.
          </FeatureCard>
          <FeatureCard
            title="Recursos Centralizados"
            icon={<BookOpen size={32} />}
            delay={0.3}
          >
            Accede a guías, plantillas y material de soporte para la elaboración
            y defensa del TEG en un solo lugar.
          </FeatureCard>
        </div>
      </motion.section>

      {/* Teachers Section Wrapper */}
      <div className="bg-slate-50/70 border-t border-slate-200">
        <motion.section
          className="container mx-auto py-24 md:py-32 px-4"
          initial="offscreen"
          whileInView="onscreen"
          viewport={{ once: true, amount: 0.2 }}
          transition={{ staggerChildren: 0.25 }}
          aria-labelledby="teachers-heading"
        >
          <motion.div
            className="mb-16 text-center max-w-3xl mx-auto"
            variants={headerVariants}
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
          </motion.div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3 items-stretch">
            <FeatureCard
              title="Gestión de Jurados"
              icon={<UserCheck size={32} />}
              delay={0.1}
            >
              Organiza jurados, asigna evaluadores y gestiona convocatorias de
              defensa de manera sencilla y eficiente.
            </FeatureCard>

            <FeatureCard
              title="Evaluación con Rúbricas"
              icon={<FileText size={32} />}
              delay={0.2}
            >
              Define rúbricas personalizadas, registra calificaciones y
              proporciona retroalimentación estructurada.
            </FeatureCard>

            <FeatureCard
              title="Calendario de Defensas"
              icon={<Calendar size={32} />}
              delay={0.3}
            >
              Programa fechas de defensa, sincroniza eventos y notifica a
              estudiantes y jurados automáticamente.
            </FeatureCard>
          </div>
        </motion.section>
      </div>
    </>
  );
}
