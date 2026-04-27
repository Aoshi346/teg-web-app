"use client";

import React from "react";
import {
  TERNARY_OPTIONS,
  TERNARY_NA_OPTIONS,
  TERNARY_INFO_OPTIONS,
} from "@features/evaluations/lib/questions/questions";

type Variant = "ternary" | "ternary_na" | "ternary_info";

interface TernaryInputProps {
  value: number;
  onChange: (value: number) => void;
  variant: Variant;
  onAdvance?: () => void;
}

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

  const handleClick = (v: number) => {
    onChange(v);
    onAdvance?.();
  };

  return (
    <div className="inp-seg">
      {options.map((opt) => {
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
