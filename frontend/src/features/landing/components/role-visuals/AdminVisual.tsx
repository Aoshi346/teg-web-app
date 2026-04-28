import React from "react";

export default function AdminVisual() {
  return (
    <div className="lh-rv lh-rv-adm" data-testid="rv-admin">
      <div className="grid">
        <div className="tile"><div className="lbl">Activos</div><div className="num">42</div><div className="delta">+ 3 esta semana</div></div>
        <div className="tile warn"><div className="lbl">Atrasados</div><div className="num">5</div><div className="delta">requieren atención</div></div>
        <div className="tile ok"><div className="lbl">Aprobados</div><div className="num">23</div><div className="delta">2026-01</div></div>
        <div className="tile"><div className="lbl">Defensas hoy</div><div className="num">3</div><div className="delta">14 abr</div></div>
      </div>
    </div>
  );
}
