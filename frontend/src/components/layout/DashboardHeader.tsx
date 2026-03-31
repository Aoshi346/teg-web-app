"use client";

import React, { useState, useEffect, useRef } from "react";
import { useSidebar } from "./SidebarContext";
import {
  Bell,
  ChevronDown,
  Menu,
  ChevronsLeft,
  LogOut,
  User,
} from "lucide-react";
import { getUserRole, getUserEmail, logout } from "@/features/auth/clientAuth";
import { useRouter } from "next/navigation";

interface DashboardHeaderProps {
  pageTitle: string;
}

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

  const avatarColors = ["bg-blue-100 text-blue-600", "bg-purple-100 text-purple-600", "bg-emerald-100 text-emerald-600", "bg-amber-100 text-amber-600"];
  const avatarColor = userEmail ? avatarColors[userEmail.length % avatarColors.length] : avatarColors[0];

  return (
    <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 sticky top-0 z-10 h-14 sm:h-16 md:h-[72px] flex-shrink-0">
      <div className="px-3 sm:px-4 md:px-6 lg:px-8 h-full flex items-center justify-between gap-2">
        {/* Left: menu + title */}
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
          {/* Mobile menu toggle */}
          <button
            className={`lg:hidden inline-flex items-center justify-center p-2.5 rounded-xl border transition-colors touch-manipulation ${
              sidebar.mobileOpen
                ? "bg-usm-blue border-usm-blue text-white shadow-sm"
                : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50 active:bg-slate-100"
            }`}
            aria-label={sidebar.mobileOpen ? "Cerrar menú" : "Abrir menú"}
            onClick={sidebar.toggleMobile}
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Desktop collapse toggle */}
          <button
            className="hidden lg:inline-flex items-center justify-center p-2 rounded-lg hover:bg-slate-100 text-slate-600 active:bg-slate-200 transition-colors"
            aria-label={sidebar.isCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral"}
            onClick={sidebar.toggleCollapse}
          >
            <ChevronsLeft className={`w-5 h-5 transition-transform duration-200 ${sidebar.isCollapsed ? "rotate-180" : ""}`} />
          </button>

          {/* Page title */}
          <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-slate-900 tracking-tight truncate">
            {pageTitle}
          </h2>
        </div>

        {/* Right: notifications + profile */}
        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          {/* Notification bell */}
          <button className="relative p-2 sm:p-2.5 rounded-xl bg-slate-50 border border-slate-100/50 hover:bg-white hover:border-blue-200 hover:shadow-sm active:scale-95 transition-all duration-200 touch-manipulation">
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
              className={`flex items-center gap-2 p-1 pr-2 rounded-xl border transition-all duration-200 touch-manipulation focus:outline-none ${
                isProfileOpen
                  ? "bg-blue-50/50 border-blue-200 shadow-sm"
                  : "bg-white border-slate-100 hover:border-slate-200 hover:shadow-sm active:scale-95"
              }`}
            >
              {/* Avatar */}
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

              {/* Name + role (desktop) */}
              <div className="hidden md:block text-left">
                <p className="text-sm font-bold text-slate-800 leading-none truncate max-w-[120px]">
                  {userEmail ? userEmail.split("@")[0].charAt(0).toUpperCase() + userEmail.split("@")[0].slice(1) : "Usuario"}
                </p>
                <p className="text-[10px] uppercase tracking-widest font-bold text-usm-blue mt-0.5 flex items-center gap-1 opacity-80">
                  <span className="w-1 h-1 rounded-full bg-usm-blue/60" />
                  {userRole || "Invitado"}
                </p>
              </div>

              <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${isProfileOpen ? "rotate-180" : ""}`} />
            </button>

            {/* Dropdown */}
            {isProfileOpen && (
              <div className="absolute right-0 top-full mt-2 w-64 sm:w-72 bg-white/95 backdrop-blur-xl rounded-2xl shadow-[0_16px_40px_rgba(0,0,0,0.12)] border border-slate-100 p-2 z-50 animate-in fade-in zoom-in-95 slide-in-from-top-2 duration-200 origin-top-right">
                {/* Header card */}
                <div className="px-4 py-3 bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl mb-2 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-16 h-16 bg-usm-blue/10 rounded-full -mr-4 -mt-4 blur-2xl" />
                  <div className="relative z-10">
                    <p className="text-xs font-bold text-blue-300/80 uppercase tracking-widest mb-1">Identificado como</p>
                    <p className="text-sm font-bold text-white truncate">{userEmail || "Usuario"}</p>
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded-md bg-usm-blue/20 border border-blue-400/20 text-[10px] font-bold tracking-widest text-blue-100 uppercase mt-1">
                      {userRole || "Invitado"}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="space-y-0.5">
                  <p className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Cuenta</p>
                  <button
                    className="w-full text-left flex items-center gap-3 px-3 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 hover:text-blue-700 rounded-xl transition-colors"
                    onClick={() => { setIsProfileOpen(false); router.push("/dashboard/settings"); }}
                  >
                    <div className="p-1.5 bg-slate-100 rounded-lg"><User className="w-4 h-4 text-slate-500" /></div>
                    Configuración
                  </button>

                  <div className="my-1.5 border-t border-slate-100 mx-2" />

                  <button
                    onClick={handleLogout}
                    className="w-full text-left flex items-center gap-3 px-3 py-2.5 text-sm font-semibold text-red-600 hover:bg-red-50 rounded-xl transition-colors"
                  >
                    <div className="p-1.5 bg-red-50 rounded-lg"><LogOut className="w-4 h-4 text-red-500" /></div>
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
