"use client";

import React, { useEffect, useRef, useCallback, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  BookOpen,
  CalendarDays,
  TrendingUp,
  PlusCircle,
  Settings,
} from "lucide-react";
import { getUser, getUserRole, logout } from "@features/auth/api/clientAuth";
import ProfileMenu from "@widgets/header/ProfileMenu";

export interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (isCollapsed: boolean) => void;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}

// Estructura completa del menú antes de filtrar por rol
const ALL_MENU_ITEMS = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    index: 1,
    group: "Workspace",
  },
  {
    label: "PTEG",
    href: "/dashboard/proyectos",
    icon: FileText,
    index: 2,
    group: "Workspace",
  },
  {
    label: "TEG",
    href: "/dashboard/tesis",
    icon: BookOpen,
    index: 3,
    group: "Workspace",
  },
  {
    label: "Planificación",
    href: "/dashboard/planificacion",
    icon: CalendarDays,
    index: 4,
    group: "Workspace",
  },
  {
    label: "Seguimiento",
    href: "/dashboard/tracking",
    icon: TrendingUp,
    index: 5,
    group: "Operación",
  },
  {
    label: "Agregar",
    href: "/dashboard/agregar",
    icon: PlusCircle,
    index: 6,
    group: "Operación",
  },
  {
    label: "Configuración",
    href: "/dashboard/settings",
    icon: Settings,
    index: 7,
    group: "Operación",
  },
];

// Grupos y su orden de renderizado
const GROUPS = [
  { title: "Workspace", items: ["Dashboard", "PTEG", "TEG", "Planificación"] },
  { title: "Operación", items: ["Seguimiento", "Agregar", "Configuración"] },
];

function deriveName(email: string): string {
  const local = email.split("@")[0] ?? "";
  return local.charAt(0).toUpperCase() + local.slice(1);
}

type StudentDocType = "PTEG" | "TEG" | null;

/**
 * Determina si el semestre de un estudiante corresponde a PTEG (9°) o TEG (10°).
 * Se evalúa "10" antes que "9" para evitar que "10" sea capturado por includes("1").
 * Retorna null si el semestre es vacío, desconocido, o si el usuario no es Estudiante.
 */
function studentDocType(semester: string | undefined | null): StudentDocType {
  const s = (semester ?? "").toString();
  if (s.includes("10")) return "TEG";
  if (s.includes("9")) return "PTEG";
  return null;
}

