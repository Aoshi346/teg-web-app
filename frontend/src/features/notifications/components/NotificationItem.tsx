"use client";

import React from "react";
import type { Notification } from "../types";
import { formatRelativeTime } from "../lib/relativeTime";
import { getKindMeta } from "../lib/kindMeta";

interface NotificationItemProps {
  notification: Notification;
  onMarkRead: (id: number) => void;
  now?: Date;
}

export function NotificationItem({ notification, onMarkRead, now }: NotificationItemProps) {
  const isUnread = notification.read_at === null;
  const timestamp = formatRelativeTime(new Date(notification.created_at), now);
  const meta = getKindMeta(notification.kind);
  const { IconComponent, tintBg, tintFg } = meta;

  const handleClick = () => {
    onMarkRead(notification.id);
  };

  const content = (
    <div
      className={`flex items-start gap-3 px-4 py-3 hover:bg-slate-50 transition-colors cursor-pointer ${
        isUnread ? "bg-primary/[0.03]" : ""
      }`}
      onClick={handleClick}
    >
      {/* Kind icon block — 32×32 tinted square, same idiom as ActivityFeed */}
      <div
        className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-[10px] ${tintBg} ${tintFg}`}
        aria-hidden="true"
      >
        <IconComponent className="w-4 h-4" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <p className={`text-sm text-slate-800 truncate ${isUnread ? "font-bold" : "font-semibold"}`}>
            {notification.title}
          </p>
          {isUnread && (
            <span
              data-testid="notification-unread-marker"
              className="flex-shrink-0 w-2 h-2 rounded-full bg-primary"
              aria-hidden="true"
            />
          )}
        </div>
        <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{notification.body}</p>
        <p className="text-[11px] text-slate-400 mt-1">{timestamp}</p>
      </div>
    </div>
  );

  if (notification.link_url) {
    return (
      <a
        href={notification.link_url}
        className="block no-underline"
        onClick={handleClick}
      >
        {content}
      </a>
    );
  }

  return content;
}
