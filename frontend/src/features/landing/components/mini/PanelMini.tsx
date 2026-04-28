import React from "react";

export default function PanelMini() {
  return (
    <div className="lh-fcard-mini lh-mini-panel" data-testid="mini-panel">
      <div className="bar">
        <span className="pin" aria-hidden />
        <span className="ttl">Mi proyecto</span>
        <span className="meta">vista actual</span>
      </div>
      <div className="hero">
        <div className="left">
          <div className="eb">— en curso</div>
          <div className="nm">Modelo predictivo de deserción</div>
        </div>
        <span className="pill">activo</span>
      </div>
      <div className="gates">
        <div className="gate passed"><div className="n">01</div><div className="l">Aprobada</div><div className="t">Artículo</div></div>
        <div className="gate now"><div className="n">02</div><div className="l">En curso</div><div className="t">Tomo</div></div>
        <div className="gate"><div className="n">03</div><div className="l">Por venir</div><div className="t">Defensa</div></div>
      </div>
      <div className="next">
        <span className="l">Próximo paso</span>
        <span className="v">Subir tomo final · vence vie 18</span>
      </div>
    </div>
  );
}
