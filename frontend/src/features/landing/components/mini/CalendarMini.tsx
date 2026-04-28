import React from "react";

export default function CalendarMini() {
  return (
    <div className="lh-fcard-mini lh-mini-cal" data-testid="mini-cal">
      <div className="bar">
        <span className="pin" aria-hidden />
        <span className="ttl">Calendario</span>
        <span className="meta">abr 2026</span>
      </div>
      <div className="calhead">
        <b>Abril 2026</b>
        <span>3 eventos esta semana</span>
      </div>
      <div className="grid">
        <div className="cell dim">L</div>
        <div className="cell dim">M</div>
        <div className="cell dim">M</div>
        <div className="cell dim">J</div>
        <div className="cell dim">V</div>
        <div className="cell dim">S</div>
        <div className="cell dim">D</div>
        <div className="cell">7</div>
        <div className="cell">8</div>
        <div className="cell pteg">9</div>
        <div className="cell">10</div>
        <div className="cell teg">11</div>
        <div className="cell">12</div>
        <div className="cell">13</div>
        <div className="cell today">14</div>
        <div className="cell">15</div>
        <div className="cell pteg">16</div>
        <div className="cell">17</div>
        <div className="cell teg">18</div>
        <div className="cell dim">19</div>
        <div className="cell dim">20</div>
      </div>
      <div className="timeline">
        <div className="row today">
          <span className="time">09:30</span>
          <span className="ttl">Modelo predictivo de deserción</span>
          <span className="pill">teg</span>
        </div>
        <div className="row teg">
          <span className="time">11:00</span>
          <span className="ttl">Sistema de inventario · IoT</span>
          <span className="pill">teg</span>
        </div>
        <div className="row">
          <span className="time">14:00</span>
          <span className="ttl">Análisis sentimiento redes</span>
          <span className="pill">pteg</span>
        </div>
      </div>
    </div>
  );
}
