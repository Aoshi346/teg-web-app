"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import {
  getAllUsers,
  getUser,
  getUserRole,
  getStudents,
  getTutors,
} from "@/features/auth/clientAuth";
import {
  getAvailableSemesters,
  getCurrentSemester,
  getSemesters,
  getStoredSemester,
  setStoredSemester,
  fetchActiveSemester,
  compareSemesters,
  getAvailableSemesterPeriods,
} from "@/lib/semesters";
import { getAllProjects } from "@/features/projects/projectService";

export interface UserOption {
  id: number;
  label: string;
  email: string;
}

export function useDocumentData() {
  const userRole = useMemo(() => getUserRole(), []);
  const currentUser = useMemo(() => getUser(), []);

  const isStudent = userRole === "Estudiante";
  const isStaffReviewer = userRole === "Tutor" || userRole === "Jurado";

  const [students, setStudents] = useState<UserOption[]>([]);
  const [tutors, setTutors] = useState<UserOption[]>([]);
  const [partners, setPartners] = useState<UserOption[]>([]);
  const [semesters, setSemesters] = useState<string[]>([]);
  const [defaultSemester, setDefaultSemester] = useState("");

  const [loading, setLoading] = useState({ users: true, semesters: true });
  const isLoaded = !loading.users && !loading.semesters;

  // Determine allowed document types from student semester
  const allowedDocumentTypes = useMemo(() => {
    if (!isStudent) return ["proyecto", "tesis"] as const;
    const sem = (currentUser?.semester || "").toLowerCase();
    if (sem.includes("9")) return ["proyecto"] as const;
    if (sem.includes("10")) return ["tesis"] as const;
    // Fallback: allow both if semester is unknown
    return ["proyecto", "tesis"] as const;
  }, [isStudent, currentUser?.semester]);

  const defaultDocType = allowedDocumentTypes[0] ?? "proyecto";

  // Load semesters
  useEffect(() => {
    (async () => {
      try {
        const [projects, semestersFromApi, active] = await Promise.all([
          getAllProjects(),
          getSemesters(),
          fetchActiveSemester(),
        ]);
        const periods = semestersFromApi.map((s) => s.period);
        const available = getAvailableSemesters(
          projects,
          periods,
        );
        const sorted = available.length
          ? available
          : getAvailableSemesterPeriods();

        const stored = getStoredSemester();
        const fallback = getCurrentSemester();
        const chosen = active
          ? active.period
          : sorted.includes(stored)
            ? stored
            : sorted[0] || fallback;

        setSemesters(sorted.length ? sorted : [chosen]);
        setDefaultSemester(chosen);
        setStoredSemester(chosen);
      } catch (err) {
        console.error("Failed to load semesters", err);
        const fallback = getCurrentSemester();
        setSemesters([fallback]);
        setDefaultSemester(fallback);
      } finally {
        setLoading((p) => ({ ...p, semesters: false }));
      }
    })();
  }, []);

  // Load users
  useEffect(() => {
    (async () => {
      try {
        const [studentUsers, tutorUsers] = await Promise.all([
          getStudents(),
          getTutors(),
        ]);

        const toOption = (u: { id?: number; fullName?: string; email: string }) => ({
          id: u.id!,
          label: u.fullName?.trim() ? u.fullName : u.email,
          email: u.email,
        });

        const studentOptions = studentUsers
          .filter((u) => typeof u.id === "number")
          .map(toOption);

        setStudents(studentOptions);
        setPartners(
          userRole === "Estudiante"
            ? studentOptions.filter((s) => s.id !== currentUser?.id)
            : studentOptions,
        );

        setTutors(
          tutorUsers
            .filter((u) => typeof u.id === "number")
            .map(toOption),
        );
      } catch (err) {
        console.error("Failed to load users", err);
      } finally {
        setLoading((p) => ({ ...p, users: false }));
      }
    })();
  }, [userRole, currentUser?.id]);

  const handleSemesterChange = useCallback((semester: string) => {
    setStoredSemester(semester);
  }, []);

  return {
    userRole,
    currentUser,
    isStudent,
    isStaffReviewer,
    students,
    tutors,
    partners,
    semesters,
    defaultSemester,
    defaultDocType,
    allowedDocumentTypes,
    isLoaded,
    handleSemesterChange,
  };
}
