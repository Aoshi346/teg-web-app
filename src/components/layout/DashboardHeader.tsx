"use client";

import React, { useContext } from "react";
import SidebarContext, { SidebarContextType } from "./SidebarContext";

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
              className={`flex items-center gap-2 sm:gap-3 p-1.5 sm:p-2 pr-3 sm:pr-4 rounded-full border-2 transition-all duration-300 touch-manipulation focus:outline-none bg-white ${isProfileOpen ? 'border-blue-200 shadow-md ring-4 ring-blue-50/50 scale-[0.98]' : 'border-transparent shadow-sm hover:shadow-md hover:border-slate-200 active:scale-[0.98]'}`}
            >
              {userEmail ? (
                <div className={`w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold ${getAvatarColor(userEmail)} shadow-sm`}>
                  {userEmail[0].toUpperCase()}
                </div>
              ) : (
                <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-slate-100 border-2 border-slate-200 flex items-center justify-center">
                  <User className="w-4 h-4 text-slate-400" />
                </div>
              )}
              <div className="hidden sm:block text-left mr-1">
                 <p className="text-sm font-bold text-slate-700 leading-tight truncate max-w-[120px]">{userEmail ? userEmail.split('@')[0] : 'Usuario'}</p>
                 <p className="text-[10px] uppercase tracking-wider font-semibold text-blue-600">{userRole || 'Invitado'}</p>
              </div>
              <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-300 ${isProfileOpen ? "rotate-180 text-blue-500" : "group-hover:text-blue-500"}`} />
            </button>

            {isProfileOpen && (
              <div className="absolute right-0 top-full mt-3 w-64 bg-white/95 backdrop-blur-2xl rounded-2xl shadow-2xl border border-slate-100/80 p-2 z-50 animate-in fade-in zoom-in-95 duration-200 origin-top-right overflow-hidden">
                <div className="px-4 py-3 bg-slate-50/50 rounded-xl mb-2 border border-slate-100/50">
                  <p className="text-sm font-bold text-slate-900 truncate">
                    {userEmail || "Usuario"}
                  </p>
                  <p className="text-xs text-slate-500 truncate mt-1 font-semibold">
                    {userRole || "Invitado"}
                  </p>
                </div>

                <div className="px-1 pb-1 space-y-1">
                  <button
                    className="w-full text-left flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-700 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-all group"
                    onClick={() => { setIsProfileOpen(false); router.push("/dashboard/settings"); }}
                  >
                    <div className="p-1.5 bg-slate-100 group-hover:bg-blue-100 rounded-md transition-colors">
                      <User className="w-4 h-4 text-slate-500 group-hover:text-blue-600" />
                    </div>
                    Configuración
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-all group mt-1"
                  >
                    <div className="p-1.5 bg-red-50 group-hover:bg-red-100 rounded-md transition-colors">
                      <LogOut className="w-4 h-4 text-red-500 group-hover:text-red-700" />
                    </div>
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

