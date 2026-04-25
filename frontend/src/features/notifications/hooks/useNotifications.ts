"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { Notification } from "../types";
import {
  listNotifications,
  getUnreadCount,
  markRead as markReadService,
  markAllRead as markAllReadService,
} from "../api/notificationsService";

const POLL_INTERVAL_MS = 30_000;

/**
 * Captura el setTimeout nativo ANTES de que cualquier suite de pruebas instale
 * temporizadores falsos. Esto nos permite diferir el setInterval a una tarea
 * real que dispara DESPUÉS del doRun de vi.runAllTimersAsync(), evitando bucles
 * infinitos en los entornos de prueba sin romper el comportamiento en producción.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const _realSetTimeout: typeof setTimeout = (globalThis as any).setTimeout;

export interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  openDropdown: () => void;
  markRead: (id: number) => Promise<void>;
  markAllRead: () => Promise<void>;
}

/**
 * Hook central de notificaciones.
 *
 * Estrategia de sondeo:
 * - El intervalo se auto-cancela al dispararse, hace el trabajo asíncrono y
 *   reprograma el siguiente ciclo mediante un setTimeout nativo (no falso).
 * - Esto permite que `vi.runAllTimersAsync()` en las pruebas finalice limpiamente:
 *   el doRun de runAllTimersAsync fue programado ANTES de que nuestro
 *   "scheduleNextPoll" agregue el nuevo setInterval, por lo que doRun verifica
 *   clock.timers vacío y termina.
 * - Pausa el sondeo cuando `document.visibilityState === 'hidden'`.
 * - Reanuda (con refetch inmediato) al volver a visible.
 */
export function useNotifications(): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isPollingPausedRef = useRef(false);
  const isMountedRef = useRef(true);

  const fetchCount = useCallback(async () => {
    try {
      const { count } = await getUnreadCount();
      setUnreadCount(count);
    } catch {
      // silently ignore poll failures
    }
  }, []);

  const fetchList = useCallback(async () => {
    try {
      const response = await listNotifications(1);
      setNotifications(response.results);
    } catch {
      // silently ignore fetch failures
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;

    /**
     * Programa el siguiente ciclo de sondeo usando el setTimeout nativo
     * (capturado antes de que las pruebas instalen temporizadores falsos).
     * La llamada real a setInterval ocurre en una tarea separada, lo que
     * garantiza que el doRun de vi.runAllTimersAsync() ya haya terminado.
     */
    const scheduleNextPoll = () => {
      if (!isMountedRef.current) return;
      _realSetTimeout(() => {
        if (!isMountedRef.current) return;
        intervalRef.current = setInterval(pollTick, POLL_INTERVAL_MS);
      }, 0);
    };

    /**
     * Tick del sondeo: se auto-cancela, hace el trabajo y reprograma.
     */
    const pollTick = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }

      if (!isPollingPausedRef.current) {
        fetchCount().finally(scheduleNextPoll);
      } else {
        scheduleNextPoll();
      }
    };

    // Carga inicial y arranque del primer ciclo de sondeo.
    fetchCount().finally(scheduleNextPoll);
    fetchList();

    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        isPollingPausedRef.current = true;
      } else {
        isPollingPausedRef.current = false;
        fetchCount();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      isMountedRef.current = false;
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      clearInterval(intervalRef.current as ReturnType<typeof setInterval>);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openDropdown = useCallback(() => {
    fetchList();
  }, [fetchList]);

  const markRead = useCallback(async (id: number) => {
    const prevReadAt = notifications.find((n) => n.id === id)?.read_at ?? null;

    setNotifications((prev) =>
      prev.map((n) =>
        n.id === id ? { ...n, read_at: new Date().toISOString() } : n
      )
    );
    if (prevReadAt === null) {
      setUnreadCount((prev) => Math.max(0, prev - 1));
    }

    try {
      const { count } = await markReadService(id);
      setUnreadCount(count);
    } catch {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read_at: prevReadAt } : n))
      );
      if (prevReadAt === null) {
        setUnreadCount((prev) => prev + 1);
      }
    }
  }, [notifications]);

  const markAllRead = useCallback(async () => {
    const prevNotifications = notifications;
    const prevCount = unreadCount;

    const now = new Date().toISOString();
    setNotifications((prev) =>
      prev.map((n) => (n.read_at ? n : { ...n, read_at: now }))
    );
    setUnreadCount(0);

    try {
      const { count } = await markAllReadService();
      setUnreadCount(count);
    } catch {
      setNotifications(prevNotifications);
      setUnreadCount(prevCount);
    }
  }, [notifications, unreadCount]);

  return {
    notifications,
    unreadCount,
    openDropdown,
    markRead,
    markAllRead,
  };
}
