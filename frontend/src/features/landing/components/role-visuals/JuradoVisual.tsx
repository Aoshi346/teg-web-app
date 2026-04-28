import React from "react";

export default function JuradoVisual() {
  return (
    <div className="lh-rv lh-rv-jur" data-testid="rv-jurado">
      <div className="gauge">
        <span className="n">17<em>/20</em></span>
      </div>
      <div className="info">
        <div className="top">— Defensa oral</div>
        <h6>M. Salas · 14 abr</h6>
        <div className="rows">
          <div className="r"><span>Técnica</span><span><b>9.5</b>/10</span></div>
          <div className="r"><span>Divulgativa</span><span><b>7.5</b>/10</span></div>
          <div className="r"><span>Resultado</span><span className="ok">Aprobado</span></div>
        </div>
      </div>
    </div>
  );
}
