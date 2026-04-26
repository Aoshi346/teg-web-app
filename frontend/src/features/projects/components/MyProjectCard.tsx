import * as React from "react";
import Link from "next/link";
import type { Project, ProjectState, ProjectType } from "@features/projects/types/project";
import { StatePill } from "./StatePill";

interface GateDef {
  key: string;
  label: string;
  desc: string;
}

const PTEG_GATES: GateDef[] = [
  { key: "review_1", label: "Revisión 1", desc: "Primera revisión del jurado." },
  { key: "review_2", label: "Reentrega", desc: "Activa sólo si la primera revisión no aprueba." },
  { key: "defense", label: "Defensa", desc: "Presentación oral final." },
];

const TEG_GATES: GateDef[] = [
  { key: "articulo", label: "Artículo", desc: "Aprobación del trabajo escrito." },
  { key: "entrega", label: "Entrega", desc: "Presentación del ejemplar final." },
  { key: "defensa", label: "Defensa", desc: "Presentación oral final." },
];

type GateStatus = "plain" | "done" | "now" | "fail";

/*
 * Deriva el estado visual de cada gate a partir del estado del proyecto.
 * Las reglas siguen la secuencia lineal de fases:
 * - Las fases anteriores a la activa quedan "done".
 * - La fase activa queda "now" (o "fail" si el proyecto terminó en fallo).
 * - Las fases posteriores quedan "plain".
 * Para failed_final se marca la última fase activa como "fail".
 */
function deriveGateStatuses(type: ProjectType | undefined, state: ProjectState): GateStatus[] {
  const isProjecto = type !== "tesis";

  if (isProjecto) {
    switch (state) {
      case "pending_review_1":
        return ["now", "plain", "plain"];
      case "pending_review_2":
        return ["done", "now", "plain"];
      case "pending_defense":
        return ["done", "done", "now"];
      case "approved":
        return ["done", "done", "done"];
      case "failed_final":
        return ["done", "done", "fail"];
      default:
        return ["plain", "plain", "plain"];
    }
  } else {
    switch (state) {
      case "pending_articulo":
        return ["now", "plain", "plain"];
      case "pending_entrega":
        return ["done", "now", "plain"];
      case "pending_defensa":
        return ["done", "done", "now"];
      case "approved":
        return ["done", "done", "done"];
      case "failed_final":
        return ["done", "done", "fail"];
      default:
        return ["plain", "plain", "plain"];
    }
  }
}

const TERMINAL_STATES: ProjectState[] = ["approved", "failed_final"];

function isTerminal(state: ProjectState): boolean {
  return TERMINAL_STATES.includes(state);
}

export interface MyProjectCardProps {
  project: Project;
}

export default function MyProjectCard({ project }: MyProjectCardProps) {
  const gates = project.type === "tesis" ? TEG_GATES : PTEG_GATES;
  const statuses = deriveGateStatuses(project.type, project.state);
  const detailHref =
    project.type === "tesis"
      ? `/dashboard/tesis/${project.id}`
      : `/dashboard/proyectos/${project.id}`;
  const showNextStep = !isTerminal(project.state);
  const tutor = project.advisorNames?.[0];

  return (
    <div className="my-card">
      <div className="my-card-head">
        <div>
          <h3>{project.title}</h3>
          {(tutor || project.reviewerName) && (
            <p className="meta">
              {tutor && (
                <span>
                  <span className="meta-role-lbl">Tutor: </span>
                  <span>{tutor}</span>
                </span>
              )}
              {tutor && project.reviewerName && <span> · </span>}
              {project.reviewerName && (
                <span>
                  <span className="meta-role-lbl">Jurado: </span>
                  <span>{project.reviewerName}</span>
                </span>
              )}
            </p>
          )}
        </div>
        <StatePill state={project.state} projectType={project.type} />
      </div>

      <div className="progress-row">
        {gates.map((gate, idx) => {
          const status = statuses[idx];
          const cls = status === "plain" ? "pgate" : `pgate ${status}`;
          return (
            <div key={gate.key} className={cls}>
              <div className="num font-display">{idx + 1}</div>
              <div className="lbl">{gate.label}</div>
              <div className="desc">{gate.desc}</div>
            </div>
          );
        })}
      </div>

      {showNextStep && (
        <div className="next-step">
          <div className="what">
            <b>Próximo paso</b>
            <span>Revisa el detalle para más información.</span>
          </div>
          <Link href={detailHref} className="btn primary">
            Abrir detalle
          </Link>
        </div>
      )}
    </div>
  );
}
