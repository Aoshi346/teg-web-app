// src/app/Hero.tsx

"use client";

import React from "react";
import { motion, Variants } from "framer-motion";
import { ArrowDown } from "lucide-react";

// Animation variants for the container to orchestrate children animations
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.3, // Time delay between each child animating in
    },
  },
};

// Animation variants for the text elements
const itemVariants: Variants = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.8,
      // Use an easing array (cubic-bezier) to satisfy the Typescript types
      ease: [0.22, 1, 0.36, 1],
    },
  },
};

export default function Hero() {
  return (
    <section className="relative h-[90vh] w-full flex items-center justify-center text-white overflow-hidden">
      {/* Background Image with Ken Burns Effect */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        aria-hidden
        animate={{ scale: [1, 1.05, 1] }}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: [0.42, 0, 0.58, 1],
        }}
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
        style={{ zIndex: 1 }}               // overlay sits above bg but below content
      />

      {/* Content Container */}
      <motion.div
        className="relative z-20 flex flex-col items-center px-4 text-center" // higher z to ensure visibility
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.h1
          className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight text-white"
          style={{ textShadow: "0px 4px 12px rgba(0, 0, 0, 0.5)" }}
          variants={itemVariants}
        >
          Sistema de evaluación para el{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-blue-700">
            Trabajo Especial de Grado (TEG)
          </span>
        </motion.h1>

        <motion.p
          className="mt-6 max-w-3xl text-lg md:text-xl text-slate-200"
          style={{ textShadow: "0px 2px 8px rgba(0, 0, 0, 0.5)" }}
          variants={itemVariants}
        >
          Gestiona, entrega y evalúa los proyectos de grado de forma segura y
          colaborativa. Facilita la comunicación entre estudiantes, tutores y
          jurados, y centraliza calificaciones y comentarios.
        </motion.p>
      </motion.div>

      {/* Bouncing Arrow Indicator */}
      <motion.div
        className="absolute bottom-10 z-20"
        aria-hidden
        animate={{ y: [0, 15, 0] }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: [0.42, 0, 0.58, 1],
        }}
      >
        <ArrowDown className="h-10 w-10 text-white/70" />
      </motion.div>
    </section>
  );
}