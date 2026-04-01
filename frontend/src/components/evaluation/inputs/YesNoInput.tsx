"use client";

import React from "react";
import { Check, X } from "lucide-react";
import { YESNO_OPTIONS } from "@/lib/questions/questions";

interface YesNoInputProps {
  value: number;
  onChange: (value: number) => void;
  onAdvance?: () => void;
}

export default function YesNoInput({ value, onChange, onAdvance }: YesNoInputProps) {
  const handleClick = (v: number) => {
    onChange(v);
    onAdvance?.();
  };

  return (
    <div className="grid grid-cols-2 gap-2">
      {YESNO_OPTIONS.map((opt) => {
        const active = value === opt.value;
        const isYes = opt.value === 2;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => handleClick(opt.value)}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleClick(opt.value); } }}
            className={`relative flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-bold border transition-all active:scale-[0.97] ${
              active
                ? isYes
                  ? "bg-emerald-500 text-white border-emerald-500 shadow-md shadow-emerald-500/20"
                  : "bg-rose-500 text-white border-rose-500 shadow-md shadow-rose-500/20"
                : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:border-gray-300"
            }`}
          >
            {active && (isYes ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />)}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
