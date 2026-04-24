"use client";
import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { profileSchema, type ProfileInput } from "../../lib/schemas";
import { CedulaField } from "./CedulaField";

interface ProfileFormProps {
  initialValues: ProfileInput;
  onSubmit: (values: ProfileInput) => Promise<void>;
}

const INPUT_CLASS =
  "w-full h-10 px-3 bg-surface border border-border-default rounded-lg text-[13.5px] font-medium text-text-strong transition-colors hover:border-[#b8bccb] focus:outline-none focus:border-primary focus:ring-[3px] focus:ring-[rgba(0,102,255,0.16)]";
const LABEL_CLASS = "block text-[13px] font-semibold text-text-default mb-1.5";
const REQ_CLASS = "text-destructive ml-0.5";

const ROLE_PILL_STYLES: Record<string, string> = {
  Administrador: "bg-[#f5f0fc] text-[#6e35d1] border-[#d9c8f1]",
  Tutor: "bg-[rgba(0,102,255,0.08)] text-primary border-[rgba(0,102,255,0.18)]",
  Jurado: "bg-pending-soft text-pending border-[rgba(184,121,0,0.22)]",
  Estudiante: "bg-success-soft text-success border-[rgba(26,135,84,0.2)]",
};

function initials(name: string): string {
  return name.split(" ").filter(Boolean).map((p) => p[0] || "").join("").slice(0, 2).toUpperCase() || "?";
}

export function ProfileForm({ initialValues, onSubmit }: ProfileFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isDirty, isSubmitting },
    reset,
  } = useForm<ProfileInput>({
    resolver: zodResolver(profileSchema),
    defaultValues: initialValues,
    mode: "onBlur",
  });

  const nationality = watch("nationality");
  const cedula = watch("cedula");
  const role = watch("role");
  const fullName = watch("fullName");
  const email = watch("email");

  const submit = handleSubmit(async (values) => {
    await onSubmit(values);
    reset(values);
  });

  const rolePillClass = ROLE_PILL_STYLES[role] || ROLE_PILL_STYLES.Estudiante;

  return (
    <form
      onSubmit={submit}
      className="bg-surface border border-border-subtle rounded-[14px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden"
    >
      <div className="relative h-[88px] bg-gradient-to-br from-[#1a1f33] via-[#011638] to-[#0066ff]">
        <div
          className="absolute inset-0 opacity-60 pointer-events-none"
          style={{
            backgroundImage:
              "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='1.5' numOctaves='2'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.05 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
          }}
        />
      </div>

      <div className="px-6 -mt-[40px] relative z-[2]">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] text-white flex items-center justify-center text-[28px] font-bold border-4 border-surface shadow-[0_4px_14px_rgba(15,23,42,0.12)]">
          {initials(fullName || "")}
        </div>
      </div>

      <div className="px-6 pt-3 pb-4">
        <h3 className="text-[19px] font-extrabold text-text-strong tracking-tight mb-1.5 truncate">
          {fullName || "—"}
        </h3>
        <div className="flex flex-wrap gap-2 items-center text-[12.5px] text-text-muted">
          <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-bold border ${rolePillClass}`}>
            {role}
          </span>
          <span className="truncate">{email}</span>
        </div>
      </div>

      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="profile-fullname" className={LABEL_CLASS}>
            Nombre completo <span className={REQ_CLASS}>*</span>
          </label>
          <input id="profile-fullname" {...register("fullName")} className={INPUT_CLASS} />
          {errors.fullName && <p className="mt-1.5 text-[11.5px] text-destructive">{errors.fullName.message}</p>}
        </div>

        <div>
          <label htmlFor="profile-email" className={LABEL_CLASS}>
            Email <span className={REQ_CLASS}>*</span>
          </label>
          <input id="profile-email" type="email" {...register("email")} className={INPUT_CLASS} />
          {errors.email && <p className="mt-1.5 text-[11.5px] text-destructive">{errors.email.message}</p>}
        </div>

        <div className="md:col-span-2">
          <CedulaField
            nationality={nationality}
            cedula={cedula}
            onChange={({ nationality: n, cedula: c }) => {
              setValue("nationality", n, { shouldDirty: true, shouldValidate: true });
              setValue("cedula", c, { shouldDirty: true, shouldValidate: true });
            }}
            error={errors.cedula?.message}
          />
        </div>

        <div>
          <label htmlFor="profile-phone" className={LABEL_CLASS}>
            Teléfono
          </label>
          <input id="profile-phone" {...register("phone")} className={INPUT_CLASS} />
          {errors.phone && <p className="mt-1.5 text-[11.5px] text-destructive">{errors.phone.message}</p>}
        </div>

        {role === "Estudiante" && (
          <div>
            <label htmlFor="semester-select" className={LABEL_CLASS}>
              Semestre <span className={REQ_CLASS}>*</span>
            </label>
            <select
              id="semester-select"
              {...register("semester")}
              className={`${INPUT_CLASS} appearance-none pr-8`}
              style={{
                backgroundImage:
                  "url(\"data:image/svg+xml,%3Csvg width='10' height='6' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%236b7589' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E\")",
                backgroundRepeat: "no-repeat",
                backgroundPosition: "right 12px center",
              }}
            >
              <option value="9no">9no Semestre</option>
              <option value="10mo">10mo Semestre</option>
              <option value="N/A">N/A</option>
            </select>
          </div>
        )}
      </div>

      <div className="px-6 py-4 border-t border-border-subtle bg-surface-muted flex items-center justify-between gap-3 flex-wrap">
        <div className="text-xs text-text-muted flex items-center gap-1.5">
          {isDirty ? (
            <>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-success" />
              <span>Cambios sin guardar — los datos se actualizarán al presionar Guardar.</span>
            </>
          ) : (
            <span>Tus cambios se guardan solo cuando presionas Guardar.</span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => reset(initialValues)}
            disabled={!isDirty || isSubmitting}
            className="h-9 px-3.5 bg-surface border border-border-default rounded-lg text-[13px] font-semibold text-text-default shadow-[0_1px_2px_rgba(15,23,42,0.03)] hover:bg-surface-sunken hover:text-text-strong hover:border-[#b8bccb] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Descartar
          </button>
          <button
            type="submit"
            disabled={!isDirty || isSubmitting}
            className="h-9 px-3.5 bg-primary text-white rounded-lg text-[13px] font-semibold shadow-[0_1px_2px_rgba(0,102,255,0.25),inset_0_1px_0_rgba(255,255,255,0.12)] hover:bg-[#0052cc] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Guardar cambios
          </button>
        </div>
      </div>
    </form>
  );
}
