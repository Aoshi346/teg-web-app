// src/components/landing/FeatureCard.tsx

"use client";

import React, { ReactNode, memo } from "react";

type FeatureCardProps = {
  icon: ReactNode;
  title: string;
  children: ReactNode;
  accentColor?: string;
};

function FeatureCardImpl({
  icon,
  title,
  children,
  accentColor = "usm-blue",
}: FeatureCardProps) {
  const isOrange = accentColor === "usm-orange";

  // Per-accent color scheme — each card gets a colorful tinted background
  const cardBg = isOrange
    ? "bg-gradient-to-br from-orange-50 to-amber-50/60"
    : "bg-gradient-to-br from-blue-50 to-sky-50/60";
  const borderColor = isOrange
    ? "border-usm-orange/15 hover:border-usm-orange/30"
    : "border-usm-blue/15 hover:border-usm-blue/30";
  const iconBg = isOrange
    ? "bg-gradient-to-br from-usm-orange to-orange-400"
    : "bg-gradient-to-br from-usm-blue to-blue-400";
  const titleHover = isOrange
    ? "group-hover:text-usm-orange"
    : "group-hover:text-usm-blue";
  const accentLine = isOrange
    ? "from-usm-orange to-orange-400"
    : "from-usm-blue to-blue-400";

  return (
    <div className="h-full">
      <div
        className={`h-full relative ${cardBg} border ${borderColor} rounded-2xl overflow-hidden
                   shadow-sm hover:shadow-lg transition-all duration-300 ease-out group`}
      >
        {/* Top accent bar */}
        <div className={`w-full h-1 bg-gradient-to-r ${accentLine}`} />

        <div className="p-6 flex flex-col h-full">
          {/* Icon — white icon on colored pill */}
          <div className="mb-5">
            <div
              className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${iconBg}
                         shadow-md transition-transform duration-300 group-hover:scale-105 group-hover:-translate-y-0.5`}
            >
              <div className="text-white">{icon}</div>
            </div>
          </div>

          {/* Title */}
          <h3
            className={`text-lg font-bold text-usm-navy mb-2 leading-snug transition-colors duration-300 ${titleHover}`}
          >
            {title}
          </h3>

          {/* Small accent line */}
          <div className="mb-3">
            <div
              className={`h-0.5 w-8 bg-gradient-to-r ${accentLine} rounded-full transition-all duration-300 group-hover:w-12`}
            />
          </div>

          {/* Description */}
          <p className="text-gray-500 leading-relaxed text-[0.9rem] flex-1">
            {children}
          </p>
        </div>
      </div>
    </div>
  );
}

export default memo(FeatureCardImpl);
