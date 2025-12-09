"use client";

import { useMemo, useState } from "react";

interface HelpContent {
  image: string;
  title?: string;
  description?: string;
  tips?: string[];
}

interface EvaluationHelpSidebarProps {
  currentSection?: string;
  suggestions?: string[];
  helpContent?: Record<string, HelpContent>;
}

const DEFAULT_SUGGESTIONS = [
  "Revise todos los criterios antes de enviar.",
  "Puede navegar entre páginas sin perder sus respuestas.",
  "Use \"No aplica\" cuando la pregunta no sea relevante.",
  "Use 5 solo para trabajos excepcionales.",
];

const DEFAULT_HELP_CONTENT: Record<string, HelpContent> = {
  diagramacion: {
    image: "/help-diagramacion.svg",
    title: "Diagramación",
    description: "Revisar portadas, márgenes, tipografía y consistencia visual.",
  },
  contenido: {
    image: "/help-contenido.svg",
    title: "Contenido",
    description: "Verificar claridad, profundidad y referencias bibliográficas.",
  },
  tesis: {
    image: "/help-tesis.svg",
    title: "Tesis",
    description: "Enfoque en metodología, análisis y conclusiones.",
  },
  proyecto: {
    image: "/help-proyecto.svg",
    title: "Proyecto",
    description: "Evaluar objetivos, entregables y viabilidad técnica.",
  },
};

const normalizeKey = (text?: string) =>
  (text || "general")
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

export function EvaluationHelpSidebar({
  currentSection,
  suggestions = DEFAULT_SUGGESTIONS,
  helpContent = DEFAULT_HELP_CONTENT,
}: EvaluationHelpSidebarProps) {
  const [showModal, setShowModal] = useState(false);

  const selectedHelp = useMemo(() => {
    const key = normalizeKey(currentSection);
    if (helpContent[key]) return helpContent[key];
    // Try fallback keys
    if (helpContent["proyecto"]) return helpContent["proyecto"];
    if (helpContent["tesis"]) return helpContent["tesis"];
    if (helpContent["general"]) return helpContent["general"];
    return {
      image:
        "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=900&q=80",
      title: currentSection || "Guía visual",
      description: "Recursos de apoyo para esta sección.",
    } satisfies HelpContent;
  }, [currentSection, helpContent]);

  const helpCard = (
    <div className="rounded-xl border-2 border-dashed border-gray-300 bg-gradient-to-br from-gray-50 to-blue-50 p-6 text-center shadow-sm">
      <div className="aspect-video mb-3 flex items-center justify-center rounded-lg overflow-hidden bg-gradient-to-br from-blue-100 via-white to-blue-50 text-gray-400 shadow-inner relative">
        {selectedHelp.image ? (
          <img
            src={selectedHelp.image}
            alt={selectedHelp.title || "Guía visual"}
            className="h-full w-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="text-center text-sm text-gray-500 w-full h-full flex items-center justify-center">
            Sin imagen disponible
          </div>
        )}
      </div>
      <div className="space-y-1">
        <p className="text-sm font-semibold text-gray-800">
          {selectedHelp.title || currentSection || "Guía visual"}
        </p>
        {selectedHelp.description && (
          <p className="text-sm text-gray-600">{selectedHelp.description}</p>
        )}
      </div>
    </div>
  );

  const suggestionsCard = (
    <div className="rounded-xl border border-gray-200 p-4 bg-white shadow-sm">
      <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
        <svg
          className="w-5 h-5 text-blue-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        Sugerencias
      </h4>
      <ul className="space-y-2 text-sm text-gray-700">
        {suggestions.map((tip, idx) => (
          <li key={idx} className="flex items-start gap-2">
            <span className="text-blue-600 mt-0.5">•</span>
            <span>{tip}</span>
          </li>
        ))}
      </ul>
    </div>
  );

  return (
    <>
      {/* Desktop / large screens: sticky sidebar inside form grid */}
      <aside className="w-full">
        <div className="flex flex-col gap-4 sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto pr-1 pb-2">
          {helpCard}
          {suggestionsCard}
        </div>
      </aside>

      {/* Mobile / small screens: floating button with modal */}
      <div className="lg:hidden">
        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="fixed bottom-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-full bg-blue-600 text-white shadow-lg shadow-blue-500/30 hover:bg-blue-700 transition-all"
          aria-label="Ver guía visual"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M4 6h8a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2zm0 0l4 4 4-4"
            />
          </svg>
          Guía visual
        </button>

        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-4 space-y-4 relative">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="absolute top-3 right-3 text-gray-500 hover:text-gray-800"
                aria-label="Cerrar"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>

              {helpCard}
              {suggestionsCard}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
