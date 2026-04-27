"use client";

import React, { useMemo } from "react";
import { getUserRole, getUser } from "@features/auth/api/clientAuth";
import { usePlanificacion } from "../hooks/usePlanificacion";
import { planificacionRoleView } from "../lib/roleView";
import PlanAdminView from "./PlanAdminView";
import PlanReviewerView from "./PlanReviewerView";
import PlanStudentView from "./PlanStudentView";

export default function PlanificacionView() {
  const { days, loading, refresh } = usePlanificacion();
  const role = useMemo(() => getUserRole(), []);
  const user = useMemo(() => getUser(), []);
  const view = planificacionRoleView(role ?? "", user?.id);

  return (
    <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-surface-muted">
      <div className="max-w-screen-2xl mx-auto">
        {view === "admin" && (
          <PlanAdminView days={days} loading={loading} onRefresh={refresh} />
        )}
        {view === "reviewer" && (
          role === "Tutor" ? (
            <PlanReviewerView
              days={days}
              loading={loading}
              reviewerKind="tutor"
              viewerId={user!.id!}
              viewerName={user?.firstName ?? undefined}
            />
          ) : (
            <PlanReviewerView
              days={days}
              loading={loading}
              reviewerKind="jurado"
              viewerId={user!.id!}
              viewerName={user?.firstName ?? undefined}
            />
          )
        )}
        {view === "student" && (
          <PlanStudentView
            days={days}
            loading={loading}
            viewerEmail={user?.email ?? ""}
          />
        )}
      </div>
    </main>
  );
}
