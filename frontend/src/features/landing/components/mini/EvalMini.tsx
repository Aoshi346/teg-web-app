import React from "react";

export default function EvalMini() {
  return (
    <div className="lh-fcard-mini lh-mini-eval" data-testid="mini-eval">
      <div className="bar">
        <span className="pin" aria-hidden />
        <span className="ttl">Evaluación · Defensa oral</span>
        <span className="meta">15 preguntas</span>
      </div>
      <div className="ribbon">
        <span>Criterios de Evaluación Técnica</span>
        <span className="frac">07/10</span>
      </div>
      <div className="qcard">
        <div className="qhead">
          <span className="qnum">08</span>
          <span className="qttl">¿Demuestra dominio del marco metodológico durante la exposición?</span>
          <span className="qstatus">respondida</span>
        </div>
        <div className="qopts">
          <span className="qopt">Deficiente</span>
          <span className="qopt">Regular</span>
          <span className="qopt active">Satisfact.</span>
          <span className="qopt">Excelente</span>
        </div>
      </div>
      <div className="rail">
        <span>Progreso</span>
        <span className="bar" aria-hidden />
        <span>13/20</span>
      </div>
    </div>
  );
}
