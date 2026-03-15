"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  BookOpen,
  User,
  GraduationCap,
  PenTool,
  ArrowRight,
  Plus,
  X,
  Users,
} from "lucide-react";
import { useValidation } from "@/hooks/useValidation";
import Banner from "@/components/ui/Banner";
import SemesterSelector from "@/components/ui/SemesterSelector";
import { Project } from "@/types/project";
import {
  createProject,
  updateProject as apiUpdateProject,
  reassignStudent,
} from "@/features/projects/projectService";
import {
  getAllUsers,
  getUser,
  getUserRole,
  ApiUser,
} from "@/features/auth/clientAuth";
import { api } from "@/lib/api";
import {
  compareSemesters,
  getAvailableSemesterPeriods,
  getSemesters,
} from "@/lib/semesters";

interface DocumentFormProps {
  initialData?: Project;
  mode: "create" | "edit";
  // If provided, locks the type (for Edit mode or specific filtered add)
  forcedType?: "proyecto" | "tesis";
  // If not forced, this sets the initial selection
  defaultType?: "proyecto" | "tesis";
}

export default function DocumentForm({
  initialData,
  mode,
  forcedType,
  defaultType = "proyecto",
}: DocumentFormProps) {
  const router = useRouter();

  // If forcedType is present, use it. Otherwise use state.
  const [selectedType, setSelectedType] = useState<"proyecto" | "tesis">(
    forcedType || (initialData ? initialData.type || defaultType : defaultType),
    // Note: Project interface might not have 'type' property explicitly stored everywhere,
    // so we might need to rely on passed props.
  );

  // Effect to ensure if forcedType changes (unlikely) we update
  useEffect(() => {
    if (forcedType) setSelectedType(forcedType);
  }, [forcedType]);

  // Derived document type for logic
  const documentType = forcedType || selectedType;

  // Form State
  const [title, setTitle] = useState(initialData?.title || "");
  const [advisors, setAdvisors] = useState<(number | "")[]>(
    initialData?.advisors && initialData.advisors.length > 0
      ? initialData.advisors
      : [""],
  );

  const [availablePeriods, setAvailablePeriods] = useState<string[]>(() =>
    getAvailableSemesterPeriods(),
  );
  const [semesterPeriod, setSemesterPeriod] = useState(
    initialData?.period || "",
  );

  // Ensure semester is set on load
  useEffect(() => {
    if (!semesterPeriod && availablePeriods.length > 0) {
      setSemesterPeriod(availablePeriods[0]);
    }
  }, [availablePeriods, semesterPeriod]);

  // Load semesters from backend, fallback to local list
  useEffect(() => {
    const loadSemesters = async () => {
      const semesters = await getSemesters();
      const periods = semesters.map((s) => s.period);
      const sorted = periods.sort((a, b) => compareSemesters(b, a));
      const fallback = sorted.length ? sorted : getAvailableSemesterPeriods();
      const merged =
        initialData?.period && !fallback.includes(initialData.period)
          ? [initialData.period, ...fallback]
          : fallback;
      setAvailablePeriods(merged);
      if (!semesterPeriod && merged.length > 0) {
        setSemesterPeriod(merged[0]);
      }
    };
    loadSemesters();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialData?.period]);

  // Validation State
  const [errors, setErrors] = useState<{
    title?: boolean;
    advisors: boolean[];
  }>({
    advisors: [],
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showBanner, bannerProps } = useValidation();
  const [studentsList, setStudentsList] = useState<
    Array<{ id: number; label: string }>
  >([]);
  const [tutorsList, setTutorsList] = useState<
    Array<{ id: number; label: string }>
  >([]);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(
    null,
  );
  const [partnerId, setPartnerId] = useState<number | null>(
    initialData?.partner || null,
  );
  const [potentialPartners, setPotentialPartners] = useState<
    Array<{ id: number; label: string }>
  >([]);
  const userRole = getUserRole();
  const currentUser = useMemo(() => getUser(), []);

  // Fetch users (Students for assignment or partners)
  useEffect(() => {
    const fetchUsers = async () => {
      if (userRole === "Administrador") {
        const users = await getAllUsers();
        const students = users.filter(
          (u) => u.role === "Estudiante" && typeof u.id === "number",
        );
        const formatted = students.map((u) => ({
          id: u.id!,
          label: (u.fullName || u.email) as string,
        }));
        setStudentsList(formatted);
        setPotentialPartners(formatted);

        if (initialData) {
          const match = students.find(
            (u) => (u.fullName || u.email) === initialData.student,
          );
          if (match && match.id) setSelectedStudentId(match.id);
        } else if (students.length === 1) {
          setSelectedStudentId(students[0].id || null);
        }
      } else if (userRole === "Estudiante") {
        // Students fetch other students for partner selection
        // We use direct API call to use the query param
        try {
          const response = await api.get<ApiUser[]>("/users/?role=Estudiante");
          const students = response.filter((u) => u.id !== currentUser?.id);
          setPotentialPartners(
            students.map((u) => ({
              id: u.id!,
              label: u.full_name || u.email,
            })),
          );
        } catch (err) {
          console.error("Failed to fetch potential partners", err);
        }
      }

      // Fetch Tutors for everyone
      try {
        const tutors = await api.get<ApiUser[]>("/users/?role=Tutor");
        setTutorsList(
          tutors.map((u) => ({
            id: u.id!,
            label: u.full_name || u.email,
          })),
        );
      } catch (err) {
        console.error("Failed to fetch tutors", err);
      }
    };
    fetchUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, userRole, currentUser?.id]);

  const handleAdvisorChange = (index: number, value: string) => {
    const numericValue = value ? Number(value) : "";
    const newAdvisors = [...advisors];
    newAdvisors[index] = numericValue;
    setAdvisors(newAdvisors);
    if (errors.advisors[index]) {
      const newErrs = [...errors.advisors];
      newErrs[index] = false;
      setErrors((prev) => ({ ...prev, advisors: newErrs }));
    }
  };

  const addAdvisor = () => {
    if (advisors.length < 2) {
      setAdvisors([...advisors, ""]);
    }
  };

  const removeAdvisor = (index: number) => {
    if (advisors.length > 1) {
      setAdvisors(advisors.filter((_, i) => i !== index));
      setErrors((prev) => ({
        ...prev,
        advisors: prev.advisors.filter((_, i) => i !== index),
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation Logic
    const titleError = !title.trim();
    const advisorsErrors = advisors.map((a) => a === "");

    const hasErrors = titleError || advisorsErrors.some(Boolean);

    if (hasErrors) {
      setErrors({
        title: titleError,
        advisors: advisorsErrors,
      });
      showBanner(
        "Por favor complete todos los campos marcados en rojo.",
        "error",
      );
      return;
    }

    setIsSubmitting(true);

    try {
      const validAdvisors = advisors.filter((a) => a !== "") as number[];

      const payload: Partial<Project> & { advisors: number[] } = {
        title: title.trim(),
        advisors: validAdvisors,
        period: semesterPeriod,
        type: documentType,
        partner: partnerId || undefined, // Use undefined if null to skip or handle properly
        // Status and dates might be preserved or reset?
        // For Edit: preserve existing properties not in form
        // For Create: defaults handled by add functions
      };

      if (mode === "create") {
        // Backend create (student assigned server-side)
        await createProject({
          title: payload.title || "",
          advisors: payload.advisors,
          period: payload.period || "",
          partner: payload.partner,
          project_type: documentType,
          status: "pending",
          ...(userRole === "Administrador" && selectedStudentId
            ? { student: selectedStudentId }
            : {}),
        });
        showBanner("Documento agregado exitosamente.", "success");
      } else {
        // Edit Mode
        if (!initialData) throw new Error("No initial data for edit");

        const updatedDoc = {
          ...initialData,
          ...payload,
        };
        // Backend update first
        await apiUpdateProject(updatedDoc.id, {
          title: updatedDoc.title,
          advisors: payload.advisors,
          period: updatedDoc.period,
          partner: payload.partner,
          project_type: documentType,
          status: updatedDoc.status,
        });
        // If Admin selected a different student, reassign
        if (userRole === "Administrador" && selectedStudentId) {
          await reassignStudent(updatedDoc.id, { student: selectedStudentId });
        }
        showBanner("Cambios guardados exitosamente.", "success");
      }

      await new Promise((resolve) => setTimeout(resolve, 800));

      // Redirect
      const targetPath =
        documentType === "tesis" ? "/dashboard/tesis" : "/dashboard/proyectos";
      router.push(targetPath);
    } catch (err) {
      console.error(err);
      showBanner("Ocurrió un error al guardar.", "error");
      setIsSubmitting(false);
    }
  };

  // Styling helpers
  const isProyecto = documentType === "proyecto";
  const ThemeIcon = isProyecto ? FileText : BookOpen;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <Banner {...bannerProps} />

      <form onSubmit={handleSubmit}>
        <div className="p-6 sm:p-8 space-y-8">
          {/* Header / Semester Row */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-gray-100">
            <div className="flex items-center gap-4">
              <div
                className={`p-3 rounded-xl ${isProyecto ? "bg-blue-50 text-blue-600" : "bg-emerald-50 text-emerald-600"}`}
              >
                <ThemeIcon className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">
                  {mode === "create"
                    ? "Información del Documento"
                    : "Editar Documento"}
                </h3>
                <p className="text-sm text-gray-500 font-medium">
                  {mode === "create"
                    ? "Complete los detalles básicos"
                    : "Modifique los detalles necesarios"}
                </p>
              </div>
            </div>

            {/* Semester Selector */}
            <div className="w-full sm:w-auto">
              <SemesterSelector
                selectedSemester={semesterPeriod}
                availableSemesters={availablePeriods}
                onSemesterChange={setSemesterPeriod}
              />
            </div>
          </div>

          {/* Title Input */}
          <div className="space-y-2 group">
            <label
              htmlFor="title"
              className="text-sm font-semibold text-gray-700 ml-1"
            >
              Título del {isProyecto ? "Proyecto" : "Trabajo"}
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <PenTool className="w-5 h-5 text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
              </div>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  if (errors.title) setErrors((p) => ({ ...p, title: false }));
                }}
                placeholder="Ingrese el título completo..."
                className={`w-full pl-12 pr-4 py-3.5 bg-white border rounded-xl shadow-sm focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all text-sm font-medium ${
                  errors.title
                    ? "border-red-300 ring-4 ring-red-50 focus:border-red-500 focus:ring-red-100"
                    : "border-gray-200 hover:border-indigo-300"
                }`}
              />
              {errors.title && (
                <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1 text-red-500 text-xs font-bold animate-in fade-in">
                  <X className="w-4 h-4" />
                  <span>Requerido</span>
                </div>
              )}
            </div>
          </div>

          {/* Student Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-purple-500" />
                <label className="text-sm font-bold text-gray-800">
                  Estudiante responsable
                </label>
              </div>
            </div>

            <div className="group relative bg-gradient-to-br from-purple-50/50 to-transparent border-purple-100 border rounded-xl p-4 hover:shadow-md transition-all duration-300">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center mt-0.5 bg-purple-100 text-purple-600">
                  <User className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <label className="text-xs font-semibold mb-1.5 block text-purple-700">
                    Estudiante asignado
                  </label>
                  {userRole === "Administrador" ? (
                    <select
                      value={selectedStudentId ?? ""}
                      onChange={(e) =>
                        setSelectedStudentId(Number(e.target.value) || null)
                      }
                      className="w-full px-3 py-2.5 bg-white border rounded-lg shadow-sm focus:border-purple-500 focus:ring-4 focus:ring-purple-500/10 transition-all text-sm font-medium border-gray-200"
                    >
                      <option value="">Seleccione un estudiante</option>
                      {studentsList.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      disabled
                      value={
                        initialData?.student ||
                        currentUser?.fullName ||
                        currentUser?.email ||
                        "Asignado automáticamente"
                      }
                      className="w-full px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-lg shadow-sm text-sm font-medium text-gray-600 cursor-not-allowed"
                    />
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Partner Section */}
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
                  <User className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <label className="text-xs font-semibold mb-1.5 block text-indigo-700">
                    Seleccionar Compañero
                  </label>
                  <select
                    value={partnerId ?? ""}
                    onChange={(e) =>
                      setPartnerId(Number(e.target.value) || null)
                    }
                    className="w-full px-3 py-2.5 bg-white border rounded-lg shadow-sm focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all text-sm font-medium border-gray-200"
                  >
                    <option value="">Sin compañero</option>
                    {potentialPartners
                      .filter(
                        (p) =>
                          p.id !==
                          (userRole === "Administrador"
                            ? selectedStudentId
                            : currentUser?.id),
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

          {/* Advisors Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-teal-500" />
                <label className="text-sm font-bold text-gray-800">
                  Tutores Académicos
                </label>
                <span className="text-xs font-semibold text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                  {advisors.length}/2
                </span>
              </div>
            </div>

            <div className="space-y-3">
              {advisors.map((advisor, index) => (
                <div
                  key={`ad-${index}`}
                  className={`group relative bg-gradient-to-br ${errors.advisors[index] ? "from-red-50 to-white border-red-200" : "from-teal-50/50 to-transparent border-teal-100"} border rounded-xl p-4 hover:shadow-md transition-all duration-300`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center mt-0.5 ${errors.advisors[index] ? "bg-red-100 text-red-600" : "bg-teal-100 text-teal-600"}`}
                    >
                      <GraduationCap className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <label
                        className={`text-xs font-semibold mb-1.5 block ${errors.advisors[index] ? "text-red-700" : "text-teal-700"}`}
                      >
                        Tutor {index + 1}
                      </label>
                      <select
                        value={advisor}
                        onChange={(e) =>
                          handleAdvisorChange(index, e.target.value)
                        }
                        className={`w-full px-3 py-2.5 bg-white border rounded-lg shadow-sm focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 transition-all text-sm font-medium ${errors.advisors[index] ? "border-red-300" : "border-gray-200"}`}
                      >
                        <option value="">Seleccionar Tutor</option>
                        {tutorsList.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    {advisors.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeAdvisor(index)}
                        className="mt-6 p-2 rounded-lg hover:bg-red-50 text-red-400 hover:text-red-600 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {advisors.length < 2 && (
                <button
                  type="button"
                  onClick={addAdvisor}
                  className="w-full p-3 border border-dashed border-teal-300 rounded-xl bg-teal-50/30 text-teal-600 hover:bg-teal-50 font-semibold text-sm flex items-center justify-center gap-2 transition-all"
                >
                  <Plus className="w-4 h-4" /> Agregar Tutor
                </button>
              )}
            </div>
          </div>

          {/* Actions */}
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
              disabled={isSubmitting}
              className={`w-full sm:flex-1 flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl font-bold text-white shadow-lg transition-all transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed order-1 sm:order-2 ${
                isProyecto
                  ? "bg-gradient-to-r from-blue-600 to-indigo-600 hover:shadow-blue-500/30"
                  : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:shadow-emerald-500/30"
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
                  <span>Guardando...</span>
                </>
              ) : (
                <>
                  <span>
                    {mode === "create"
                      ? "Agregar Documento"
                      : "Guardar Cambios"}
                  </span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
