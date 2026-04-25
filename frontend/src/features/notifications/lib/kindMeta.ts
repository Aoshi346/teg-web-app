import {
  Star,
  RefreshCw,
  UserCheck,
  MessageSquare,
  Calendar,
  Bell,
  type LucideIcon,
} from "lucide-react";
import type { NotificationKind } from "../types";

export interface KindMeta {
  label: string;
  /** Nombre de icono legado (string) — mantenido para compatibilidad con Wave 4. */
  icon: string;
  /** Componente lucide para renderizado real del ícono. */
  IconComponent: LucideIcon;
  /**
   * Clase Tailwind para el fondo del bloque de ícono.
   * Paleta determinista por tipo de evento:
   *   evaluation_received → azul (primary)
   *   state_change        → violeta
   *   assignment          → verde (success)
   *   comment_added       → ámbar
   *   semester_activated  → naranja (accent)
   *   fallback            → gris
   */
  tintBg: string;
  tintFg: string;
}

/**
 * Mapeo de valores `kind` del backend a metadatos de presentación en el frontend.
 * Los valores de kind provienen de backend/api/notifications.py.
 */
const KIND_META_MAP: Record<NotificationKind, KindMeta> = {
  evaluation_received: {
    label: "Evaluación recibida",
    icon: "star",
    IconComponent: Star,
    tintBg: "bg-blue-100",
    tintFg: "text-blue-600",
  },
  state_change: {
    label: "Cambio de estado",
    icon: "refresh-cw",
    IconComponent: RefreshCw,
    tintBg: "bg-violet-100",
    tintFg: "text-violet-600",
  },
  assignment: {
    label: "Asignación",
    icon: "user-check",
    IconComponent: UserCheck,
    tintBg: "bg-emerald-100",
    tintFg: "text-emerald-600",
  },
  comment_added: {
    label: "Nuevo comentario",
    icon: "message-square",
    IconComponent: MessageSquare,
    tintBg: "bg-amber-100",
    tintFg: "text-amber-600",
  },
  semester_activated: {
    label: "Semestre activo",
    icon: "calendar",
    IconComponent: Calendar,
    tintBg: "bg-orange-100",
    tintFg: "text-orange-600",
  },
};

const FALLBACK_META: KindMeta = {
  label: "Notificación",
  icon: "bell",
  IconComponent: Bell,
  tintBg: "bg-slate-100",
  tintFg: "text-slate-500",
};

export function getKindMeta(kind: string): KindMeta {
  return (KIND_META_MAP as Record<string, KindMeta>)[kind] ?? FALLBACK_META;
}
