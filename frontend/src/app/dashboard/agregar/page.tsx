"use client";

import React from "react";
import DashboardHeader from "@widgets/header/DashboardHeader";
import { useDocumentData } from "./hooks/useDocumentData";
import DocumentFormNew from "./components/DocumentFormNew";
import FormSkeleton from "./components/FormSkeleton";
import AccessDenied from "./components/AccessDenied";

function getHeroCopy(
  userRole: string,
  defaultDocType: string,
  defaultSemester: string,
): { eyebrow: string; title: string; lede: string } {
  if (userRole === "Administrador") {
    return {
      eyebrow: `Registro · Período ${defaultSemester}`,
      title: "Registrar trabajo académico",
      lede: "Crea el registro inicial de un proyecto o tesis para el período activo. Asignación de jurado y seguimiento se manejan después desde la cola.",
    };
  }
  const isTesis = defaultDocType === "tesis";
  return {
    eyebrow: `Tu proyecto · Período ${defaultSemester}`,
    title: isTesis ? "Sube tu trabajo final" : "Sube tu propuesta inicial",
    lede: "Sólo necesitas el título, los tutores y al menos un archivo. El jurado lo asigna la administración.",
  };
}

export default function AgregarDocumentoPage() {
  const data = useDocumentData();

  const pageTitle =
    data.userRole === "Administrador"
      ? "Agregar Documento"
      : data.defaultDocType === "tesis"
        ? "Subir Tesis"
        : "Subir Proyecto";

  if (data.isStaffReviewer) {
    return (
      <>
        <DashboardHeader pageTitle="Acceso restringido" />
        <main className="flex-1 p-4 sm:p-5 lg:p-6 overflow-y-auto bg-surface-muted">
          <div className="max-w-5xl mx-auto space-y-4">
            <AccessDenied />
          </div>
        </main>
      </>
    );
  }

  const { eyebrow, title, lede } = getHeroCopy(
    data.userRole || "",
    data.defaultDocType,
    data.defaultSemester,
  );

  return (
    <>
      <DashboardHeader pageTitle={pageTitle} />

      <main className="flex-1 p-4 sm:p-5 lg:p-6 overflow-y-auto bg-surface-muted">
        <div className="max-w-5xl mx-auto space-y-4">
          {!data.isLoaded ? (
            <FormSkeleton />
          ) : (
            <>
              <section className="dashboard-hero-bg relative overflow-hidden rounded-2xl border border-border-subtle px-6 sm:px-7 py-6 mb-6">
                <div className="relative z-10 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div className="flex flex-col gap-1.5">
                    <p className="flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.14em] text-primary">
                      <span
                        aria-hidden
                        className="inline-block h-[2px] w-6 rounded-full bg-gradient-to-r from-primary to-[var(--brand-orange)]"
                      />
                      {eyebrow}
                    </p>
                    <h1 className="text-3xl font-extrabold leading-tight tracking-[-0.03em] text-text-strong md:text-[34px]">
                      {title}
                    </h1>
                    <p className="max-w-[520px] text-sm font-medium leading-relaxed text-text-muted mt-1">
                      {lede}
                    </p>
                  </div>
                  <span className="period-chip">
                    <span className="period-chip-lbl">Período</span>
                    {data.defaultSemester}
                  </span>
                </div>
              </section>

              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <DocumentFormNew
                  userRole={data.userRole || ""}
                  currentUser={data.currentUser}
                  isStudent={data.isStudent}
                  students={data.students}
                  tutors={data.tutors}
                  jurados={data.jurados}
                  partners={data.partners}
                  semesters={data.semesters}
                  defaultSemester={data.defaultSemester}
                  defaultDocType={data.defaultDocType}
                  allowedDocumentTypes={data.allowedDocumentTypes}
                />
              </div>
            </>
          )}
        </div>
      </main>
    </>
  );
}
