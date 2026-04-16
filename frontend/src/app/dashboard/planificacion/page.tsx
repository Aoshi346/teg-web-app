"use client";

import React from "react";
import DashboardHeader from "@widgets/header/DashboardHeader";
import PlanificacionView from "@features/planificacion/components/PlanificacionView";

export default function PlanificacionPage() {
  return (
    <>
      <DashboardHeader pageTitle="Planificación" />
      <PlanificacionView />
    </>
  );
}
