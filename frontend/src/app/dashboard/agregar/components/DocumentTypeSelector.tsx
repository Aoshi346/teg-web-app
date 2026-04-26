"use client";

import { cn } from "@shared/lib/utils";

type DocType = "proyecto" | "tesis";

interface DocumentTypeSelectorProps {
  value: DocType;
  onChange: (type: DocType) => void;
  allowedTypes: readonly DocType[];
  disabled?: boolean;
}

const ALL_TYPES: DocType[] = ["proyecto", "tesis"];

const CARD_CONFIG = {
  proyecto: {
    typeClass: "pteg",
    num: "9°",
    pill: "PTEG",
    label: "Proyecto de TEG",
    meta: "Propuesta inicial",
  },
  tesis: {
    typeClass: "teg",
    num: "10°",
    pill: "TEG",
    label: "Trabajo Especial de Grado",
    meta: "Proyecto final",
  },
} as const;

export default function DocumentTypeSelector({
  value,
  onChange,
  allowedTypes,
  disabled,
}: DocumentTypeSelectorProps) {
  return (
    <div>
      <h3 className="agg-tb-title">
        {disabled ? "Documento asignado" : "Tipo de documento"}
      </h3>

      <div className="agg-tcards">
        {ALL_TYPES.map((type) => {
          const cfg = CARD_CONFIG[type];
          const isAllowed = allowedTypes.includes(type);
          const isActive = value === type;
          const isLocked = !isAllowed;

          return (
            <div
              key={type}
              role="button"
              tabIndex={isLocked || disabled ? -1 : 0}
              aria-pressed={isActive}
              aria-disabled={isLocked || disabled}
              onClick={() => {
                if (!disabled && isAllowed) onChange(type);
              }}
              onKeyDown={(e) => {
                if ((e.key === "Enter" || e.key === " ") && !disabled && isAllowed) {
                  onChange(type);
                }
              }}
              className={cn("agg-tcard", cfg.typeClass, {
                active: isActive,
                locked: isLocked,
              })}
            >
              <div className="agg-tcard-head">
                <div className="agg-tcard-num font-display">{cfg.num}</div>
                {isActive && <div className="agg-tcard-check">✓</div>}
              </div>
              <span className="agg-tcard-pill">{cfg.pill}</span>
              <div className="agg-tcard-label">{cfg.label}</div>
              <div className="agg-tcard-meta">{cfg.meta}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
