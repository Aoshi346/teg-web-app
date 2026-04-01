"use client";

import React from "react";

function Pulse({ className }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded-lg bg-gray-200/70 ${className || ""}`} />
  );
}

export default function FormSkeleton() {
  return (
    <div className="animate-in fade-in duration-500">
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left column — type selector skeleton */}
        <div className="lg:col-span-1 space-y-4">
          <Pulse className="h-4 w-32" />
          <div className="flex flex-row lg:flex-col gap-3">
            <div className="flex-1 lg:flex-none rounded-2xl border-2 border-gray-100 bg-white p-5 space-y-3">
              <Pulse className="w-12 h-12 rounded-xl" />
              <Pulse className="h-5 w-36" />
              <Pulse className="h-3 w-20" />
            </div>
            <div className="flex-1 lg:flex-none rounded-2xl border-2 border-gray-100 bg-white p-5 space-y-3">
              <Pulse className="w-12 h-12 rounded-xl" />
              <Pulse className="h-5 w-44" />
              <Pulse className="h-3 w-20" />
            </div>
          </div>
        </div>

        {/* Right column — form skeleton */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-6 sm:p-8 space-y-8">
              {/* Header */}
              <div className="flex items-center justify-between pb-6 border-b border-gray-100">
                <div className="flex items-center gap-4">
                  <Pulse className="w-12 h-12 rounded-xl" />
                  <div className="space-y-2">
                    <Pulse className="h-6 w-56" />
                    <Pulse className="h-4 w-40" />
                  </div>
                </div>
                <Pulse className="h-8 w-28 rounded-full" />
              </div>

              {/* Title field */}
              <div className="space-y-2">
                <Pulse className="h-4 w-32" />
                <Pulse className="h-12 w-full rounded-xl" />
              </div>

              {/* Student field */}
              <div className="space-y-3">
                <Pulse className="h-4 w-44" />
                <div className="rounded-xl border border-gray-100 p-4">
                  <div className="flex items-center gap-3">
                    <Pulse className="w-10 h-10 rounded-lg" />
                    <div className="flex-1 space-y-2">
                      <Pulse className="h-3 w-24" />
                      <Pulse className="h-10 w-full rounded-lg" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Partner field */}
              <div className="space-y-3">
                <Pulse className="h-4 w-36" />
                <div className="rounded-xl border border-gray-100 p-4">
                  <div className="flex items-center gap-3">
                    <Pulse className="w-10 h-10 rounded-lg" />
                    <div className="flex-1 space-y-2">
                      <Pulse className="h-3 w-32" />
                      <Pulse className="h-10 w-full rounded-lg" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Advisors */}
              <div className="space-y-3">
                <Pulse className="h-4 w-40" />
                <div className="rounded-xl border border-gray-100 p-4">
                  <div className="flex items-center gap-3">
                    <Pulse className="w-10 h-10 rounded-lg" />
                    <div className="flex-1 space-y-2">
                      <Pulse className="h-3 w-16" />
                      <Pulse className="h-10 w-full rounded-lg" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="pt-6 border-t border-gray-100 flex gap-3">
                <Pulse className="h-12 w-28 rounded-xl" />
                <Pulse className="h-12 flex-1 rounded-xl" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
