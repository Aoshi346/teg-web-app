"use client";

import React from "react";
import { QUINTARY_OPTIONS } from "@features/evaluations/lib/questions/questions";

interface QuintaryInputProps {
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
  onFocus?: () => void;
  onAdvance?: () => void;
}

const VARIANT_CLASS: Record<number, string> = {
  1: "danger",
  2: "warning",
  3: "neutral",
  4: "info",
  5: "success",
};

export default function QuintaryInput({
  value,
  onChange,
  disabled,
  onFocus,
  onAdvance,
}: QuintaryInputProps) {
  const handleClick = (v: number) => {
    onChange(v);
    onAdvance?.();
  };

  return (
    <div className="inp-seg v-quintary">
      {QUINTARY_OPTIONS.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            disabled={disabled}
            onFocus={onFocus}
            onClick={() => handleClick(opt.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleClick(opt.value);
              }
            }}
            className={active ? `active ${VARIANT_CLASS[opt.value]}` : ""}
            aria-pressed={active}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
