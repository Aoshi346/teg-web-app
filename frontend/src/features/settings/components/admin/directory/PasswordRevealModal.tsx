"use client";
import React, { useState } from "react";

interface PasswordRevealModalProps {
  isOpen: boolean;
  password: string;
  onClose: () => void;
}

export function PasswordRevealModal({ isOpen, password, onClose }: PasswordRevealModalProps) {
  const [copied, setCopied] = useState(false);
  if (!isOpen) return null;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Note: clipboard blocked — user can still select the text
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" role="dialog" aria-modal="true">
      <div className="bg-white rounded-lg p-6 max-w-md w-full text-center">
        <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-3 text-xl">✓</div>
        <h3 className="text-base font-semibold mb-1">Usuario creado</h3>
        <p className="text-xs text-gray-500 mb-4">
          Comparta esta contraseña con el usuario de forma segura. No podrá verla de nuevo.
        </p>
        <div className="bg-gray-100 border border-dashed border-gray-400 rounded-lg p-3 mb-3">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Contraseña temporal</div>
          <div className="font-mono text-base font-semibold text-gray-900 tracking-wider">{password}</div>
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-2.5 mb-4 text-xs text-amber-900 text-left">
          El usuario debe cambiarla en su primer inicio de sesión. Esta ventana no puede reabrirse.
        </div>
        <div className="flex gap-2 justify-center">
          <button onClick={handleCopy} className="px-3 py-2 border border-gray-300 rounded-md text-sm">
            {copied ? "Copiado" : "Copiar contraseña"}
          </button>
          <button onClick={onClose} className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm font-semibold">
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
}
