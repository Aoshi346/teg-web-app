"use client";

import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { createPortal } from 'react-dom';
import { gsap } from 'gsap';
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  BarChart3,
  Settings,
  ScanLine,
  TrendingUp,
  X,
} from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (isCollapsed: boolean) => void;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, mobileOpen, setMobileOpen }) => {
  const pathname = usePathname();
  const router = useRouter();
  const closeBtnRef = useRef<HTMLButtonElement>(null);
  const [portalTarget, setPortalTarget] = useState<HTMLElement | null>(null);
  const linkRefs = useRef<Map<string, HTMLAnchorElement>>(new Map());

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setPortalTarget(document.body);
    }
  }, []);

  // Lock body scroll when mobile drawer is open and focus the close button
  useEffect(() => {
    if (mobileOpen) {
      try {
        document.body.style.overflow = 'hidden';
        // Focus close button for accessibility
        setTimeout(() => closeBtnRef.current?.focus(), 0);
      } catch {}
    } else {
      try { document.body.style.overflow = ''; } catch {}
    }
    return () => { try { document.body.style.overflow = ''; } catch {} };
  }, [mobileOpen]);

  const menuItems = useMemo(() => [
    { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard' },
    { icon: FileText, label: 'Proyecto (PTEG)', href: '/dashboard/proyectos' },
    { icon: BookOpen, label: 'Trabajo Especial (TEG)', href: '/dashboard/tesis' },
    { icon: ScanLine, label: 'Escanear Documento', href: '/dashboard/scan' },
    { icon: TrendingUp, label: 'Seguimiento', href: '/dashboard/tracking' },
    { icon: BarChart3, label: 'Analíticas', href: '/dashboard/analytics' },
    { icon: Settings, label: 'Configuración', href: '/dashboard/settings' },
  ], []);

  // Prefetch routes on hover for instant navigation
  const handleLinkHover = useCallback((href: string) => {
    router.prefetch(href);
  }, [router]);

  // Animate menu items on mount and pathname change
  useEffect(() => {
    const menuItems = document.querySelectorAll('.sidebar-menu-item');
    if (menuItems.length > 0) {
      gsap.fromTo(
        menuItems,
        {
          opacity: 0,
          x: -20,
        },
        {
          opacity: 1,
          x: 0,
          duration: 0.3,
          stagger: 0.05,
          ease: 'power2.out',
        }
      );
    }
  }, [pathname]);

  // Keyboard shortcuts for navigation (1-7 for menu items)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Only handle if not typing in an input/textarea
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      // Alt/Cmd + 1-7 for navigation
      if ((e.altKey || e.metaKey) && e.key >= '1' && e.key <= '7') {
        e.preventDefault();
        const index = parseInt(e.key) - 1;
        if (menuItems[index]) {
          router.push(menuItems[index].href);
          setMobileOpen(false);
        }
      }

      // Escape to close mobile menu
      if (e.key === 'Escape' && mobileOpen) {
        setMobileOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [router, mobileOpen, setMobileOpen, menuItems]);

  return (
    <div className="sidebar-container">
      {portalTarget &&
        createPortal(
          <>
            {/* Mobile drawer (left off-canvas) - rendered in portal to ensure it overlays app content */}
            <div
              className={`lg:hidden fixed inset-y-0 left-0 z-[100] w-[85vw] max-w-xs sm:max-w-sm bg-white border-r border-gray-200 shadow-2xl transform transition-transform duration-300 ease-out ${
                mobileOpen ? 'translate-x-0' : '-translate-x-full'
              }`}
              role="dialog"
              aria-modal="true"
              aria-label="Menú de navegación"
            >
              <div className="flex flex-col h-full pt-[env(safe-area-inset-top)]">
                <div className="p-4 flex items-center justify-between border-b border-gray-200">
                  <div className="flex items-center gap-3 min-w-0">
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center">
                      <Image src="/tesisfar_logo.svg" alt="Tesisfar logo" width={32} height={32} className="w-8 h-8 object-contain drop-shadow-sm" draggable={false} />
                    </div>
                    <div>
                      <h1 className="text-lg font-bold text-gray-900">Tesisfar</h1>
                      <p className="text-xs text-gray-500">Gestión de TEG</p>
                    </div>
                  </div>
                  <button
                    ref={closeBtnRef}
                    onClick={() => setMobileOpen(false)}
                    className="p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                    aria-label="Cerrar menú"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <nav className="flex-1 p-4 overflow-y-auto" aria-label="Main navigation">
                  <ul className="space-y-1">
                    {menuItems.map((item, index) => {
                      const isActive = pathname
                        ? item.href === '/dashboard'
                          ? pathname === item.href
                          : pathname.startsWith(item.href)
                        : false;
                      return (
                        <li key={index} className="sidebar-menu-item">
                          <Link
                            ref={(el) => {
                              if (el) linkRefs.current.set(item.href, el);
                            }}
                            href={item.href}
                            onClick={() => setMobileOpen(false)}
                            onMouseEnter={() => handleLinkHover(item.href)}
                            prefetch={true}
                            className={`w-full flex items-center gap-3 py-3 px-3 rounded-lg transition-all duration-200 relative group ${
                              isActive 
                                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30' 
                                : 'text-gray-700 hover:bg-gray-100 hover:translate-x-1'
                            }`}
                            title={`${item.label} (Alt+${index + 1})`}
                          >
                            <item.icon className={`w-5 h-5 flex-shrink-0 transition-transform duration-200 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`} />
                            <span className="text-sm font-medium whitespace-nowrap overflow-hidden">{item.label}</span>
                            {isActive && (
                              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-r-full" />
                            )}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </nav>
              </div>
            </div>

            {/* Overlay backdrop - z-[90] ensures it's below the drawer but above main content */}
            <div
              className={`lg:hidden fixed inset-0 z-[90] bg-black/50 transition-opacity duration-300 ${mobileOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
              onClick={() => setMobileOpen(false)}
              aria-hidden="true"
            />
          </>,
          portalTarget
        )}

      {/* Desktop persistent side rail */}
      <aside
        className={`hidden lg:flex lg:flex-col lg:sticky top-0 lg:relative lg:z-40 min-h-screen bg-white border-r border-gray-200 shadow-none ${
          isCollapsed ? 'w-20' : 'w-64'
        }`}
      >
        <div className={`p-4 h-[89px] flex items-center border-b border-gray-200 ${isCollapsed ? 'px-3 justify-center' : 'px-6 justify-start'}`}>
          <div className={`flex items-center gap-3 min-w-0 transition-all duration-300 ${isCollapsed ? 'gap-0' : ''}`}>
            <div className="w-10 h-10 rounded-xl flex items-center justify-center">
              <Image src="/tesisfar_logo.svg" alt="Tesisfar logo" width={32} height={32} className="w-8 h-8 object-contain drop-shadow-sm" draggable={false} />
            </div>
            {!isCollapsed && (
              <div className="overflow-hidden transition-all duration-200">
                <h1 className="text-lg font-bold text-gray-900">Tesisfar</h1>
                <p className="text-xs text-gray-500">Gestión de TEG</p>
              </div>
            )}
          </div>
        </div>
        <nav className="flex-1 p-4 overflow-y-auto" aria-label="Main navigation">
          <ul className="space-y-1">
            {menuItems.map((item, index) => {
              const isActive = pathname
                ? item.href === '/dashboard'
                  ? item.href === pathname
                  : pathname.startsWith(item.href)
                : false;
              return (
                <li key={index} className="sidebar-menu-item">
                  <Link
                    ref={(el) => {
                      if (el) linkRefs.current.set(item.href, el);
                    }}
                    href={item.href}
                    onMouseEnter={() => handleLinkHover(item.href)}
                    prefetch={true}
                    className={`w-full flex items-center ${isCollapsed ? 'justify-center gap-0 px-3' : 'gap-3 px-4'} py-3 rounded-lg transition-all duration-200 relative group ${
                      isActive 
                        ? 'bg-blue-700 text-white shadow-lg shadow-blue-500/30' 
                        : 'text-gray-700 hover:bg-gray-100 hover:translate-x-1'
                    }`}
                    title={isCollapsed ? `${item.label} (Alt+${index + 1})` : `Alt+${index + 1}`}
                  >
                    <item.icon className={`w-5 h-5 flex-shrink-0 transition-transform duration-200 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`} />
                    <span className={`font-medium whitespace-nowrap overflow-hidden transition-all duration-200 ${isCollapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'}`}>{item.label}</span>
                    {isActive && !isCollapsed && (
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-r-full" />
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        {/* Removed footer collapse button to allow sidebar to extend fully */}
      </aside>

    </div>
  );
};

export default Sidebar;

