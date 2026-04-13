"use client";

import React from "react";

interface FreeTextInputProps {
  value: string;
  onChange: (value: string) => void;
}

export default function FreeTextInput({ value, onChange }: FreeTextInputProps) {
  return (
    <div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={3}
        className="w-full bg-white border border-gray-200 rounded-lg p-3 text-sm shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all resize-none placeholder:text-gray-400"
        placeholder="Escriba sus observaciones..."
      />
      <p className="text-[11px] text-gray-400 mt-1">
        Texto libre — no afecta el puntaje numérico.
      </p>
    </div>
  );
}
