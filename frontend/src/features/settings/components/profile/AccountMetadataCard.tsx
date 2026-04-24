"use client";
import React from "react";
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
    <aside className="p-5 bg-white rounded-lg border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Información de la cuenta</h3>
      <dl className="flex flex-col gap-3 text-sm">
        <div>
          <dt className="text-xs uppercase tracking-wide text-gray-500">Rol</dt>
          <dd className="font-medium text-gray-900">{metadata.role}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-gray-500">Cuenta creada</dt>
          <dd className="text-gray-900">{formatDate(metadata.dateJoined)}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-gray-500">Último acceso</dt>
          <dd className="text-gray-900">{formatDate(metadata.lastLogin)}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-gray-500">Semestre asignado</dt>
          <dd className="text-gray-900">{metadata.semesterPeriod || "—"}</dd>
        </div>
      </dl>
    </aside>
  );
}
