"use client";

import React from "react";
import { QUATERNARY_OPTIONS } from "@features/evaluations/lib/questions/questions";

interface QuaternaryInputProps {
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
  onFocus?: () => void;
  onAdvance?: () => void;
}

const VARIANT_CLASS: Record<number, string> = {
  1: "danger",
  2: "warning",
  3: "info",
  4: "success",
};

export default function QuaternaryInput({
  value,
  onChange,
  disabled,
  onFocus,
  onAdvance,
}: QuaternaryInputProps) {
  const handleClick = (v: number) => {
    onChange(v);
    onAdvance?.();
  };

  return (
    <div className="inp-seg v-quaternary">
      {QUATERNARY_OPTIONS.map((opt) => {
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
