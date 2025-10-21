"use client";

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Dashboard from '../modules/Dashboard';
import { isAuthenticated } from '@/features/auth/clientAuth';

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      try {
        router.push('/');
      } catch {
        window.location.href = '/';
      }
    }
  }, [router]);

  return (
    <main className="min-h-screen bg-gray-50">
      <Dashboard />
    </main>
  );
}
