"use client";

import React from "react";

/**
 * Lightweight skeleton fallback matching the dashboard layout.
 * Pre-calculated heights prevent CLS (Cumulative Layout Shift).
 * Used inside Suspense boundaries and loading states.
 */

const Pulse = ({ className = "" }: { className?: string }) => (
  <div className={`animate-pulse rounded-2xl bg-slate-200/60 ${className}`} />
);

export function DashboardSkeleton({ columns = 2 }: { columns?: number }) {
  return (
    <div className="p-3 sm:p-4 md:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Welcome bar */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Pulse className="h-7 w-48 sm:w-64" />
          <Pulse className="h-4 w-32 sm:w-40" />
        </div>
        <Pulse className="h-8 w-24 rounded-full" />
      </div>

      {/* Semester bar */}
      <Pulse className="h-[72px]" />

      {/* Stat cards */}
      <div className={`grid grid-cols-1 ${columns > 1 ? "lg:grid-cols-2" : ""} gap-5`}>
        {Array.from({ length: columns }).map((_, i) => (
          <Pulse key={i} className="h-44" />
        ))}
      </div>

      {/* Content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <Pulse className="lg:col-span-2 h-72" />
        <Pulse className="lg:col-span-1 h-72" />
      </div>
    </div>
  );
}

export function ListPageSkeleton() {
  return (
    <div className="p-3 sm:p-4 md:p-6 lg:p-8 space-y-5 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Pulse className="h-7 w-40" />
        <Pulse className="h-9 w-28 rounded-xl" />
      </div>

      {/* Filter bar */}
      <Pulse className="h-12 rounded-xl" />

      {/* List items */}
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
    <div className="p-3 sm:p-4 md:p-6 lg:p-8 space-y-6 max-w-4xl mx-auto">
      <Pulse className="h-8 w-64" />
      <Pulse className="h-48" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Pulse className="h-32" />
        <Pulse className="h-32" />
      </div>
      <Pulse className="h-64" />
    </div>
  );
}

export default DashboardSkeleton;
