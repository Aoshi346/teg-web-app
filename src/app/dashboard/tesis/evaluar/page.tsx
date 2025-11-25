"use client";

import React from 'react';
import { useSearchParams } from 'next/navigation';
import PageTransition from '@/components/ui/PageTransition';
import DashboardHeader from '@/components/layout/DashboardHeader';
import EvaluationForm from '@/components/evaluation/EvaluationForm';
import { TESIS_QUESTIONS } from '@/lib/questions/questions';

interface EvaluarProps {
  handleSidebarCollapse?: () => void;
  handleMobileSidebarToggle?: () => void;
  isSidebarCollapsed?: boolean;
  isMobileSidebarOpen?: boolean;
}

export default function EvaluarTesisPage({
  handleSidebarCollapse,
  handleMobileSidebarToggle,
  isSidebarCollapsed,
  isMobileSidebarOpen,
}: EvaluarProps) {
  const searchParams = useSearchParams();
  const projectId = searchParams?.get('projectId');

  return (
    <>
      <DashboardHeader
        pageTitle={`Evaluar Tesis`}
        isSidebarCollapsed={isSidebarCollapsed}
        isMobileSidebarOpen={isMobileSidebarOpen}
        onMobileSidebarToggle={handleMobileSidebarToggle}
        onSidebarCollapse={handleSidebarCollapse}
      />

      <PageTransition>
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-gray-50">
          <EvaluationForm projectId={projectId} typeParam={'tesis'} questions={TESIS_QUESTIONS} />
        </main>
      </PageTransition>
    </>
  );
}
