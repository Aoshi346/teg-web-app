"use client";

import React from "react";
import { FREQUENCY_OPTIONS } from "@/lib/questions/questions";

interface FrequencyInputProps {
  value: number;
  onChange: (value: number) => void;
  onAdvance?: () => void;
}

export default function FrequencyInput({ value, onChange, onAdvance }: FrequencyInputProps) {
  const handleClick = (v: number) => {
    onChange(v);
    onAdvance?.();
  };

  return (
    <div className="space-y-1.5">
      {FREQUENCY_OPTIONS.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => handleClick(opt.value)}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleClick(opt.value); } }}
            className={`w-full px-3.5 py-2.5 rounded-lg text-sm font-medium border text-left transition-all ${
              active
                ? `${opt.color} shadow-sm ring-1 ring-offset-1 ring-transparent`
                : "bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
