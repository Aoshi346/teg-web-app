// src/app/Header.tsx

"use client";

import { motion } from "framer-motion";
import { LogIn } from "lucide-react"; // Using lucide-react for a cleaner icon
import React from "react";

export default function Header() {
  return (
    <motion.header
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="sticky top-0 z-50 w-full bg-white/90 backdrop-blur-lg border-b border-slate-200 shadow-sm"
    >
      <div className="container mx-auto flex h-20 items-center justify-between px-4">
        {/* Logo and Brand Name */}
        <motion.a
          href="/"
          className="flex items-center gap-4 no-underline"
          aria-label="EVTEG home"
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="flex-shrink-0 rounded-full bg-white p-1.5 shadow-md transition-shadow duration-300 hover:shadow-lg">
            <img
              src="/usmlogo.png"
              alt="EVTEG logo"
              className="h-12 w-12 object-contain rounded-full"
            />
          </div>

          <div className="flex flex-col leading-tight">
            <span className="text-2xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-blue-500">
              EVTEG
            </span>
            <span className="block text-sm text-gray-500">
              Gestión del Trabajo Especial de Grado
            </span>
          </div>
        </motion.a>

        {/* Action Button */}
        <div className="hidden md:flex items-center">
          <motion.button
            whileHover={{
              scale: 1.05,
              boxShadow: "0 10px 25px -5px rgba(99, 102, 241, 0.4)", // A softer, larger shadow
            }}
            whileTap={{ scale: 0.95 }}
            transition={{ type: "spring", stiffness: 400, damping: 15 }}
            className="inline-flex items-center gap-2.5 rounded-full px-5 py-2.5 text-white text-sm font-semibold
                  bg-gradient-to-r from-indigo-500 to-blue-600 shadow-lg
                  hover:from-indigo-600 hover:to-blue-700
                  focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-300
                  transition-all duration-300"
            aria-label="Ingresar"
            title="Ingresar"
          >
            <LogIn className="h-4 w-4" aria-hidden />
            Ingresar
          </motion.button>
        </div>
      </div>
    </motion.header>
  );
}
