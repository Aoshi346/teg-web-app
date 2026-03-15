"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  BookOpen,
  CheckCircle,
  User as UserIcon,
  GraduationCap,
  PenTool,
  ArrowRight,
  Plus,
  X,
  Users,
} from "lucide-react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import Banner from "@/components/ui/Banner";
import SemesterSelector from "@/components/ui/SemesterSelector";
import {
  createProject,
  getAllProjects,
  uploadProjectFile,
} from "@/features/projects/projectService";
import {
  getAvailableSemesters,
  getCurrentSemester,
  getSemesters,
  getStoredSemester,
  setStoredSemester,
} from "@/lib/semesters";
import {
  getAllUsers,
  getUser,
  getUserRole,
  ApiUser,
} from "@/features/auth/clientAuth";
import { api } from "@/lib/api";
import type { User } from "@/features/auth/clientAuth";

type DocumentType = "proyecto" | "tesis";

type UserOption = {
  id: number;
  label: string;
  email: string;
  role: User["role"];
  status: User["status"];
};

interface FormData {
  title: string;
  studentId: number | "";
  partnerId: number | "";
  advisors: (number | "")[];
  semesterPeriod: string;
}

export default function AgregarDocumentoPage() {
  const router = useRouter();
  const [documentType, setDocumentType] = useState<DocumentType>("proyecto");
  const [formData, setFormData] = useState<FormData>({
    title: "",
    studentId: "",
    partnerId: "",
    advisors: [""],
    semesterPeriod: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [bannerState, setBannerState] = useState<{
    visible: boolean;
    message: string;
    type: "success" | "error" | "warning" | "info";
  }>({ visible: false, message: "", type: "info" });

  const [errors, setErrors] = useState<{
    title?: boolean;
    student?: boolean;
    advisors: boolean[];
    files?: boolean;
  }>({
    advisors: [],
  });

  const [availableSemesters, setAvailableSemesters] = useState<string[]>([]);
  const [students, setStudents] = useState<UserOption[]>([]);
  const [potentialPartners, setPotentialPartners] = useState<UserOption[]>([]);
  // Proper tutors list
  const [tutorsList, setTutorsList] = useState<UserOption[]>([]);
  const userRole = useMemo(() => getUserRole(), []);
  const currentUser = useMemo(() => getUser(), []);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const isStudent = userRole === "Estudiante";
  const isStaffReviewer = userRole === "Tutor" || userRole === "Jurado";
  const studentSemester = (currentUser?.semester || "").toLowerCase();
  
  const [dataLoaded, setDataLoaded] = useState({ semesters: false, users: false });
  const isDataLoaded = dataLoaded.semesters && dataLoaded.users;

  const allowedDocumentTypes = useMemo(() => {
    if (!isStudent) return ["proyecto", "tesis"] as DocumentType[];
    if (studentSemester.includes("9")) return ["proyecto"];
    if (studentSemester.includes("10")) return ["tesis"];
    return [documentType];
  }, [isStudent, studentSemester, documentType]);

  // Load semesters from backend projects and choose a safe default
  useEffect(() => {
    const loadSemesters = async () => {
      // Small native promise delay to skip the blocking layout paint
      await new Promise(resolve => setTimeout(resolve, 0));
      const [projects, semestersFromApi] = await Promise.all([
        getAllProjects(),
        getSemesters(),
      ]);
      const semesters = getAvailableSemesters(
        projects,
        semestersFromApi.map((s) => s.period),
      );

      const stored = getStoredSemester();
      const fallback = getCurrentSemester();
      const chosen = semesters.length
        ? semesters.includes(stored)
          ? stored
          : semesters[0]
        : stored || fallback;

      setAvailableSemesters(semesters.length ? semesters : [chosen]);
      setFormData((prev) => ({ ...prev, semesterPeriod: chosen }));
      setStoredSemester(chosen);
      setDataLoaded(p => ({ ...p, semesters: true }));
    };

    loadSemesters();
  }, []);

  // Fetch selectable users (students & tutors)
  useEffect(() => {
    const loadUsers = async () => {
      // Small native promise delay to skip the blocking layout paint
      await new Promise(resolve => setTimeout(resolve, 0));
      const users = await getAllUsers();
      const studentOptions = users
        .filter((u) => u.role === "Estudiante" && typeof u.id === "number")
        .map((u) => ({
          id: u.id!,
          label: u.fullName?.trim() ? u.fullName : u.email,
          email: u.email,
          role: u.role,
          status: u.status,
        }));

      setStudents(studentOptions);

      // Fetch Tutors
      try {
        const tutors = await api.get<ApiUser[]>("/users/?role=Tutor");
        setTutorsList(
          tutors.map((u) => ({
            id: u.id!,
            label: u.full_name || u.email,
            email: u.email,
            role: "Tutor",
            status: "active",
          })),
        );
      } catch (err) {
        console.error("Failed to fetch tutors", err);
      }
      setPotentialPartners(studentOptions); // Default for Admin

      if (userRole === "Estudiante") {
        try {
          const response = await api.get<ApiUser[]>("/users/?role=Estudiante");
          setPotentialPartners(
            response
              .filter((u) => u.id !== currentUser?.id)
              .map((u) => ({
                id: u.id!,
                label: u.full_name || u.email,
                email: u.email,
                role: "Estudiante",
                status: u.status || "active",
              })),
          );
        } catch (err) {
          console.error("Failed to fetch partners", err);
        }
      }

      // Auto-select current student for non-admins
      if (userRole !== "Administrador" && currentUser?.id) {
        setFormData((prev) => ({ ...prev, studentId: currentUser.id! }));
      } else if (studentOptions.length === 1) {
        setFormData((prev) => ({ ...prev, studentId: studentOptions[0].id }));
      }
      setDataLoaded(p => ({ ...p, users: true }));
    };

    loadUsers();
  }, [userRole, currentUser?.id]);

  // Force document type for students based on their semester
  useEffect(() => {
    if (userRole !== "Estudiante") return;
    if (!currentUser?.semester) return;
    const semesterValue = currentUser.semester.toLowerCase();
    if (semesterValue.includes("9")) {
      setDocumentType("proyecto");
    } else if (semesterValue.includes("10")) {
      setDocumentType("tesis");
    }
  }, [userRole, currentUser?.semester]);

  const semesterLabel =
    documentType === "proyecto"
      ? "9no Semestre (Proyecto TEG)"
      : "10mo Semestre (TEG)";

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, title: e.target.value }));
    if (errors.title) setErrors((prev) => ({ ...prev, title: false }));
  };

  const handleSemesterChange = (semester: string) => {
    setStoredSemester(semester);
    setFormData((prev) => ({ ...prev, semesterPeriod: semester }));
  };

  // Student Handler
  const handleStudentSelect = (value: string) => {
    const numericValue = value ? Number(value) : "";
    setFormData((prev) => ({ ...prev, studentId: numericValue }));
    if (errors.student) setErrors((prev) => ({ ...prev, student: false }));
  };

  const handlePartnerSelect = (value: string) => {
    const numericValue = value ? Number(value) : "";
    setFormData((prev) => ({ ...prev, partnerId: numericValue }));
  };

  // Advisor Handlers
  const handleAdvisorChange = (index: number, value: string) => {
    const numericValue = value ? Number(value) : "";
    const newAdvisors = [...formData.advisors];
    newAdvisors[index] = numericValue;
    setFormData((prev) => ({ ...prev, advisors: newAdvisors }));

    if (errors.advisors[index]) {
      const newAdvisorErrors = [...errors.advisors];
      newAdvisorErrors[index] = false;
      setErrors((prev) => ({ ...prev, advisors: newAdvisorErrors }));
    }
  };

  const addAdvisor = () => {
    if (formData.advisors.length < 2) {
      setFormData((prev) => ({ ...prev, advisors: [...prev.advisors, ""] }));
      setErrors((prev) => ({ ...prev, advisors: [...prev.advisors, false] }));
    }
  };

  const removeAdvisor = (index: number) => {
    if (formData.advisors.length > 1) {
      const newAdvisors = formData.advisors.filter((_, i) => i !== index);
      setFormData((prev) => ({ ...prev, advisors: newAdvisors }));

      const newAdvisorErrors = errors.advisors.filter((_, i) => i !== index);
      setErrors((prev) => ({ ...prev, advisors: newAdvisorErrors }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isStaffReviewer) {
      setBannerState({
        visible: true,
        message:
          "Los tutores y jurados no pueden registrar documentos directamente.",
        type: "warning",
      });
      return;
    }

    // Validation
    const titleError = !formData.title.trim();
    const studentError = !formData.studentId;
    const advisorsErrors = formData.advisors.map((a) => a === "");
    const filesError = userRole === "Estudiante" && selectedFiles.length === 0;

    const hasErrors =
      titleError || studentError || advisorsErrors.some(Boolean) || filesError;

    if (hasErrors) {
      setErrors({
        title: titleError,
        student: studentError,
        advisors: advisorsErrors,
        files: filesError,
      });

      setBannerState({
        visible: true,
        message: "Por favor complete todos los campos marcados en rojo.",
        type: "error",
      });
      return;
    }

    // Clear errors if any existed
    setErrors({
      student: false,
      advisors: [],
      files: false,
    });

    setIsSubmitting(true);

    try {
      const validAdvisors = formData.advisors.filter(
        (a) => a !== "",
      ) as number[];

      const created = await createProject({
        title: formData.title,
        advisors: validAdvisors,
        period: formData.semesterPeriod,
        project_type: documentType,
        status: "pending",
        ...(userRole === "Administrador" && formData.studentId
          ? { student: formData.studentId as number }
          : {}),
        ...(formData.partnerId
          ? { partner: formData.partnerId as number }
          : {}),
      });

      if (selectedFiles.length > 0) {
        await Promise.all(
          selectedFiles.map((file) => uploadProjectFile(created.id, file)),
        );
      }
      setBannerState({
        visible: true,
        message: `${documentType === "proyecto" ? "Proyecto" : "Tesis"} agregado exitosamente.`,
        type: "success",
      });

      // Reset form
      const resetSemester =
        availableSemesters[0] ||
        formData.semesterPeriod ||
        getCurrentSemester();
      setFormData({
        title: "",
        studentId: userRole === "Administrador" ? "" : currentUser?.id || "",
        partnerId: "",
        advisors: [""],
        semesterPeriod: resetSemester,
      });
      setSelectedFiles([]);

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
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-gray-50/50">
          <div className="max-w-5xl mx-auto space-y-6">
            {/* Header Section with Semester Selector */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="mt-1 p-2 bg-purple-100 rounded-lg text-purple-600">
                  <UserIcon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-gray-900">
                    Nuevo Registro
                  </h2>
                  <p className="text-gray-500 text-sm mt-1">
                    Complete la información para añadir un nuevo documento
                    académico
                  </p>
                </div>
              </div>
              <div className="w-full sm:w-auto">
                <SemesterSelector
                  selectedSemester={formData.semesterPeriod}
                  availableSemesters={availableSemesters}
                  onSemesterChange={handleSemesterChange}
                />
              </div>
            </div>

            {isStaffReviewer && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                Los tutores y jurados no pueden registrar documentos. Si
                necesitas crear uno, solicita acceso de administrador.
              </div>
            )}

            {!isDataLoaded ? (
              <div className="flex justify-center items-center py-24">
                <div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin shadow-sm" />
              </div>
            ) : (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="grid lg:grid-cols-3 gap-6">
                  {/* Left Column: Document Type Selection */}
              <div className="lg:col-span-1 space-y-4">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                  {isStudent ? "Documento asignado" : "Tipo de Documento"}
                </h3>

                {allowedDocumentTypes.includes("proyecto") && (
                  <div className="relative group/tooltip">
                    <button
                      type="button"
                      onClick={() => setDocumentType("proyecto")}
                      disabled={isStudent}
                      className={`relative w-full overflow-hidden flex flex-col items-start gap-3 p-5 rounded-2xl border-2 transition-all duration-300 group ${
                        documentType === "proyecto"
                          ? "border-blue-500 bg-white shadow-2xl shadow-blue-500/20 scale-[1.04]"
                          : "border-transparent bg-white shadow-sm hover:shadow-xl hover:shadow-blue-500/10 hover:bg-gradient-to-br hover:from-blue-50/30 hover:to-white hover:scale-[1.02] hover:border-blue-200"
                      }`}
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/0 via-blue-500/0 to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                      <div
                        className={`p-3 rounded-xl ${documentType === "proyecto" ? "bg-blue-100 text-blue-600 ring-2 ring-blue-200" : "bg-gray-100 text-gray-500 group-hover:bg-blue-50 group-hover:text-blue-600 group-hover:ring-2 group-hover:ring-blue-100"} transition-all duration-300`}
                      >
                        <FileText className="w-6 h-6 group-hover:scale-110 transition-transform" />
                      </div>
                      <div className="text-left relative z-10">
                        <p
                          className={`font-bold text-lg ${documentType === "proyecto" ? "text-blue-900" : "text-gray-700 group-hover:text-blue-800"} transition-colors`}
                        >
                          Proyecto (PTEG)
                        </p>
                        <p className="text-xs font-medium text-gray-500 mt-1">
                          9no Semestre
                        </p>
                      </div>
                      {documentType === "proyecto" && (
                        <>
                          <div className="absolute top-0 right-0 p-4 animate-in fade-in duration-300">
                            <CheckCircle className="w-5 h-5 text-blue-500" />
                          </div>
                          <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-blue-400 rounded-full blur-3xl opacity-30 pointer-events-none animate-pulse" />
                          <div
                            className="absolute inset-0 rounded-2xl bg-blue-500/10 animate-ping pointer-events-none"
                            style={{
                              animationDuration: "1s",
                              animationIterationCount: 1,
                            }}
                          />
                        </>
                      )}
                    </button>
                    <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover/tooltip:opacity-100 group-hover/tooltip:visible transition-all duration-200 whitespace-nowrap z-50 pointer-events-none">
                      Propuesta inicial del TEG
                      <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
                    </div>
                  </div>
                )}

                {allowedDocumentTypes.includes("tesis") && (
                  <div className="relative group/tooltip">
                    <button
                      type="button"
                      onClick={() => setDocumentType("tesis")}
                      disabled={isStudent}
                      className={`relative w-full overflow-hidden flex flex-col items-start gap-3 p-5 rounded-2xl border-2 transition-all duration-300 group ${
                        documentType === "tesis"
                          ? "border-emerald-500 bg-white shadow-2xl shadow-emerald-500/20 scale-[1.04]"
                          : "border-transparent bg-white shadow-sm hover:shadow-xl hover:shadow-emerald-500/10 hover:bg-gradient-to-br hover:from-emerald-50/30 hover:to-white hover:scale-[1.02] hover:border-emerald-200"
                      }`}
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/0 via-emerald-500/0 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                      <div
                        className={`p-3 rounded-xl ${documentType === "tesis" ? "bg-emerald-100 text-emerald-600 ring-2 ring-emerald-200" : "bg-gray-100 text-gray-500 group-hover:bg-emerald-50 group-hover:text-emerald-600 group-hover:ring-2 group-hover:ring-emerald-100"} transition-all duration-300`}
                      >
                        <BookOpen className="w-6 h-6 group-hover:scale-110 transition-transform" />
                      </div>
                      <div className="text-left relative z-10">
                        <p
                          className={`font-bold text-lg ${documentType === "tesis" ? "text-emerald-900" : "text-gray-700 group-hover:text-emerald-800"} transition-colors`}
                        >
                          Trabajo Especial (TEG)
                        </p>
                        <p className="text-xs font-medium text-gray-500 mt-1">
                          10mo Semestre
                        </p>
                      </div>
                      {documentType === "tesis" && (
                        <>
                          <div className="absolute top-0 right-0 p-4 animate-in fade-in duration-300">
                            <CheckCircle className="w-5 h-5 text-emerald-500" />
                          </div>
                          <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-emerald-400 rounded-full blur-3xl opacity-30 pointer-events-none animate-pulse" />
                          <div
                            className="absolute inset-0 rounded-2xl bg-emerald-500/10 animate-ping pointer-events-none"
                            style={{
                              animationDuration: "1s",
                              animationIterationCount: 1,
                            }}
                          />
                        </>
                      )}
                    </button>
                    <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover/tooltip:opacity-100 group-hover/tooltip:visible transition-all duration-200 whitespace-nowrap z-50 pointer-events-none">
                      Proyecto final completo
                      <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column: Main Form */}
              <div className="lg:col-span-2">
                <form
                  onSubmit={handleSubmit}
                  className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
                >
                  <div className="p-6 sm:p-8 space-y-8">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-gray-100">
                      <div className="flex items-center gap-4">
                        <div
                          className={`p-3 rounded-xl ${documentType === "proyecto" ? "bg-blue-50 text-blue-600" : "bg-emerald-50 text-emerald-600"}`}
                        >
                          {documentType === "proyecto" ? (
                            <FileText className="w-6 h-6" />
                          ) : (
                            <BookOpen className="w-6 h-6" />
                          )}
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-900">
                            Información del Documento
                          </h3>
                          <p className="text-sm text-gray-500 font-medium">
                            Complete los detalles básicos
                          </p>
                        </div>
                      </div>
                      <div
                        className={`self-start sm:self-center px-4 py-2 rounded-full text-xs font-bold border flex items-center gap-2 ${
                          documentType === "proyecto"
                            ? "bg-blue-50 text-blue-700 border-blue-100"
                            : "bg-emerald-50 text-emerald-700 border-emerald-100"
                        }`}
                      >
                        <span
                          className={`w-2 h-2 rounded-full ${documentType === "proyecto" ? "bg-blue-500" : "bg-emerald-500"}`}
                        />
                        {semesterLabel}
                      </div>
                    </div>

                    {/* Title Input */}
                    <div className="space-y-2 group">
                      <label
                        htmlFor="title"
                        className="text-sm font-semibold text-gray-700 ml-1"
                      >
                        Título del{" "}
                        {documentType === "proyecto" ? "Proyecto" : "Trabajo"}
                      </label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                          <PenTool className="w-5 h-5 text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
                        </div>
                        <input
                          type="text"
                          id="title"
                          name="title"
                          value={formData.title}
                          onChange={handleTitleChange}
                          placeholder="Ingrese el título completo..."
                          className={`w-full pl-12 pr-4 py-3.5 bg-white border rounded-xl shadow-sm focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all text-sm font-medium ${
                            errors.title
                              ? "border-red-300 ring-4 ring-red-50 focus:border-red-500 focus:ring-red-100"
                              : "border-gray-200 hover:border-indigo-300"
                          }`}
                        />
                        {errors.title && (
                          <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1 text-red-500 text-xs font-bold animate-in fade-in slide-in-from-left-2">
                            <X className="w-4 h-4" />
                            <span>Requerido</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Students Section */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Users className="w-5 h-5 text-purple-500" />
                          <label className="text-sm font-bold text-gray-800">
                            Estudiante responsable
                          </label>
                        </div>
                      </div>

                      <div
                        className={`group relative bg-gradient-to-br ${
                          errors.student
                            ? "from-red-50 to-white border-red-200"
                            : "from-purple-50/50 to-transparent border-purple-100"
                        } border rounded-xl p-4 hover:shadow-md transition-all duration-300`}
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center mt-0.5 ${
                              errors.student
                                ? "bg-red-100 text-red-600"
                                : "bg-purple-100 text-purple-600"
                            }`}
                          >
                            <UserIcon className="w-5 h-5" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <label
                              className={`text-xs font-semibold mb-1.5 block ${errors.student ? "text-red-700" : "text-purple-700"}`}
                            >
                              Seleccione al estudiante
                            </label>
                            <div className="relative">
                              {userRole === "Estudiante" ? (
                                <input
                                  type="text"
                                  disabled
                                  value={
                                    currentUser?.fullName ||
                                    currentUser?.email ||
                                    "Estudiante"
                                  }
                                  className="w-full px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg shadow-sm text-sm font-medium text-gray-600 cursor-not-allowed"
                                />
                              ) : (
                                <select
                                  value={formData.studentId}
                                  onChange={(e) =>
                                    handleStudentSelect(e.target.value)
                                  }
                                  className={`w-full px-3 py-2.5 bg-white border rounded-lg shadow-sm focus:border-purple-500 focus:ring-4 focus:ring-purple-500/10 transition-all text-sm font-medium ${
                                    errors.student
                                      ? "border-red-300 focus:border-red-500 focus:ring-red-100"
                                      : "border-gray-200 hover:border-purple-300"
                                  }`}
                                >
                                  <option value="">
                                    Seleccione un estudiante
                                  </option>
                                  {students.map((stu) => (
                                    <option key={stu.id} value={stu.id}>
                                      {stu.label}{" "}
                                      {stu.status === "pending"
                                        ? "(Pendiente)"
                                        : ""}
                                    </option>
                                  ))}
                                </select>
                              )}
                              {errors.student && (
                                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                  <X className="w-4 h-4 text-red-500" />
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Partner Selection */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Users className="w-5 h-5 text-indigo-500" />
                          <label className="text-sm font-bold text-gray-800">
                            Compañero (Opcional)
                          </label>
                        </div>
                      </div>
                      <div className="group relative bg-gradient-to-br from-indigo-50/50 to-transparent border-indigo-100 border rounded-xl p-4 hover:shadow-md transition-all duration-300">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center mt-0.5 bg-indigo-100 text-indigo-600">
                            <UserIcon className="w-5 h-5" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <label className="text-xs font-semibold mb-1.5 block text-indigo-700">
                              Seleccionar Compañero
                            </label>
                            <select
                              value={formData.partnerId}
                              onChange={(e) =>
                                handlePartnerSelect(e.target.value)
                              }
                              className="w-full px-3 py-2.5 bg-white border rounded-lg shadow-sm focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all text-sm font-medium border-gray-200"
                            >
                              <option value="">Sin compañero</option>
                              {potentialPartners
                                .filter(
                                  (s) =>
                                    s.id !==
                                    (Number(formData.studentId) ||
                                      currentUser?.id),
                                )
                                .map((s) => (
                                  <option key={s.id} value={s.id}>
                                    {s.label}
                                  </option>
                                ))}
                            </select>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* File Upload Section (Students) */}
                    {userRole === "Estudiante" && (
                      <div className="space-y-4">
                        <div className="flex items-center gap-2">
                          <FileText className="w-5 h-5 text-indigo-500" />
                          <label className="text-sm font-bold text-gray-800">
                            Subir documento (PDF o Word)
                          </label>
                        </div>
                        <div
                          className={`border-2 border-dashed rounded-xl p-4 bg-white ${
                            errors.files
                              ? "border-red-300 bg-red-50/40"
                              : "border-indigo-200 hover:border-indigo-300"
                          }`}
                        >
                          <input
                            type="file"
                            accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            multiple
                            onChange={(e) => {
                              const files = Array.from(e.target.files || []);
                              setSelectedFiles(files);
                              if (errors.files) {
                                setErrors((prev) => ({
                                  ...prev,
                                  files: false,
                                }));
                              }
                            }}
                            className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                          />
                          {selectedFiles.length > 0 && (
                            <div className="mt-3 text-xs text-gray-500">
                              {selectedFiles.length} archivo(s) seleccionado(s)
                            </div>
                          )}
                          {errors.files && (
                            <p className="mt-2 text-xs text-red-600 font-semibold">
                              Debe adjuntar al menos un archivo.
                            </p>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Advisors Section */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <GraduationCap className="w-5 h-5 text-teal-500" />
                          <label className="text-sm font-bold text-gray-800">
                            Tutores Académicos
                          </label>
                          <span className="text-xs font-semibold text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                            {formData.advisors.length}/2
                          </span>
                        </div>
                      </div>

                      <div className="space-y-3">
                        {formData.advisors.map((advisor, index) => (
                          <div
                            key={`advisor-${index}`}
                            className={`group relative bg-gradient-to-br ${
                              errors.advisors[index]
                                ? "from-red-50 to-white border-red-200"
                                : "from-teal-50/50 to-transparent border-teal-100"
                            } border rounded-xl p-4 hover:shadow-md transition-all duration-300`}
                          >
                            <div className="flex items-start gap-3">
                              <div
                                className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center mt-0.5 ${
                                  errors.advisors[index]
                                    ? "bg-red-100 text-red-600"
                                    : "bg-teal-100 text-teal-600"
                                }`}
                              >
                                <GraduationCap className="w-5 h-5" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <label
                                  className={`text-xs font-semibold mb-1.5 block ${errors.advisors[index] ? "text-red-700" : "text-teal-700"}`}
                                >
                                  Tutor {index + 1}
                                </label>
                                <div className="relative">
                                  <select
                                    value={advisor}
                                    onChange={(e) =>
                                      handleAdvisorChange(index, e.target.value)
                                    }
                                    className={`w-full px-3 py-2.5 bg-white border rounded-lg shadow-sm focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 transition-all text-sm font-medium ${
                                      errors.advisors[index]
                                        ? "border-red-300 focus:border-red-500 focus:ring-red-100"
                                        : "border-gray-200 hover:border-teal-300"
                                    }`}
                                  >
                                    <option value="">
                                      Seleccione un tutor
                                    </option>
                                    {tutorsList.map((t) => (
                                      <option key={t.id} value={t.id}>
                                        {t.label}
                                      </option>
                                    ))}
                                  </select>
                                  {errors.advisors[index] && (
                                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                      <X className="w-4 h-4 text-red-500" />
                                    </div>
                                  )}
                                </div>
                              </div>
                              {formData.advisors.length > 1 && (
                                <button
                                  type="button"
                                  onClick={() => removeAdvisor(index)}
                                  className="flex-shrink-0 w-8 h-8 rounded-lg bg-white border border-red-100 hover:border-red-200 hover:bg-red-50 flex items-center justify-center text-red-500 hover:text-red-600 transition-all shadow-sm hover:shadow mt-6"
                                  title="Eliminar tutor"
                                >
                                  <X className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                          </div>
                        ))}

                        {formData.advisors.length < 2 && (
                          <button
                            type="button"
                            onClick={addAdvisor}
                            className="w-full p-4 border border-dashed border-teal-300 rounded-xl bg-teal-50/30 hover:bg-teal-50 hover:border-teal-400 transition-all group shadow-sm hover:shadow"
                          >
                            <div className="flex items-center justify-center gap-2 text-teal-600 group-hover:text-teal-700">
                              <div className="w-8 h-8 rounded-lg bg-white border border-teal-100 group-hover:border-teal-200 flex items-center justify-center transition-colors shadow-sm">
                                <Plus className="w-4 h-4" />
                              </div>
                              <span className="text-sm font-semibold">
                                Agregar Tutor
                              </span>
                            </div>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="pt-6 border-t border-gray-100 flex flex-col sm:flex-row items-center gap-3">
                      <button
                        type="button"
                        onClick={() => router.back()}
                        className="w-full sm:w-auto px-6 py-3 rounded-xl font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-all order-2 sm:order-1"
                      >
                        Cancelar
                      </button>
                      <button
                        type="submit"
                        disabled={isSubmitting || isStaffReviewer}
                        className={`w-full sm:flex-1 flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl font-bold text-white shadow-lg transition-all transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none order-1 sm:order-2 ${
                          documentType === "proyecto"
                            ? "bg-gradient-to-r from-blue-600 to-indigo-600 hover:shadow-blue-500/30"
                            : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:shadow-emerald-500/30"
                        }`}
                      >
                        {isSubmitting ? (
                          <>
                            <svg
                              className="animate-spin h-5 w-5"
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
                            <span>Guardando...</span>
                          </>
                        ) : (
                          <>
                            <span>Agregar Documento</span>
                            <ArrowRight className="w-5 h-5" />
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            </div>
            </div>
            )}
          </div>
        </main>
      </PageTransition>
    </>
  );
}
