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

const INPUT_BASE =
  "h-10 px-3 bg-surface border border-border-default rounded-lg text-[13.5px] font-medium text-text-strong transition-colors hover:border-[#b8bccb] focus:outline-none focus:border-primary focus:ring-[3px] focus:ring-[rgba(0,102,255,0.16)] disabled:opacity-60";

export function CedulaField({ nationality, cedula, onChange, error, disabled }: CedulaFieldProps) {
  return (
    <div>
      <label htmlFor="cedula-field-input" className="block text-[13px] font-semibold text-text-default mb-1.5">
        Cédula <span className="text-destructive ml-0.5">*</span>
      </label>
      <div className="grid grid-cols-[84px_1fr] gap-1.5">
        <select
          aria-label="Nacionalidad"
          value={nationality}
          disabled={disabled}
          onChange={(e) => onChange({ nationality: e.target.value as Nationality, cedula })}
          className={`${INPUT_BASE} appearance-none pr-7`}
          style={{
            backgroundImage:
              "url(\"data:image/svg+xml,%3Csvg width='10' height='6' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%236b7589' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E\")",
            backgroundRepeat: "no-repeat",
            backgroundPosition: "right 10px center",
          }}
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
          className={INPUT_BASE}
        />
      </div>
      {error && <p className="mt-1.5 text-[11.5px] text-destructive">{error}</p>}
      <p className="mt-1.5 text-[11.5px] text-text-muted">V = Venezolano, E = Extranjero, P = Pasaporte</p>
    </div>
  );
}
