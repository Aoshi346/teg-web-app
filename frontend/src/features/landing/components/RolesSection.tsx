"use client";

import React, { useEffect, useRef } from "react";
import EstudianteVisual from "./role-visuals/EstudianteVisual";
import TutorVisual from "./role-visuals/TutorVisual";
import JuradoVisual from "./role-visuals/JuradoVisual";
import AdminVisual from "./role-visuals/AdminVisual";

export default function RolesSection() {
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
    <section ref={sectionRef} id="roles" className="lh-roles">
      <div className="lh-roles-h">
        <h3>
          Cuatro roles.<br />Una <em>conversación</em>.
        </h3>
        <span className="vol">— Cada uno ve solo lo que le toca</span>
      </div>

      <div ref={gridRef} className="lh-rgrid lh-stagger">
        <article className="lh-role estu" style={{ "--stagger-i": 0 } as React.CSSProperties} data-testid="role-card-estudiante">
          <div className="text">
            <div className="head">
              <div className="num">I</div>
              <div className="lbl">— Estudiante</div>
            </div>
            <h5>Tu trabajo, <em>en orden</em>.</h5>
            <p>No tienes que adivinar qué sigue. La plataforma te muestra el próximo paso y te avisa cuando recibes una observación.</p>
            <div className="verbs">
              <span className="v">Sube tu propuesta o tomo en <b>un solo lugar</b></span>
              <span className="v">Lee las observaciones <b>sin buscar correos</b></span>
              <span className="v">Sabes <b>cuándo</b> y <b>dónde</b> es tu defensa</span>
            </div>
          </div>
          <div className="visual"><EstudianteVisual /></div>
        </article>

        <article className="lh-role tut" style={{ "--stagger-i": 1 } as React.CSSProperties} data-testid="role-card-tutor">
          <div className="text">
            <div className="head">
              <div className="num">II</div>
              <div className="lbl">— Tutor</div>
            </div>
            <h5>Acompaña <em>sin ruido</em>.</h5>
            <p>Solo ves lo que tienes que revisar. Comenta donde haga falta, deja tu firma cuando esté listo, y la plataforma le avisa al estudiante por ti.</p>
            <div className="verbs">
              <span className="v">Comenta directo en <b>la entrega</b>, no en un correo</span>
              <span className="v">Aprueba con <b>un click</b> cuando esté listo</span>
              <span className="v">Recibes alertas <b>solo cuando te toca</b></span>
            </div>
          </div>
          <div className="visual"><TutorVisual /></div>
        </article>

        <article className="lh-role jur" style={{ "--stagger-i": 2 } as React.CSSProperties} data-testid="role-card-jurado">
          <div className="text">
            <div className="head">
              <div className="num">III</div>
              <div className="lbl">— Jurado</div>
            </div>
            <h5>Evalúa <em>con criterio</em>.</h5>
            <p>Solo te aparecen las defensas que te asignaron. La rúbrica está integrada — terminas, firmas, y el resultado se entrega solo.</p>
            <div className="verbs">
              <span className="v">Solo ves <b>tus defensas</b>, no las del resto</span>
              <span className="v">Rúbrica con <b>escala clara</b>, sin Excel</span>
              <span className="v">Resultado firmado <b>al instante</b></span>
            </div>
          </div>
          <div className="visual"><JuradoVisual /></div>
        </article>

        <article className="lh-role adm" style={{ "--stagger-i": 3 } as React.CSSProperties} data-testid="role-card-admin">
          <div className="text">
            <div className="head">
              <div className="num">IV</div>
              <div className="lbl">— Coordinación</div>
            </div>
            <h5>Tienes <em>todo el panorama</em>.</h5>
            <p>Cuántos proyectos hay, en qué fase, quién está atrasado y qué semestre cierra cuándo. Si hay que destrabar algo, lo haces y queda registrado.</p>
            <div className="verbs">
              <span className="v"><b>Asigna jurados</b> con un solo paso</span>
              <span className="v"><b>Destraba</b> casos con motivo registrado</span>
              <span className="v"><b>Cierra el semestre</b> con reportes listos</span>
            </div>
          </div>
          <div className="visual"><AdminVisual /></div>
        </article>
      </div>
    </section>
  );
}
