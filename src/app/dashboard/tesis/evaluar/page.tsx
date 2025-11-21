"use client";

import React, { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import PageTransition from '@/components/ui/PageTransition';

export default function EvaluarTesisRedirectPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = searchParams?.get('projectId');

  useEffect(() => {
    // Redirect to the Projects evaluation page but pass type=tesis
    const qs = new URLSearchParams();
    if (projectId) qs.set('projectId', projectId);
    qs.set('type', 'tesis');
    router.replace(`/dashboard/proyectos/evaluar?${qs.toString()}`);
  }, [projectId, router]);

  return (
    <PageTransition>
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-2">Redirigiendo a la evaluación de tesis…</h3>
          <p className="text-sm text-gray-500">Por favor espere un momento mientras cargamos el formulario de evaluación.</p>
        </div>
      </div>
    </PageTransition>
  );
}
