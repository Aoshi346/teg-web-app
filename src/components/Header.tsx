"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import React from "react";

export default function Header() {
  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className="sticky top-0 z-50 w-full bg-white/80 backdrop-blur-md border-b border-slate-200"
    >
      <div className="container mx-auto flex h-20 items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <img src="/usmlogo.png" alt="TEG Logo" width={32} height={32} />
          <span className="text-2xl font-bold text-gray-900 tracking-wide">
            EVTEG
          </span>
        </div>

        <form
          className="hidden items-center space-x-2 md:flex"
          role="search"
          aria-label="Sign in form"
        >
          <Input
            id="username"
            aria-label="username"
            type="text"
            placeholder="Usuario"
            className="w-auto bg-slate-100 border-slate-300 focus:ring-indigo-500"
          />
          <Input
            id="password"
            aria-label="password"
            type="password"
            placeholder="Contraseña"
            className="w-auto bg-slate-100 border-slate-300 focus:ring-indigo-500"
          />
          <Button className="bg-indigo-600 hover:bg-indigo-700 transition-colors duration-300 shadow">
            Ingresar
          </Button>
        </form>
      </div>
    </motion.header>
  );
}
