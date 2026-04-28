"use client";

import React, { useEffect, useRef } from "react";
import { Star, Check, AlertTriangle } from "lucide-react";

export default function HeroExplainer() {
  const sectionRef = useRef<HTMLElement>(null);
  const copyRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const fillRef = useRef<HTMLDivElement>(null);
  const floatsRef = useRef<HTMLDivElement[]>([]);

  useEffect(() => {
    const node = sectionRef.current;
    if (!node) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      copyRef.current?.classList.add("is-visible");
      cardRef.current?.classList.add("is-visible");
      floatsRef.current.forEach((f) => f?.classList.add("is-visible"));
      if (fillRef.current) fillRef.current.style.width = "62%";
      return;
    }

    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            copyRef.current?.classList.add("is-visible");
            cardRef.current?.classList.add("is-visible");
            floatsRef.current.forEach((f, i) => {
              if (!f) return;
              setTimeout(() => f.classList.add("is-visible"), 200 + i * 80);
            });
            setTimeout(() => {
              if (fillRef.current) fillRef.current.style.width = "62%";
            }, 400);
            obs.disconnect();
          }
        });
      },
      { threshold: 0.25 }
    );
    obs.observe(node);
    return () => obs.disconnect();
  }, []);

  return (
    <section ref={sectionRef} id="hero2" className="lh-h2" data-testid="hero-explainer">
      <div ref={copyRef} className="lh-h2-copy lh-fade-up">
        <span className="lh-h2-eyebrow">
          <b>Para estudiantes, tutores, jurados y coordinación</b>
        </span>
        <h2 className="lh-h2-title">
          Tu tesis,<br />de principio <em>a</em>{" "}
          <span className="lh-h2-title-underline">defensa</span>.
        </h2>
        <p className="lh-h2-lede">
          Sube tu trabajo, recibe observaciones, sigue tu próximo paso y prepara tu defensa — todo en una sola pantalla.
          Quien evalúa ve solo lo que le toca, y nadie pierde el hilo entre correos y hojas de cálculo.
        </p>
        <div className="lh-h2-trust">
          <div className="it"><span className="n">3</span><span className="l">Fases guiadas</span></div>
          <div className="it"><span className="n">4</span><span className="l">Roles coordinados</span></div>
          <div className="it"><span className="n"><em>1</em></span><span className="l">Lugar para todo</span></div>
          <div className="it"><span className="n">100%</span><span className="l">Tu progreso visible</span></div>
        </div>
      </div>

      <div className="lh-h2-preview">
        <div
          ref={(el) => { if (el) floatsRef.current[0] = el; }}
          className="lh-h2-float fc-1 lh-fade-up"
        >
          <div className="ic"><Star size={14} /></div>
          <div><b>Tu defensa</b><span>jue 14 abr · 09:30</span></div>
        </div>

        <div ref={cardRef} className="lh-h2-pcard lh-tilt-in">
          <div className="head">
            <div className="ctitle">
              <span className="dot" aria-hidden />
              <b>Mi proyecto</b>
            </div>
            <span className="pill">en curso</span>
          </div>
          <div className="eb">— Próximo paso</div>
          <h5>Modelo predictivo de deserción universitaria</h5>
          <div className="ladder">
            <div className="gate passed"><div className="num">01</div><div className="lbl">Aprobada</div><div className="ttl">Artículo</div></div>
            <div className="gate active"><div className="num">02</div><div className="lbl">En curso</div><div className="ttl">Tomo</div></div>
            <div className="gate"><div className="num">03</div><div className="lbl">Por venir</div><div className="ttl">Defensa</div></div>
          </div>
          <div className="progress"><div ref={fillRef} className="fill" style={{ width: 0 }} /></div>
          <div className="row">
            <span className="left"><span className="ico">T</span>Tutor · L. Pérez</span>
            <span className="right">comentó · 12 abr</span>
          </div>
          <div className="row">
            <span className="left"><span className="ico">⚑</span>Te toca</span>
            <span className="right">subir tomo final</span>
          </div>
          <div className="row">
            <span className="left"><span className="ico">★</span>Defensa</span>
            <span className="right">14 abr · 09:30</span>
          </div>
        </div>

        <div
          ref={(el) => { if (el) floatsRef.current[1] = el; }}
          className="lh-h2-float fc-2 lh-fade-up"
        >
          <div className="ic green"><Check size={14} /></div>
          <div><b>Artículo aprobado</b><span>14/20 · 12 abr</span></div>
        </div>
        <div
          ref={(el) => { if (el) floatsRef.current[2] = el; }}
          className="lh-h2-float fc-3 lh-fade-up"
        >
          <div className="ic yellow"><AlertTriangle size={14} /></div>
          <div><b>Tomo pendiente</b><span>vence en 4 días</span></div>
        </div>
      </div>
    </section>
  );
}
