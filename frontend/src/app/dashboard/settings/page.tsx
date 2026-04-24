"use client";

import React from "react";
import DashboardHeader from "@widgets/header/DashboardHeader";
import { SettingsShell } from "@features/settings";

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <DashboardHeader pageTitle="Configuración" />
      <main className="max-w-7xl mx-auto px-4 py-8">
        <SettingsShell />
      </main>
    </div>
  );
}
