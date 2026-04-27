"use client";

import React from "react";
import { Loader2, Check } from "lucide-react";

interface StickyActionBarProps {
  answeredCount: number;
  totalRequired: number;
  isSubmitting: boolean;
  onSubmit: () => void;
  onCancel: () => void;
  onClearDraft: () => void;
  errorMode?: boolean;
  onJumpToMissing?: () => void;
}

export default function StickyActionBar({
  answeredCount,
  totalRequired,
  isSubmitting,
  onSubmit,
  onCancel,
  onClearDraft,
  errorMode,
  onJumpToMissing,
}: StickyActionBarProps) {
  const pct = totalRequired > 0 ? Math.round((answeredCount / totalRequired) * 100) : 0;
  const remaining = totalRequired - answeredCount;

  return (
    <div className="actions">
      <div className="actions-inner">
        <div className="actions-progress">
          <span className="font-display actions-frac">
            {answeredCount}/{totalRequired}
          </span>
          {remaining > 0 && (
            <span className="actions-remaining">{remaining} restantes</span>
          )}
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${pct}%` }} />
          </div>
        </div>

        <div className="actions-btns">
          <button
            type="button"
            onClick={onClearDraft}
            className="btn ghost"
          >
            Limpiar
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="btn outline"
          >
            Cancelar
          </button>

          {errorMode ? (
            <button
              type="button"
              onClick={onJumpToMissing}
              className="btn cta danger"
            >
              Saltar a falta
            </button>
          ) : (
            <button
              type="button"
              onClick={onSubmit}
              disabled={isSubmitting}
              className="btn cta"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Enviar evaluación
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
