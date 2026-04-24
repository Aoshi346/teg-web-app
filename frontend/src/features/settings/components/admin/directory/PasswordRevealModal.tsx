"use client";
import React, { useState } from "react";
import { Check, Copy } from "lucide-react";

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
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" role="dialog" aria-modal="true">
      <div className="bg-surface rounded-2xl p-7 max-w-md w-full text-center shadow-xl">
        <div className="w-14 h-14 rounded-full bg-success-soft text-success flex items-center justify-center mx-auto mb-4">
          <Check className="w-7 h-7" strokeWidth={3} />
        </div>
        <h3 className="text-lg font-bold text-text-strong tracking-tight mb-1.5">Usuario creado</h3>
        <p className="text-[13px] text-text-muted mb-5">
          Comparte esta contraseña con el usuario de forma segura. No podrá verla de nuevo.
        </p>
        <div className="bg-surface-sunken border border-dashed border-border-default rounded-xl p-4 mb-4">
          <div className="text-[11px] font-semibold text-text-muted uppercase tracking-[0.05em] mb-1.5">
            Contraseña temporal
          </div>
          <div className="font-mono text-xl font-bold text-text-strong tracking-wider select-all">
            {password}
          </div>
        </div>
        <div className="bg-pending-soft border border-[rgba(184,121,0,0.22)] rounded-lg p-3 mb-5 text-[12.5px] text-[#6e4308] text-left">
          El usuario debe cambiarla en su primer inicio de sesión. Esta ventana no puede reabrirse.
        </div>
        <div className="flex gap-2 justify-center">
          <button
            onClick={handleCopy}
            className="h-10 px-4 bg-surface border border-border-default rounded-lg text-[13.5px] font-semibold text-text-default inline-flex items-center gap-1.5 shadow-[0_1px_2px_rgba(15,23,42,0.03)] hover:bg-surface-sunken hover:text-text-strong transition-colors"
          >
            <Copy className="w-3.5 h-3.5" />
            {copied ? "Copiado" : "Copiar contraseña"}
          </button>
          <button
            onClick={onClose}
            className="h-10 px-4 bg-primary text-white rounded-lg text-[13.5px] font-semibold shadow-[0_1px_2px_rgba(0,102,255,0.25),inset_0_1px_0_rgba(255,255,255,0.12)] hover:bg-[#0052cc] transition-colors"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
}
