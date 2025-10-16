import React from "react";
import { Instagram, Twitter, Linkedin } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          <div className="md:col-span-1">
            <h3 className="text-2xl font-bold">TesisFar</h3>
            <p className="mt-2 text-gray-400">
              Plataforma para la gestión, entrega y evaluación del Trabajo
              Especial de Grado.
            </p>
          </div>
          <div>
            <h4 className="font-semibold">Enlaces</h4>
            <ul className="mt-4 space-y-2">
              <li>
                <a
                  href="#"
                  className="text-gray-400 transition-colors hover:text-indigo-400"
                >
                  Acerca de
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-400 transition-colors hover:text-indigo-400"
                >
                  Soporte
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-400 transition-colors hover:text-indigo-400"
                >
                  Blog
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold">Dirección</h4>
            <address className="not-italic mt-4 text-gray-400 space-y-2">
              <div>La Florencia - Caracas. Km. 3 de la carretera Petare-Santa Lucía, Estado Miranda.</div>
              <div>Email: decanato.farmacia@usm.edu.ve</div>
            </address>
          </div>
          <div>
            <h4 className="font-semibold">Síguenos</h4>
            <div className="mt-4 flex space-x-4">
              <a
                href="#"
                className="text-gray-400 transition-colors hover:text-indigo-400"
                aria-label="Instagram"
              >
                <Instagram size={24} />
              </a>
            </div>
          </div>
        </div>
        <div className="mt-12 border-t border-gray-700 pt-8 text-center text-gray-500">
          <p>
            &copy; {new Date().getFullYear()} Aoshi Blanco. Todos los derechos
            reservados.
          </p>
        </div>
      </div>
    </footer>
  );
}
