"use client";

import React from "react";

export default function PlanificacionLoading() {
  return (
    <div className="flex-1 bg-gray-50 animate-pulse">
      {/* Header skeleton */}
      <div className="h-14 bg-white border-b border-gray-200/60" />

      <main className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          {/* Title row */}
          <div className="mb-10 flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div className="space-y-2">
              <div className="h-9 w-72 rounded-xl bg-gray-200" />
              <div className="h-4 w-80 rounded bg-gray-100" />
            </div>
            <div className="h-10 w-40 rounded-xl bg-gray-200" />
          </div>

          {/* Overview calendar skeleton */}
          <div className="bg-white/60 rounded-[2rem] border border-gray-200/60 shadow-xl shadow-slate-200/40 p-5 sm:p-6 mb-8">
            <div className="h-7 w-56 rounded-lg bg-gray-200 mb-2" />
            <div className="h-4 w-64 rounded bg-gray-100 mb-6" />
            <div className="flex items-center justify-between mb-4">
              <div className="w-8 h-8 rounded-lg bg-gray-200" />
              <div className="h-6 w-32 rounded bg-gray-200" />
              <div className="w-8 h-8 rounded-lg bg-gray-200" />
            </div>
            <div className="grid grid-cols-7 gap-2">
              {Array.from({ length: 35 }).map((_, i) => (
                <div key={i} className="h-16 rounded-xl bg-gray-100" />
              ))}
            </div>
          </div>

          {/* 12-col grid skeleton */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
            {/* Editor calendar skeleton */}
            <div className="xl:col-span-7">
              <div className="bg-white rounded-2xl border border-gray-200/60 shadow-xl shadow-slate-200/40 p-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-8 h-8 rounded-lg bg-gray-200" />
                  <div className="h-7 w-40 rounded-lg bg-gray-200" />
                  <div className="w-8 h-8 rounded-lg bg-gray-200" />
                </div>
                <div className="grid grid-cols-7 gap-2">
                  {Array.from({ length: 35 }).map((_, i) => (
                    <div key={i} className="h-16 rounded-xl bg-gray-100" />
                  ))}
                </div>
                <div className="mt-4 h-12 rounded-xl bg-gray-200" />
              </div>
            </div>

            {/* Day cards skeleton */}
            <div className="xl:col-span-5 space-y-6">
              {[1, 2, 3].map((n) => (
                <div
                  key={n}
                  className="bg-white rounded-2xl border border-gray-200/60 shadow-xl shadow-slate-200/40 p-5 sm:p-6"
                >
                  <div className="flex items-center gap-4 mb-4">
                    <div className="space-y-2 flex-1">
                      <div className="h-7 w-12 rounded bg-gray-200" />
                      <div className="h-4 w-24 rounded bg-gray-100" />
                    </div>
                  </div>
                  <div className="h-px bg-gray-200 mb-4" />
                  <div className="space-y-3">
                    <div className="h-16 rounded-lg bg-gray-50" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
