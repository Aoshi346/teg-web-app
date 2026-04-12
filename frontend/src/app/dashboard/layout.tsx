"use client";

import React, { Suspense, useState, useCallback, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { redirect } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import { SidebarProvider } from "@/components/layout/SidebarContext";
import { isAuthenticated, getUser, logout } from "@/features/auth/clientAuth";
import { DashboardSkeleton } from "@/components/ui/DashboardSkeleton";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // P0 FIX: Synchronous auth check BEFORE any render/flash.
  // isAuthenticated() reads sessionStorage instantly — no useEffect needed,
  // no render-then-redirect flash.
  if (!isAuthenticated()) {
    redirect("/");
  }

  const handleSidebarCollapse = useCallback(() => {
    setIsSidebarCollapsed((prev) => !prev);
  }, []);

  const handleMobileSidebarToggle = useCallback(() => {
    setIsMobileSidebarOpen((prev) => !prev);
  }, []);

  // Close mobile sidebar on route change
  useEffect(() => {
    setIsMobileSidebarOpen(false);
  }, [pathname]);

  // Prefetch only the top 3 most-visited routes to avoid wasting bandwidth
  useEffect(() => {
    const routes = [
      "/dashboard",
      "/dashboard/proyectos",
      "/dashboard/tesis",
    ];
    routes.forEach((r) => router.prefetch(r));
  }, [router]);

  // Pending account gate — getUser() is cached from above sync check
  const user = getUser();
  if (user && user.status === "pending") {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full text-center space-y-6">
          <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto">
            <svg className="w-8 h-8 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cuenta en Revisión</h1>
            <p className="text-gray-500 mt-2">
              Tu registro ha sido exitoso, pero tu cuenta debe ser validada por un administrador antes de poder acceder al sistema.
            </p>
          </div>
          <div className="p-4 bg-blue-50 rounded-xl text-left border border-blue-100">
            <p className="text-sm text-blue-800 font-medium mb-1">¿Qué sucede ahora?</p>
            <p className="text-sm text-blue-600">
              Un administrador verificará tus datos. Una vez aprobado, podrás iniciar sesión normalmente.
            </p>
          </div>
          <button
            onClick={() => { logout(); router.push("/"); }}
            className="w-full py-3 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 transition-colors"
          >
            Volver al Inicio
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full flex bg-slate-50 overflow-x-hidden">
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
        mobileOpen={isMobileSidebarOpen}
        setMobileOpen={setIsMobileSidebarOpen}
      />
      <div className="flex-1 flex flex-col min-h-0 overflow-y-auto overflow-x-hidden">
        <SidebarProvider
          value={{
            isCollapsed: isSidebarCollapsed,
            setIsCollapsed: setIsSidebarCollapsed,
            toggleCollapse: handleSidebarCollapse,
            mobileOpen: isMobileSidebarOpen,
            setMobileOpen: setIsMobileSidebarOpen,
            toggleMobile: handleMobileSidebarToggle,
          }}
        >
          <Suspense fallback={<DashboardSkeleton />}>
            {children}
          </Suspense>
        </SidebarProvider>
      </div>
    </div>
  );
}
