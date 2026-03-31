"use client";

import React, { useEffect, useRef } from "react";
import { Instagram, ArrowRight } from "lucide-react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export default function Footer() {
  const ctaSectionRef = useRef<HTMLElement>(null);
  const ctaContentRef = useRef<HTMLDivElement>(null);
  const footerRef = useRef<HTMLElement>(null);
  const footerGridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // CTA Banner reveal
      if (ctaContentRef.current) {
        const elements = ctaContentRef.current.children;
        gsap.set(elements, { autoAlpha: 0, y: 40 });

        ScrollTrigger.create({
          trigger: ctaSectionRef.current,
          start: "top 80%",
          onEnter: () => {
            gsap.to(elements, {
              autoAlpha: 1,
              y: 0,
              duration: 0.8,
              stagger: 0.15,
              ease: "power3.out",
            });
          },
        });
      }

      // Footer grid columns stagger in
      if (footerGridRef.current) {
        const cols = footerGridRef.current.children;
        gsap.set(cols, { autoAlpha: 0, y: 30 });

        ScrollTrigger.create({
          trigger: footerRef.current,
          start: "top 90%",
          onEnter: () => {
            gsap.to(cols, {
              autoAlpha: 1,
              y: 0,
              duration: 0.7,
              stagger: 0.1,
              ease: "power2.out",
            });
          },
        });
      }
    });

    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach((t) => t.kill());
    };
  }, []);

  return (
    <>
      {/* CTA Banner */}
      <section
        ref={ctaSectionRef}
        className="relative bg-gradient-to-br from-usm-navy via-usm-navy to-blue-900 py-20 px-4 overflow-hidden noise-overlay"
      >
        {/* Background decoration */}
        <div className="absolute inset-0 dot-grid opacity-10" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-usm-blue/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-72 h-72 bg-usm-orange/10 rounded-full blur-3xl" />

        <div
          ref={ctaContentRef}
          className="relative container mx-auto max-w-3xl text-center z-10"
        >
          <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-4">
            ¿Listo para comenzar?
          </h2>
          <p className="text-lg text-slate-300 mb-8 max-w-xl mx-auto">
            Simplifica la gestión de tu Trabajo Especial de Grado con una
            herramienta diseñada para ti.
          </p>
          <button
            onClick={() => {
              const btn = document.querySelector(
                '[aria-label="Ingresar"]'
              ) as HTMLButtonElement;
              if (btn) btn.click();
            }}
            className="group inline-flex items-center gap-2.5 px-8 py-3.5 text-base font-bold text-white
                       bg-gradient-to-r from-usm-orange to-orange-500
                       rounded-full shadow-lg shadow-orange-500/25
                       hover:shadow-xl hover:shadow-orange-500/40 hover:-translate-y-1
                       active:translate-y-0 active:shadow-md
                       transition-all duration-300 ease-out"
          >
            Ingresar a la plataforma
            <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer ref={footerRef} className="bg-gray-950 text-white">
        <div className="container mx-auto px-4 py-12">
          <div
            ref={footerGridRef}
            className="grid grid-cols-1 gap-8 md:grid-cols-4"
          >
            <div className="md:col-span-1">
              <h3 className="text-2xl font-bold">TesisFar</h3>
              <p className="mt-3 text-gray-400 leading-relaxed text-sm">
                Plataforma para la gestión, entrega y evaluación del Trabajo
                Especial de Grado.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-sm uppercase tracking-wider text-gray-300">
                Enlaces
              </h4>
              <ul className="mt-4 space-y-2.5">
                <li>
                  <a
                    href="#"
                    className="text-gray-400 transition-colors hover:text-usm-blue text-sm"
                  >
                    Acerca de
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 transition-colors hover:text-usm-blue text-sm"
                  >
                    Soporte
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 transition-colors hover:text-usm-blue text-sm"
                  >
                    Blog
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-sm uppercase tracking-wider text-gray-300">
                Dirección
              </h4>
              <address className="not-italic mt-4 text-gray-400 space-y-2 text-sm leading-relaxed">
                <div>
                  La Florencia - Caracas. Km. 3 de la carretera Petare-Santa
                  Lucía, Estado Miranda.
                </div>
                <div>Email: decanato.farmacia@usm.edu.ve</div>
              </address>
            </div>
            <div>
              <h4 className="font-semibold text-sm uppercase tracking-wider text-gray-300">
                Síguenos
              </h4>
              <div className="mt-4 flex space-x-4">
                <a
                  href="#"
                  className="flex items-center justify-center w-10 h-10 rounded-full bg-white/5 border border-white/10
                           text-gray-400 transition-all hover:text-usm-blue hover:bg-usm-blue/10 hover:border-usm-blue/30 hover:scale-110"
                  aria-label="Instagram"
                >
                  <Instagram size={18} />
                </a>
              </div>
            </div>
          </div>
          <div className="mt-12 border-t border-gray-800 pt-8 text-center text-gray-500 text-sm">
            <p>
              &copy; {new Date().getFullYear()} Aoshi Blanco. Todos los derechos
              reservados.
            </p>
          </div>
        </div>
      </footer>
    </>
  );
}
