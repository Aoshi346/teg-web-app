"use client";

import React from "react";

const Pulse = ({ className = "" }: { className?: string }) => (
  <div className={`animate-pulse rounded-2xl bg-slate-200/60 ${className}`} />
);

export function DashboardSkeleton({ columns: _columns }: { columns?: number } = {}) {
  return (
    <div className="mx-auto max-w-7xl space-y-4 p-3 sm:p-4 md:p-6 lg:p-8">
      <Pulse className="h-[140px]" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Pulse key={i} className="h-[180px]" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[2fr_1fr]">
        <Pulse className="h-[260px]" />
        <Pulse className="h-[260px]" />
      </div>
    </div>
  );
}

export function ListPageSkeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-5 p-3 sm:p-4 md:p-6 lg:p-8">
      <div className="flex items-center justify-between">
        <Pulse className="h-7 w-40" />
        <Pulse className="h-9 w-28 rounded-xl" />
      </div>
      <Pulse className="h-12 rounded-xl" />
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Pulse key={i} className="h-24" />
        ))}
      </div>
    </div>
  );
}

export function DetailPageSkeleton() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 p-3 sm:p-4 md:p-6 lg:p-8">
      <Pulse className="h-8 w-64" />
      <Pulse className="h-48" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Pulse className="h-32" />
        <Pulse className="h-32" />
      </div>
      <Pulse className="h-64" />
    </div>
  );
}

export default DashboardSkeleton;
