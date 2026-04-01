"use client";

import React from "react";
import { FileText, BookOpen, CheckCircle } from "lucide-react";

type DocType = "proyecto" | "tesis";

interface DocumentTypeSelectorProps {
  value: DocType;
  onChange: (type: DocType) => void;
  allowedTypes: readonly DocType[];
  disabled?: boolean;
}

const TYPE_CONFIG = {
  proyecto: {
    Icon: FileText,
    label: "Proyecto (PTEG)",
    description: "9no Semestre",
    tooltip: "Propuesta inicial del TEG",
    activeColor: "blue",
    border: "border-blue-500",
    shadow: "shadow-blue-500/20",
    bg: "bg-blue-100 text-blue-600 ring-blue-200",
    bgHover: "hover:bg-blue-50 hover:text-blue-600 hover:ring-blue-100",
    borderHover: "hover:border-blue-200",
    textActive: "text-blue-900",
    textHover: "group-hover:text-blue-800",
    glow: "bg-blue-400",
    check: "text-blue-500",
  },
  tesis: {
    Icon: BookOpen,
    label: "Trabajo Especial (TEG)",
    description: "10mo Semestre",
    tooltip: "Proyecto final completo",
    activeColor: "emerald",
    border: "border-emerald-500",
    shadow: "shadow-emerald-500/20",
    bg: "bg-emerald-100 text-emerald-600 ring-emerald-200",
    bgHover: "hover:bg-emerald-50 hover:text-emerald-600 hover:ring-emerald-100",
    borderHover: "hover:border-emerald-200",
    textActive: "text-emerald-900",
    textHover: "group-hover:text-emerald-800",
    glow: "bg-emerald-400",
    check: "text-emerald-500",
  },
} as const;

export default function DocumentTypeSelector({
  value,
  onChange,
  allowedTypes,
  disabled,
}: DocumentTypeSelectorProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
        {disabled ? "Documento asignado" : "Tipo de Documento"}
      </h3>

      {/* Horizontal on mobile, vertical on lg */}
      <div className="flex flex-row lg:flex-col gap-3">
        {allowedTypes.map((type) => {
          const cfg = TYPE_CONFIG[type];
          const isActive = value === type;
          const { Icon } = cfg;

          return (
            <button
              key={type}
              type="button"
              onClick={() => !disabled && onChange(type)}
              disabled={disabled}
              className={`relative flex-1 lg:flex-none w-full overflow-hidden flex items-center lg:items-start gap-3 lg:gap-0 lg:flex-col p-4 lg:p-5 rounded-2xl border-2 transition-all duration-300 group ${
                isActive
                  ? `${cfg.border} bg-white shadow-2xl ${cfg.shadow} scale-[1.02] lg:scale-[1.04]`
                  : `border-transparent bg-white shadow-sm hover:shadow-xl ${cfg.borderHover} hover:scale-[1.01] lg:hover:scale-[1.02]`
              } ${disabled ? "cursor-default" : "cursor-pointer"}`}
            >
              <div
                className={`p-2.5 lg:p-3 rounded-xl transition-all duration-300 flex-shrink-0 ${
                  isActive
                    ? `${cfg.bg} ring-2`
                    : `bg-gray-100 text-gray-500 ${cfg.bgHover} group-hover:ring-2`
                }`}
              >
                <Icon className="w-5 h-5 lg:w-6 lg:h-6 group-hover:scale-110 transition-transform" />
              </div>

              <div className="text-left lg:mt-3 min-w-0">
                <p
                  className={`font-bold text-sm lg:text-lg transition-colors truncate ${
                    isActive ? cfg.textActive : `text-gray-700 ${cfg.textHover}`
                  }`}
                >
                  {cfg.label}
                </p>
                <p className="text-xs font-medium text-gray-500 mt-0.5 hidden sm:block">
                  {cfg.description}
                </p>
              </div>

              {isActive && (
                <>
                  <div className="absolute top-2 right-2 lg:top-4 lg:right-4 animate-in fade-in duration-300">
                    <CheckCircle className={`w-4 h-4 lg:w-5 lg:h-5 ${cfg.check}`} />
                  </div>
                  <div className={`absolute -bottom-10 -right-10 w-32 h-32 ${cfg.glow} rounded-full blur-3xl opacity-20 pointer-events-none`} />
                </>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
