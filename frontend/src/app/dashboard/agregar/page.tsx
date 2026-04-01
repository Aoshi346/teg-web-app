"use client";

import React from "react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import { useDocumentData } from "./hooks/useDocumentData";
import DocumentFormNew from "./components/DocumentFormNew";
import FormSkeleton from "./components/FormSkeleton";
import AccessDenied from "./components/AccessDenied";

export default function AgregarDocumentoPage() {
  const data = useDocumentData();

  return (
    <>
      <DashboardHeader pageTitle="Agregar Documento" />

      <PageTransition>
        <main className="flex-1 p-4 sm:p-5 lg:p-6 overflow-y-auto bg-gray-50/50">
          <div className="max-w-5xl mx-auto space-y-4">
            {data.isStaffReviewer ? (
              <AccessDenied />
            ) : !data.isLoaded ? (
              <FormSkeleton />
            ) : (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <DocumentFormNew
                  userRole={data.userRole || ""}
                  currentUser={data.currentUser}
                  isStudent={data.isStudent}
                  students={data.students}
                  tutors={data.tutors}
                  partners={data.partners}
                  semesters={data.semesters}
                  defaultSemester={data.defaultSemester}
                  defaultDocType={data.defaultDocType}
                  allowedDocumentTypes={data.allowedDocumentTypes}
                />
              </div>
            )}
          </div>
        </main>
      </PageTransition>
    </>
  );
}
