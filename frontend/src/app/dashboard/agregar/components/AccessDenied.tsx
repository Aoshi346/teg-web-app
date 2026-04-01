"use client";

import React from "react";
import { ShieldOff, ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function AccessDenied() {
  const router = useRouter();

  return (
    <div className="max-w-lg mx-auto py-16 text-center animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mx-auto w-20 h-20 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center mb-6">
        <ShieldOff className="w-10 h-10 text-amber-500" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        Acceso restringido
      </h2>
      <p className="text-gray-500 mb-8 max-w-sm mx-auto leading-relaxed">
        Los tutores y jurados no pueden registrar documentos académicos.
        Si necesitas crear un documento, solicita acceso de administrador.
      </p>
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-gray-700 bg-white border border-gray-200 hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm"
      >
        <ArrowLeft className="w-4 h-4" />
        Volver
      </button>
    </div>
  );
}
