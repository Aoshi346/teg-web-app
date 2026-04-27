"use client";

import React from "react";
import { TERNARY_DEFENSE_OPTIONS } from "@features/evaluations/lib/questions/questions";

interface TernaryDefenseInputProps {
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
  onFocus?: () => void;
  onAdvance?: () => void;
}

const VARIANT_CLASS: Record<number, string> = {
  1: "danger",
  2: "warning",
  3: "success",
};

export default function TernaryDefenseInput({
  value,
  onChange,
  disabled,
  onFocus,
  onAdvance,
}: TernaryDefenseInputProps) {
  const handleClick = (v: number) => {
    onChange(v);
    onAdvance?.();
  };

  return (
    <div className="inp-seg v-defense">
      {TERNARY_DEFENSE_OPTIONS.map((opt) => {
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
