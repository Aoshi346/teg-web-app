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
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" role="dialog" aria-modal="true">
      <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h3 className="text-base font-semibold mb-1">{initialData ? "Editar usuario" : "Nuevo usuario"}</h3>
        <p className="text-xs text-gray-500 mb-4">
          {initialData ? "Actualice los datos del usuario" : "Se generará una contraseña temporal al guardar"}
        </p>
        <form onSubmit={submit} className="flex flex-col gap-3">
          <div>
            <label htmlFor="user-modal-fullname" className="block text-xs font-semibold mb-1">Nombre completo *</label>
            <input id="user-modal-fullname" {...register("fullName")} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
            {errors.fullName && <p className="mt-1 text-xs text-red-600">{errors.fullName.message}</p>}
          </div>
          <div>
            <label htmlFor="user-modal-email" className="block text-xs font-semibold mb-1">Email *</label>
            <input id="user-modal-email" type="email" {...register("email")} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="user-modal-role" className="block text-xs font-semibold mb-1">Rol *</label>
              <select
                id="user-modal-role"
                {...register("role", { onChange: onRoleChange })}
                className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm bg-white"
              >
                <option value="Estudiante">Estudiante</option>
                <option value="Tutor">Tutor</option>
                <option value="Jurado">Jurado</option>
                <option value="Administrador">Administrador</option>
              </select>
            </div>
            {role === "Estudiante" && (
              <div>
                <label htmlFor="user-modal-semester" className="block text-xs font-semibold mb-1">Semestre *</label>
                <select
                  id="user-modal-semester"
                  {...register("semester")}
                  className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm bg-white"
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
            <label htmlFor="user-modal-phone" className="block text-xs font-semibold mb-1">Teléfono</label>
            <input id="user-modal-phone" {...register("phone")} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
          </div>
          <div className="flex gap-2 justify-end mt-2 pt-3 border-t border-gray-100">
            <button type="button" onClick={onClose} className="px-3 py-2 border border-gray-300 rounded-md text-sm">Cancelar</button>
            <button type="submit" disabled={isSubmitting} className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm font-semibold disabled:opacity-50">
              {initialData ? "Guardar" : "Crear usuario"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
