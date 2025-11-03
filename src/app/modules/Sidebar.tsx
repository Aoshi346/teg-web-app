"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  BarChart3,
  Settings,
  Menu,
  X,
  ScanLine,
  TrendingUp,
  GraduationCap,
  ChevronsLeft
} from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (isCollapsed: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, setIsCollapsed }) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleCollapse = () => setIsCollapsed(!isCollapsed);
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
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white shadow-lg hover:bg-gray-50 transition-colors"
        aria-label="Toggle menu"
      >
        {isOpen ? <X className="w-6 h-6 text-gray-700" /> : <Menu className="w-6 h-6 text-gray-700" />}
      </button>

      <div
        className={`fixed lg:relative inset-y-0 left-0 z-40 bg-white border-r border-gray-200 transform transition-all duration-300 ease-in-out lg:transform-none ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } ${
          isCollapsed ? 'w-20' : 'w-64'
        }`}
      >
        <div className="flex flex-col h-full">
          <div className={`p-4 h-[89px] flex items-center border-b border-gray-200 ${isCollapsed ? 'justify-center' : 'px-6'}`}>
            <div className={`flex items-center gap-3 transition-all duration-300 ${isCollapsed ? 'justify-center' : ''}`}>
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-cyan-500 rounded-xl flex items-center justify-center">
                <GraduationCap className="w-6 h-6 text-white" />
              </div>
              <div className={`overflow-hidden transition-all duration-200 ${isCollapsed ? 'w-0' : 'w-auto'}`}>
                <h1 className="text-lg font-bold text-gray-900">Tesisfar</h1>
                <p className="text-xs text-gray-500">Gestión de TEG</p>
              </div>
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
                      onClick={() => setIsOpen(false)}
                      className={`w-full flex items-center gap-3 py-3 rounded-lg transition-all duration-200 ${
                        isActive
                          ? 'bg-violet-700 text-white shadow-lg shadow-violet-500/30'
                          : 'text-gray-700 hover:bg-gray-100'
                      } ${isCollapsed ? 'px-3 justify-center' : 'px-4'}`}
                      style={{ animationDelay: `${index * 50}ms` }}
                      title={isCollapsed ? item.label : undefined}
                    >
                      <item.icon className="w-5 h-5 flex-shrink-0" />
                      <span className={`font-medium whitespace-nowrap transition-all duration-200 ${isCollapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'}`}>{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
          
          <div className="p-4 border-t border-gray-200">
            <button 
              onClick={toggleCollapse} 
              className={`w-full flex items-center gap-3 py-3 rounded-lg transition-all duration-200 text-gray-700 hover:bg-gray-100 ${isCollapsed ? 'px-3 justify-center' : 'px-4'}`}
              title={isCollapsed ? 'Expandir barra lateral' : 'Colapsar barra lateral'}
            >
              <ChevronsLeft className={`w-5 h-5 flex-shrink-0 transition-transform duration-300 ${isCollapsed ? 'rotate-180' : 'rotate-0'}`} />
              <span className={`font-medium whitespace-nowrap transition-all duration-200 ${isCollapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'}`}>
                Colapsar
              </span>
            </button>
          </div>
        </div>
      </div>

      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-30 transition-opacity duration-300"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
