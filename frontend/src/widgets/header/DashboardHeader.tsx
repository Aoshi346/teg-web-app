"use client";

import React, { useState, useEffect, useRef } from "react";
import { useSidebar } from "@widgets/sidebar/SidebarContext";
import {
  Bell,
  ChevronDown,
  Menu,
  ChevronsLeft,
  LogOut,
  User,
} from "lucide-react";
import { getUserRole, getUserEmail, logout } from "@features/auth/api/clientAuth";
import { useRouter } from "next/navigation";
import { cn } from "@shared/lib/utils";

interface DashboardHeaderProps {
  pageTitle: string;
}

const AVATAR_GRADIENTS = [
  "from-indigo-600 to-blue-500",
  "from-slate-800 to-indigo-700",
  "from-emerald-600 to-teal-500",
  "from-rose-500 to-amber-500",
];

const DashboardHeader: React.FC<DashboardHeaderProps> = ({ pageTitle }) => {
  const sidebar = useSidebar();
  const router = useRouter();

  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setUserEmail(getUserEmail());
    setUserRole(getUserRole());

    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setIsProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const gradientIdx = userEmail ? userEmail.length % AVATAR_GRADIENTS.length : 0;
  const gradient = AVATAR_GRADIENTS[gradientIdx];

  const displayName = userEmail
    ? userEmail.split("@")[0].charAt(0).toUpperCase() + userEmail.split("@")[0].slice(1)
    : "Usuario";

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 h-16 lg:h-[72px] flex-shrink-0">
      <div className="px-3 sm:px-4 md:px-6 lg:px-8 h-full flex items-center justify-between gap-2">
        {/* Left: menu + title */}
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
          {/* Mobile menu toggle */}
          <button
            className={`lg:hidden inline-flex items-center justify-center p-2.5 rounded-lg border transition-colors touch-manipulation ${
              sidebar.mobileOpen
                ? "bg-primary text-white border-primary"
                : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
            }`}
            aria-label={sidebar.mobileOpen ? "Cerrar menú" : "Abrir menú"}
            onClick={sidebar.toggleMobile}
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Desktop collapse toggle */}
          <button
            className="hidden lg:inline-flex items-center justify-center p-2 rounded-lg hover:bg-slate-100 text-slate-600 transition-colors"
            aria-label={sidebar.isCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral"}
            onClick={sidebar.toggleCollapse}
          >
            <ChevronsLeft className={`w-5 h-5 transition-transform duration-200 ${sidebar.isCollapsed ? "rotate-180" : ""}`} />
          </button>

          {/* Page title */}
          <h2 className="text-lg lg:text-xl font-bold text-slate-900 tracking-tight truncate">
            {pageTitle}
          </h2>
        </div>

        {/* Right: notifications + profile */}
        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          {/* Notification bell */}
          <button className="relative p-2 sm:p-2.5 rounded-lg hover:bg-slate-100 active:scale-95 transition-all duration-200 touch-manipulation">
            <Bell className="w-4 h-4 sm:w-5 sm:h-5 text-slate-500" />
            <span className="absolute top-1 right-1 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500 border border-white" />
            </span>
          </button>

          {/* Divider (desktop) */}
          <div className="h-7 w-px bg-slate-200/60 hidden sm:block" />

          {/* Profile dropdown */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              aria-expanded={isProfileOpen}
              aria-haspopup="menu"
              className={`flex items-center gap-2 p-1 pr-2 rounded-xl border transition-all duration-200 touch-manipulation focus:outline-none ${
                isProfileOpen
                  ? "bg-primary/10 border-primary/20 shadow-sm"
                  : "bg-transparent border-transparent hover:bg-slate-100"
              }`}
            >
              {/* Avatar */}
              <div className="relative">
                {userEmail ? (
                  <div className={cn("w-8 h-8 sm:w-9 sm:h-9 rounded-lg flex items-center justify-center text-sm font-bold bg-gradient-to-br shadow-sm text-white", gradient)}>
                    {userEmail[0].toUpperCase()}
                  </div>
                ) : (
                  <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center">
                    <User className="w-4 h-4 text-slate-400" />
                  </div>
                )}
                <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 border-2 border-white rounded-full" />
              </div>

              {/* Name + role (desktop) */}
              <div className="hidden md:block text-left">
                <p className="text-sm font-bold text-slate-800 leading-none truncate max-w-[120px]">
                  {displayName}
                </p>
                <p className="text-[10px] uppercase tracking-widest font-bold text-primary mt-0.5 opacity-80">
                  {userRole || "Invitado"}
                </p>
              </div>

              <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${isProfileOpen ? "rotate-180" : ""}`} />
            </button>

            {/* Dropdown panel */}
            {isProfileOpen && (
              <div className="absolute right-0 top-full mt-3 w-72 bg-white rounded-xl shadow-xl border border-slate-200 p-1.5 z-[60] animate-in fade-in zoom-in-95 slide-in-from-top-2 duration-200 origin-top-right">
                {/* Header block */}
                <div className="flex items-center gap-3 px-3 py-3 border-b border-slate-100">
                  <div
                    className={cn(
                      "w-11 h-11 rounded-full bg-gradient-to-br shadow-sm flex items-center justify-center flex-shrink-0",
                      gradient
                    )}
                  >
                    <span className="font-display text-xl text-white select-none">
                      {userEmail ? userEmail[0].toUpperCase() : "?"}
                    </span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-slate-900 truncate">{displayName}</p>
                    <p className="text-xs text-slate-500 truncate mt-0.5">{userEmail || "—"}</p>
                    <p className="text-[10px] uppercase tracking-widest text-primary mt-1.5 font-semibold">
                      {userRole || "Invitado"}
                    </p>
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-1 space-y-0.5">
                  <button
                    className="w-full text-left flex items-center gap-3 px-3 py-2 text-sm text-slate-700 rounded-lg hover:bg-slate-50 hover:text-slate-900 transition-colors"
                    onClick={() => { setIsProfileOpen(false); router.push("/dashboard/settings"); }}
                  >
                    <User className="w-4 h-4 text-slate-500" />
                    Configuración
                  </button>

                  <button
                    onClick={handleLogout}
                    className="w-full text-left flex items-center gap-3 px-3 py-2 text-sm font-medium text-slate-700 rounded-lg hover:bg-destructive/10 hover:text-destructive transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Cerrar Sesión
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default DashboardHeader;
