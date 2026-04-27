"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Home } from "lucide-react";

export interface BreadcrumbProps {
  pageTitle: string;
  variant: "expanded" | "collapsed";
  numeral?: number;
}

const OPERACION_PAGES = new Set([
  "Seguimiento",
  "Estado de mi trabajo",
  "Agregar",
  "Configuración",
]);

function parentForPage(pageTitle: string): string {
  return OPERACION_PAGES.has(pageTitle) ? "Operación" : "Workspace";
}

export default function Breadcrumb({ pageTitle, variant, numeral }: BreadcrumbProps) {
  const router = useRouter();
  const parent = parentForPage(pageTitle);

  if (variant === "collapsed") {
    return (
      <nav className="hd-crumb-pill" aria-label="Migas de pan">
        <button
          className="step"
          type="button"
          onClick={() => router.push("/dashboard")}
        >
          {parent}
        </button>
        <span className="step now">
          {pageTitle}
          {numeral !== undefined && (
            <span className="num">{numeral}</span>
          )}
        </span>
      </nav>
    );
  }

  return (
    <nav className="hd-crumb" aria-label="Migas de pan">
      <a
        className="hd-crumb-home"
        href="/dashboard"
        onClick={(e) => {
          e.preventDefault();
          router.push("/dashboard");
        }}
      >
        <Home className="hd-crumb-home-icon" />
        {parent}
      </a>
      <span className="hd-crumb-sep">/</span>
      <span className="hd-crumb-now">
        {pageTitle}
        {numeral !== undefined && (
          <span className="num">{numeral}</span>
        )}
      </span>
    </nav>
  );
}
