"use client";

import { useFormContext } from "react-hook-form";
import { useState } from "react";
import Combobox from "./Combobox";
import type { UserOption } from "../hooks/useDocumentData";
import type { DocumentFormData } from "../schema";

interface AdvisorsChipsProps {
  tutors: UserOption[];
}

export default function AdvisorsChips({ tutors }: AdvisorsChipsProps) {
  const { watch, setValue } = useFormContext<DocumentFormData>();
  const [pending, setPending] = useState<number | "">("");

  const advisors = watch("advisors") ?? [];
  const chips = (advisors).filter((a): a is number => typeof a === "number");
  const availableTutors = tutors.filter((t) => !chips.includes(t.id));

  function handleAdd() {
    if (pending === "") return;
    if (chips.includes(pending)) {
      setPending("");
      return;
    }
    setValue("advisors", [...chips, pending], { shouldValidate: true });
    setPending("");
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
      <div className="a-input-wrap">
        <Combobox
          options={availableTutors}
          value={pending}
          onChange={(val) => setPending(val)}
          placeholder="Buscar tutor..."
          emptyLabel="Sin tutores"
          disabled={chips.length >= 2}
        />
        <button
          type="button"
          className="add"
          disabled={chips.length >= 2 || pending === ""}
          onClick={handleAdd}
        >
          + Añadir
        </button>
      </div>
    </div>
  );
}
