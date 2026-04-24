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

  const submit = handleSubmit(async (values) => {
    await onSubmit(values);
    reset(values);
  });

  return (
    <form onSubmit={submit} className="p-6 bg-white rounded-lg border border-gray-200">
      <h2 className="text-lg font-semibold mb-4">Información personal</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">Nombre completo *</label>
          <input
            {...register("fullName")}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
          {errors.fullName && <p className="mt-1 text-xs text-red-600">{errors.fullName.message}</p>}
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">Email *</label>
          <input
            type="email"
            {...register("email")}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
          {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
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
          <label className="block text-xs font-semibold text-gray-700 mb-1">Teléfono</label>
          <input
            {...register("phone")}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
          {errors.phone && <p className="mt-1 text-xs text-red-600">{errors.phone.message}</p>}
        </div>

        {role === "Estudiante" && (
          <div>
            <label htmlFor="semester-select" className="block text-xs font-semibold text-gray-700 mb-1">Semestre *</label>
            <select
              id="semester-select"
              {...register("semester")}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-white"
            >
              <option value="9no">9no Semestre</option>
              <option value="10mo">10mo Semestre</option>
              <option value="N/A">N/A</option>
            </select>
          </div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-100 flex gap-2 justify-end">
        <button
          type="button"
          onClick={() => reset(initialValues)}
          disabled={!isDirty || isSubmitting}
          className="px-4 py-2 border border-gray-300 bg-white rounded-md text-sm text-gray-700 disabled:opacity-50"
        >
          Descartar
        </button>
        <button
          type="submit"
          disabled={!isDirty || isSubmitting}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-semibold disabled:opacity-50"
        >
          Guardar cambios
        </button>
      </div>
    </form>
  );
}
