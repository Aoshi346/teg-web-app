"use client";
import React, { useState } from "react";

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
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" role="dialog" aria-modal="true">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <div className="w-11 h-11 rounded-full bg-red-100 text-red-700 flex items-center justify-center mb-3 text-xl">!</div>
        <h3 className="text-base font-semibold mb-1">¿Rechazar a {userName}?</h3>
        <p className="text-sm text-gray-500 mb-3 leading-relaxed">
          El usuario será marcado como <b>rechazado</b> y no podrá iniciar sesión.
          Podrá reactivarlo desde el Directorio en cualquier momento.
        </p>
        <label className="block text-xs font-semibold mb-1">
          Motivo <span className="text-gray-400 font-normal">(opcional, no se guarda)</span>
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Motivo (opcional)"
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm min-h-[60px] resize-y mb-3"
        />
        <div className="flex gap-2 justify-end">
          <button onClick={onCancel} className="px-3 py-2 bg-white border border-gray-300 rounded-md text-sm">Cancelar</button>
          <button onClick={() => onConfirm()} className="px-3 py-2 bg-red-600 text-white rounded-md text-sm font-semibold">Rechazar</button>
        </div>
      </div>
    </div>
  );
}
