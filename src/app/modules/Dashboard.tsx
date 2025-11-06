"use client";

import React, { useEffect, useState, useRef } from 'react';
import { gsap } from 'gsap';
import {
  Bell,
  AlertTriangle,
  CheckCircle,
  FileText,
  BookOpen,
  ChevronDown,
  XCircle,
  Clock,
  Check,
  MessageSquare,
  Menu,
  ChevronsLeft
} from 'lucide-react';
import Sidebar from './Sidebar';
import LoginLoading from '@/components/ui/LoginLoading';

interface StatCardProps {
  title: string;
  mainValue: string;
  mainLabel: string;
  secondaryStats: { label: string; value: number; color: string; icon: React.ReactNode }[];
  icon: React.ReactNode;
  delay: number;
  // When variant is "colorful", apply gradient background and switch texts to white for contrast
  variant?: 'default' | 'colorful';
  bgClass?: string; // Tailwind classes for gradient/background when variant is colorful
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  mainValue,
  mainLabel,
  secondaryStats,
  icon,
  delay,
  variant = 'default',
  bgClass,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const mainValueRef = useRef<HTMLParagraphElement>(null);
 
  useEffect(() => {
    if (mainValueRef.current) {
      const counter = { value: 0 };
      gsap.to(counter, {
        value: parseInt(mainValue, 10),
        duration: 1.5,
        ease: 'power3.out',
        delay: 0.6 + delay / 1000,
        onUpdate: () => {
          if (mainValueRef.current) {
            mainValueRef.current.textContent = Math.round(counter.value).toString();
          }
        },
      });
    }
  }, [mainValue, delay]);

  const isColorful = variant === 'colorful';

