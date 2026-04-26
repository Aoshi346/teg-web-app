"use client";

import * as React from "react";
import { adminResetPassword } from "@features/auth/api/clientAuth";

export interface ResetPasswordModalProps {
  open: boolean;
  userId: number;
  userLabel: string;
  onClose: () => void;
  onSuccess?: () => void;
}

function generatePassword(): string {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
  const groups: string[] = [];
  for (let g = 0; g < 3; g++) {
    let s = "";
    for (let i = 0; i < 4; i++) s += alphabet[Math.floor(Math.random() * alphabet.length)];
    groups.push(s);
  }
  return groups.join("-");
}

export default function ResetPasswordModal({ open, userId, userLabel, onClose, onSuccess }: ResetPasswordModalProps) {
  const [pwd, setPwd] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState<string | null>(null);
  const [done, setDone] = React.useState(false);

  React.useEffect(() => {
    if (open) {
      setPwd(generatePassword());
      setErr(null);
      setDone(false);
    }
  }, [open]);

  if (!open) return null;

  const submit = async () => {
    if (pwd.length < 8) {
      setErr("La contraseña debe tener al menos 8 caracteres.");
      return;
    }
    setBusy(true); setErr(null);
    try {
      await adminResetPassword(userId, pwd);
      setDone(true);
      onSuccess?.();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error al actualizar la contraseña.");
    } finally {
      setBusy(false);
    }
  };

  const copyPwd = async () => {
    try { await navigator.clipboard.writeText(pwd); } catch { /* noop */ }
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md bg-surface rounded-2xl shadow-2xl ring-1 ring-black/5 overflow-hidden">
        <div className="p-5 border-b border-border-subtle">
          <h3 className="text-base font-extrabold text-text-strong">Restablecer contraseña</h3>
          <p className="text-xs text-text-muted mt-0.5">Usuario: {userLabel}</p>
        </div>
        <div className="p-5 space-y-3">
          {!done ? (
            <>
              <label className="block">
                <span className="text-[10px] uppercase tracking-wider text-text-muted font-extrabold mb-1.5 block">
                  Nueva contraseña
                </span>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={pwd}
                    onChange={(e) => setPwd(e.target.value)}
                    minLength={8}
                    className="flex-1 px-3 py-2.5 bg-surface border border-border-subtle rounded-xl text-[14px] font-mono font-semibold text-text-strong focus:outline-none focus:border-primary transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setPwd(generatePassword())}
                    className="px-3 py-2.5 text-[12px] font-bold text-text-muted hover:text-text-strong border border-border-subtle rounded-xl transition-colors whitespace-nowrap"
                    title="Generar otra"
                  >
                    Regenerar
                  </button>
                </div>
                <p className="text-[11px] text-text-muted font-medium mt-1.5">
                  Mínimo 8 caracteres. Compártela con el usuario por un canal seguro.
                </p>
              </label>
              {err && <p className="text-[11px] text-destructive font-semibold">{err}</p>}
            </>
          ) : (
            <div className="space-y-2">
              <p className="text-[13px] text-success font-bold">✓ Contraseña actualizada.</p>
              <p className="text-[12.5px] text-text-default font-medium">
                Comparte esta contraseña con el usuario:
              </p>
              <div className="flex gap-2 items-center">
                <code className="flex-1 px-3 py-2.5 bg-surface-sunken border border-border-subtle rounded-xl text-[14px] font-mono font-semibold text-text-strong">
                  {pwd}
                </code>
                <button
                  type="button"
                  onClick={copyPwd}
                  className="px-3 py-2.5 text-[12px] font-bold text-text-muted hover:text-text-strong border border-border-subtle rounded-xl transition-colors"
                >
                  Copiar
                </button>
              </div>
            </div>
          )}
        </div>
        <div className="flex flex-col gap-2 p-5 pt-0">
          {!done ? (
            <>
              <button
                type="button"
                onClick={submit}
                disabled={busy || !pwd}
                className="w-full px-4 py-2.5 text-sm font-bold text-white bg-text-strong hover:bg-[#0a1424] rounded-xl disabled:opacity-50 transition-colors"
              >
                {busy ? "Guardando..." : "Confirmar cambio"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="w-full px-4 py-2.5 text-sm font-semibold text-text-muted hover:bg-surface-muted rounded-xl transition-colors"
              >
                Cancelar
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={onClose}
              className="w-full px-4 py-2.5 text-sm font-bold text-white bg-text-strong hover:bg-[#0a1424] rounded-xl transition-colors"
            >
              Cerrar
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
