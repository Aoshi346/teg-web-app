"use client";

import React from "react";
import { ChevronLeft, ChevronRight, Check, Loader2 } from "lucide-react";

interface StickyActionBarProps {
  page: number;
  totalPages: number;
  answeredCount: number;
  totalRequired: number;
  isSubmitting: boolean;
  onPrev: () => void;
  onNext: () => void;
  onSubmit: () => void;
  onCancel: () => void;
  onClearDraft: () => void;
}

export default function StickyActionBar({
  page,
  totalPages,
  answeredCount,
  totalRequired,
  isSubmitting,
  onPrev,
  onNext,
  onSubmit,
  onCancel,
  onClearDraft,
}: StickyActionBarProps) {
  const isLastPage = page === totalPages;
  const remaining = totalRequired - answeredCount;
  const pct = totalRequired > 0 ? Math.round((answeredCount / totalRequired) * 100) : 0;

  return (
    <div className="sticky bottom-0 z-40 bg-white/95 backdrop-blur-sm border-t border-gray-200 shadow-[0_-4px_12px_rgba(0,0,0,0.06)]">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-3">
        {/* Progress */}
        <div className="hidden sm:flex items-center gap-2.5 flex-shrink-0">
          <div className="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs font-semibold text-gray-500 whitespace-nowrap">
            {answeredCount}/{totalRequired}
            {remaining > 0 && (
              <span className="text-gray-400 ml-1">({remaining} restantes)</span>
            )}
          </span>
        </div>

        <div className="flex-1" />

        {/* Actions */}
        <button
          type="button"
          onClick={onClearDraft}
          className="text-xs text-gray-400 hover:text-gray-600 font-medium px-2 py-1 transition-colors hidden sm:block"
        >
          Limpiar
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-gray-500 hover:text-gray-700 font-medium px-2 py-1 transition-colors"
        >
          Cancelar
        </button>

        <button
          type="button"
          onClick={onPrev}
          disabled={page === 1}
          className="flex items-center gap-1 px-3 py-2 rounded-lg bg-white border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        >
          <ChevronLeft className="w-4 h-4" />
          <span className="hidden sm:inline">Anterior</span>
        </button>

        {isLastPage ? (
          <button
            type="button"
            onClick={onSubmit}
            disabled={isSubmitting}
            className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-green-600 text-white text-sm font-bold hover:bg-green-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
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
        ) : (
          <button
            type="button"
            onClick={onNext}
            className="flex items-center gap-1 px-5 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-bold hover:shadow-lg hover:shadow-blue-500/25 transition-all"
          >
            Siguiente
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
