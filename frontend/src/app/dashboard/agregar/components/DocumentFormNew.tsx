"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FormProvider, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  FileText,
  BookOpen,
  PenTool,
  ArrowRight,
  Users,
  User as UserIcon,
  Upload,
  X,
  AlertCircle,
  File,
  Calendar,
  GraduationCap,
} from "lucide-react";
import { documentFormSchema, type DocumentFormData } from "../schema";
import type { UserOption } from "../hooks/useDocumentData";
import DocumentTypeSelector from "./DocumentTypeSelector";
import AdvisorsFieldArray from "./AdvisorsFieldArray";
import Combobox from "./Combobox";
import Banner from "@/components/ui/Banner";
import {
  createProject,
  uploadProjectFile,
} from "@/features/projects/projectService";
import { getCurrentSemester } from "@/lib/semesters";

interface DocumentFormNewProps {
  userRole: string;
  currentUser: {
    id?: number;
    fullName?: string;
    email: string;
    semester?: string;
  } | null;
  isStudent: boolean;
  students: UserOption[];
  tutors: UserOption[];
  partners: UserOption[];
  semesters: string[];
  defaultSemester: string;
  defaultDocType: "proyecto" | "tesis";
  allowedDocumentTypes: readonly ("proyecto" | "tesis")[];
}

