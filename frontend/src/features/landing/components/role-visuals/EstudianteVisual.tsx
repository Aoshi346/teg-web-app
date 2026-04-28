import React from "react";

export default function EstudianteVisual() {
  return (
    <div className="lh-rv lh-rv-estu" data-testid="rv-estudiante">
      <div className="top">
        <span className="name">Mi proyecto</span>
        <span className="pct">62%</span>
      </div>
      <div className="progress"><div className="fill" /></div>
      <div className="gates">
        <div className="g ok">Artículo</div>
        <div className="g now">Tomo</div>
        <div className="g">Defensa</div>
      </div>
      <div className="next">
        <span><b>PRÓXIMO PASO</b> · subir tomo</span>
        <span>4 días</span>
      </div>
    </div>
  );
}
