"use client";

import React from "react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="lh-footer">
      <span className="lh-footer-rule-top" aria-hidden />

      {/* Desktop / tablet 4-col grid */}
      <div className="brandcol hidden md:block">
        <h5>TesisFar</h5>
        <p>
          La plataforma que acompaña tu Trabajo Especial de Grado, desde el primer artículo hasta la defensa.
        </p>
      </div>
      <div className="hidden md:block">
        <h5>Plataforma</h5>
        <Link href="/">Inicio</Link>
        <Link href="#features">Funciones</Link>
        <Link href="#roles">Roles</Link>
      </div>
      <div className="hidden md:block">
        <h5>Universidad</h5>
        <a href="#">Reglamento TEG</a>
        <a href="#">Coordinación</a>
        <a href="#">Calendario</a>
      </div>
      <div className="hidden md:block">
        <h5>Contacto</h5>
        <a href="mailto:decanato.farmacia@usm.edu.ve">Soporte</a>
        <a href="#">Cuenta</a>
        <a href="#">Estado del sistema</a>
      </div>

      {/* Mobile accordion (≤640px shown via CSS, replaces md:block above) */}
      <div className="md:hidden" style={{ gridColumn: "1 / -1" }}>
        <div style={{ marginBottom: 16 }}>
          <h5 style={{ fontFamily: "Fraunces, serif", fontWeight: 800, fontSize: 18, color: "#011638", margin: 0 }}>TesisFar</h5>
          <p style={{ fontSize: 13, color: "#64748b", margin: "8px 0 0", lineHeight: 1.55 }}>
            La plataforma que acompaña tu Trabajo Especial de Grado, desde el primer artículo hasta la defensa.
          </p>
        </div>
        <details open>
          <summary>Plataforma</summary>
          <div className="links">
            <Link href="/">Inicio</Link>
            <Link href="#features">Funciones</Link>
            <Link href="#roles">Roles</Link>
          </div>
        </details>
        <details>
          <summary>Universidad</summary>
          <div className="links">
            <a href="#">Reglamento TEG</a>
            <a href="#">Coordinación</a>
            <a href="#">Calendario</a>
          </div>
        </details>
        <details>
          <summary>Contacto</summary>
          <div className="links">
            <a href="mailto:decanato.farmacia@usm.edu.ve">Soporte</a>
            <a href="#">Cuenta</a>
            <a href="#">Estado del sistema</a>
          </div>
        </details>
      </div>

      <div className="lh-footer-rule" />
      <div className="lh-footer-meta">
        <span>© {new Date().getFullYear()} TesisFar · Universidad Santa María · Caracas</span>
        <span>v2026.04</span>
      </div>
    </footer>
  );
}
