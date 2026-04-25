"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Inbox, Clock, ArrowLeft, ArrowRight, Check } from "lucide-react";
import type { Notification, NotificationListResponse } from "../types";
import { listNotifications, markAllRead } from "../api/notificationsService";
import { NotificationItem } from "./NotificationItem";

/**
 * Calcula el bucket de agrupación por día para una notificación.
 * - "Hoy": misma fecha calendario que ahora.
 * - "Esta semana": dentro de los últimos 7 días pero no hoy.
 * - "Anteriores": más antiguo que 7 días.
 */
function getDayBucket(dateStr: string, now: Date): "Hoy" | "Esta semana" | "Anteriores" {
  const date = new Date(dateStr);
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diffMs = todayStart.getTime() - new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays <= 0) return "Hoy";
  if (diffDays < 7) return "Esta semana";
  return "Anteriores";
}

const BUCKET_ORDER = ["Hoy", "Esta semana", "Anteriores"] as const;
type Bucket = (typeof BUCKET_ORDER)[number];

function groupByBucket(items: Notification[], now: Date): Map<Bucket, Notification[]> {
  const map = new Map<Bucket, Notification[]>();
  for (const item of items) {
    const bucket = getDayBucket(item.created_at, now);
    if (!map.has(bucket)) map.set(bucket, []);
    map.get(bucket)!.push(item);
  }
  return map;
}

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [pageData, setPageData] = useState<Pick<NotificationListResponse, "count" | "next" | "previous">>({
    count: -1,
    next: null,
    previous: null,
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const now = new Date();

  const fetchPage = useCallback(async (page: number) => {
    setLoading(true);
    try {
      const response = await listNotifications(page);
      setNotifications(response.results);
      setPageData({
        count: response.count,
        next: response.next,
        previous: response.previous,
      });
    } catch {
      // silently ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPage(currentPage);
  }, [fetchPage, currentPage]);

  const handleMarkAllRead = async () => {
    await markAllRead();
    setNotifications((prev) =>
      prev.map((n) => (n.read_at ? n : { ...n, read_at: new Date().toISOString() }))
    );
  };

  const handleMarkRead = (id: number) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n))
    );
  };

  const handleNextPage = () => setCurrentPage((p) => p + 1);
  const handlePrevPage = () => setCurrentPage((p) => Math.max(1, p - 1));

  const displayed = unreadOnly ? notifications.filter((n) => n.read_at === null) : notifications;
  const unreadCount = notifications.filter((n) => n.read_at === null).length;
  const totalCount = notifications.length;
  const isEmpty = !loading && pageData.count === 0;
  const grouped = groupByBucket(displayed, now);
  const bucketCounts: Record<Bucket, number> = {
    Hoy: grouped.get("Hoy")?.length ?? 0,
    "Esta semana": grouped.get("Esta semana")?.length ?? 0,
    Anteriores: grouped.get("Anteriores")?.length ?? 0,
  };

  return (
    <section
      aria-labelledby="inbox-heading"
      className="bg-surface border border-border-subtle rounded-[14px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden"
    >
      <header className="px-7 pt-6 pb-5 border-b border-border-subtle flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-[10px] bg-gradient-to-br from-[rgba(0,102,255,0.08)] to-[rgba(255,107,53,0.08)] text-primary inline-flex items-center justify-center shrink-0">
            <Inbox className="w-[18px] h-[18px]" />
          </div>
          <div className="min-w-0">
            <h3
              id="inbox-heading"
              className="text-[15px] font-extrabold text-text-strong tracking-tight leading-tight truncate"
            >
              Bandeja de notificaciones
            </h3>
            <p className="text-[12.5px] text-text-muted leading-tight mt-0.5">
              Todo lo que pasó en tus proyectos.
            </p>
          </div>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            className="text-[12.5px] font-semibold text-primary hover:underline whitespace-nowrap"
          >
            Marcar todas como leídas
          </button>
        )}
      </header>

      <div className="px-7 py-3.5 flex items-center justify-between gap-3 border-b border-border-subtle">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setUnreadOnly(false)}
            className={`px-3.5 py-1.5 rounded-full text-[12.5px] font-semibold transition-colors inline-flex items-center gap-1.5 ${
              !unreadOnly
                ? "bg-primary text-white"
                : "bg-[var(--color-surface-sunken,#eef0f5)] text-text-muted hover:bg-slate-200"
            }`}
          >
            Todas
            {totalCount > 0 && (
              <span
                className={`text-[11px] px-1.5 py-px rounded-full ${
                  !unreadOnly ? "bg-white/20 text-white" : "bg-white text-slate-500"
                }`}
              >
                {totalCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setUnreadOnly(true)}
            className={`px-3.5 py-1.5 rounded-full text-[12.5px] font-semibold transition-colors inline-flex items-center gap-1.5 ${
              unreadOnly
                ? "bg-primary text-white"
                : "bg-[var(--color-surface-sunken,#eef0f5)] text-text-muted hover:bg-slate-200"
            }`}
          >
            Solo no leídas
            {unreadCount > 0 && (
              <span
                className={`text-[11px] px-1.5 py-px rounded-full ${
                  unreadOnly ? "bg-white/20 text-white" : "bg-white text-slate-500"
                }`}
              >
                {unreadCount}
              </span>
            )}
          </button>
        </div>
        <span className="hidden sm:inline-flex items-center gap-1.5 text-[11.5px] text-text-muted">
          <Clock className="w-3.5 h-3.5" aria-hidden="true" />
          Actualizada ahora
        </span>
      </div>

      {isEmpty ? (
        <div
          data-testid="notifications-empty"
          className="flex flex-col items-center gap-4 py-20 px-6 text-center"
        >
          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[rgba(0,102,255,0.08)] to-[rgba(255,107,53,0.08)] inline-flex items-center justify-center text-primary">
              <Inbox className="w-8 h-8" aria-hidden="true" />
            </div>
            <span
              aria-hidden="true"
              className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 border-2 border-[var(--color-surface,#fff)] inline-flex items-center justify-center"
            >
              <Check className="w-2.5 h-2.5 text-white" />
            </span>
          </div>
          <div>
            <p className="text-[15px] font-bold text-text-strong">Bandeja al día</p>
            <p className="text-[12.5px] text-text-muted mt-1 max-w-xs mx-auto leading-relaxed">
              Te avisaremos aquí cuando algo cambie en tus proyectos.
            </p>
          </div>
        </div>
      ) : displayed.length === 0 ? (
        <div className="py-16 px-6 text-center">
          <p className="text-[13px] text-text-muted">No hay notificaciones sin leer.</p>
        </div>
      ) : (
        <div>
          {BUCKET_ORDER.map((bucket) => {
            const items = grouped.get(bucket);
            if (!items || items.length === 0) return null;
            return (
              <div key={bucket}>
                <div className="px-7 py-2 flex items-center justify-between bg-gradient-to-b from-[rgba(15,23,42,0.02)] to-transparent border-y border-[rgba(15,23,42,0.05)]">
                  <span className="text-[11.5px] font-bold text-text-muted uppercase tracking-[0.06em]">
                    {bucket}
                  </span>
                  <span className="text-[10.5px] font-semibold text-text-muted">
                    {bucketCounts[bucket]} {bucketCounts[bucket] === 1 ? "elemento" : "elementos"}
                  </span>
                </div>
                <div className="divide-y divide-border-subtle">
                  {items.map((notification) => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onMarkRead={handleMarkRead}
                      now={now}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!isEmpty && (pageData.previous || pageData.next) && (
        <div className="px-7 py-4 border-t border-border-subtle flex items-center justify-between gap-3 bg-[#fafbfd]">
          <button
            onClick={handlePrevPage}
            disabled={!pageData.previous}
            className="px-3.5 py-1.5 text-[12.5px] font-semibold text-text-muted bg-surface border border-border-subtle rounded-[8px] hover:bg-[var(--color-surface-sunken,#eef0f5)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors inline-flex items-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
            Anterior
          </button>
          {pageData.count > 0 && (
            <span className="text-[11.5px] text-text-muted">
              Página {currentPage}
            </span>
          )}
          <button
            onClick={handleNextPage}
            disabled={!pageData.next}
            className="px-3.5 py-1.5 text-[12.5px] font-semibold text-primary bg-[rgba(0,102,255,0.06)] border border-[rgba(0,102,255,0.18)] rounded-[8px] hover:bg-[rgba(0,102,255,0.1)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors inline-flex items-center gap-1.5"
          >
            Siguiente
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>
      )}
    </section>
  );
}
