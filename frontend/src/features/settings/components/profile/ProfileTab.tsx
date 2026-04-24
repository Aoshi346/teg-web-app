"use client";
import React, { useEffect, useState } from "react";
import { getUser, updateProfile } from "@features/auth/api/clientAuth";
import { getSemesters } from "@features/semesters/api/semesters";
import Toast, { type ToastType } from "@shared/ui/Toast";
import { ProfileForm } from "./ProfileForm";
import { AccountMetadataCard } from "./AccountMetadataCard";
import type { ProfileInput } from "../../lib/schemas";
import type { AccountMetadata } from "../../types/settings";

export function ProfileTab() {
  const [initial, setInitial] = useState<ProfileInput | null>(null);
  const [metadata, setMetadata] = useState<AccountMetadata | null>(null);
  const [toast, setToast] = useState<{ msg: string; type: ToastType; isVisible: boolean }>({
    msg: "",
    type: "info",
    isVisible: false,
  });

  useEffect(() => {
    async function load() {
      const u = getUser();
      if (!u) return;
      const base: ProfileInput = u.role === "Estudiante"
        ? {
            role: "Estudiante",
            fullName: u.fullName || "",
            email: u.email || "",
            nationality: (u.nationality as "V" | "E" | "P") || "V",
            cedula: String(u.cedula || ""),
            phone: u.phone || "",
            semester: (u.semester as "9no" | "10mo" | "N/A") || "N/A",
          }
        : {
            role: u.role as "Administrador" | "Tutor" | "Jurado",
            fullName: u.fullName || "",
            email: u.email || "",
            nationality: (u.nationality as "V" | "E" | "P") || "V",
            cedula: String(u.cedula || ""),
            phone: u.phone || "",
          };
      setInitial(base);

      let semesterPeriod: string | null = null;
      try {
        const semesters = await getSemesters();
        semesterPeriod = semesters.find((s) => s.is_active)?.period ?? null;
      } catch {
        semesterPeriod = null;
      }

      setMetadata({
        role: u.role,
        dateJoined: u.dateJoined || new Date().toISOString(),
        lastLogin: u.lastLogin || null,
        semesterPeriod,
      });
    }
    load();
  }, []);

  if (!initial || !metadata) return <div className="text-gray-500 text-sm">Cargando perfil...</div>;

  async function handleSubmit(values: ProfileInput) {
    try {
      await updateProfile({
        fullName: values.fullName,
        cedula: values.cedula,
        nationality: values.nationality,
        phone: values.phone || "",
        ...(values.role === "Estudiante" ? { semester: values.semester } : {}),
      });
      setToast({ msg: "Perfil actualizado", type: "success", isVisible: true });
    } catch (e) {
      setToast({ msg: "Error al guardar", type: "error", isVisible: true });
      throw e;
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-5">
      <ProfileForm initialValues={initial} onSubmit={handleSubmit} />
      <AccountMetadataCard metadata={metadata} />
      <Toast
        message={toast.msg}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={() => setToast((p) => ({ ...p, isVisible: false }))}
      />
    </div>
  );
}
