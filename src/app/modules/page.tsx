"use client";

import React from 'react';
import Link from 'next/link';
import { isAuthenticated, getUserEmail } from '@/features/auth/clientAuth';

export default function ModulesPage() {
  const authenticated = isAuthenticated();
  const user = getUserEmail();

  const modules = [
    { id: 'tesis', name: 'Tesis', desc: 'Gestión de trabajo de grado' },
    { id: 'biblioteca', name: 'Biblioteca', desc: 'Referencias y recursos' },
    { id: 'evaluacion', name: 'Evaluación', desc: 'Rubricas y entregas' },
  ];

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
      <div className="max-w-3xl w-full">
        <h1 className="text-3xl font-bold mb-4">Seleccionar módulo</h1>
        <p className="mb-6 text-sm text-gray-600">Elige un módulo para continuar. {authenticated ? `Conectado como ${user}` : 'No estás autenticado.'}</p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {modules.map(m => (
            <Link key={m.id} href={`/${m.id}`} className="block p-4 rounded-lg border hover:shadow-lg">
              <h3 className="font-semibold">{m.name}</h3>
              <p className="text-sm text-gray-500">{m.desc}</p>
            </Link>
          ))}
        </div>

        <div className="mt-8 p-4 bg-white border rounded">
          <h4 className="font-medium">Credenciales de prueba</h4>
          <p className="text-sm text-gray-600 mt-2">Usa estas credenciales en el modal para iniciar sesión:</p>
          <pre className="mt-2 p-2 bg-gray-100 rounded text-sm">Email: test@tesisfar.local
Password: Test1234!</pre>
        </div>
      </div>
    </main>
  );
}