export default function DocumentFormNew({
  userRole,
  currentUser,
  isStudent,
  students,
  tutors,
  partners,
  semesters,
  defaultSemester,
  defaultDocType,
  allowedDocumentTypes,
}: DocumentFormNewProps) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isDragOver, setIsDragOver] = useState(false);

  const [banner, setBanner] = useState<{
    visible: boolean;
    message: string;
    type: "success" | "error" | "warning" | "info";
  }>({ visible: false, message: "", type: "info" });

  const methods = useForm<DocumentFormData>({
    resolver: zodResolver(documentFormSchema),
    defaultValues: {
      title: "",
      documentType: defaultDocType,
      studentId:
        userRole !== "Administrador" && currentUser?.id ? currentUser.id : "",
      partnerId: "",
      advisors: [""],
      semesterPeriod: defaultSemester,
      files: [],
      userRole: userRole || "",
    },
    mode: "onTouched",
  });

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
    reset,
  } = methods;

  useEffect(() => {
    if (userRole !== "Administrador" && currentUser?.id) {
      setValue("studentId", currentUser.id);
    }
  }, [userRole, currentUser?.id, setValue]);

  useEffect(() => {
    if (defaultSemester) setValue("semesterPeriod", defaultSemester);
  }, [defaultSemester, setValue]);

  const documentType = watch("documentType");
  const selectedFiles = watch("files") || [];
  const studentId = watch("studentId");
  const semesterPeriod = watch("semesterPeriod");
  const isProyecto = documentType === "proyecto";

  // File handling
  const handleFiles = useCallback(
    (fileList: FileList | File[]) => {
      const files = Array.from(fileList);
      const valid = files.filter((f) => {
        const ext = f.name.split(".").pop()?.toLowerCase();
        return ["pdf", "doc", "docx"].includes(ext || "");
      });
      if (valid.length < files.length) {
        setBanner({
          visible: true,
          message:
            "Algunos archivos fueron ignorados. Solo se permiten PDF y Word.",
          type: "warning",
        });
      }
      const current = watch("files") || [];
      setValue("files", [...current, ...valid], { shouldValidate: true });
    },
    [setValue, watch],
  );

  const removeFile = useCallback(
    (index: number) => {
      const current = watch("files") || [];
      setValue(
        "files",
        current.filter((_, i) => i !== index),
        { shouldValidate: true },
      );
    },
    [setValue, watch],
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };
  const handleDragLeave = () => setIsDragOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
  };

  const onSubmit = async (data: DocumentFormData) => {
    try {
      const validAdvisors = data.advisors.filter(
        (a): a is number => a !== "",
      );

      const created = await createProject({
        title: data.title,
        advisors: validAdvisors,
        period: data.semesterPeriod,
        project_type: data.documentType,
        status: "pending",
        ...(userRole === "Administrador" && data.studentId
          ? { student: data.studentId as number }
          : {}),
        ...(data.partnerId ? { partner: data.partnerId as number } : {}),
      });

      const files = data.files || [];
      if (files.length > 0) {
        setIsUploading(true);
        for (let i = 0; i < files.length; i++) {
          await uploadProjectFile(created.id, files[i]);
          setUploadProgress(Math.round(((i + 1) / files.length) * 100));
        }
        setIsUploading(false);
        setUploadProgress(0);
      }

      setBanner({
        visible: true,
        message: `${data.documentType === "proyecto" ? "Proyecto" : "Tesis"} registrado exitosamente.`,
        type: "success",
      });

      reset({
        title: "",
        documentType: defaultDocType,
        studentId:
          userRole === "Administrador" ? "" : currentUser?.id || "",
        partnerId: "",
        advisors: [""],
        semesterPeriod:
          semesters[0] || defaultSemester || getCurrentSemester(),
        files: [],
        userRole: userRole || "",
      });

      setTimeout(() => {
        router.push(
          data.documentType === "proyecto"
            ? "/dashboard/proyectos"
            : "/dashboard/tesis",
        );
      }, 1200);
    } catch {
      setBanner({
        visible: true,
        message: "Error al registrar el documento. Intente nuevamente.",
        type: "error",
      });
    }
  };

  const filteredPartners = partners.filter(
    (p) => p.id !== (Number(studentId) || currentUser?.id),
  );

  return (
    <>
      {banner.visible && (
        <div className="fixed top-4 inset-x-0 z-[9999] flex justify-center px-4 pointer-events-none">
          <div className="pointer-events-auto w-full max-w-xl">
            <Banner
              visible={banner.visible}
              message={banner.message}
              type={banner.type}
              onClose={() => setBanner((s) => ({ ...s, visible: false }))}
              autoHide={5000}
            />
          </div>
        </div>
      )}

      <FormProvider {...methods}>
        <div className="grid lg:grid-cols-[280px_1fr] gap-5">
          {/* ── Left: Type + Period ── */}
          <div className="space-y-4">
            <DocumentTypeSelector
              value={documentType}
              onChange={(type) => setValue("documentType", type)}
              allowedTypes={allowedDocumentTypes as ("proyecto" | "tesis")[]}
              disabled={isStudent && allowedDocumentTypes.length === 1}
            />

            {/* Active period — read only */}
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                Período activo
              </p>
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                  <Calendar className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-sm font-bold text-gray-900">
                    {semesterPeriod || defaultSemester || "—"}
                  </p>
                  <p className="text-[11px] text-gray-400">
                    Definido por el administrador
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* ── Right: Form ── */}
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
          >
            <div className="p-5 sm:p-6 space-y-5">
              {/* Header */}
              <div className="flex items-center gap-3 pb-4 border-b border-gray-100">
                <div
                  className={`p-2.5 rounded-xl ${
                    isProyecto
                      ? "bg-blue-50 text-blue-600"
                      : "bg-emerald-50 text-emerald-600"
                  }`}
                >
                  {isProyecto ? (
                    <FileText className="w-5 h-5" />
                  ) : (
                    <BookOpen className="w-5 h-5" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-bold text-gray-900">
                    Información del Documento
                  </h3>
                  <p className="text-xs text-gray-500">
                    Complete los detalles básicos
                  </p>
                </div>
                <div
                  className={`hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-bold border ${
                    isProyecto
                      ? "bg-blue-50 text-blue-700 border-blue-100"
                      : "bg-emerald-50 text-emerald-700 border-emerald-100"
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      isProyecto ? "bg-blue-500" : "bg-emerald-500"
                    }`}
                  />
                  {isProyecto ? "Proyecto TEG" : "Tesis TEG"}
                </div>
              </div>

              {/* Title */}
              <div className="space-y-1.5 group">
                <label
                  htmlFor="title"
                  className="text-xs font-semibold text-gray-600"
                >
                  Título del {isProyecto ? "Proyecto" : "Trabajo"}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <PenTool className="w-4 h-4 text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
                  </div>
                  <input
                    type="text"
                    id="title"
                    {...register("title")}
                    placeholder="Ingrese el título completo..."
                    className={`w-full pl-10 pr-4 py-2.5 bg-white border rounded-lg shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/10 transition-all text-sm ${
                      errors.title
                        ? "border-red-300 ring-2 ring-red-50"
                        : "border-gray-200 hover:border-indigo-300"
                    }`}
                  />
                  {errors.title && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-red-500 text-[11px] font-bold">
                      <AlertCircle className="w-3.5 h-3.5" />
                      <span>{errors.title.message}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* People row: Student + Partner side by side */}
              <div className="grid sm:grid-cols-2 gap-4">
                {/* Student */}
                <div className="space-y-1.5">
                  <div className="flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-purple-500" />
                    <label className="text-xs font-bold text-gray-700">
                      Estudiante
                    </label>
                  </div>
                  <div
                    className={`border rounded-lg p-3 ${
                      errors.studentId
                        ? "border-red-200 bg-red-50/30"
                        : "border-purple-100 bg-purple-50/30"
                    }`}
                  >
                    {userRole === "Estudiante" ? (
                      <input
                        type="text"
                        disabled
                        value={
                          currentUser?.fullName ||
                          currentUser?.email ||
                          "Estudiante"
                        }
                        className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600 cursor-not-allowed"
                      />
                    ) : (
                      <Combobox
                        options={students}
                        value={studentId as number | ""}
                        onChange={(val) =>
                          setValue("studentId", val, {
                            shouldValidate: true,
                          })
                        }
                        placeholder="Buscar estudiante..."
                        emptyLabel="Sin estudiantes"
                        error={!!errors.studentId}
                        icon={
                          <UserIcon className="w-4 h-4" />
                        }
                      />
                    )}
                    {errors.studentId && (
                      <p className="text-[11px] text-red-600 font-semibold mt-1">
                        {errors.studentId.message}
                      </p>
                    )}
                  </div>
                </div>

                {/* Partner */}
                <div className="space-y-1.5">
                  <div className="flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-indigo-500" />
                    <label className="text-xs font-bold text-gray-700">
                      Compañero
                    </label>
                    <span className="text-[10px] text-gray-400">
                      (Opcional)
                    </span>
                  </div>
                  <div className="border border-indigo-100 bg-indigo-50/30 rounded-lg p-3">
                    <Combobox
                      options={filteredPartners}
                      value={watch("partnerId") as number | "" | null}
                      onChange={(val) => setValue("partnerId", val)}
                      placeholder="Buscar compañero..."
                      emptyLabel="Sin compañeros"
                      allowClear
                      icon={<UserIcon className="w-4 h-4" />}
                    />
                  </div>
                </div>
              </div>

              {/* Advisors — compact */}
              <AdvisorsFieldArray tutors={tutors} />

              {/* File Upload (students only) — compact */}
              {userRole === "Estudiante" && (
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5">
                    <Upload className="w-4 h-4 text-indigo-500" />
                    <label className="text-xs font-bold text-gray-700">
                      Documento
                    </label>
                    <span className="text-[10px] text-gray-400">
                      PDF/Word, máx. 10 MB
                    </span>
                  </div>

                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-lg p-4 cursor-pointer transition-all text-center ${
                      errors.files
                        ? "border-red-300 bg-red-50/40"
                        : isDragOver
                          ? "border-indigo-400 bg-indigo-50/60"
                          : "border-gray-200 bg-gray-50/30 hover:border-indigo-300 hover:bg-indigo-50/30"
                    }`}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.doc,.docx"
                      multiple
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files) handleFiles(e.target.files);
                        e.target.value = "";
                      }}
                    />
                    <Upload
                      className={`w-6 h-6 mx-auto mb-1 ${
                        isDragOver ? "text-indigo-500" : "text-gray-300"
                      }`}
                    />
                    <p className="text-xs font-semibold text-gray-500">
                      {isDragOver
                        ? "Suelta aquí"
                        : "Arrastra o haz clic para seleccionar"}
                    </p>
                  </div>

                  {isUploading && (
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                      <span className="text-[11px] text-gray-500 font-semibold">
                        {uploadProgress}%
                      </span>
                    </div>
                  )}

                  {selectedFiles.length > 0 && (
                    <div className="space-y-1">
                      {selectedFiles.map((file, i) => {
                        const sizeMb = file.size > 1024 * 1024;
                        const sizeStr = sizeMb
                          ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
                          : `${(file.size / 1024).toFixed(0)} KB`;
                        const overLimit = file.size > 10 * 1024 * 1024;
                        return (
                          <div
                            key={i}
                            className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs ${
                              overLimit
                                ? "border-red-200 bg-red-50"
                                : "border-gray-100 bg-white"
                            }`}
                          >
                            <File
                              className={`w-3.5 h-3.5 flex-shrink-0 ${
                                overLimit ? "text-red-500" : "text-indigo-500"
                              }`}
                            />
                            <span className="flex-1 truncate text-gray-700 font-medium">
                              {file.name}
                            </span>
                            <span
                              className={`flex-shrink-0 ${
                                overLimit ? "text-red-500 font-bold" : "text-gray-400"
                              }`}
                            >
                              {sizeStr}
                            </span>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                removeFile(i);
                              }}
                              className="p-0.5 rounded hover:bg-gray-100 text-gray-400 hover:text-red-500"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {errors.files && (
                    <p className="text-[11px] text-red-600 font-semibold flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {errors.files.message}
                    </p>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="pt-4 border-t border-gray-100 flex flex-col sm:flex-row items-center gap-2">
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="w-full sm:w-auto px-5 py-2.5 rounded-xl font-semibold text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-all order-2 sm:order-1"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || isUploading}
                  className={`w-full sm:flex-1 flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl font-bold text-sm text-white shadow-lg transition-all hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none order-1 sm:order-2 ${
                    isProyecto
                      ? "bg-gradient-to-r from-blue-600 to-indigo-600 hover:shadow-blue-500/30"
                      : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:shadow-emerald-500/30"
                  }`}
                >
                  {isSubmitting ? (
                    <>
                      <svg
                        className="animate-spin h-4 w-4"
                        viewBox="0 0 24 24"
                      >
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
                      Agregar Documento
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </FormProvider>
    </>
  );
}
