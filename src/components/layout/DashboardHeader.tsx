"use client";

import React, { useContext } from "react";
import SidebarContext, { SidebarContextType } from "./SidebarContext";
import Image from 'next/image';
import {
  Bell,
  ChevronDown,
  Menu,
  ChevronsLeft,
} from "lucide-react";

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
  const effectiveOnMobileToggle = onMobileSidebarToggle ?? sidebarCtx?.toggleMobile ?? (() => {});
  const effectiveOnCollapse = onSidebarCollapse ?? sidebarCtx?.toggleCollapse ?? (() => {});

  return (
    <header className="header-container bg-white border-b border-gray-200 sticky top-0 z-10 h-16 sm:h-20 md:h-[89px] flex-shrink-0">
      <div className="px-3 sm:px-4 md:px-6 lg:px-8 h-full flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
          <button
            className={`lg:hidden inline-flex items-center justify-center p-2 sm:p-3 rounded-md border transition-colors touch-manipulation ${
              effectiveIsMobileOpen
                ? "bg-blue-600 border-blue-600 text-white"
                : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50 active:bg-gray-100"
            }`}
            aria-label={effectiveIsMobileOpen ? "Cerrar menú" : "Abrir menú"}
            onClick={effectiveOnMobileToggle}
          >
            <Menu className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
          <button
            className="hidden lg:inline-flex items-center justify-center p-2 rounded-md hover:bg-gray-100 active:bg-gray-200 transition-colors touch-manipulation"
            aria-label="Colapsar barra lateral"
            onClick={() => {
              try {
                console.debug('[DashboardHeader] collapse click - calling effectiveOnCollapse');
              } catch {}
              try {
                effectiveOnCollapse();
              } catch (err) {
                try { console.debug('[DashboardHeader] effectiveOnCollapse threw', err); } catch {}
              }

              // Fallback: if context exists and the effective handler is not the same as the
              // context toggle, call setIsCollapsed directly to ensure UI updates.
              try {
                if (sidebarCtx && typeof sidebarCtx.setIsCollapsed === 'function' && effectiveOnCollapse !== sidebarCtx.toggleCollapse) {
                  console.debug('[DashboardHeader] fallback: toggling context.setIsCollapsed directly');
                  sidebarCtx.setIsCollapsed(!sidebarCtx.isCollapsed);
                }
              } catch (err) {
                try { console.debug('[DashboardHeader] fallback threw', err); } catch {}
              }
            }}
            title={effectiveIsCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral"}
          >
            <ChevronsLeft className={`w-5 h-5 ${effectiveIsCollapsed ? "rotate-180 transition-transform" : "transition-transform"}`} />
          </button>
          <h2 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold text-gray-900 truncate">
            {pageTitle}
          </h2>
        </div>
        <div className="flex items-center gap-1 sm:gap-2 bg-gray-100 p-1 sm:p-1.5 rounded-full flex-shrink-0">
          <button className="relative p-1.5 sm:p-2 rounded-full hover:bg-gray-200/70 active:bg-gray-300 transition-all duration-200 group touch-manipulation">
            <Bell className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600 group-hover:text-blue-600 transition-colors" />
            <span className="absolute top-1 right-1 sm:top-2 sm:right-2 flex h-3 w-3 sm:h-4 sm:w-4 items-center justify-center">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 sm:h-3 sm:w-3 bg-red-500"></span>
            </span>
          </button>
          <div className="relative group">
            <button className="flex items-center gap-1 sm:gap-2 p-1 pr-1.5 sm:pr-2 rounded-full hover:bg-gray-200/70 active:bg-gray-300 transition-colors touch-manipulation">
              <Image src="https://i.pravatar.cc/300" alt="User avatar" width={32} height={32} className="rounded-full border-2 border-white shadow-sm" />
              <ChevronDown className="w-3 h-3 sm:w-4 sm:h-4 text-gray-500 hidden sm:block" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default DashboardHeader;

