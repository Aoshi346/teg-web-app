import React from "react";

export default function TutorVisual() {
  return (
    <div className="lh-rv lh-rv-tut" data-testid="rv-tutor">
      <div className="top">
        <span className="name">Comentarios · Capítulo II</span>
        <span className="pill">3 nuevos</span>
      </div>
      <div className="thread">
        <div className="msg you">
          <span className="av">L</span>
          <div className="b">
            <span className="by">Tú · tutor <span>hace 2 h</span></span>
            <span className="tx">Revisa la pág. 14: faltan citas APA en el segundo párrafo.</span>
          </div>
        </div>
        <div className="msg">
          <span className="av">M</span>
          <div className="b">
            <span className="by">Estudiante <span>hace 1 h</span></span>
            <span className="tx">Listo, las añadí. ¿Puedes revisar?</span>
          </div>
        </div>
      </div>
    </div>
  );
}
