import type { Presentation } from "../types/planificacion";

export type PresentationRowRole = "admin" | "tutor" | "jurado" | "estudiante";

export interface PresentationRowProps {
  presentation: Presentation;
  role: PresentationRowRole;
  viewerId?: number;
  onClick?: (p: Presentation) => void;
  onEdit?: (p: Presentation) => void;
  onDelete?: (p: Presentation) => void;
}

/**
 * Determina si el viewer es el propietario de la presentación según su rol.
 * - tutor: el viewerId debe coincidir con presentation.tutor
 * - jurado: el viewerId debe estar en presentation.jurado
 * - estudiante: siempre es "suya"
 */
function isMine(
  role: PresentationRowRole,
  presentation: Presentation,
  viewerId?: number
): boolean {
  if (role === "estudiante") return true;
  if (role === "tutor") return viewerId !== undefined && viewerId === presentation.tutor;
  if (role === "jurado") return viewerId !== undefined && presentation.jurado.includes(viewerId);
  return false;
}

export default function PresentationRow({
  presentation,
  role,
  viewerId,
  onClick,
  onEdit,
  onDelete,
}: PresentationRowProps) {
  const mine = isMine(role, presentation, viewerId);
  const isTesis = presentation.project_type === "tesis";

  const handleRowClick = () => {
    onClick?.(presentation);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit?.(presentation);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete?.(presentation);
  };

  const handleVerDetalle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClick?.(presentation);
  };

  let youChip: string | null = null;
  if (mine) {
    if (role === "tutor") youChip = "Tutoreas";
    else if (role === "jurado") youChip = "Jurado";
    else if (role === "estudiante") youChip = "Tu defensa";
  }

  return (
    <div className={`prow${mine ? " mine" : ""}`} onClick={handleRowClick}>
      <div className="ptime">
        <span className="h">{presentation.start_time}</span>
        <span className="d">{presentation.duration_minutes} min</span>
      </div>

      <div className="prow-mid">
        <div className="ptitle">
          <span className={`tdot ${isTesis ? "teg" : "pteg"}`} aria-hidden />
          <span className="ptitle-text" title={presentation.project_title}>{presentation.project_title}</span>
          <span className={`spill ${isTesis ? "teg" : "pteg"}`}>
            {isTesis ? "TEG" : "PTEG"}
          </span>
          {mine && youChip && (
            <span className="spill you">{youChip}</span>
          )}
        </div>

        <div className="pmeta">
          {role === "admin" ? (
            <>
              <span>
                <b>Estud.</b> {presentation.student_name}
              </span>
              <span>
                <b>Tutor</b> {presentation.tutor_name}
              </span>
              <span>
                <b>Jur.</b> {presentation.jurado.length}
              </span>
            </>
          ) : (
            <span>{presentation.jurado_names.join(", ")}</span>
          )}
        </div>
      </div>

      <div className="pactions">
        {role === "admin" && onEdit && (
          <button aria-label="Editar" onClick={handleEdit}>
            ✎
          </button>
        )}
        {role === "admin" && onDelete && (
          <button aria-label="Eliminar" onClick={handleDelete}>
            ×
          </button>
        )}
        {(role === "tutor" || role === "jurado") && mine && (
          <button aria-label="Ver detalle" onClick={handleVerDetalle}>
            →
          </button>
        )}
      </div>
    </div>
  );
}
