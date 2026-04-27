"use client";

import React, { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  User,
  Settings,
  Shield,
  HelpCircle,
  MessageSquare,
  LogOut,
} from "lucide-react";

export interface ProfileMenuProps {
  isOpen: boolean;
  email: string;
  role: string;
  onClose: () => void;
  onLogout: () => void;
  anchorRef?: React.RefObject<HTMLElement | null>;
}

function deriveName(email: string): string {
  const local = email.split("@")[0] ?? "";
  return local.charAt(0).toUpperCase() + local.slice(1);
}

export default function ProfileMenu({
  isOpen,
  email,
  role,
  onClose,
  onLogout,
  anchorRef,
}: ProfileMenuProps) {
  const router = useRouter();
  const menuRef = useRef<HTMLDivElement>(null);

  // Cierra al presionar ESC
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  // Cierra al hacer clic fuera del menú o del anchorRef
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as Node;
      if (menuRef.current?.contains(target)) return;
      if (anchorRef?.current?.contains(target)) return;
      // Note: ignora si esta instancia está oculta (display:none ancestro) —
      // sucede cuando el sidebar renderiza dos copias (escritorio + drawer móvil)
      // y la oculta cerraría el estado compartido antes de que dispare el click.
      if (menuRef.current && menuRef.current.offsetParent === null) return;
      onClose();
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [isOpen, onClose, anchorRef]);

  if (!isOpen) return null;

  const initials = email.charAt(0).toUpperCase();
  const displayName = deriveName(email);

  function navigate(path: string) {
    router.push(path);
    onClose();
  }

  return (
    <div
      ref={menuRef}
      className="prof-pop"
      role="menu"
      aria-label="Menú de perfil"
    >
      {/* Banda de cabecera */}
      <div className="prof-band">
        <div className="prof-band-row">
          <div className="prof-band-ava">{initials}</div>
          <div className="prof-band-info">
            <span className="prof-band-eyebrow">Identificado como</span>
            <span className="prof-band-name">{displayName}</span>
            <span className="prof-band-email">{email}</span>
          </div>
        </div>
        <span className="prof-band-role">
          <span className="dot" />
          {role}
        </span>
      </div>

      {/* Sección Cuenta */}
      <div className="prof-sec">
        <p className="prof-sec-title">Cuenta</p>
        <button
          className="prof-item"
          role="menuitem"
          type="button"
          onClick={() => navigate("/dashboard/settings")}
        >
          <span className="prof-item-ic">
            <User />
          </span>
          Mi perfil
          <span className="arrow">→</span>
        </button>
        <button
          className="prof-item"
          role="menuitem"
          type="button"
          onClick={() => navigate("/dashboard/settings")}
        >
          <span className="prof-item-ic">
            <Settings />
          </span>
          Configuración
          <span className="prof-shortcut">⌘ ,</span>
        </button>
        <button
          className="prof-item"
          role="menuitem"
          type="button"
          onClick={() => navigate("/dashboard/settings")}
        >
          <span className="prof-item-ic">
            <Shield />
          </span>
          Privacidad
          <span className="arrow">→</span>
        </button>
      </div>

      {/* Sección Soporte */}
      <div className="prof-sec">
        <p className="prof-sec-title">Soporte</p>
        <button
          className="prof-item"
          role="menuitem"
          type="button"
          onClick={() => navigate("/dashboard/settings")}
        >
          <span className="prof-item-ic">
            <HelpCircle />
          </span>
          Centro de ayuda
          <span className="arrow">↗</span>
        </button>
        <button
          className="prof-item"
          role="menuitem"
          type="button"
          onClick={() => navigate("/dashboard/settings")}
        >
          <span className="prof-item-ic">
            <MessageSquare />
          </span>
          Reportar problema
          <span className="arrow">→</span>
        </button>
      </div>

      {/* Sección logout (destructivo) */}
      <div className="prof-sec">
        <button
          className="prof-item danger"
          role="menuitem"
          type="button"
          onClick={onLogout}
        >
          <span className="prof-item-ic">
            <LogOut />
          </span>
          Cerrar sesión
          <span className="prof-shortcut">⇧⌘ Q</span>
        </button>
      </div>
    </div>
  );
}
