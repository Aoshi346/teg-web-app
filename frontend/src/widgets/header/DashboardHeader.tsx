"use client";

import React, { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ChevronsLeft, ChevronDown } from "lucide-react";
import { getUserEmail, getUserRole, logout } from "@features/auth/api/clientAuth";
import { NotificationBell } from "@features/notifications";
import { useSidebar } from "@widgets/sidebar/SidebarContext";
import Breadcrumb from "@widgets/header/Breadcrumb";
import ProfileMenu from "@widgets/header/ProfileMenu";

export interface DashboardHeaderProps {
  /**
   * pageTitle es mantenido por compatibilidad con todas las páginas existentes.
   * Sub-M: la cadena alimenta el Breadcrumb como segmento "now" — NO se renderiza
   * como un <h2> autónomo en el header.
   */
  pageTitle: string;
}

function deriveName(email: string): string {
  const local = email.split("@")[0] ?? "";
  return local.charAt(0).toUpperCase() + local.slice(1);
}

export default function DashboardHeader({ pageTitle }: DashboardHeaderProps) {
  const router = useRouter();
  const sidebar = useSidebar();
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLButtonElement>(null);

  const email = getUserEmail() ?? "";
  const role = getUserRole() ?? "";
  const displayName = deriveName(email);
  const initials = email.charAt(0).toUpperCase();

  const handleLogout = useCallback(() => {
    logout();
    router.push("/");
  }, [router]);

  return (
    <header className="hd">
      <div className="hd-left">
        {/* Botón hamburguesa para móvil */}
        <button
          className="hd-menu-btn lg:hidden"
          type="button"
          onClick={sidebar.toggleMobile}
          aria-label={sidebar.mobileOpen ? "Cerrar menú" : "Abrir menú"}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {sidebar.mobileOpen ? (
              <>
                <path d="M18 6 6 18" />
                <path d="M6 6l12 12" />
              </>
            ) : (
              <>
                <line x1="4" y1="6" x2="20" y2="6" />
                <line x1="4" y1="12" x2="20" y2="12" />
                <line x1="4" y1="18" x2="20" y2="18" />
              </>
            )}
          </svg>
        </button>

        {/* Botón colapsar para escritorio */}
        <button
          className={`hd-collapse-btn hidden lg:inline-flex${sidebar.isCollapsed ? " is-collapsed" : ""}`}
          type="button"
          onClick={sidebar.toggleCollapse}
          aria-label={
            sidebar.isCollapsed
              ? "Expandir barra lateral"
              : "Colapsar barra lateral"
          }
        >
          <ChevronsLeft />
        </button>

        {/* Breadcrumb (expanded text trail | collapsed pill) */}
        <Breadcrumb
          pageTitle={pageTitle}
          variant={sidebar.isCollapsed ? "collapsed" : "expanded"}
        />
      </div>

      <div className="hd-actions">
        <NotificationBell />

        {/* Chip de perfil */}
        <button
          ref={profileRef}
          className={`hd-prof${profileOpen ? " open" : ""}`}
          type="button"
          onClick={() => setProfileOpen((prev) => !prev)}
          aria-label="Abrir menú de perfil"
          aria-expanded={profileOpen}
        >
          <div className="hd-prof-ava">{initials}</div>
          <span className="hd-prof-name">{displayName}</span>
          <ChevronDown className="chev" />
        </button>

        {/* Dropdown de perfil */}
        <ProfileMenu
          isOpen={profileOpen}
          email={email}
          role={role}
          onClose={() => setProfileOpen(false)}
          onLogout={handleLogout}
          anchorRef={profileRef}
        />
      </div>
    </header>
  );
}