const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  mobileOpen,
  setMobileOpen,
}) => {
  const pathname = usePathname();
  const router = useRouter();
  const drawerRef = useRef<HTMLElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const touchStartX = useRef<number>(0);
  const linkRefs = useRef<Map<string, HTMLAnchorElement>>(new Map());
  const footMoreRef = useRef<HTMLButtonElement>(null);
  const [footMenuOpen, setFootMenuOpen] = useState(false);

  const handleFootLogout = useCallback(() => {
    setFootMenuOpen(false);
    logout();
    router.push("/");
  }, [router]);

  const user = getUser();
  const role = getUserRole() ?? "Estudiante";
  const email = user?.email ?? "";
  const displayName = email ? deriveName(email) : "Usuario";

  // Filtra ítems de menú según el rol del usuario y, para Estudiante, según semestre
  const docType = role === "Estudiante" ? studentDocType(user?.semester) : null;
  const menuItems = ALL_MENU_ITEMS.filter((item) => {
    if (item.label === "Agregar") return role === "Administrador";
    if (item.label === "Planificación") return role !== "Estudiante";
    if (item.label === "PTEG") return docType !== "TEG";
    if (item.label === "TEG") return docType !== "PTEG";
    return true;
  });

  // Obtiene los ítems de un grupo específico, respetando el filtrado por rol
  function getGroupItems(groupName: string) {
    const groupDef = GROUPS.find((g) => g.title === groupName);
    if (!groupDef) return [];
    return menuItems.filter((item) => groupDef.items.includes(item.label));
  }

  // Prefetch al hacer hover sobre un enlace
  const handleLinkHover = useCallback(
    (href: string) => {
      router.prefetch(href);
    },
    [router]
  );

  // Cierra el drawer móvil al presionar ESC
  useEffect(() => {
    if (!mobileOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [mobileOpen, setMobileOpen]);

  // Bloquea el scroll del body cuando el drawer móvil está abierto
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  // Animación GSAP del drawer móvil
  useEffect(() => {
    if (!drawerRef.current) return;
    import("gsap").then(({ gsap }) => {
      if (mobileOpen) {
        gsap.fromTo(
          drawerRef.current,
          { x: "-100%" },
          { x: "0%", duration: 0.28, ease: "power2.out" }
        );
      } else {
        gsap.to(drawerRef.current, {
          x: "-100%",
          duration: 0.22,
          ease: "power2.in",
        });
      }
    });
  }, [mobileOpen]);

  // Swipe-to-close para el drawer móvil
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0]?.clientX ?? 0;
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    const delta = touchStartX.current - (e.changedTouches[0]?.clientX ?? 0);
    if (delta > 60) setMobileOpen(false);
  };

  // Atajos de teclado Alt+1..7
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!e.altKey) return;
      const n = parseInt(e.key, 10);
      if (isNaN(n) || n < 1 || n > 7) return;
      const item = ALL_MENU_ITEMS.find((m) => m.index === n);
      if (item) {
        e.preventDefault();
        router.push(item.href);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [router]);

  function isActive(href: string): boolean {
    if (href === "/dashboard") {
      return pathname === "/dashboard" || pathname === "/";
    }
    return pathname.startsWith(href);
  }

  function renderNavItem(item: (typeof ALL_MENU_ITEMS)[0]) {
    const active = isActive(item.href);
    const Icon = item.icon;
    return (
      <Link
        key={item.href}
        href={item.href}
        ref={(el) => {
          if (el) linkRefs.current.set(item.href, el);
          else linkRefs.current.delete(item.href);
        }}
        className={`sb-item${active ? " active" : ""}`}
        data-label={item.label}
        aria-current={active ? "page" : undefined}
        onMouseEnter={() => handleLinkHover(item.href)}
      >
        <Icon className="sb-item-icon" />
        {!isCollapsed && (
          <span className="sb-item-label">{item.label}</span>
        )}
      </Link>
    );
  }

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="sb-logo">
        <div className="sb-logo-mark">T</div>
        {!isCollapsed && (
          <div className="sb-logo-word">
            <span className="sb-logo-name">Tesisfar</span>
            <span className="sb-logo-tag">Gestión TEG</span>
          </div>
        )}
      </div>

      {/* Navegación agrupada */}
      <nav className="sb-nav">
        {GROUPS.map((group) => {
          const groupItems = getGroupItems(group.title);
          if (groupItems.length === 0) return null;
          return (
            <div
              key={group.title}
              data-testid={`sb-group-${group.title}`}
            >
              <span className="sb-group-title">
                {isCollapsed
                  ? group.title === "Workspace"
                    ? "WS"
                    : "OP"
                  : group.title}
              </span>
              {groupItems.map(renderNavItem)}
            </div>
          );
        })}
      </nav>

      {/* Foot card */}
      <div className="sb-foot">
        <div className="sb-foot-ava">
          {email.charAt(0).toUpperCase()}
        </div>
        {!isCollapsed && (
          <>
            <div className="sb-foot-who">
              <span className="sb-foot-name">{displayName}</span>
              <span className="sb-foot-role">{role}</span>
            </div>
            <button
              ref={footMoreRef}
              className="sb-foot-more"
              type="button"
              aria-label="Más opciones"
              aria-expanded={footMenuOpen}
              onClick={() => setFootMenuOpen((v) => !v)}
            >
              ⋯
            </button>
          </>
        )}
        <ProfileMenu
          isOpen={footMenuOpen}
          email={email}
          role={role}
          onClose={() => setFootMenuOpen(false)}
          onLogout={handleFootLogout}
          anchorRef={footMoreRef}
        />
      </div>
    </>
  );

  return (
    <>
      {/* Sidebar de escritorio */}
      <aside className={`sb sb-desktop${isCollapsed ? " is-collapsed" : ""}`}>
        {sidebarContent}
      </aside>

      {/* Overlay y drawer móvil */}
      {mobileOpen && (
        <div
          ref={overlayRef}
          className="fixed inset-0 z-40"
          style={{
            background: "rgba(1,22,56,.45)",
            backdropFilter: "blur(4px)",
          }}
          onClick={() => setMobileOpen(false)}
        >
          <aside
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="Menú de navegación"
            className="sb sb-drawer"
            style={{ width: "84%", maxWidth: 300, height: "100%", position: "relative" }}
            onClick={(e) => e.stopPropagation()}
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
          >
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
};

export default Sidebar;
