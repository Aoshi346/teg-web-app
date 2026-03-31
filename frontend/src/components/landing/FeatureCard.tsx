// src/components/landing/FeatureCard.tsx

"use client";

import React, { ReactNode, memo } from "react";
import { Card, CardTitle, CardContent } from "@/components/ui/card";

type FeatureCardProps = {
  icon: ReactNode;
  title: string;
  children: ReactNode;
  accentColor?: string;
};

// Use the memoized component for export
function FeatureCardImpl({ icon, title, children, accentColor = "usm-blue" }: FeatureCardProps) {
  const gradientFrom = accentColor === "usm-orange" ? "from-usm-orange" : "from-usm-blue";
  const gradientTo = accentColor === "usm-orange" ? "to-orange-400" : "to-blue-400";
  const iconBg = accentColor === "usm-orange" ? "bg-gradient-to-br from-usm-orange/15 to-orange-400/10" : "bg-gradient-to-br from-usm-blue/15 to-blue-400/10";
  const iconBorder = accentColor === "usm-orange" ? "border-usm-orange/20" : "border-usm-blue/20";
  const iconHoverBg = accentColor === "usm-orange" ? "group-hover:from-usm-orange/25 group-hover:to-orange-400/15" : "group-hover:from-usm-blue/25 group-hover:to-blue-400/15";
  const iconColor = accentColor === "usm-orange" ? "text-usm-orange" : "text-usm-blue";

  return (
    <div className="h-full">
      <Card
        className={`h-full p-0 flex flex-col items-center text-center
                   bg-white border border-slate-200/60 shadow-lg rounded-2xl
                   transition-all duration-300 ease-out
                   hover:-translate-y-2 hover:shadow-2xl
                   hover:border-slate-300/80 group cursor-pointer
                   gradient-border-top card-shine overflow-hidden`}
      >
        {/* Colored accent stripe at top */}
        <div className={`w-full h-1 bg-gradient-to-r ${gradientFrom} ${gradientTo}`} />

        <div className="p-6 pt-5 flex flex-col items-center">
          {/* Icon Container */}
          <div
            className={`mb-5 flex h-16 w-16 items-center justify-center 
                       rounded-2xl ${iconBg} border ${iconBorder} shadow-sm
                       transition-all duration-300 ${iconHoverBg}
                       group-hover:shadow-md group-hover:scale-110`}
          >
            {/* Apply accent color to the icon itself */}
            <div className={`${iconColor} transition-all duration-300 group-hover:scale-110`}>
              {icon}
            </div>
          </div>

          {/* Text Content */}
          <div className="flex flex-col gap-2.5">
            <CardTitle className="text-xl font-bold text-usm-navy transition-colors duration-300 group-hover:text-usm-blue">
              {title}
            </CardTitle>
            <CardContent className="p-0">
              <p className="text-gray-500 leading-relaxed text-[0.938rem] transition-colors duration-300 group-hover:text-gray-600">
                {children}
              </p>
            </CardContent>
          </div>
        </div>
      </Card>
    </div>
  );
}

// Using memo for performance optimization, preventing re-renders if props haven't changed.
export default memo(FeatureCardImpl);
