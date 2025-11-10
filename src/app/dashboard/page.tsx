"use client";

import React from 'react';
import Dashboard from '@/components/dashboard/Dashboard';

// This page receives props from the layout component
interface DashboardPageProps {
  handleSidebarCollapse?: () => void;
  handleMobileSidebarToggle?: () => void;
  isSidebarCollapsed?: boolean;
  isMobileSidebarOpen?: boolean;
}

export default function DashboardPage({
  handleSidebarCollapse = () => {},
  handleMobileSidebarToggle = () => {},
  isSidebarCollapsed = false,
  isMobileSidebarOpen = false,
}: DashboardPageProps) {
  return (
    <Dashboard
      handleSidebarCollapse={handleSidebarCollapse}
      handleMobileSidebarToggle={handleMobileSidebarToggle}
      isSidebarCollapsed={isSidebarCollapsed}
      isMobileSidebarOpen={isMobileSidebarOpen}
    />
  );
}
