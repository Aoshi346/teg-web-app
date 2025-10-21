"use client";

import React from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

export default function SelectedModulePage() {
  const search = useSearchParams();
  const router = useRouter();
  const role = search.get('role') || '';
  const semester = search.get('semester') || '';
  const project = search.get('project') || '';

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
      <div className="max-w-2xl w-full bg-white p-8 rounded shadow">
        <h1 className="text-2xl font-bold mb-4">Resumen de selección</h1>
        <p className="mb-2"><strong>Rol:</strong> {role}</p>
        <p className="mb-2"><strong>Semestre:</strong> {semester}</p>
        <p className="mb-2"><strong>Trabajo:</strong> {project === 'anteproyecto' ? 'Anteproyecto' : project === 'tesg' ? 'Trabajo especial de Grado' : project}</p>

        <div className="mt-6">
          <button onClick={() => router.back()} className="px-4 py-2 rounded border">Volver</button>
        </div>
      </div>
    </main>
  );
}
