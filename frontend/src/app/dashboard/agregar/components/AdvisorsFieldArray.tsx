"use client";

import React from "react";
import { useFieldArray, useFormContext } from "react-hook-form";
import { GraduationCap, Plus, X } from "lucide-react";
import Combobox from "./Combobox";
import type { UserOption } from "../hooks/useDocumentData";
import type { DocumentFormData } from "../schema";

interface AdvisorsFieldArrayProps {
  tutors: UserOption[];
}

export default function AdvisorsFieldArray({ tutors }: AdvisorsFieldArrayProps) {
  const {
    control,
    watch,
    setValue,
    formState: { errors },
  } = useFormContext<DocumentFormData>();

  const { fields, append, remove } = useFieldArray({
    control,
    name: "advisors" as never,
  });

  const advisors = watch("advisors");
  const globalError = errors.advisors?.message || errors.advisors?.root?.message;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <GraduationCap className="w-4 h-4 text-teal-500" />
          <label className="text-xs font-bold text-gray-700">
            Tutores
          </label>
          <span className="text-[10px] font-semibold text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full">
            {advisors.length}/2
          </span>
        </div>
      </div>

      {globalError && (
        <p className="text-[11px] font-semibold text-red-600">{globalError}</p>
      )}

      <div className="space-y-2">
        {fields.map((field, index) => {
          const fieldError = errors.advisors?.[index];
          const hasError = !!fieldError;

          return (
            <div
              key={field.id}
              className={`flex items-center gap-2 border rounded-lg p-3 ${
                hasError
                  ? "border-red-200 bg-red-50/30"
                  : "border-teal-100 bg-teal-50/30"
              }`}
            >
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
                  hasError
                    ? "bg-red-100 text-red-600"
                    : "bg-teal-100 text-teal-600"
                }`}
              >
                <GraduationCap className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <Combobox
                  options={tutors}
                  value={advisors[index] as number | ""}
                  onChange={(val) => {
                    const updated = [...advisors];
                    updated[index] = val;
                    setValue("advisors", updated, { shouldValidate: true });
                  }}
                  placeholder="Buscar tutor..."
                  emptyLabel="Sin tutores"
                  error={hasError}
                />
              </div>
              {advisors.length > 1 && (
                <button
                  type="button"
                  onClick={() => remove(index)}
                  className="flex-shrink-0 w-7 h-7 rounded-lg bg-white border border-red-100 hover:border-red-200 hover:bg-red-50 flex items-center justify-center text-red-500 hover:text-red-600 transition-all"
                  title="Eliminar tutor"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          );
        })}

        {advisors.length < 2 && (
          <button
            type="button"
            onClick={() => append("" as never)}
            className="w-full py-2.5 border border-dashed border-teal-300 rounded-lg bg-teal-50/30 hover:bg-teal-50 hover:border-teal-400 transition-all group"
          >
            <div className="flex items-center justify-center gap-1.5 text-teal-600 group-hover:text-teal-700">
              <Plus className="w-3.5 h-3.5" />
              <span className="text-xs font-semibold">Agregar Tutor</span>
            </div>
          </button>
        )}
      </div>
    </div>
  );
}
