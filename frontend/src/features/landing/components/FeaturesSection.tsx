"use client";

import React, { useEffect, useRef } from "react";
import PanelMini from "./mini/PanelMini";
import EvalMini from "./mini/EvalMini";
import CalendarMini from "./mini/CalendarMini";

export default function FeaturesSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = sectionRef.current;
    if (!node) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      gridRef.current?.classList.add("is-visible");
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            gridRef.current?.classList.add("is-visible");
            obs.disconnect();
          }
        });
      },
      { threshold: 0.15 }
    );
    obs.observe(node);
    return () => obs.disconnect();
  }, []);

  return (
    <section ref={sectionRef} id="features" className="lh-features">
      <div className="lh-features-h">
        <div>
          <span className="pill">Lo que vas a usar</span>
          <h3>
            Todo lo que necesitas,<br />en un solo <em>panel</em>.
          </h3>
        </div>
        <p>
          Un panel personal que te dice qué hacer, un formulario que te lleva sección por sección,
          y un calendario que te recuerda cuándo presentar. Mira cómo se ven las pantallas que vas a usar todos los días.
        </p>
      </div>

      <div ref={gridRef} className="lh-fgrid lh-stagger">
        <article className="lh-fcard" style={{ "--stagger-i": 0 } as React.CSSProperties}>
          <div className="body">
            <span className="lh-fcard-step">— Tu panel</span>
            <h4>Sabes exactamente dónde estás.</h4>
            <p>
              Una sola pantalla muestra tu trabajo, las tres fases y el próximo paso pendiente — sin hojas de cálculo, sin correos perdidos.
            </p>
          </div>
          <PanelMini />
          <a className="read">Ver tu panel</a>
        </article>

        <article className="lh-fcard" style={{ "--stagger-i": 1 } as React.CSSProperties}>
          <div className="body">
            <span className="lh-fcard-step">— Evaluaciones</span>
            <h4>Evalúa con foco, sin perderte.</h4>
            <p>
              Pregunta por pregunta, con tu progreso siempre visible. Si falta algo, te lleva directo a corregirlo — sin buscar en menús.
            </p>
          </div>
          <EvalMini />
          <a className="read">Ver el formulario</a>
        </article>

        <article className="lh-fcard" style={{ "--stagger-i": 2 } as React.CSSProperties}>
          <div className="body">
            <span className="lh-fcard-step">— Calendario</span>
            <h4>Nunca te pierdes una fecha.</h4>
            <p>
              Tu defensa, las del resto, y las modalidades en colores que reconoces de inmediato. La de hoy se enciende sola.
            </p>
          </div>
          <CalendarMini />
          <a className="read">Ver el calendario</a>
        </article>
      </div>
    </section>
  );
}
