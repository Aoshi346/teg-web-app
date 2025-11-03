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
  MessageSquare
} from 'lucide-react';
import Sidebar from './Sidebar';
import LoginLoading from '@/components/ui/LoginLoading';

interface StatCardProps {
  title: string;
  mainValue: string;
  mainLabel: string;
  secondaryStats: { label: string; value: number; color: string, icon: React.ReactNode }[];
  icon: React.ReactNode;
  delay: number;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  mainValue,
  mainLabel,
  secondaryStats,
  icon,
  delay,
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

  return (
    <div
      ref={cardRef}
      className="kbi-card bg-white rounded-2xl p-6 shadow-md shadow-gray-900/5 border border-gray-200/80 opacity-0"
    >
      <div className="flex items-center gap-5">
        <div className="flex-shrink-0">{icon}</div>
        <div className="flex-1">
          <h3 className="text-base font-semibold text-gray-500">{title}</h3>
          <div className="flex items-baseline gap-2 mt-2">
            <p ref={mainValueRef} className="text-4xl font-bold text-gray-800">{mainValue}</p>
            <p className="text-sm text-gray-600 font-medium">{mainLabel}</p>
          </div>
        </div>
      </div>
      <div className="mt-6 pt-4 border-t border-gray-200/75 flex flex-col sm:flex-row sm:justify-around gap-4">
        {secondaryStats.map((stat) => (
          <div key={stat.label} className="flex items-center gap-2">
            <div style={{ color: stat.color }}>{stat.icon}</div>
            <span className="text-lg font-bold text-gray-700">{stat.value}</span>
            <span className="text-sm text-gray-500">{stat.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
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
      icon: <FileText className="w-10 h-10 text-blue-600" />,
      secondaryStats: [
        { label: 'Aprobados', value: 58, color: '#10B981', icon: <Check size={20} /> },
        { label: 'Rechazados', value: 7, color: '#EF4444', icon: <XCircle size={20} /> },
      ],
    },
    {
      title: 'Tesis de Grado (TEG)',
      mainValue: '43',
      mainLabel: 'En Progreso',
      icon: <BookOpen className="w-10 h-10 text-violet-700" />,
      secondaryStats: [
        { label: 'Completadas', value: 21, color: '#10B981', icon: <Check size={20} /> },
        { label: 'Pend. Jurado', value: 9, color: '#F59E0B', icon: <Clock size={20} /> },
      ],
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
        <Sidebar isCollapsed={isSidebarCollapsed} setIsCollapsed={setIsSidebarCollapsed} />
      </div>
      <div ref={mainContentRef} className="flex-1 flex flex-col overflow-hidden transition-all duration-300">
        <header className="header-container bg-white border-b border-gray-200 sticky top-0 z-20 h-[89px] flex-shrink-0">
          <div className="px-8 h-full">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
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
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {stats.map((stat, index) => (
                <StatCard key={index} {...stat} delay={index * 100} />
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
              <div className="content-section lg:col-span-3 bg-white rounded-2xl p-6 shadow-md shadow-gray-900/5 border border-gray-200/80">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-900">Revisión de Proyectos</h3>
                  <button className="text-sm text-violet-700 border border-violet-700 rounded-md px-3 py-1 font-semibold hover:bg-violet-700 hover:text-white transition-all duration-200">
                    Ver todos los proyectos
                  </button>
                </div>
                <div className="space-y-4">
                  {projectsToReview.map((project, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-4 p-4 rounded-xl hover:bg-gray-100 transition-all duration-200 cursor-pointer group"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-gray-800 truncate">{project.title}</p>
                        <p className="text-sm text-gray-500">
                          {project.student} - <span className="text-xs">{project.date}</span>
                        </p>
                      </div>
                      <button className="flex-shrink-0 bg-violet-700 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-violet-800 transition-all duration-200 shadow-md shadow-violet-700/20 hover:shadow-lg transform hover:scale-105">
                        Revisar Ahora
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="content-section lg:col-span-2 bg-white rounded-2xl p-6 shadow-md shadow-gray-900/5 border border-gray-200/80">
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