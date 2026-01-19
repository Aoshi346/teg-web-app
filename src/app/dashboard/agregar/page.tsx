"use client";

import React, { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { FileText, BookOpen, CheckCircle } from "lucide-react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import Banner from "@/components/ui/Banner";
import { addProyecto, addTesis } from "@/lib/data/mockData";
import { getAvailableSemesterPeriods } from "@/lib/semesters";

type DocumentType = "proyecto" | "tesis";

interface FormData {
  title: string;
  student: string;
  advisor: string;
  semesterPeriod: string;
}

export default function AgregarDocumentoPage() {
  const router = useRouter();
  const [documentType, setDocumentType] = useState<DocumentType>("proyecto");
  const [formData, setFormData] = useState<FormData>({
    title: "",
    student: "",
    advisor: "",
    semesterPeriod: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [bannerState, setBannerState] = useState<{
    visible: boolean;
    message: string;
    type: "success" | "error" | "warning" | "info";
  }>({ visible: false, message: "", type: "info" });

  const availablePeriods = useMemo(() => getAvailableSemesterPeriods(), []);

  // Set default period on first render
  React.useEffect(() => {
    if (availablePeriods.length > 0 && !formData.semesterPeriod) {
      setFormData((prev) => ({ ...prev, semesterPeriod: availablePeriods[0] }));
    }
  }, [availablePeriods, formData.semesterPeriod]);

  const semesterLabel =
    documentType === "proyecto"
      ? "9no Semestre (Proyecto TEG)"
      : "10mo Semestre (TEG)";

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (
      !formData.title.trim() ||
      !formData.student.trim() ||
      !formData.advisor.trim()
    ) {
      setBannerState({
        visible: true,
        message: "Por favor complete todos los campos requeridos.",
        type: "error",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const newDocument = {
        title: formData.title.trim(),
        student: formData.student.trim(),
        advisor: formData.advisor.trim(),
        submittedDate: new Date().toISOString().split("T")[0],
        status: "pending" as const,
        semester: formData.semesterPeriod,
      };

      if (documentType === "proyecto") {
        addProyecto(newDocument);
      } else {
        addTesis(newDocument);
      }

      // Simulate network delay
      await new Promise((resolve) => setTimeout(resolve, 500));

      setBannerState({
        visible: true,
        message: `${documentType === "proyecto" ? "Proyecto" : "Tesis"} agregado exitosamente.`,
        type: "success",
      });

      // Reset form
      setFormData({
        title: "",
        student: "",
        advisor: "",
        semesterPeriod: availablePeriods[0] || "",
      });

      // Redirect after short delay
      setTimeout(() => {
        router.push(
          documentType === "proyecto"
            ? "/dashboard/proyectos"
            : "/dashboard/tesis",
        );
      }, 1500);
    } catch {
      setBannerState({
        visible: true,
        message: "Error al agregar el documento. Intente nuevamente.",
        type: "error",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <DashboardHeader pageTitle="Agregar Documento" />

      {bannerState.visible && (
        <div className="fixed top-4 inset-x-0 z-[9999] flex justify-center px-4 pointer-events-none">
          <div className="pointer-events-auto w-full max-w-xl">
            <Banner
              visible={bannerState.visible}
              message={bannerState.message}
              type={bannerState.type}
              onClose={() => setBannerState((s) => ({ ...s, visible: false }))}
              autoHide={5000}
            />
          </div>
        </div>
      )}

      <PageTransition>
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-gray-50">
          <div className="max-w-2xl mx-auto">
            {/* Document Type Selector */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Tipo de Documento
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setDocumentType("proyecto")}
                  className={`relative flex flex-col items-center gap-3 p-6 rounded-xl border-2 transition-all duration-200 ${
                    documentType === "proyecto"
                      ? "border-blue-500 bg-blue-50 shadow-md"
                      : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <FileText
                    className={`w-8 h-8 ${documentType === "proyecto" ? "text-blue-600" : "text-gray-500"}`}
                  />
                  <div className="text-center">
                    <p
                      className={`font-semibold ${documentType === "proyecto" ? "text-blue-900" : "text-gray-700"}`}
                    >
                      Proyecto (PTEG)
                    </p>
                    <p className="text-xs text-gray-500 mt-1">9no Semestre</p>
                  </div>
                  {documentType === "proyecto" && (
                    <div className="absolute top-3 right-3">
                      <CheckCircle className="w-5 h-5 text-blue-600" />
                    </div>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setDocumentType("tesis")}
                  className={`relative flex flex-col items-center gap-3 p-6 rounded-xl border-2 transition-all duration-200 ${
                    documentType === "tesis"
                      ? "border-emerald-500 bg-emerald-50 shadow-md"
                      : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <BookOpen
                    className={`w-8 h-8 ${documentType === "tesis" ? "text-emerald-600" : "text-gray-500"}`}
                  />
                  <div className="text-center">
                    <p
                      className={`font-semibold ${documentType === "tesis" ? "text-emerald-900" : "text-gray-700"}`}
                    >
                      Trabajo Especial (TEG)
                    </p>
                    <p className="text-xs text-gray-500 mt-1">10mo Semestre</p>
                  </div>
                  {documentType === "tesis" && (
                    <div className="absolute top-3 right-3">
                      <CheckCircle className="w-5 h-5 text-emerald-600" />
                    </div>
                  )}
                </button>
              </div>
            </div>

            {/* Form */}
            <form
              onSubmit={handleSubmit}
              className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                Información del Documento
              </h2>

              <div className="space-y-5">
                {/* Title */}
                <div>
                  <label
                    htmlFor="title"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Título <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    placeholder="Ingrese el título del documento"
                    className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-100 transition-all text-sm"
                    required
                  />
                </div>

                {/* Student */}
                <div>
                  <label
                    htmlFor="student"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Estudiante <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="student"
                    name="student"
                    value={formData.student}
                    onChange={handleInputChange}
                    placeholder="Nombre completo del estudiante"
                    className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-100 transition-all text-sm"
                    required
                  />
                </div>

                {/* Advisor */}
                <div>
                  <label
                    htmlFor="advisor"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Tutor <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="advisor"
                    name="advisor"
                    value={formData.advisor}
                    onChange={handleInputChange}
                    placeholder="Nombre del tutor o director"
                    className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-100 transition-all text-sm"
                    required
                  />
                </div>

                {/* Semester Period */}
                <div>
                  <label
                    htmlFor="semesterPeriod"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Período
                  </label>
                  <select
                    id="semesterPeriod"
                    name="semesterPeriod"
                    value={formData.semesterPeriod}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-100 transition-all text-sm"
                  >
                    {availablePeriods.map((period) => (
                      <option key={period} value={period}>
                        {period}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Semester Type Display */}
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Semestre:</span>{" "}
                    <span
                      className={
                        documentType === "proyecto"
                          ? "text-blue-600"
                          : "text-emerald-600"
                      }
                    >
                      {semesterLabel}
                    </span>
                  </p>
                </div>
              </div>

              {/* Submit Button */}
              <div className="mt-8 flex flex-col sm:flex-row gap-3">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={`flex-1 flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-white transition-all shadow-md hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed ${
                    documentType === "proyecto"
                      ? "bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
                      : "bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700"
                  }`}
                >
                  {isSubmitting ? (
                    <>
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Guardando...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5" />
                      Agregar{" "}
                      {documentType === "proyecto" ? "Proyecto" : "Tesis"}
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="px-6 py-3.5 rounded-xl font-semibold text-gray-700 bg-white border-2 border-gray-300 hover:bg-gray-50 hover:border-gray-400 transition-all"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </main>
      </PageTransition>
    </>
  );
}
