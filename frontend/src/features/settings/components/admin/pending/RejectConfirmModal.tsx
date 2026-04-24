"use client";
import React, { useState } from "react";
import { AlertTriangle } from "lucide-react";

interface RejectConfirmModalProps {
  isOpen: boolean;
  userName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function RejectConfirmModal({ isOpen, userName, onConfirm, onCancel }: RejectConfirmModalProps) {
  const [reason, setReason] = useState("");
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" role="dialog" aria-modal="true">
      <div className="bg-surface rounded-2xl p-7 max-w-md w-full shadow-xl">
        <div className="w-11 h-11 rounded-full bg-destructive-soft text-destructive flex items-center justify-center mb-4">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <h3 className="text-lg font-bold text-text-strong tracking-tight mb-1.5">
          ¿Rechazar a {userName}?
        </h3>
        <p className="text-[13px] text-text-muted mb-4 leading-relaxed">
          El usuario será marcado como <b className="text-text-default">rechazado</b> y no podrá iniciar sesión.
          Podrá reactivarlo desde el Directorio en cualquier momento.
        </p>
        <label className="block text-[13px] font-semibold text-text-default mb-1.5">
          Motivo <span className="text-text-muted font-normal">(opcional, no se guarda)</span>
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Motivo (opcional)"
          className="w-full px-3 py-2.5 bg-surface border border-border-default rounded-lg text-[13.5px] font-medium text-text-strong resize-y min-h-[80px] leading-[1.5] mb-4 focus:outline-none focus:border-primary focus:ring-[3px] focus:ring-[rgba(0,102,255,0.16)]"
        />
        <div className="flex gap-2 justify-end">
          <button
            onClick={onCancel}
            className="h-10 px-4 bg-surface border border-border-default rounded-lg text-[13.5px] font-semibold text-text-default shadow-[0_1px_2px_rgba(15,23,42,0.03)] hover:bg-surface-sunken hover:text-text-strong transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={() => onConfirm()}
            className="h-10 px-4 bg-destructive text-white rounded-lg text-[13.5px] font-semibold hover:bg-[#b32f2f] transition-colors"
          >
            Rechazar
          </button>
        </div>
      </div>
    </div>
  );
}
