"use client";

import React, { useContext } from "react";
import SidebarContext, { SidebarContextType } from "./SidebarContext";
import Image from 'next/image';
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
  isSidebarCollapsed?: boolean;
  isMobileSidebarOpen?: boolean;
  onMobileSidebarToggle?: () => void;
  onSidebarCollapse?: () => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({ pageTitle, isSidebarCollapsed, isMobileSidebarOpen, onMobileSidebarToggle, onSidebarCollapse }) => {
  // Read sidebar context as a fallback when props are not passed through cloneElement
  const sidebarCtx = useContext(SidebarContext) as SidebarContextType | undefined;

  const effectiveIsCollapsed = typeof isSidebarCollapsed !== "undefined" ? isSidebarCollapsed : sidebarCtx?.isCollapsed ?? false;
  const effectiveIsMobileOpen = typeof isMobileSidebarOpen !== "undefined" ? isMobileSidebarOpen : sidebarCtx?.mobileOpen ?? false;
  const effectiveOnMobileToggle = onMobileSidebarToggle ?? sidebarCtx?.toggleMobile ?? (() => { });
  const effectiveOnCollapse = onSidebarCollapse ?? sidebarCtx?.toggleCollapse ?? (() => { });

  const router = useRouter();
  const [userEmail, setUserEmail] = React.useState<string | null>(null);
  const [userRole, setUserRole] = React.useState<string | null>(null);
  const [isProfileOpen, setIsProfileOpen] = React.useState(false);
  const profileRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    setUserEmail(getUserEmail());
    setUserRole(getUserRole());

    const handleClickOutside = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
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

  // Deterministic avatar color
  const getAvatarColor = (email: string) => {
    const colors = ["bg-blue-100 text-blue-600", "bg-purple-100 text-purple-600", "bg-emerald-100 text-emerald-600", "bg-amber-100 text-amber-600"];
    return colors[email.length % colors.length];
  };

  return (
    // ... (header structure)
    <header className="header-container bg-white/80 backdrop-blur-md border-b border-gray-200/50 sticky top-0 z-10 h-16 sm:h-20 md:h-[89px] flex-shrink-0 transition-all duration-300">
      <div className="px-3 sm:px-4 md:px-6 lg:px-8 h-full flex items-center justify-between gap-2">
        {/* ... (left side controls unchanged) */}
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
          <button
            className={`lg:hidden inline-flex items-center justify-center p-2 sm:p-3 rounded-md border transition-colors touch-manipulation ${effectiveIsMobileOpen
              ? "bg-blue-600 border-blue-600 text-white shadow-sm"
              : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50 active:bg-slate-100"
              }`}
            aria-label={effectiveIsMobileOpen ? "Cerrar menú" : "Abrir menú"}
            onClick={effectiveOnMobileToggle}
          >
            <Menu className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
          <button
            className="hidden lg:inline-flex items-center justify-center p-2 rounded-md hover:bg-slate-100 hover:text-blue-700 text-slate-600 active:bg-slate-200 transition-colors touch-manipulation"
            aria-label="Colapsar barra lateral"
            onClick={() => {
              // ... existing collapse logic
              try { if (sidebarCtx && effectiveOnCollapse !== sidebarCtx.toggleCollapse) sidebarCtx.setIsCollapsed(!sidebarCtx.isCollapsed); } catch { }
              try { effectiveOnCollapse(); } catch { }
            }}
            title={effectiveIsCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral"}
          >
            <ChevronsLeft className={`w-5 h-5 ${effectiveIsCollapsed ? "rotate-180 transition-transform" : "transition-transform"}`} />
          </button>
          <h2 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold text-slate-900 font-montserrat tracking-tight truncate">
            {pageTitle}
          </h2>
        </div>

        <div className="flex items-center gap-1 sm:gap-2 bg-slate-50/80 p-1 sm:p-1.5 rounded-full flex-shrink-0 border border-slate-100 shadow-sm">
          <button className="relative p-1.5 sm:p-2 rounded-full hover:bg-white hover:shadow-[0_2px_8px_rgba(0,0,0,0.06)] active:bg-slate-100 transition-all duration-200 group touch-manipulation">
            <Bell className="w-4 h-4 sm:w-5 sm:h-5 text-slate-600 group-hover:text-blue-700 transition-colors" />
            <span className="absolute top-1 right-1 sm:top-2 sm:right-2 flex h-3 w-3 sm:h-4 sm:w-4 items-center justify-center">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 sm:h-3 sm:w-3 bg-red-500"></span>
            </span>
          </button>

          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className="flex items-center gap-1 sm:gap-2 p-1 pr-1.5 sm:pr-2 rounded-full hover:bg-white hover:shadow-sm active:bg-gray-100 transition-all duration-200 touch-manipulation focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500/20"
            >
              {userEmail ? (
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${getAvatarColor(userEmail)} shadow-sm ring-2 ring-white`}>
                  {userEmail[0].toUpperCase()}
                </div>
              ) : (
                <Image src="https://i.pravatar.cc/300" alt="User avatar" width={32} height={32} className="rounded-full border-2 border-white shadow-sm" />
              )}
              <ChevronDown className={`w-3 h-3 sm:w-4 sm:h-4 text-slate-400 hidden sm:block transition-transform duration-200 ${isProfileOpen ? "rotate-180" : ""}`} />
            </button>

            {isProfileOpen && (
              <div className="absolute right-0 top-full mt-2 w-56 bg-white/95 backdrop-blur-xl rounded-xl shadow-xl border border-slate-100 py-1 z-50 animate-in fade-in zoom-in-95 duration-200 origin-top-right">
                <div className="px-4 py-3 border-b border-slate-100/80">
                  <p className="text-sm font-bold text-slate-900 truncate">
                    {userEmail || "Usuario"}
                  </p>
                  <p className="text-xs text-slate-500 truncate mt-1 font-semibold">
                    {userRole || "Invitado"}
                  </p>
                </div>

                <div className="p-1">
                  <button
                    className="w-full text-left flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                    onClick={() => { setIsProfileOpen(false); router.push("/dashboard/settings"); }}
                  >
                    <User className="w-4 h-4 text-gray-400" />
                    Mi Perfil
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
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

