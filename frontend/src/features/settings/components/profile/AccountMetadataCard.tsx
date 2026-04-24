"use client";
import React from "react";
import { Info } from "lucide-react";
import type { AccountMetadata } from "../../types/settings";

interface AccountMetadataCardProps {
  metadata: AccountMetadata;
}

function formatDate(isoOrNull: string | null): string {
  if (!isoOrNull) return "—";
  const d = new Date(isoOrNull);
  return d.toLocaleDateString("es-VE", { day: "numeric", month: "long", year: "numeric" });
}

export function AccountMetadataCard({ metadata }: AccountMetadataCardProps) {
  return (
    <aside className="bg-surface border border-border-subtle rounded-[14px] p-[18px] shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
      <h4 className="text-[13px] font-bold text-text-strong mb-3.5 pb-3 border-b border-border-subtle flex items-center gap-1.5">
        <Info className="w-3.5 h-3.5 text-primary" />
        Información de la cuenta
      </h4>
      <dl className="flex flex-col gap-3.5">
        <div className="flex flex-col gap-0.5">
          <dt className="text-[11px] font-semibold text-text-muted uppercase tracking-[0.05em]">Rol</dt>
          <dd className="text-[13.5px] font-semibold text-text-strong">{metadata.role}</dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="text-[11px] font-semibold text-text-muted uppercase tracking-[0.05em]">Semestre asignado</dt>
          <dd className="text-[13.5px] font-semibold text-text-strong">{metadata.semesterPeriod || "—"}</dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="text-[11px] font-semibold text-text-muted uppercase tracking-[0.05em]">Cuenta creada</dt>
          <dd className="text-[13.5px] font-semibold text-text-strong">{formatDate(metadata.dateJoined)}</dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="text-[11px] font-semibold text-text-muted uppercase tracking-[0.05em]">Último acceso</dt>
          <dd className="text-[13.5px] font-semibold text-text-strong">{formatDate(metadata.lastLogin)}</dd>
        </div>
      </dl>
    </aside>
  );
}
