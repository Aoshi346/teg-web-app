"use client";

import React from "react";
import { FREQUENCY_OPTIONS } from "@features/evaluations/lib/questions/questions";

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
    <div className="inp-seg">
      {FREQUENCY_OPTIONS.map((opt) => {
        const active = value === opt.value;
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
            className={active ? "active blue" : ""}
            aria-pressed={active}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
