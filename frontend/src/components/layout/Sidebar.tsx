"use client";

import React, {
  useEffect,
  useRef,
  useState,
  useCallback,
  useMemo,
} from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createPortal } from "react-dom";
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  PlusCircle,
  Settings,
  ScanLine,
  TrendingUp,
  X,
} from "lucide-react";
import { getUser, getUserRole } from "@/features/auth/clientAuth";

interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (isCollapsed: boolean) => void;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  mobileOpen,
  setMobileOpen,
}) => {
  const pathname = usePathname();
  const router = useRouter();
  const closeBtnRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const backdropRef = useRef<HTMLDivElement>(null);
  const touchStartX = useRef(0);
  const [portalTarget, setPortalTarget] = useState<HTMLElement | null>(null);
  const linkRefs = useRef<Map<string, HTMLAnchorElement>>(new Map());

  useEffect(() => {
    if (typeof window !== "undefined") setPortalTarget(document.body);
  }, []);

  // GSAP-driven mobile drawer animation — lazy-loaded so gsap never enters
  // the dashboard shell critical path on desktop.
  useEffect(() => {
    const drawer = drawerRef.current;
    const backdrop = backdropRef.current;
    if (!drawer || !backdrop) return;

    let cancelled = false;

    if (mobileOpen) {
      document.body.style.overflow = "hidden";
      setTimeout(() => closeBtnRef.current?.focus(), 100);

      import("gsap").then(({ gsap }) => {
        if (cancelled) return;
        gsap.to(backdrop, { opacity: 1, pointerEvents: "auto", duration: 0.25, ease: "power2.out" });
        gsap.fromTo(drawer,
          { x: "-100%" },
          { x: "0%", duration: 0.4, ease: "power3.out" }
        );
        const items = drawer.querySelectorAll(".sidebar-menu-item");
        gsap.fromTo(items,
          { opacity: 0, x: -16 },
          { opacity: 1, x: 0, duration: 0.3, stagger: 0.04, delay: 0.15, ease: "power2.out" }
        );
      });
    } else {
      document.body.style.overflow = "";
      import("gsap").then(({ gsap }) => {
        if (cancelled) return;
        gsap.to(drawer, { x: "-100%", duration: 0.3, ease: "power2.in" });
        gsap.to(backdrop, { opacity: 0, duration: 0.25, ease: "power2.in", onComplete: () => { backdrop.style.pointerEvents = "none"; } });
      });
    }

    return () => { cancelled = true; document.body.style.overflow = ""; };
  }, [mobileOpen]);

  // Swipe-to-close gesture
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  }, []);

  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    // Swipe left to close (negative diff means swipe left when drawer is on left)
    if (diff > 60) {
      setMobileOpen(false);
    }
  }, [setMobileOpen]);

  const [userRole, setUserRole] = useState<string | null>(null);
  const user = useMemo(() => getUser(), []);

  useEffect(() => {
    setUserRole(getUserRole());
  }, []);

  const menuItems = useMemo(() => {
    if (userRole === "Estudiante") {
      const semester = user?.semester?.toLowerCase() || "";
      const isTesis = semester.includes("10");
      return [
        { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
        isTesis
          ? { icon: BookOpen, label: "TEG", href: "/dashboard/tesis" }
          : { icon: FileText, label: "PTEG", href: "/dashboard/proyectos" },
        { icon: TrendingUp, label: "Seguimiento", href: "/dashboard/tracking" },
        { icon: Settings, label: "Configuración", href: "/dashboard/settings" },
      ];
    }

    const baseItems = [
      { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
      { icon: FileText, label: "PTEG", href: "/dashboard/proyectos" },
      { icon: BookOpen, label: "TEG", href: "/dashboard/tesis" },
      { icon: ScanLine, label: "Escanear", href: "/dashboard/scan", requiredRole: ["Administrador", "Estudiante", "Tutor", "Jurado"] },
      { icon: TrendingUp, label: "Seguimiento", href: "/dashboard/tracking" },
      { icon: PlusCircle, label: "Agregar", href: "/dashboard/agregar" },
      { icon: Settings, label: "Configuración", href: "/dashboard/settings" },
    ];

    return baseItems.filter((item) => {
      if (!("requiredRole" in item)) return true;
      if (!userRole) return true;
      return item.requiredRole?.includes(userRole);
    });
  }, [userRole, user]);

  const handleLinkHover = useCallback((href: string) => {
    router.prefetch(href);
  }, [router]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if ((e.altKey || e.metaKey) && e.key >= "1" && e.key <= "7") {
        e.preventDefault();
        const idx = parseInt(e.key) - 1;
        if (menuItems[idx]) { router.push(menuItems[idx].href); setMobileOpen(false); }
      }
      if (e.key === "Escape" && mobileOpen) setMobileOpen(false);
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [router, mobileOpen, setMobileOpen, menuItems]);

  // Shared link renderer
  const renderLink = (item: typeof menuItems[0], index: number, opts: { collapsed?: boolean; mobile?: boolean } = {}) => {
    const isActive = pathname
      ? item.href === "/dashboard" ? pathname === item.href : pathname.startsWith(item.href)
      : false;

    return (
      <li key={index} className="sidebar-menu-item">
        <Link
          ref={(el) => { if (el) linkRefs.current.set(item.href, el); }}
          href={item.href}
          onClick={opts.mobile ? () => setMobileOpen(false) : undefined}
          onMouseEnter={() => handleLinkHover(item.href)}
          prefetch={true}
          className={`w-full flex items-center ${opts.collapsed ? "justify-center gap-0 px-3" : "gap-3 px-4"} py-3 rounded-xl transition-all duration-200 relative group overflow-hidden border border-transparent ${
            isActive
              ? "text-blue-700 bg-blue-50/80 shadow-sm border-blue-100/50"
              : "text-slate-600 hover:bg-blue-50/80 hover:text-blue-700 hover:shadow-sm hover:border-blue-100/50"
          }`}
          title={opts.collapsed ? `${item.label} (Alt+${index + 1})` : `Alt+${index + 1}`}
        >
          {isActive && (
            <div className="absolute inset-0 opacity-10 pointer-events-none bg-gradient-to-r from-blue-500 to-blue-600" />
          )}
          <item.icon className={`w-5 h-5 flex-shrink-0 transition-transform duration-200 relative z-10 ${isActive ? "scale-110 text-blue-600" : "group-hover:text-blue-600 group-hover:scale-110"}`} />
          <span className={`font-bold tracking-wide whitespace-nowrap overflow-hidden transition-all duration-200 relative z-10 ${opts.collapsed ? "w-0 opacity-0" : "w-auto opacity-100"} ${isActive ? "text-blue-800" : "group-hover:text-blue-800"}`}>
            {item.label}
          </span>
          {isActive && !opts.collapsed && (
            <div className="absolute left-0 top-0 bottom-0 w-1.5 rounded-r-full bg-gradient-to-b from-usm-orange to-usm-yellow shadow-[0_0_10px_rgba(249,115,22,0.5)]" />
          )}
        </Link>
      </li>
    );
  };

  // Logo block
  const LogoBlock = ({ compact = false }: { compact?: boolean }) => (
    <div className={`flex items-center gap-3 min-w-0 ${compact ? "gap-0 justify-center" : ""}`}>
      <div className="w-10 h-10 rounded-xl flex items-center justify-center">
        <Image src="/tesisfar_logo.svg" alt="Tesisfar logo" width={32} height={32} className="w-8 h-8 object-contain drop-shadow-sm" draggable={false} />
      </div>
      {!compact && (
        <div className="overflow-hidden flex flex-col justify-center">
          <h1 className="text-xl font-bold text-slate-900 tracking-tight leading-none mb-1">Tesisfar</h1>
          <p className="text-[11px] uppercase tracking-wider font-bold text-slate-500">Gestión de TEG</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="sidebar-container">
      {portalTarget && createPortal(
        <>
          {/* Mobile drawer — GSAP animated */}
          <div
            ref={drawerRef}
            className="lg:hidden fixed inset-y-0 left-0 z-[100] w-[85vw] max-w-xs sm:max-w-sm bg-white border-r border-slate-200 shadow-2xl"
            style={{ transform: "translateX(-100%)" }}
            role="dialog"
            aria-modal="true"
            aria-label="Menú de navegación"
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
          >
            <div className="flex flex-col h-full pt-[env(safe-area-inset-top)]">
              <div className="p-4 flex items-center justify-between border-b border-slate-100">
                <LogoBlock />
                <button
                  ref={closeBtnRef}
                  onClick={() => setMobileOpen(false)}
                  className="p-2 rounded-lg text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition-colors touch-manipulation"
                  aria-label="Cerrar menú"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <nav className="flex-1 p-4 overflow-y-auto" aria-label="Main navigation">
                <ul className="space-y-1">
                  {menuItems.map((item, i) => renderLink(item, i, { mobile: true }))}
                </ul>
              </nav>
            </div>
          </div>

          {/* Backdrop */}
          <div
            ref={backdropRef}
            className="lg:hidden fixed inset-0 z-[90] bg-black/50"
            style={{ opacity: 0, pointerEvents: "none" }}
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
        </>,
        portalTarget,
      )}

      {/* Desktop persistent sidebar */}
      <aside
        className={`hidden lg:flex lg:flex-col h-screen bg-white border-r border-slate-200 shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-50 transition-[width] duration-300 ${isCollapsed ? "w-20" : "w-64"}`}
        style={{ position: "relative" }}
      >
        <div className={`p-4 h-[89px] flex items-center flex-shrink-0 border-b border-slate-100 ${isCollapsed ? "px-3 justify-center" : "px-6 justify-start"}`}>
          <LogoBlock compact={isCollapsed} />
        </div>
        <nav className="flex-1 p-4 overflow-y-auto min-h-0" aria-label="Main navigation">
          <ul className="space-y-1">
            {menuItems.map((item, i) => renderLink(item, i, { collapsed: isCollapsed }))}
          </ul>
        </nav>
      </aside>
    </div>
  );
};

export default Sidebar;
