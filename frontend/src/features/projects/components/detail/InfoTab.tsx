"use client";

import * as React from "react";
import { Download } from "lucide-react";
import type { Project } from "@features/projects/types/project";

export interface InfoTabProps {
  project: Project;
  description: string;
}

export function InfoTab({ project, description }: InfoTabProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8">
      <div className="space-y-5">
        <Section title="Descripción del proyecto">
          {description.trim() ? (
            <div className="text-[14px] leading-[1.7] text-text-default font-medium space-y-3">
              {description.split(/\n\n+/).map((para, i) => (
                <p key={i}>{para}</p>
              ))}
            </div>
          ) : (
            <p className="text-[13px] text-text-muted font-medium italic">
              Sin descripción registrada.
            </p>
          )}
        </Section>

        {project.files && project.files.length > 0 && (
          <Section title="Archivos adjuntos" count={project.files.length}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {project.files.map((f) => (
                <a
                  key={f.url}
                  href={f.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="filecard"
                >
                  <div className={f.type === "pdf" ? "fileicon" : "fileicon fileicon-doc"}>
                    {f.type.toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[13px] font-extrabold text-text-strong truncate">{f.name}</div>
                    <div className="text-[11.5px] text-text-muted font-semibold">{f.date}</div>
                  </div>
                  <Download className="w-4 h-4 text-text-muted" />
                </a>
              ))}
            </div>
          </Section>
        )}
      </div>

      <aside className="space-y-4">
        <Section title="Datos del proyecto">
          <dl className="space-y-3 text-[12.5px]">
            <Row dt="Período" dd={project.period} />
            <Row dt="Tipo" dd={project.type === "tesis" ? "Tesis (TEG)" : "Proyecto (PTEG)"} />
            <Row dt="Identificador" dd={`#${project.id}`} />
            <Row dt="Enviado" dd={project.submittedDate} />
          </dl>
        </Section>
      </aside>
    </div>
  );
}

function Section({ title, count, children }: { title: string; count?: number; children: React.ReactNode }) {
  return (
    <div className="dsec">
      <div className="dsec-head">
        <h3 className="dsec-title">{title}</h3>
        {count != null && <span className="dsec-count">{count} {count === 1 ? "archivo" : "archivos"}</span>}
      </div>
      {children}
    </div>
  );
}

function Row({ dt, dd }: { dt: string; dd: React.ReactNode }) {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-wider text-text-muted font-extrabold mb-0.5">{dt}</dt>
      <dd className="text-text-strong font-extrabold">{dd}</dd>
    </div>
  );
}
