import React from "react";
import { CalendarDays } from "lucide-react";

interface EmptyDayStateProps {
  isAdmin: boolean;
}

export default function EmptyDayState({ isAdmin }: EmptyDayStateProps) {
  return (
    <div className="bg-white/40 backdrop-blur-sm rounded-[2.5rem] border border-dashed border-gray-300 py-20 text-center relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-blue-50/50 rounded-full blur-3xl -z-10" />
      <div className="w-20 h-20 bg-gray-50 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-inner border border-gray-100">
        <CalendarDays className="w-10 h-10 text-gray-300" />
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-2">
        Aún no hay días planificados
      </h3>
      <p className="text-gray-500 font-medium max-w-sm mx-auto">
        {isAdmin
          ? "Selecciona días en el calendario para empezar a programar presentaciones."
          : "Pídele al administrador que planifique los días de presentación del período."}
      </p>
    </div>
  );
}
