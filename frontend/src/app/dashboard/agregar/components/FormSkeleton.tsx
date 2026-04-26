"use client";

import React from "react";

export default function FormSkeleton() {
  return (
    <div className="space-y-4 animate-in fade-in duration-500">
      <div className="h-32 rounded-2xl bg-surface-sunken border border-border-subtle animate-pulse" />
      <div className="grid lg:grid-cols-[280px_1fr] gap-5">
        <div className="space-y-3">
          <div className="h-32 rounded-xl bg-surface-sunken border border-border-subtle animate-pulse" />
          <div className="h-32 rounded-xl bg-surface-sunken border border-border-subtle animate-pulse" />
        </div>
        <div className="rounded-2xl bg-surface border border-border-subtle p-6 space-y-4">
          <div className="h-6 w-1/3 rounded bg-surface-sunken animate-pulse" />
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 rounded-lg bg-surface-sunken animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}
