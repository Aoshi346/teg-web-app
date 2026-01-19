"use client";

import React from "react";
import { useRouter, useParams } from "next/navigation";
import {
  ArrowLeft,
  Calendar,
  User,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
} from "lucide-react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import { mockTesis } from "@/lib/data/mockData";

export default function TesisDetailsPage() {
  const router = useRouter();
  const params = useParams();
  const id = Number(params.id);

  const project = mockTesis.find((p) => p.id === id);

  if (!project) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">
            Tesis no encontrada
          </h2>
          <button
            onClick={() => router.back()}
            className="mt-4 text-blue-600 hover:underline"
          >
            Volver
          </button>
        </div>
      </div>
    );
  }

  const getStatusColor = () => {
    switch (project.status) {
      case "checked":
        return "text-green-600 bg-green-50 border-green-200";
      case "pending":
        return "text-amber-600 bg-amber-50 border-amber-200";
      case "rejected":
        return "text-red-600 bg-red-50 border-red-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getStatusIcon = () => {
    switch (project.status) {
      case "checked":
        return <CheckCircle className="w-6 h-6" />;
      case "pending":
        return <Clock className="w-6 h-6" />;
      case "rejected":
        return <XCircle className="w-6 h-6" />;
      default:
        return null;
    }
  };

  return (
    <>
      <DashboardHeader pageTitle="Detalles de Tesis" />
      <PageTransition>
        <main className="flex-1 p-4 md:p-8 overflow-y-auto bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <button
              onClick={() => router.back()}
              className="flex items-center text-gray-600 hover:text-gray-900 mb-6 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Volver
            </button>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-6 md:p-8 border-b border-gray-100">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  <div className="flex-1">
                    <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                      {project.title}
                    </h1>
                    <div
                      className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border ${getStatusColor()}`}
                    >
                      {getStatusIcon()}
                      <span className="font-semibold capitalize">
                        {project.status === "checked"
                          ? "Aprobado"
                          : project.status === "rejected"
                            ? "Rechazado"
                            : "Pendiente"}
                      </span>
                    </div>
                  </div>
                  {project.score !== undefined && (
                    <div className="flex flex-col items-center justify-center bg-gray-50 rounded-xl p-4 border border-gray-100 min-w-[120px]">
                      <span className="text-sm text-gray-500 font-medium uppercase tracking-wider">
                        Calificación
                      </span>
                      <span
                        className={`text-4xl font-bold ${
                          project.score >= 10
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {project.score}/20
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-6 md:p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Información del Estudiante
                    </h3>
                    <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                      <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                        <User className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {project.student}
                        </p>
                        <p className="text-sm text-gray-500">Estudiante</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Tutor Académico
                    </h3>
                    <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                      <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {project.advisor}
                        </p>
                        <p className="text-sm text-gray-500">Tutor</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Fechas Importantes
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 border-b border-gray-100">
                        <span className="text-gray-600 flex items-center gap-2">
                          <Calendar className="w-4 h-4" />
                          Fecha de Entrega
                        </span>
                        <span className="font-medium text-gray-900">
                          {project.submittedDate}
                        </span>
                      </div>
                      {project.reviewDate && (
                        <div className="flex items-center justify-between p-3 border-b border-gray-100">
                          <span className="text-gray-600 flex items-center gap-2">
                            <CheckCircle className="w-4 h-4" />
                            Fecha de Revisión
                          </span>
                          <span className="font-medium text-gray-900">
                            {project.reviewDate}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Attached Files & Documents */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Documentos Adicionales
                    </h3>
                    {project.files && project.files.length > 0 ? (
                      <div className="space-y-3">
                        {project.files.map((file, index) => (
                          <a
                            key={index}
                            href={file.url}
                            className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-xl hover:border-emerald-300 hover:shadow-md transition-all group"
                          >
                            <div
                              className={`p-2 rounded-lg ${
                                file.type === "pdf"
                                  ? "bg-red-50 text-red-500"
                                  : "bg-blue-50 text-blue-500"
                              }`}
                            >
                              <FileText className="w-5 h-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-gray-900 truncate group-hover:text-emerald-600 transition-colors">
                                {file.name}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-gray-500">
                                <span className="uppercase">{file.type}</span>
                                <span>•</span>
                                <span>{file.date}</span>
                              </div>
                            </div>
                          </a>
                        ))}
                      </div>
                    ) : (
                      <div className="p-4 border border-dashed border-gray-300 rounded-lg text-center bg-gray-50/50">
                        <p className="text-sm text-gray-500">
                          No hay documentos adjuntos.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Footer */}
              <div className="p-6 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
                {project.status === "pending" && (
                  <button
                    onClick={() =>
                      router.push(`/dashboard/tesis/${project.id}/evaluar`)
                    }
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                  >
                    Evaluar Tesis
                  </button>
                )}
              </div>
            </div>
          </div>
        </main>
      </PageTransition>
    </>
  );
}
