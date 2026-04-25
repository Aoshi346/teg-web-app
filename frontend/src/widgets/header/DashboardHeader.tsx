"use client";

import React, { useState, useEffect, useRef } from "react";
import { useSidebar } from "@widgets/sidebar/SidebarContext";
import {
  ChevronDown,
  Menu,
  ChevronsLeft,
  LogOut,
  User,
} from "lucide-react";
import { NotificationBell } from "@features/notifications";
import { getUserRole, getUserEmail, logout } from "@features/auth/api/clientAuth";
import { useRouter } from "next/navigation";
import { Surface } from "@shared/ui/Surface";

interface DashboardHeaderProps {
  pageTitle: string;
}

const AVATAR_COLORS = [
  "bg-blue-100 text-blue-600",
  "bg-purple-100 text-purple-600",
  "bg-emerald-100 text-emerald-600",
  "bg-amber-100 text-amber-600",
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

  const avatarColor = userEmail
    ? AVATAR_COLORS[userEmail.length % AVATAR_COLORS.length]
    : AVATAR_COLORS[0];

  const displayName = userEmail
    ? userEmail.split("@")[0].charAt(0).toUpperCase() + userEmail.split("@")[0].slice(1)
    : "Usuario";

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 h-16 lg:h-[72px] flex-shrink-0">
      <div className="px-3 sm:px-4 md:px-6 lg:px-8 h-full flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
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

          <button
            className="hidden lg:inline-flex items-center justify-center p-2 rounded-lg hover:bg-slate-100 text-slate-600 transition-colors"
            aria-label={sidebar.isCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral"}
            onClick={sidebar.toggleCollapse}
          >
            <ChevronsLeft className={`w-5 h-5 transition-transform duration-200 ${sidebar.isCollapsed ? "rotate-180" : ""}`} />
          </button>

          <h2 className="text-lg lg:text-xl font-bold text-slate-900 tracking-tight truncate">
            {pageTitle}
          </h2>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          <NotificationBell />

          <div className="h-7 w-px bg-slate-200/60 hidden sm:block" />

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
              <div className="relative">
                {userEmail ? (
                  <div className={`w-8 h-8 sm:w-9 sm:h-9 rounded-lg flex items-center justify-center text-sm font-bold ${avatarColor} shadow-sm`}>
                    {userEmail[0].toUpperCase()}
                  </div>
                ) : (
                  <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center">
                    <User className="w-4 h-4 text-slate-400" />
                  </div>
                )}
                <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 border-2 border-white rounded-full" />
              </div>

              <div className="hidden md:block text-left">
                <p className="text-sm font-bold text-slate-800 leading-none truncate max-w-[120px]">
                  {displayName}
                </p>
              </div>

              <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${isProfileOpen ? "rotate-180" : ""}`} />
            </button>

            {isProfileOpen && (
              <div className="absolute right-0 top-full mt-3 w-64 sm:w-72 bg-white border border-slate-200 rounded-xl shadow-xl p-2 z-[60] animate-in fade-in zoom-in-95 slide-in-from-top-2 duration-200 origin-top-right">
                <Surface tone="inverse" className="px-4 py-3 rounded-xl mb-2 gap-0">
                  <p className="text-xs font-bold text-blue-300/80 uppercase tracking-widest mb-1">Identificado como</p>
                  <p className="text-sm font-bold text-white truncate">{userEmail || "Usuario"}</p>
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded-md bg-white/15 border border-white/20 text-[10px] font-bold tracking-widest text-white uppercase mt-1">
                    {userRole || "Invitado"}
                  </span>
                </Surface>

                <div className="space-y-0.5">
                  <p className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Cuenta</p>
                  <button
                    className="w-full text-left flex items-center gap-3 px-3 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 hover:text-primary rounded-xl transition-colors"
                    onClick={() => { setIsProfileOpen(false); router.push("/dashboard/settings"); }}
                  >
                    <div className="p-1.5 bg-slate-100 rounded-lg text-slate-500"><User className="w-4 h-4" /></div>
                    Configuración
                  </button>

                  <div className="my-1.5 border-t border-slate-100 mx-2" />

                  <button
                    onClick={handleLogout}
                    className="w-full text-left flex items-center gap-3 px-3 py-2.5 text-sm font-semibold text-destructive hover:bg-destructive/10 rounded-xl transition-colors"
                  >
                    <div className="p-1.5 bg-destructive/10 rounded-lg text-destructive"><LogOut className="w-4 h-4" /></div>
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
