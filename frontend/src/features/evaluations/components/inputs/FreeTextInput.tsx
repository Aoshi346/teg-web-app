"use client";

import React from "react";

interface FreeTextInputProps {
  value: string;
  onChange: (value: string) => void;
}

export default function FreeTextInput({ value, onChange }: FreeTextInputProps) {
  return (
    <div className="inp-text">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={3}
        className="inp-text-area"
        placeholder="Escriba sus observaciones..."
      />
    </div>
  );
}
