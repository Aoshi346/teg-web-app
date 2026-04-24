"use client";
import React from "react";

type Nationality = "V" | "E" | "P";

interface CedulaFieldProps {
  nationality: Nationality;
  cedula: string;
  onChange: (value: { nationality: Nationality; cedula: string }) => void;
  error?: string;
  disabled?: boolean;
}

export function CedulaField({ nationality, cedula, onChange, error, disabled }: CedulaFieldProps) {
  return (
    <div>
      <label htmlFor="cedula-field-input" className="block text-xs font-semibold text-gray-700 mb-1">Cédula *</label>
      <div className="flex gap-2">
        <select
          aria-label="Nacionalidad"
          value={nationality}
          disabled={disabled}
          onChange={(e) => onChange({ nationality: e.target.value as Nationality, cedula })}
          className="w-20 px-2 py-2 border border-gray-300 rounded-md text-sm bg-white"
        >
          <option value="V">V</option>
          <option value="E">E</option>
          <option value="P">P</option>
        </select>
        <input
          id="cedula-field-input"
          type="text"
          value={cedula}
          disabled={disabled}
          onChange={(e) => onChange({ nationality, cedula: e.target.value })}
          placeholder="30243721"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      <p className="mt-1 text-xs text-gray-500">V = Venezolano, E = Extranjero, P = Pasaporte</p>
    </div>
  );
}
