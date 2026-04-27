"use client";

import React from "react";
import { YESNO_OPTIONS } from "@features/evaluations/lib/questions/questions";

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
    <div className="inp-seg v-yesno">
      {YESNO_OPTIONS.map((opt) => {
        const active = value === opt.value;
        const isYes = opt.value === 2;
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
            className={active ? (isYes ? "active success" : "active danger") : ""}
            aria-pressed={active}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
