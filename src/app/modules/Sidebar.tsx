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
  GraduationCap,
  
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
    { icon: FileText, label: 'Proyectos (PTEG)', href: '/dashboard/projects' },
    { icon: BookOpen, label: 'Tesis (TEG)', href: '/dashboard/theses' },
    { icon: ScanLine, label: 'Escanear Documento', href: '/dashboard/scan' },
    { icon: TrendingUp, label: 'Seguimiento', href: '/dashboard/tracking' },
    { icon: BarChart3, label: 'Analíticas', href: '/dashboard/analytics' },
    { icon: Settings, label: 'Configuración', href: '/dashboard/settings' },
  ];

  return (
    <>
      <div
        className={`fixed lg:sticky lg:top-0 inset-y-0 left-0 z-40 bg-white border-r border-gray-200 h-screen lg:h-screen transform transition-all duration-300 ease-in-out lg:transform-none overflow-x-hidden ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } ${
          isCollapsed ? 'w-20' : 'w-64'
        }`}
      >
        <div className="flex flex-col h-full">
          <div className={`p-4 h-[89px] flex items-center ${isCollapsed ? 'justify-center' : 'justify-start'} border-b border-gray-200 ${isCollapsed ? 'px-3' : 'px-6'}`}>
            <div className={`flex items-center ${isCollapsed ? 'gap-0' : 'gap-3'} min-w-0 transition-all duration-300`}>
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-cyan-500 rounded-xl flex items-center justify-center">
                <GraduationCap className="w-6 h-6 text-white" />
              </div>
              <div className={`overflow-hidden transition-all duration-200 ${isCollapsed ? 'w-0' : 'w-auto'}`}>
                <h1 className="text-lg font-bold text-gray-900">Tesisfar</h1>
                <p className="text-xs text-gray-500">Gestión de TEG</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 p-4 overflow-y-auto overflow-x-hidden" aria-label="Main navigation">
            <ul className="space-y-1">
              {menuItems.map((item, index) => {
                const isActive = pathname ? pathname.startsWith(item.href) : false;
                return (
                  <li key={index}>
                    <Link
                      href={item.href}
                      onClick={() => setMobileOpen(false)}
                      className={`w-full flex items-center ${isCollapsed ? 'justify-center gap-0' : 'gap-3'} py-3 rounded-lg transition-all duration-200 text-center ${
                        isActive
                          ? 'bg-blue-700 text-white shadow-lg shadow-blue-500/30'
                          : 'text-gray-700 hover:bg-gray-100'
                      } ${isCollapsed ? 'px-3 justify-center' : 'px-4'}`}
                      style={{ animationDelay: `${index * 50}ms` }}
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

        </div>
      </div>

      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-30 transition-opacity duration-300"
          onClick={() => setMobileOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
