"use client";

/**
 * NotificationProvider — the single global notification stack.
 *
 * Any component can call `useNotify()` to push a friendly notification.
 * Errors thrown from API calls are automatically normalized into friendly
 * Spanish messages via `normalizeError`.
 *
 *   const notify = useNotify();
 *   notify.success("Perfil actualizado.");
 *   notify.error(err);                      // err: unknown → friendly text
 *   notify.error(err, "No pudimos guardar"); // with context-specific fallback
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import Notice, { NoticeVariant } from "./Notice";
import { normalizeError } from "@/lib/normalizeError";

interface NotificationItem {
  id: string;
  variant: NoticeVariant;
  message: string;
  duration: number;
  createdAt: number;
  leaving?: boolean;
  progress: number;
}

interface NotifyOptions {
  /** Milliseconds before auto-dismiss. Use `0` to keep it open. */
  duration?: number;
}

interface NotifyApi {
  show: (variant: NoticeVariant, message: string, opts?: NotifyOptions) => string;
  success: (message: string, opts?: NotifyOptions) => string;
  info: (message: string, opts?: NotifyOptions) => string;
  warning: (message: string, opts?: NotifyOptions) => string;
  /** Accepts raw Error/string/API object — runs it through normalizeError. */
  error: (err: unknown, fallback?: string, opts?: NotifyOptions) => string;
  dismiss: (id: string) => void;
  clear: () => void;
}

const NotifyContext = createContext<NotifyApi | null>(null);

const DEFAULT_DURATIONS: Record<NoticeVariant, number> = {
  success: 3500,
  info: 3500,
  warning: 5000,
  error: 6000,
};

const EXIT_MS = 260;
const MAX_VISIBLE = 4;

let _id = 0;
const nextId = () => `n_${++_id}_${Date.now().toString(36)}`;

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const timers = useRef<Map<string, { hide: number; tick: number }>>(new Map());

  const dismiss = useCallback((id: string) => {
    setItems((prev) =>
      prev.map((it) => (it.id === id ? { ...it, leaving: true } : it))
    );
    const t = timers.current.get(id);
    if (t) {
      window.clearTimeout(t.hide);
      window.clearInterval(t.tick);
      timers.current.delete(id);
    }
    window.setTimeout(() => {
      setItems((prev) => prev.filter((it) => it.id !== id));
    }, EXIT_MS);
  }, []);

  const show = useCallback<NotifyApi["show"]>(
    (variant, message, opts) => {
      const id = nextId();
      const duration = opts?.duration ?? DEFAULT_DURATIONS[variant];

      setItems((prev) => {
        const next = [...prev, {
          id,
          variant,
          message,
          duration,
          createdAt: Date.now(),
          progress: 1,
        }];
        // Evict oldest if stack is too tall
        if (next.length > MAX_VISIBLE) {
          const evict = next[0];
          window.setTimeout(() => dismiss(evict.id), 0);
        }
        return next;
      });

      if (duration > 0) {
        const start = Date.now();
        const tick = window.setInterval(() => {
          const elapsed = Date.now() - start;
          const p = Math.max(0, 1 - elapsed / duration);
          setItems((prev) =>
            prev.map((it) => (it.id === id ? { ...it, progress: p } : it))
          );
        }, 60);
        const hide = window.setTimeout(() => dismiss(id), duration);
        timers.current.set(id, { hide, tick });
      }

      return id;
    },
    [dismiss]
  );

  const api = useMemo<NotifyApi>(
    () => ({
      show,
      success: (m, o) => show("success", m, o),
      info: (m, o) => show("info", m, o),
      warning: (m, o) => show("warning", m, o),
      error: (err, fallback, o) => show("error", normalizeError(err, fallback), o),
      dismiss,
      clear: () => {
        timers.current.forEach(({ hide, tick }) => {
          window.clearTimeout(hide);
          window.clearInterval(tick);
        });
        timers.current.clear();
        setItems([]);
      },
    }),
    [show, dismiss]
  );

  useEffect(() => {
    const timersMap = timers.current;
    return () => {
      timersMap.forEach(({ hide, tick }) => {
        window.clearTimeout(hide);
        window.clearInterval(tick);
      });
      timersMap.clear();
    };
  }, []);

  return (
    <NotifyContext.Provider value={api}>
      {children}
      <NotificationStack items={items} onDismiss={dismiss} />
    </NotifyContext.Provider>
  );
}

function NotificationStack({
  items,
  onDismiss,
}: {
  items: NotificationItem[];
  onDismiss: (id: string) => void;
}) {
  if (!items.length) return null;

  // Newest on top: reverse so most recent item renders first in a
  // normal (top-down) flex column.
  const ordered = [...items].reverse();

  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed z-[200] top-3 right-3 left-3 sm:left-auto sm:top-6 sm:right-6 sm:w-[400px] flex flex-col gap-2.5"
      style={{
        top: "max(0.75rem, env(safe-area-inset-top))",
        right: "max(0.75rem, env(safe-area-inset-right))",
      }}
    >
      {ordered.map((it) => (
        <div
          key={it.id}
          className={[
            "pointer-events-auto w-full will-change-transform",
            it.leaving ? "notice-exit" : "notice-enter",
          ].join(" ")}
        >
          <Notice
            variant={it.variant}
            message={it.message}
            onClose={() => onDismiss(it.id)}
            progress={it.duration > 0 ? it.progress : undefined}
          />
        </div>
      ))}
    </div>
  );
}

export function useNotify(): NotifyApi {
  const ctx = useContext(NotifyContext);
  if (!ctx) {
    // Graceful no-op fallback so components don't crash if the provider
    // is somehow missing (e.g. a mis-rooted Storybook).
    if (typeof window !== "undefined") {
      // eslint-disable-next-line no-console
      console.warn("[useNotify] NotificationProvider is missing.");
    }
    const noop = () => "";
    return {
      show: noop,
      success: noop,
      info: noop,
      warning: noop,
      error: noop,
      dismiss: () => {},
      clear: () => {},
    };
  }
  return ctx;
}
