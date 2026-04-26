"use client";

import * as React from "react";
import { Download, Upload } from "lucide-react";
import type { Project, ProjectFile } from "@features/projects/types/project";

export interface FilesTabProps {
  project: Project;
  canUpload?: boolean;
  onUpload?: (file: File) => void;
  isUploading?: boolean;
  uploadError?: string | null;
}

export function FilesTab({ project, canUpload, onUpload, isUploading, uploadError }: FilesTabProps) {
  const inputRef = React.useRef<HTMLInputElement | null>(null);

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f && onUpload) onUpload(f);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8">
      <div className="space-y-5">
        <div className="dsec">
          <div className="dsec-head">
            <h3 className="dsec-title">Documentos del proyecto</h3>
            {canUpload && (
              <>
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  disabled={isUploading}
                  className="pact pact-primary text-[12px] disabled:opacity-60"
                >
                  {isUploading ? "Subiendo…" : "Subir archivo"} <Upload className="w-3 h-3" strokeWidth={2.6} />
                </button>
                <input
                  ref={inputRef}
                  type="file"
                  accept=".pdf,.doc,.docx"
                  className="hidden"
                  onChange={handleFile}
                />
              </>
            )}
          </div>
          {uploadError && (
            <p className="text-[11px] text-destructive font-semibold mt-2">{uploadError}</p>
          )}
          {project.files && project.files.length > 0 ? (
            <div className="space-y-3">
              {project.files.map((f) => <FileRow key={f.url} file={f} />)}
            </div>
          ) : (
            <p className="text-[13px] text-text-muted font-medium italic">Sin archivos adjuntos.</p>
          )}
        </div>
      </div>
      <aside className="space-y-4">
        <div className="dsec">
          <div className="dsec-head"><h3 className="dsec-title">Reglas de subida</h3></div>
          <ul className="text-[11.5px] text-text-muted font-medium leading-relaxed space-y-1.5">
            <li>· Solo PDF, DOC, DOCX</li>
            <li>· Tamaño máximo 10 MB</li>
            <li>· Las versiones anteriores se archivan</li>
          </ul>
        </div>
      </aside>
    </div>
  );
}

function FileRow({ file }: { file: ProjectFile }) {
  return (
    <a href={file.url} target="_blank" rel="noopener noreferrer" className="filecard">
      <div className={file.type === "pdf" ? "fileicon" : "fileicon fileicon-doc"}>
        {file.type.toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[13.5px] font-extrabold text-text-strong truncate">{file.name}</div>
        <div className="text-[11.5px] text-text-muted font-semibold mt-0.5">{file.date}</div>
      </div>
      <span className="pact pact-muted">
        Descargar <Download className="w-3 h-3" strokeWidth={2.6} />
      </span>
    </a>
  );
}
