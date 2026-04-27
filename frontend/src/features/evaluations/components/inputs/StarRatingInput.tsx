"use client";

import React from "react";

interface StarRatingInputProps {
  value: number;
  onChange: (value: number) => void;
  onAdvance?: () => void;
}

export default function StarRatingInput({ value, onChange, onAdvance }: StarRatingInputProps) {
  const handleClick = (v: number) => {
    onChange(v);
    onAdvance?.();
  };

  return (
    <div className="inp-stars">
      {Array.from({ length: 5 }, (_, i) => {
        const val = i + 1;
        const active = value === val;
        return (
          <button
            key={val}
            type="button"
            onClick={() => handleClick(val)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleClick(val);
              }
            }}
            aria-label={`Puntuación ${val}`}
            aria-pressed={active}
            className={active ? "active yellow" : ""}
          >
            {val}
          </button>
        );
      })}
    </div>
  );
}
