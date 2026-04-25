"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Bell, BellOff } from "lucide-react";
import type { Notification } from "../types";
import { NotificationItem } from "./NotificationItem";

const MAX_VISIBLE = 10;

interface NotificationsDropdownProps {
  notifications: Notification[];
  unreadCount: number;
  onMarkRead: (id: number) => void;
  onMarkAllRead: () => void;
  onOpen: () => void;
}

export function NotificationsDropdown({
  notifications,
  unreadCount,
  onMarkRead,
  onMarkAllRead,
  onOpen,
}: NotificationsDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleToggle = () => {
    if (!isOpen) {
      onOpen();
    }
    setIsOpen((prev) => !prev);
  };

  const visible = notifications.slice(0, MAX_VISIBLE);

  return (
    <div className="relative" ref={containerRef}>
      <button
        onClick={handleToggle}
        aria-label={`Notificaciones${unreadCount > 0 ? ` (${unreadCount} sin leer)` : ""}`}
        aria-expanded={isOpen}
        className="relative p-2 sm:p-2.5 rounded-lg hover:bg-slate-100 active:scale-95 transition-all duration-200 touch-manipulation"
      >
        <Bell className="w-4 h-4 sm:w-5 sm:h-5 text-slate-500" />
        {unreadCount > 0 && (
          <span
            data-testid="notification-badge"
            className="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[10px] font-bold border-2 border-white leading-none"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div
          role="menu"
          className="absolute right-0 top-full mt-3 w-80 sm:w-96 bg-white border border-slate-200 rounded-xl shadow-xl z-[60] animate-in fade-in zoom-in-95 slide-in-from-top-2 duration-200 origin-top-right overflow-hidden"
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-800">Notificaciones</h3>
            {notifications.length > 0 && (
              <button
                onClick={onMarkAllRead}
                className="text-xs text-primary font-semibold hover:underline"
                aria-label="Marcar todas como leídas"
              >
                Marcar todas como leídas
              </button>
            )}
          </div>

          <div className="max-h-[360px] overflow-y-auto divide-y divide-slate-100">
            {visible.length === 0 ? (
              <div className="flex flex-col items-center gap-2 px-4 py-8 text-center">
                <BellOff className="w-8 h-8 text-slate-300" aria-hidden="true" />
                <p className="text-sm font-semibold text-slate-600">
                  No tienes notificaciones
                </p>
                <p className="text-xs text-slate-400 max-w-[200px]">
                  Te avisaremos cuando algo cambie en tus proyectos.
                </p>
              </div>
            ) : (
              visible.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkRead={onMarkRead}
                />
              ))
            )}
          </div>

          <div className="border-t border-slate-100 px-4 py-2.5">
            <Link
              href="/dashboard/settings#notifications"
              className="text-xs text-primary font-semibold hover:underline"
              aria-label="Ver todas las notificaciones"
            >
              Ver todas
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
