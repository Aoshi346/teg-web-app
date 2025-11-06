"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
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

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, setIsCollapsed, mobileOpen, setMobileOpen }) => {
  const pathname = usePathname();

  const menuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard' },
    { icon: FileText, label: 'Proyecto (PTEG)', href: '/dashboard/projects' },
    { icon: BookOpen, label: 'Trabajo Especial (TEG)', href: '/dashboard/theses' },
    { icon: ScanLine, label: 'Escanear Documento', href: '/dashboard/scan' },
    { icon: TrendingUp, label: 'Seguimiento', href: '/dashboard/tracking' },
    { icon: BarChart3, label: 'Analíticas', href: '/dashboard/analytics' },
    { icon: Settings, label: 'Configuración', href: '/dashboard/settings' },
  ];

  return (
    <>
      {/* Mobile dropdown (top) */}
      <div
        className={`lg:hidden fixed top-0 left-0 w-full z-50 bg-white border-b border-gray-200 shadow-xl transform transition-transform duration-300 ease-out ${
          mobileOpen ? 'translate-y-0' : '-translate-y-full'
        }`}
      >
        <div className="flex flex-col max-h-[80vh]">
          <div className="p-4 flex items-center justify-between border-b border-gray-200">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center">
                <img src="/tesisfar_logo.svg" alt="Tesisfar logo" className="w-8 h-8 object-contain drop-shadow-sm" draggable={false} />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">Tesisfar</h1>
                <p className="text-xs text-gray-500">Gestión de TEG</p>
              </div>
            </div>
            <button
              onClick={() => setMobileOpen(false)}
              className="p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
              aria-label="Cerrar menú"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <nav className="flex-1 p-4 overflow-y-auto" aria-label="Main navigation">
            <ul className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {menuItems.map((item, index) => {
                const isActive = pathname ? pathname.startsWith(item.href) : false;
                return (
                  <li key={index}>
                    <Link
                      href={item.href}
                      onClick={() => setMobileOpen(false)}
                      className={`group w-full flex items-center justify-start gap-2 py-3 px-2 rounded-lg transition-colors duration-200 ${
                        isActive ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30' : 'text-gray-700 hover:bg-gray-100'
                      }`}
                      title={item.label}
                    >
                      <item.icon className="w-5 h-5 flex-shrink-0" />
                      <span className="text-xs sm:text-sm font-medium whitespace-nowrap overflow-hidden">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
      </div>

      {/* Desktop persistent side rail */}
      <aside
        className={`hidden lg:flex lg:flex-col lg:sticky top-0 h-screen bg-white border-r border-gray-200 shadow-none ${
          isCollapsed ? 'w-20' : 'w-64'
        }`}
      >
        <div className={`p-4 h-[89px] flex items-center border-b border-gray-200 ${isCollapsed ? 'px-3 justify-center' : 'px-6 justify-start'}`}>
          <div className={`flex items-center gap-3 min-w-0 transition-all duration-300 ${isCollapsed ? 'gap-0' : ''}`}>
            <div className="w-10 h-10 rounded-xl flex items-center justify-center">
              <img src="/tesisfar_logo.svg" alt="Tesisfar logo" className="w-8 h-8 object-contain drop-shadow-sm" draggable={false} />
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
              const isActive = pathname ? pathname.startsWith(item.href) : false;
              return (
                <li key={index}>
                  <Link
                    href={item.href}
                    className={`w-full flex items-center ${isCollapsed ? 'justify-center gap-0 px-3' : 'gap-3 px-4'} py-3 rounded-lg transition-colors duration-200 ${
                      isActive ? 'bg-blue-700 text-white shadow-lg shadow-blue-500/30' : 'text-gray-700 hover:bg-gray-100'
                    }`}
                    title={isCollapsed ? item.label : undefined}
                  >
                    <item.icon className="w-5 h-5 flex-shrink-0" />
                    <span className={`font-medium whitespace-nowrap overflow-hidden transition-all duration-200 ${isCollapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'}`}>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>

      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300"
          onClick={() => setMobileOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
