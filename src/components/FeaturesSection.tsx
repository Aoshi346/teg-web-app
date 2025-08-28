"use client";

import React from "react";
import { motion } from "framer-motion";
import FeatureCard from "@/components/FeatureCard";
import { ClipboardCheck, Users, BookOpen } from "lucide-react";

export default function FeaturesSection() {
  return (
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
          Comunícate con tutores y compañeros, comparte archivos del proyecto y
          coordina revisiones.
        </FeatureCard>
        <FeatureCard
          title="Recursos y Documentación"
          icon={<BookOpen size={32} />}
          delay={0.3}
        >
          Accede a guías, plantillas y material de soporte para la elaboración y
          defensa del TEG.
        </FeatureCard>
      </div>
    </motion.section>
  );
}
