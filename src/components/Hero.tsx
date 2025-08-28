"use client";

import React from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ArrowDown } from "lucide-react";

export default function Hero() {
  return (
    <section
      className="relative flex h-[80vh] w-full items-center justify-center bg-cover bg-center text-white"
      style={{
        backgroundImage:
          "url('/usm_hero.jpg')",
      }}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-black/70 to-black/40" />
      <motion.div
        className="relative z-10 flex flex-col items-center px-4 text-center"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, delay: 0.2, ease: "easeOut" }}
      >
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight text-white drop-shadow-lg">
          Sistema de evaluación para el{" "}
          <span className="text-indigo-300">
            Trabajo Especial de Grado (TEG)
          </span>
        </h1>
        <p className="mt-4 max-w-3xl text-base md:text-lg text-slate-200">
          Gestiona, entrega y evalúa los proyectos de grado de forma segura y
          colaborativa. Facilita la comunicación entre estudiantes, tutores y
          jurados, y centraliza calificaciones y comentarios.
        </p>
      </motion.div>
      <motion.div
        className="absolute bottom-10 z-10"
        aria-hidden
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
      >
        <ArrowDown className="h-8 w-8 text-white/70" />
      </motion.div>
    </section>
  );
}
