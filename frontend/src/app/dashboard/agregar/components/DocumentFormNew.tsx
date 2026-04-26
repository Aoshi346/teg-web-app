"use client";

import React, { useCallback, useRef, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FormProvider, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { documentFormSchema, type DocumentFormData } from "../schema";
import type { UserOption } from "../hooks/useDocumentData";
import DocumentTypeSelector from "./DocumentTypeSelector";
import AdvisorsChips from "./AdvisorsChips";
import Combobox from "./Combobox";
import Banner from "@shared/ui/Banner";
import { cn } from "@shared/lib/utils";
import { PenLine, User as UserIcon, Users, GraduationCap, Scale } from "lucide-react";
import {
  createProject,
  uploadProjectFile,
} from "@features/projects/api/projectService";
import { getCurrentSemester } from "@features/semesters/api/semesters";

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
  jurados: UserOption[];
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
  jurados,
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
      reviewer: null,
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
        ...(userRole === "Administrador" && data.studentId
          ? { student: data.studentId as number }
          : {}),
        ...(data.partnerId ? { partner: data.partnerId as number } : {}),
        ...(userRole === "Administrador" && data.reviewer
          ? { reviewer: data.reviewer }
          : {}),
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
        reviewer: null,
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

  const submitLabel = isStudent
    ? isProyecto
      ? "Subir proyecto"
      : "Subir tesis"
    : "Registrar trabajo";

  const formSubtitle = isStudent
    ? "2 secciones para completar."
    : "Completa las 3 secciones a continuación.";

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
        <div className="agg-stack">
          {/* ── Left: Type selector + Period ── */}
          <div className="space-y-3">
            <DocumentTypeSelector
              value={documentType}
              onChange={(type) => setValue("documentType", type)}
              allowedTypes={allowedDocumentTypes as ("proyecto" | "tesis")[]}
              disabled={isStudent && allowedDocumentTypes.length === 1}
            />

            <div className="agg-period-card">
              <p className="agg-period-lbl">Período</p>
              <p className="agg-period-val">
                {semesterPeriod || defaultSemester || "—"}
              </p>
              <p className="agg-period-sub">
                {isStudent ? "Asignado automáticamente" : "Definido por administración"}
              </p>
            </div>
          </div>

          {/* ── Right: Sectioned form ── */}
          <form onSubmit={handleSubmit(onSubmit)} className="agg-form-card">
            <div className="agg-form-head">
              <div>
                <h3 className="agg-form-h">
                  {isStudent
                    ? isProyecto
                      ? "Tu proyecto"
                      : "Tu tesis"
                    : "Registro del trabajo"}
                </h3>
                <p className="agg-form-sub">{formSubtitle}</p>
              </div>
              <span className={`ts-pill ${isProyecto ? "pteg" : "teg"}`}>
                <span className="dt" />
                {isProyecto ? "PTEG" : "TEG"} · {isProyecto ? "9°" : "10°"} semestre
              </span>
            </div>

            <div className="agg-form-body">
              {/* ── Admin layout: 3 sections ── */}
              {!isStudent && (
                <>
                  {/* Section 01: Identificación */}
                  <section className="agg-form-section">
                    <div className="agg-sec-head">
                      <span className="agg-sec-num font-display">01</span>
                      <span className="agg-sec-title">Identificación</span>
                      <span className="agg-sec-hint">Título y modalidad</span>
                    </div>
                    <div className="agg-section-body">
                      <div className="agg-field">
                        <label htmlFor="title" className="agg-field-label">
                          <PenLine className="agg-field-ic" aria-hidden />
                          Título del {isProyecto ? "proyecto" : "trabajo"}{" "}
                          <span className="agg-req">*</span>
                        </label>
                        <input
                          type="text"
                          id="title"
                          {...register("title")}
                          placeholder="Ingresa el título completo..."
                          className={cn(
                            "agg-field-input",
                            errors.title && "agg-field-error",
                          )}
                        />
                        {errors.title && (
                          <span className="agg-field-help" style={{ color: "var(--destructive)" }}>
                            {errors.title.message}
                          </span>
                        )}
                        {!errors.title && (
                          <span className="agg-field-help">
                            Mínimo 10 caracteres. Aparecerá en la cola de seguimiento.
                          </span>
                        )}
                      </div>
                    </div>
                  </section>

                  {/* Section 02: Equipo */}
                  <section className="agg-form-section">
                    <div className="agg-sec-head">
                      <span className="agg-sec-num font-display">02</span>
                      <span className="agg-sec-title">Equipo</span>
                      <span className="agg-sec-hint">Estudiante, compañero, tutores</span>
                    </div>
                    <div className="agg-section-body">
                      <div className="agg-row-2">
                        <div className="agg-field">
                          <label className="agg-field-label">
                            <UserIcon className="agg-field-ic" aria-hidden />
                            Estudiante <span className="agg-req">*</span>
                          </label>
                          <Combobox
                            options={students}
                            value={studentId as number | ""}
                            onChange={(val) =>
                              setValue("studentId", val, { shouldValidate: true })
                            }
                            placeholder="Buscar estudiante..."
                            emptyLabel="Sin estudiantes"
                            error={!!errors.studentId}
                          />
                          {errors.studentId && (
                            <span className="agg-field-help" style={{ color: "var(--destructive)" }}>
                              {errors.studentId.message}
                            </span>
                          )}
                        </div>

                        <div className="agg-field">
                          <label className="agg-field-label">
                            <Users className="agg-field-ic" aria-hidden />
                            Compañero{" "}
                            <span style={{ color: "var(--text-faint)", fontWeight: 600 }}>
                              (opcional)
                            </span>
                          </label>
                          <Combobox
                            options={filteredPartners}
                            value={watch("partnerId") as number | "" | null}
                            onChange={(val) => setValue("partnerId", val)}
                            placeholder="Buscar compañero..."
                            emptyLabel="Sin compañeros"
                            allowClear
                          />
                        </div>
                      </div>

                      <div className="agg-field">
                        <label className="agg-field-label">
                          <GraduationCap className="agg-field-ic" aria-hidden />
                          Tutores académicos <span className="agg-req">*</span>
                        </label>
                        <AdvisorsChips tutors={tutors} />
                        <span className="agg-field-help">
                          Mínimo un tutor. Sin duplicados.
                        </span>
                      </div>

                      <div className="agg-field">
                        <label className="agg-field-label">
                          <Scale className="agg-field-ic" aria-hidden />
                          Jurado{" "}
                          <span style={{ color: "var(--text-faint)", fontWeight: 600 }}>
                            (opcional · admin)
                          </span>
                        </label>
                        <Combobox
                          options={jurados}
                          value={watch("reviewer") as number | null}
                          onChange={(val) =>
                            setValue("reviewer", val === "" ? null : (val as number), {
                              shouldValidate: true,
                            })
                          }
                          placeholder="Asignar luego desde Seguimiento..."
                          emptyLabel="Sin jurados"
                          allowClear
                        />
                      </div>
                    </div>
                  </section>

                  {/* Section 03: Archivos */}
                  <section className="agg-form-section">
                    <div className="agg-sec-head">
                      <span className="agg-sec-num font-display">03</span>
                      <span className="agg-sec-title">Archivos</span>
                      <span className="agg-sec-hint">PDF, DOC, DOCX · 10 MB c/u</span>
                    </div>
                    <div className="agg-section-body">
                      {renderDropzone()}
                    </div>
                  </section>
                </>
              )}

              {/* ── Estudiante layout: 2 sections ── */}
              {isStudent && (
                <>
                  {/* Section 01: Información */}
                  <section className="agg-form-section">
                    <div className="agg-sec-head">
                      <span className="agg-sec-num font-display">01</span>
                      <span className="agg-sec-title">Información</span>
                    </div>
                    <div className="agg-section-body">
                      <div className="agg-field">
                        <label htmlFor="title-est" className="agg-field-label">
                          <PenLine className="agg-field-ic" aria-hidden />
                          Título del {isProyecto ? "proyecto" : "trabajo"}{" "}
                          <span className="agg-req">*</span>
                        </label>
                        <input
                          type="text"
                          id="title-est"
                          {...register("title")}
                          placeholder="Ingresa el título completo..."
                          className={cn(
                            "agg-field-input",
                            errors.title && "agg-field-error",
                          )}
                        />
                        {errors.title && (
                          <span className="agg-field-help" style={{ color: "var(--destructive)" }}>
                            {errors.title.message}
                          </span>
                        )}
                      </div>

                      <div className="agg-row-2">
                        <div className="agg-field">
                          <label className="agg-field-label">
                            <UserIcon className="agg-field-ic" aria-hidden />
                            Estudiante
                          </label>
                          <input
                            type="text"
                            disabled
                            value={
                              currentUser?.fullName ||
                              currentUser?.email ||
                              "Estudiante"
                            }
                            className="agg-field-input agg-field-disabled"
                          />
                        </div>

                        <div className="agg-field">
                          <label className="agg-field-label">
                            <Users className="agg-field-ic" aria-hidden />
                            Compañero{" "}
                            <span style={{ color: "var(--text-faint)", fontWeight: 600 }}>
                              (opcional)
                            </span>
                          </label>
                          <Combobox
                            options={filteredPartners}
                            value={watch("partnerId") as number | "" | null}
                            onChange={(val) => setValue("partnerId", val)}
                            placeholder="Buscar compañero..."
                            emptyLabel="Sin compañeros"
                            allowClear
                          />
                        </div>
                      </div>

                      <div className="agg-field">
                        <label className="agg-field-label">
                          <GraduationCap className="agg-field-ic" aria-hidden />
                          Tutores académicos <span className="agg-req">*</span>
                        </label>
                        <AdvisorsChips tutors={tutors} />
                        <span className="agg-field-help">
                          Mínimo un tutor.
                        </span>
                      </div>
                    </div>
                  </section>

                  {/* Section 02: Archivo */}
                  <section className="agg-form-section">
                    <div className="agg-sec-head">
                      <span className="agg-sec-num font-display">02</span>
                      <span className="agg-sec-title">Archivo</span>
                      <span className="agg-sec-hint">PDF, DOC, DOCX · 10 MB</span>
                    </div>
                    <div className="agg-section-body">
                      {renderDropzone()}
                    </div>
                  </section>
                </>
              )}
            </div>

            <div className="agg-form-actions">
              <span className="agg-form-meta">
                Los campos marcados con{" "}
                <span style={{ color: "var(--brand-orange)", fontWeight: 800 }}>*</span>{" "}
                son obligatorios.
              </span>
              <div className="agg-btnset">
                <button
                  type="button"
                  className="agg-btn agg-btn-ghost"
                  onClick={() => router.back()}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || isUploading}
                  className={cn(
                    "agg-btn",
                    isStudent ? "agg-btn-warn" : "agg-btn-primary",
                    (isSubmitting || isUploading) && "agg-btn-disabled",
                  )}
                >
                  {isSubmitting ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
                    submitLabel
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </FormProvider>
    </>
  );

  function renderDropzone() {
    return (
      <>
        <div
          className={cn("agg-dropzone", isDragOver && "is-over")}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
        >
          <div className="agg-dropzone-ic">↑</div>
          <p className="agg-dropzone-h">
            Arrastra documentos o <b>haz clic para seleccionar</b>
          </p>
          <p className="agg-dropzone-p">
            Acepta PDF, DOC, DOCX · máximo 10 MB cada uno.
          </p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx"
            style={{ display: "none" }}
            onChange={(e) => {
              if (e.target.files) handleFiles(e.target.files);
              e.currentTarget.value = "";
            }}
          />
        </div>

        {isUploading && (
          <div className="agg-upload-progress">
            <div
              className="agg-upload-bar"
              style={{ width: `${uploadProgress}%` }}
            />
            <span className="agg-upload-pct">{uploadProgress}%</span>
          </div>
        )}

        {errors.files && (
          <span className="agg-field-help" style={{ color: "var(--destructive)" }}>
            {errors.files.message}
          </span>
        )}

        {selectedFiles.length > 0 && (
          <div className="agg-file-list">
            {selectedFiles.map((file, i) => (
              <div key={i} className="filecard">
                <div className="agg-fc-ic">
                  {file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "DOC"}
                </div>
                <span className="agg-fc-nm">{file.name}</span>
                <span className="agg-fc-sz">{Math.round(file.size / 1024)} KB</span>
                <button
                  type="button"
                  className="agg-fc-x"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(i);
                  }}
                  aria-label="Quitar archivo"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </>
    );
  }
}
