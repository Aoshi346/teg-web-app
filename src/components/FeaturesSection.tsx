"use client";

import React from "react";
import { motion } from "framer-motion";
import FeatureCard from "@/components/FeatureCard";
import {
  ClipboardCheck,
  Users,
  BookOpen,
  UserCheck,
  FileText,
  Calendar,
} from "lucide-react";

export default function FeaturesSection() {
  return (
    <>
      <motion.section
        className="container mx-auto py-20 md:py-24 px-4 sm:px-6 lg:px-8"
        initial="offscreen"
        whileInView="onscreen"
        viewport={{ once: true, amount: 0.3 }}
        transition={{ staggerChildren: 0.2 }}
      >
        <div className="mb-16 text-center">
          <h2 className="text-4xl font-bold tracking-tight text-gray-900 md:text-5xl">
            Funcionalidades para Estudiantes
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            Herramientas pensadas para la gestión y evaluación del Trabajo
            Especial de Grado.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3 items-stretch">
          <FeatureCard
            title="Entregas y Plazos"
            icon={<ClipboardCheck size={32} />}
            delay={0.1}
          >
            Mantén un registro de entregas y plazos del TEG. Visualiza fechas
            límite y el estado de tus entregas.
          </FeatureCard>
          <FeatureCard
            title="Colaboración"
            icon={<Users size={32} />}
            delay={0.2}
          >
            Comunícate con tutores y compañeros, comparte archivos del proyecto
            y coordina revisiones.
          </FeatureCard>
          <FeatureCard
            title="Recursos y Documentación"
            icon={<BookOpen size={32} />}
            delay={0.3}
          >
            Accede a guías, plantillas y material de soporte para la elaboración
            y defensa del TEG.
          </FeatureCard>
        </div>
      </motion.section>

      {/* Teachers section */}
      <motion.section
        className="container mx-auto py-12 md:py-16 px-4 sm:px-6 lg:px-8 bg-transparent"
        initial="offscreen"
        whileInView="onscreen"
        viewport={{ once: true, amount: 0.25 }}
        transition={{ staggerChildren: 0.15 }}
        aria-labelledby="teachers-heading"
      >
        <div className="mb-12 text-center">
          <h2
            id="teachers-heading"
            className="text-4xl font-bold text-gray-900 md:text-4xl"
          >
            Funcionalidades para Docentes
          </h2>
          <p className="mt-3 text-md text-gray-600 max-w-2xl mx-auto">
            Herramientas para la evaluación, gestión de jurados y coordinación
            de defensas.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3 items-stretch">
          <FeatureCard
            title="Gestión de Jurados"
            icon={<UserCheck size={32} />}
            delay={0.1}
          >
            Organiza jurados, asigna evaluadores y gestiona convocatorias de
            defensa de manera sencilla.
          </FeatureCard>

          <FeatureCard
            title="Evaluación y Rúbricas"
            icon={<FileText size={32} />}
            delay={0.2}
          >
            Define rúbricas, registra calificaciones y proporciona
            retroalimentación estructurada para cada entrega.
          </FeatureCard>

          <FeatureCard
            title="Calendario y Defensas"
            icon={<Calendar size={32} />}
            delay={0.3}
          >
            Programa fechas de defensa, sincroniza eventos y notifica a
            estudiantes y jurados automáticamente.
          </FeatureCard>
        </div>
      </motion.section>
    </>
  );
}
