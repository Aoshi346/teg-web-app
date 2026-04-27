"use client";

import { useFormContext } from "react-hook-form";
import Combobox from "./Combobox";
import type { UserOption } from "../hooks/useDocumentData";
import type { DocumentFormData } from "../schema";

interface AdvisorsChipsProps {
  tutors: UserOption[];
}

export default function AdvisorsChips({ tutors }: AdvisorsChipsProps) {
  const { watch, setValue } = useFormContext<DocumentFormData>();

  const advisors = watch("advisors") ?? [];
  const chips = advisors.filter((a): a is number => typeof a === "number");
  const availableTutors = tutors.filter((t) => !chips.includes(t.id));
  const isFull = chips.length >= 2;

  function handlePick(val: number | "") {
    if (val === "" || isFull) return;
    if (chips.includes(val)) return;
    setValue("advisors", [...chips, val], { shouldValidate: true });
  }

  function handleRemove(id: number) {
    setValue("advisors", chips.filter((c) => c !== id), { shouldValidate: true });
  }

  return (
    <div>
      {chips.length > 0 && (
        <div className="advisors-chips">
          {chips.map((id) => {
            const label = tutors.find((t) => t.id === id)?.label ?? `Tutor #${id}`;
            return (
              <span key={id} className="a-chip">
                {label}
                <button
                  type="button"
                  className="x"
                  aria-label="Eliminar tutor"
                  onClick={() => handleRemove(id)}
                >
                  ×
                </button>
              </span>
            );
          })}
        </div>
      )}
      {!isFull && (
        <Combobox
          options={availableTutors}
          value=""
          onChange={handlePick}
          placeholder={
            chips.length === 0
              ? "Selecciona un tutor..."
              : "Añadir un tutor más..."
          }
          emptyLabel="Sin tutores disponibles"
        />
      )}
    </div>
  );
}
