"use client";
import React, { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { userCreateSchema, type UserInput } from "../../../lib/schemas";
import { CedulaField } from "../../profile/CedulaField";

export interface UserModalData {
  id?: number;
  role: "Administrador" | "Tutor" | "Jurado" | "Estudiante";
  fullName: string;
  email: string;
  nationality: "V" | "E" | "P";
  cedula: string;
  phone: string;
  semester?: "9no" | "10mo" | "N/A";
}

interface UserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: UserInput) => Promise<void>;
  initialData: UserModalData | null;
}

const defaultStudent: UserInput = {
  role: "Estudiante",
  fullName: "",
  email: "",
  nationality: "V",
  cedula: "",
  phone: "",
  semester: "9no",
};

const INPUT_CLASS =
  "w-full h-10 px-3 bg-surface border border-border-default rounded-lg text-[13.5px] font-medium text-text-strong transition-colors hover:border-[#b8bccb] focus:outline-none focus:border-primary focus:ring-[3px] focus:ring-[rgba(0,102,255,0.16)]";
const LABEL_CLASS = "block text-[13px] font-semibold text-text-default mb-1.5";
const SELECT_STYLE = {
  backgroundImage:
    "url(\"data:image/svg+xml,%3Csvg width='10' height='6' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%236b7589' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E\")",
  backgroundRepeat: "no-repeat" as const,
  backgroundPosition: "right 12px center",
};

export function UserModal({ isOpen, onClose, onSave, initialData }: UserModalProps) {
  const form = useForm<UserInput>({
    resolver: zodResolver(userCreateSchema),
    defaultValues: (initialData as UserInput) ?? defaultStudent,
    mode: "onBlur",
  });
  const { register, handleSubmit, watch, setValue, reset, formState: { errors, isSubmitting } } = form;

  useEffect(() => {
    reset((initialData as UserInput) ?? defaultStudent);
  }, [initialData, reset]);

  const role = watch("role");
  const nationality = watch("nationality");
  const cedula = watch("cedula");

  function onRoleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const newRole = e.target.value as UserInput["role"];
    const current = watch();
    if (newRole === "Estudiante") {
      reset({ ...current, role: "Estudiante", semester: "9no" } as UserInput);
    } else {
      const { fullName, email, nationality, cedula, phone } = current as UserInput;
      reset({ role: newRole, fullName, email, nationality, cedula, phone } as UserInput);
    }
  }

  if (!isOpen) return null;

  const submit = handleSubmit(async (values) => {
    await onSave(values);
  });

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" role="dialog" aria-modal="true">
      <div className="bg-surface rounded-2xl p-7 w-full max-w-md max-h-[90vh] overflow-y-auto shadow-xl">
        <h3 className="text-lg font-bold text-text-strong tracking-tight mb-1">
          {initialData ? "Editar usuario" : "Nuevo usuario"}
        </h3>
        <p className="text-[13px] text-text-muted mb-5">
          {initialData ? "Actualiza los datos del usuario" : "Se generará una contraseña temporal al guardar"}
        </p>
        <form onSubmit={submit} className="flex flex-col gap-4">
          <div>
            <label htmlFor="user-modal-fullname" className={LABEL_CLASS}>
              Nombre completo <span className="text-destructive ml-0.5">*</span>
            </label>
            <input id="user-modal-fullname" {...register("fullName")} className={INPUT_CLASS} />
            {errors.fullName && <p className="mt-1.5 text-[11.5px] text-destructive">{errors.fullName.message}</p>}
          </div>
          <div>
            <label htmlFor="user-modal-email" className={LABEL_CLASS}>
              Email <span className="text-destructive ml-0.5">*</span>
            </label>
            <input id="user-modal-email" type="email" {...register("email")} className={INPUT_CLASS} />
            {errors.email && <p className="mt-1.5 text-[11.5px] text-destructive">{errors.email.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="user-modal-role" className={LABEL_CLASS}>
                Rol <span className="text-destructive ml-0.5">*</span>
              </label>
              <select
                id="user-modal-role"
                {...register("role", { onChange: onRoleChange })}
                className={`${INPUT_CLASS} appearance-none pr-8`}
                style={SELECT_STYLE}
              >
                <option value="Estudiante">Estudiante</option>
                <option value="Tutor">Tutor</option>
                <option value="Jurado">Jurado</option>
                <option value="Administrador">Administrador</option>
              </select>
            </div>
            {role === "Estudiante" && (
              <div>
                <label htmlFor="user-modal-semester" className={LABEL_CLASS}>
                  Semestre <span className="text-destructive ml-0.5">*</span>
                </label>
                <select
                  id="user-modal-semester"
                  {...register("semester")}
                  className={`${INPUT_CLASS} appearance-none pr-8`}
                  style={SELECT_STYLE}
                >
                  <option value="9no">9no Semestre</option>
                  <option value="10mo">10mo Semestre</option>
                  <option value="N/A">N/A</option>
                </select>
              </div>
            )}
          </div>
          <CedulaField
            nationality={nationality}
            cedula={cedula}
            onChange={({ nationality: n, cedula: c }) => {
              setValue("nationality", n, { shouldDirty: true, shouldValidate: true });
              setValue("cedula", c, { shouldDirty: true, shouldValidate: true });
            }}
            error={errors.cedula?.message}
          />
          <div>
            <label htmlFor="user-modal-phone" className={LABEL_CLASS}>Teléfono</label>
            <input id="user-modal-phone" {...register("phone")} className={INPUT_CLASS} />
          </div>
          <div className="flex gap-2 justify-end mt-2 pt-4 border-t border-border-subtle">
            <button
              type="button"
              onClick={onClose}
              className="h-10 px-4 bg-surface border border-border-default rounded-lg text-[13.5px] font-semibold text-text-default shadow-[0_1px_2px_rgba(15,23,42,0.03)] hover:bg-surface-sunken hover:text-text-strong transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="h-10 px-4 bg-primary text-white rounded-lg text-[13.5px] font-semibold shadow-[0_1px_2px_rgba(0,102,255,0.25),inset_0_1px_0_rgba(255,255,255,0.12)] hover:bg-[#0052cc] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {initialData ? "Guardar" : "Crear usuario"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
