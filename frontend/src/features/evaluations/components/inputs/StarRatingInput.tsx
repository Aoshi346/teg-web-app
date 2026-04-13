"use client";

import React from "react";

const PALETTE = [
  "bg-red-50 text-red-700 border-red-200",
  "bg-orange-50 text-orange-700 border-orange-200",
  "bg-yellow-50 text-yellow-800 border-yellow-200",
  "bg-sky-50 text-sky-700 border-sky-200",
  "bg-green-50 text-green-700 border-green-200",
];

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
    <div className="space-y-1.5">
      <div className="grid grid-cols-5 gap-1.5">
        {Array.from({ length: 5 }, (_, i) => {
          const val = i + 1;
          const active = value === val;
          return (
            <button
              key={val}
              type="button"
              onClick={() => handleClick(val)}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleClick(val); } }}
              aria-label={`Puntuación ${val}`}
              className={`px-2.5 py-2 rounded-lg text-sm font-semibold border-2 transition-all ${
                active
                  ? `${PALETTE[i]} shadow-md scale-105`
                  : "bg-white text-gray-700 border-gray-200 hover:border-blue-300 hover:bg-blue-50"
              }`}
            >
              {val}
            </button>
          );
        })}
      </div>
      {value > 0 && (
        <p className="text-[11px] text-gray-500 text-center">
          Puntuación: {value}/5
        </p>
      )}
    </div>
  );
}
