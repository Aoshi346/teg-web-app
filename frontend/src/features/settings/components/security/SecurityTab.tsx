"use client";
import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Lock } from "lucide-react";
import { passwordChangeSchema, type PasswordChangeInput } from "../../lib/schemas";
import { changePassword } from "@features/auth/api/clientAuth";

const INPUT_CLASS =
  "w-full h-10 px-3 bg-surface border border-border-default rounded-lg text-[13.5px] font-medium text-text-strong transition-colors hover:border-[#b8bccb] focus:outline-none focus:border-primary focus:ring-[3px] focus:ring-[rgba(0,102,255,0.16)]";
const LABEL_CLASS = "block text-[13px] font-semibold text-text-default mb-1.5";
const REQ_CLASS = "text-destructive ml-0.5";

export function SecurityTab() {
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<PasswordChangeInput>({
    resolver: zodResolver(passwordChangeSchema),
  });

  const onSubmit = handleSubmit(async (data) => {
    setSuccess(false);
    try {
      await changePassword({
        currentPassword: data.currentPassword,
        newPassword: data.newPassword,
      });
      reset();
      setSuccess(true);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Error al cambiar contraseña";
      setError("currentPassword", { message });
    }
  });

  return (
    <section
      aria-labelledby="security-heading"
      className="bg-surface border border-border-subtle rounded-[14px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden"
    >
      <div className="px-8 pt-7 pb-5 border-b border-border-subtle flex items-center gap-3">
        <div className="w-10 h-10 rounded-[10px] bg-gradient-to-br from-[rgba(0,102,255,0.08)] to-[rgba(255,107,53,0.08)] text-primary inline-flex items-center justify-center shrink-0">
          <Lock className="w-[18px] h-[18px]" />
        </div>
        <div>
          <h2
            id="security-heading"
            className="text-[15px] font-extrabold text-text-strong tracking-tight leading-tight"
          >
            Seguridad
          </h2>
          <p className="text-[12.5px] text-text-muted leading-tight mt-0.5">
            Cambia tu contraseña de acceso
          </p>
        </div>
      </div>

      <form onSubmit={onSubmit} className="px-8 py-7 space-y-5">
        <div>
          <label htmlFor="currentPassword" className={LABEL_CLASS}>
            Contraseña actual<span className={REQ_CLASS}>*</span>
          </label>
          <input
            id="currentPassword"
            type="password"
            autoComplete="current-password"
            className={INPUT_CLASS}
            {...register("currentPassword")}
          />
          {errors.currentPassword && (
            <p className="mt-1.5 text-[12.5px] text-destructive font-medium">
              {errors.currentPassword.message}
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label htmlFor="newPassword" className={LABEL_CLASS}>
              Nueva contraseña<span className={REQ_CLASS}>*</span>
            </label>
            <input
              id="newPassword"
              type="password"
              autoComplete="new-password"
              className={INPUT_CLASS}
              {...register("newPassword")}
            />
            {errors.newPassword && (
              <p className="mt-1.5 text-[12.5px] text-destructive font-medium">
                {errors.newPassword.message}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="confirmPassword" className={LABEL_CLASS}>
              Confirmar nueva contraseña<span className={REQ_CLASS}>*</span>
            </label>
            <input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              className={INPUT_CLASS}
              {...register("confirmPassword")}
            />
            {errors.confirmPassword && (
              <p className="mt-1.5 text-[12.5px] text-destructive font-medium">
                {errors.confirmPassword.message}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4 pt-1">
          <button
            type="submit"
            disabled={isSubmitting}
            className="h-9 px-5 rounded-lg bg-primary text-white text-[13px] font-bold tracking-tight transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            Cambiar contraseña
          </button>

          {success && (
            <p className="text-[13px] font-semibold text-success">
              Contraseña actualizada
            </p>
          )}
        </div>
      </form>
    </section>
  );
}
