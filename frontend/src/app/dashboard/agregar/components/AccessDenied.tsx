"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function AccessDenied() {
  const router = useRouter();

  return (
    <div className="agg-denied">
      <div className="agg-denied-ic">🛡</div>
      <h3 className="agg-denied-h font-display">Esta sección no está disponible</h3>
      <p className="agg-denied-p">
        Los tutores y jurados no registran trabajos académicos. Vuelve a tu cola de seguimiento o solicita acceso al administrador.
      </p>
      <div className="agg-denied-actions">
        <button
          type="button"
          onClick={() => router.back()}
          className="agg-btn agg-btn-ghost"
        >
          Volver
        </button>
        <Link href="/dashboard/tracking" className="agg-btn agg-btn-primary">
          Ir a Seguimiento
        </Link>
      </div>
    </div>
  );
}
