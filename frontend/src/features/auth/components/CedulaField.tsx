"use client";

import React from "react";
import { Hash } from "lucide-react";

export type Nationality = "V" | "E";

interface CedulaFieldProps {
  nationality: Nationality;
  cedula: string;
  onChange: (next: { nationality: Nationality; cedula: string }) => void;
  label?: string;
  helper?: string;
}

function formatCedula(raw: string): string {
  const digits = raw.replace(/\D/g, "");
  if (!digits) return "";
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

export default function CedulaField({
  nationality,
  cedula,
  onChange,
  label = "Cédula",
  helper,
}: CedulaFieldProps) {
  const display = formatCedula(cedula);

  function emit(nextNat: Nationality, nextCedRaw: string) {
    const digits = nextCedRaw.replace(/\D/g, "");
    onChange({ nationality: nextNat, cedula: digits });
  }

  function handlePaste(e: React.ClipboardEvent<HTMLInputElement>) {
    const text = e.clipboardData.getData("text").trim();
    if (!text) return;
    const match = text.match(/^([VEve])[-\s]?(.+)$/);
    if (match) {
      e.preventDefault();
      const nat = match[1].toUpperCase() as Nationality;
      emit(nat === "E" ? "E" : "V", match[2]);
    }
  }

  return (
    <div className="lm-field">
      <span className="lm-field-lbl">{label}</span>
      <div className="lm-cedula-row">
        <div className="lm-field-row">
          <select
            aria-label="Nacionalidad"
            value={nationality}
            onChange={(e) => emit(e.target.value as Nationality, cedula)}
          >
            <option value="V">V</option>
            <option value="E">E</option>
          </select>
        </div>
        <div className="lm-field-row">
          <Hash className="icon" size={18} />
          <input
            type="text"
            inputMode="numeric"
            autoComplete="off"
            placeholder="25.487.612"
            value={display}
            onChange={(e) => emit(nationality, e.target.value)}
            onPaste={handlePaste}
          />
        </div>
      </div>
      {helper && <span className="lm-field-help">{helper}</span>}
    </div>
  );
}