  return (
    <div
      ref={cardRef}
      className={`kbi-card rounded-2xl p-6 sm:p-6 shadow-lg shadow-gray-900/10 opacity-0 ${
        isColorful
          ? `${bgClass ?? 'bg-gradient-to-br from-emerald-500 via-emerald-600 to-green-700'} border border-transparent ring-1 ring-white/20`
          : 'bg-white border border-gray-200/80 ring-1 ring-gray-200/80'
      }`}
    >
      <div className="flex items-center gap-5">
        <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center shadow-inner ${
          isColorful ? 'bg-white/15 text-white' : 'bg-blue-50 text-blue-600'
        }`}>{icon}</div>
        <div className="flex-1">
          <h3 className={`text-sm sm:text-base font-semibold ${isColorful ? 'text-white/90' : 'text-gray-600'}`}>{title}</h3>
          <div className="flex items-baseline gap-2 mt-2">
            <p ref={mainValueRef} className={`text-3xl sm:text-4xl xl:text-5xl font-bold leading-tight ${isColorful ? 'text-white' : 'text-gray-800'}`}>{mainValue}</p>
            <p className={`text-xs sm:text-sm font-medium ${isColorful ? 'text-white/80' : 'text-gray-600'}`}>{mainLabel}</p>
          </div>
        </div>
      </div>
      <div className={`mt-6 pt-4 flex flex-wrap sm:flex-row sm:justify-around gap-4 gap-y-3 ${
        isColorful ? 'border-t border-white/20' : 'border-t border-gray-200/75'
      }`}>
        {secondaryStats.map((stat) => (
          <div key={stat.label} className="flex items-center gap-2 min-w-[40%] sm:min-w-0">
            <div style={{ color: isColorful ? 'white' : stat.color }}>{stat.icon}</div>
            <span className={`text-lg font-bold ${isColorful ? 'text-white' : 'text-gray-700'}`}>{stat.value}</span>
            <span className={`text-sm ${isColorful ? 'text-white/80' : 'text-gray-500'}`}>{stat.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const mainContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // If navigation came from the login modal, skip showing a second loader
    try {
      const just = sessionStorage.getItem('justLoggedIn');
      if (just) {
        sessionStorage.removeItem('justLoggedIn');
        setLoading(false);
        return;
      }
    } catch {}

    const timer = window.setTimeout(() => setLoading(false), 800);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (loading) return;
    const sidebar = document.querySelector('.sidebar-container');
    const header = document.querySelector('.header-container');
    const kbiCards = gsap.utils.toArray('.kbi-card');
    const contentSections = gsap.utils.toArray('.content-section');

    gsap.from(sidebar, { duration: 0.7, x: '-100%', ease: 'power3.out' });
    gsap.from(header, { duration: 0.7, y: '-100%', ease: 'power3.out', delay: 0.2 });
    
    // This is the single, definitive animation for the stat cards
    gsap.to(kbiCards, {
      opacity: 1,
      y: 0,
      duration: 0.8,
      stagger: 0.15,
      ease: 'power3.out',
      delay: 0.4,
    });

    gsap.from(contentSections, { duration: 0.5, opacity: 0, y: 20, stagger: 0.2, ease: 'power2.out', delay: 0.7 });

  }, [loading]);

  const stats = [
    {
      title: 'Proyectos de Tesis (PTEG)',
      mainValue: '12',
      mainLabel: 'En Revisión',
      icon: <FileText className="w-10 h-10 text-white" />,
      secondaryStats: [
        { label: 'Aprobados', value: 58, color: '#10B981', icon: <Check size={20} /> },
        { label: 'Rechazados', value: 7, color: '#EF4444', icon: <XCircle size={20} /> },
      ],
      variant: 'colorful' as const,
      bgClass: 'bg-gradient-to-br from-sky-500 via-blue-600 to-cyan-500',
    },
    {
      title: 'Tesis de Grado (TEG)',
      mainValue: '43',
      mainLabel: 'En Progreso',
      icon: <BookOpen className="w-10 h-10 text-white" />,
      secondaryStats: [
        { label: 'Completadas', value: 21, color: '#10B981', icon: <Check size={20} /> },
        { label: 'Pend. Jurado', value: 9, color: '#F59E0B', icon: <Clock size={20} /> },
      ],
      variant: 'colorful' as const,
      bgClass: 'bg-gradient-to-br from-rose-500 via-red-600 to-orange-500',
    },
  ];

  const projectsToReview = [
    {
      student: 'Ana Pérez',
      title: 'Impacto de la IA en la farmacovigilancia',
      date: '2024-05-10',
    },
    {
      student: 'Luis Rodríguez',
      title: 'Desarrollo de un nuevo agente antibacteriano',
      date: '2024-05-09',
    },
    {
      student: 'Carla Gómez',
      title: 'Análisis de la adherencia terapéutica en pacientes crónicos',
      date: '2024-05-09',
    },
  ];

  const progressFeed = [
    {
      id: 1,
      icon: <CheckCircle className="w-5 h-5 text-green-600" />,
      text: "La tesis de 'Ana Pérez' ha sido Aprobada.",
      time: '1h ago',
    },
    {
      id: 2,
      icon: <MessageSquare className="w-5 h-5 text-blue-600" />,
      text: "Nuevo comentario del jurado en el proyecto de 'Luis Rodríguez'.",
      time: '3h ago',
    },
    {
      id: 3,
      icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
      text: "Entrega final de 'Carla Gómez' vence en 3 días.",
      time: '1d ago',
    },
  ];

  if (loading) {
    // Use the same loading overlay used by the login modal for visual consistency across the app
    return <LoginLoading visible={true} message="Cargando panel..." />;
  }

  return (
    <div className="min-h-screen w-full flex bg-gray-100">
      <div className="sidebar-container">
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          setIsCollapsed={setIsSidebarCollapsed}
          mobileOpen={isMobileSidebarOpen}
          setMobileOpen={setIsMobileSidebarOpen}
        />
      </div>
      <div ref={mainContentRef} className="flex-1 flex flex-col overflow-hidden transition-all duration-300">
        <header className="header-container bg-white border-b border-gray-200 sticky top-0 z-20 h-[89px] flex-shrink-0">
          <div className="px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Mobile menu toggle (hidden on large screens) */}
              <button
                className={`lg:hidden inline-flex items-center justify-center p-3 rounded-md border transition-colors ${
                  isMobileSidebarOpen
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
                aria-label={isMobileSidebarOpen ? 'Cerrar menú' : 'Abrir menú'}
                onClick={() => setIsMobileSidebarOpen(prev => !prev)}
              >
                <Menu className="w-6 h-6" />
              </button>
              <button
                className="hidden lg:inline-flex items-center justify-center p-2 rounded-md hover:bg-gray-100 transition-colors"
                aria-label="Colapsar barra lateral"
                onClick={() => setIsSidebarCollapsed((v) => !v)}
                title={isSidebarCollapsed ? 'Expandir barra lateral' : 'Colapsar barra lateral'}
              >
                <ChevronsLeft className={`w-5 h-5 ${isSidebarCollapsed ? 'rotate-180 transition-transform' : 'transition-transform'}`} />
              </button>
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">Dashboard</h2>
            </div>
            <div className="flex items-center gap-2 bg-gray-100 p-1.5 rounded-full">
              <button className="relative p-2 rounded-full hover:bg-gray-200/70 transition-all duration-200 group">
                <Bell className="w-5 h-5 text-gray-600 group-hover:text-blue-600 transition-colors" />
                <span className="absolute top-2 right-2 flex h-4 w-4 items-center justify-center">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
              </button>
              <div className="relative group">
                <div className="flex items-center gap-2 cursor-pointer p-1 pr-2 rounded-full hover:bg-gray-200/70 transition-colors">
                  <img
                    src="https://i.pravatar.cc/300"
                    alt="User avatar"
                    className="w-8 h-8 rounded-full border-2 border-white shadow-sm"
                  />
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {stats.map((stat, index) => (
                <StatCard key={index} {...stat} delay={index * 100} />
              ))}
            </div>

            {/* Two equal columns for symmetry */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
              <div className="content-section bg-white rounded-2xl p-4 sm:p-6 shadow-md shadow-gray-900/5 border border-gray-200/80">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-900">Revisión de Proyectos</h3>
                  <button className="text-sm text-blue-700 border border-blue-700 rounded-md px-3 py-1 font-semibold hover:bg-blue-700 hover:text-white transition-all duration-200">
                    Ver todos los proyectos
                  </button>
                </div>
                <div className="space-y-4">
                  {projectsToReview.map((project, index) => (
                    <div
                      key={index}
                      className="flex flex-col sm:flex-row sm:items-center items-start gap-3 sm:gap-4 p-4 rounded-xl hover:bg-gray-100 transition-all duration-200 cursor-pointer group"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <div className="flex-1 min-w-0 w-full">
                        <p className="text-sm font-semibold text-gray-800 truncate">{project.title}</p>
                        <p className="text-sm text-gray-500">
                          {project.student} - <span className="text-xs">{project.date}</span>
                        </p>
                      </div>
                      <button className="w-full sm:w-auto sm:flex-shrink-0 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-700 transition-all duration-200 shadow-md shadow-blue-600/20 hover:shadow-lg transform hover:scale-105">
                        Revisar Ahora
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="content-section bg-white rounded-2xl p-4 sm:p-6 shadow-md shadow-gray-900/5 border border-gray-200/80">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Seguimiento de Progreso</h3>
                  <div className="space-y-6">
                    {progressFeed.map((item, index) => (
                      <div
                        key={item.id}
                        className="flex items-start gap-4"
                        style={{ animationDelay: `${index * 120}ms` }}
                      >
                        <div className="flex-shrink-0 mt-1 bg-gray-100 p-2 rounded-full">{item.icon}</div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-800">{item.text}</p>
                          <p className="text-xs text-gray-500">{item.time}</p>
                        </div>
                      </div>
                    ))}
                  </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;