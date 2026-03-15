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

        <div className="flex items-center gap-3 sm:gap-4 flex-shrink-0">
          {/* Action Area: Notifications */}
          <div className="flex items-center">
            <button className="relative p-2 rounded-xl hover:bg-slate-100/80 active:bg-slate-200 transition-all duration-200 group touch-manipulation">
              <Bell className="w-5 h-5 text-slate-500 group-hover:text-blue-600 transition-colors" />
              <span className="absolute top-1.5 right-1.5 flex h-2.5 w-2.5 items-center justify-center">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500 border border-white"></span>
              </span>
            </button>
          </div>

          {/* Vertical Divider */}
          <div className="h-8 w-px bg-slate-200/60 hidden sm:block mx-1"></div>

          {/* User Profile Card */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className={`flex items-center gap-3 p-1 rounded-2xl transition-all duration-300 touch-manipulation focus:outline-none ${
                isProfileOpen 
                  ? 'bg-blue-50/50 shadow-sm ring-1 ring-blue-100' 
                  : 'hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-3 pr-2">
                <div className="relative">
                  {userEmail ? (
                    <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center text-sm font-bold ${getAvatarColor(userEmail)} shadow-sm ring-2 ring-white transition-transform duration-300 ${isProfileOpen ? 'scale-90' : ''}`}>
                      {userEmail[0].toUpperCase()}
                    </div>
                  ) : (
                    <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center">
                      <User className="w-5 h-5 text-slate-400" />
                    </div>
                  )}
                  {/* Status Indicator */}
                  <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-white rounded-full shadow-sm"></div>
                </div>

                <div className="hidden md:block text-left">
                  <p className="text-sm font-bold text-slate-800 leading-none truncate max-w-[140px]">
                    {userEmail ? (userEmail.split('@')[0].charAt(0).toUpperCase() + userEmail.split('@')[0].slice(1)) : 'Usuario'}
                  </p>
                  <p className="text-[10px] subpixel-antialiased uppercase tracking-widest font-black text-blue-600 mt-1 flex items-center gap-1 opacity-80">
                    <span className="w-1 h-1 rounded-full bg-blue-400"></span>
                    {userRole || 'Invitado'}
                  </p>
                </div>
                
                <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-300 ${isProfileOpen ? "rotate-180 text-blue-500" : "group-hover:text-slate-600"}`} />
              </div>
            </button>

            {isProfileOpen && (
              <div className="absolute right-0 top-full mt-3 w-72 bg-white/95 backdrop-blur-3xl rounded-3xl shadow-[0_20px_50px_rgba(0,0,0,0.15)] border border-slate-100 p-2.5 z-50 animate-in fade-in zoom-in-95 slide-in-from-top-2 duration-300 origin-top-right overflow-hidden group/menu">
                {/* Dropdown Header Card */}
                <div className="px-4 py-4 bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl mb-3 shadow-lg relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-8 bg-blue-500/10 rounded-full -mr-4 -mt-4 blur-2xl"></div>
                  <div className="relative z-10">
                    <p className="text-xs font-bold text-blue-300/80 uppercase tracking-widest mb-1">Identificado como</p>
                    <p className="text-sm font-bold text-white truncate mb-0.5">
                      {userEmail || "Usuario"}
                    </p>
                    <div className="inline-flex items-center px-1.5 py-0.5 rounded-md bg-blue-500/20 border border-blue-400/20 text-[10px] font-black tracking-widest text-blue-100 uppercase mt-1">
                      {userRole || "Invitado"}
                    </div>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="px-3 py-1.5">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Cuenta</p>
                  </div>
                  <button
                    className="w-full text-left flex items-center gap-3 px-3 py-3 text-sm font-bold text-slate-600 hover:bg-slate-50 hover:text-blue-700 rounded-xl transition-all group/item"
                    onClick={() => { setIsProfileOpen(false); router.push("/dashboard/settings"); }}
                  >
                    <div className="p-2 bg-slate-100 group-hover/item:bg-blue-100 rounded-lg transition-colors">
                      <User className="w-4 h-4 text-slate-500 group-hover/item:text-blue-600" />
                    </div>
                    Configuración de Perfil
                  </button>
                  
                  <div className="my-2 border-t border-slate-100 mx-2"></div>
                  
                  <button
                    onClick={handleLogout}
                    className="w-full text-left flex items-center gap-3 px-3 py-3 text-sm font-bold text-red-600 hover:bg-red-50 hover:text-red-700 rounded-xl transition-all group/logout"
                  >
                    <div className="p-2 bg-red-50 group-hover/logout:bg-red-100 rounded-lg transition-colors">
                      <LogOut className="w-4 h-4 text-red-500 group-hover/logout:text-red-600" />
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

