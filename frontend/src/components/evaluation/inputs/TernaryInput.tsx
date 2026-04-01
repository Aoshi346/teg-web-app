"use client";

import React from "react";
import {
  TERNARY_OPTIONS,
  TERNARY_NA_OPTIONS,
  TERNARY_INFO_OPTIONS,
} from "@/lib/questions/questions";

type Variant = "ternary" | "ternary_na" | "ternary_info";

interface TernaryInputProps {
  value: number;
  onChange: (value: number) => void;
  variant: Variant;
  onAdvance?: () => void;
}

const COLOR_MAP: Record<number, string> = {
  3: "bg-emerald-500 text-white border-emerald-500 shadow-emerald-500/20",
  2: "bg-amber-500 text-white border-amber-500 shadow-amber-500/20",
  1: "bg-rose-500 text-white border-rose-500 shadow-rose-500/20",
  4: "bg-rose-500 text-white border-rose-500 shadow-rose-500/20",
  5: "bg-blue-500 text-white border-blue-500 shadow-blue-500/20",
};

const OPTIONS_MAP: Record<Variant, typeof TERNARY_OPTIONS> = {
  ternary: TERNARY_OPTIONS,
  ternary_na: TERNARY_NA_OPTIONS,
  ternary_info: TERNARY_INFO_OPTIONS,
};

export default function TernaryInput({
  value,
  onChange,
  variant,
  onAdvance,
}: TernaryInputProps) {
  const options = OPTIONS_MAP[variant];
  const cols = variant === "ternary" ? "grid-cols-3" : "grid-cols-2";

  const handleClick = (v: number) => {
    onChange(v);
    onAdvance?.();
  };

  return (
    <div className={`grid ${cols} gap-2`}>
      {options.map((opt, idx) => {
        const active = value === opt.value;
        const isLastOdd = variant === "ternary_na" && idx === options.length - 1;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => handleClick(opt.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleClick(opt.value);
              }
            }}
            className={`flex items-center justify-center py-2.5 px-3 rounded-lg text-sm font-bold border transition-all active:scale-[0.97] ${
              active
                ? `${COLOR_MAP[opt.value] || COLOR_MAP[1]} shadow-md`
                : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:border-gray-300"
            } ${isLastOdd ? "col-span-2" : ""}`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
