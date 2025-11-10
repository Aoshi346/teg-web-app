// src/components/landing/FeatureCard.tsx

"use client";

import React, { ReactNode, memo } from "react";
import { Card, CardTitle, CardContent } from "@/components/ui/card";

type FeatureCardProps = {
  icon: ReactNode;
  title: string;
  children: ReactNode;
};

// Use the memoized component for export
function FeatureCardImpl({
  icon,
  title,
  children,
}: FeatureCardProps) {
  return (
    <div className="h-full">
      <Card
        className="h-full p-6 flex flex-col items-center text-center
                   bg-white/70 backdrop-blur-lg 
                   border border-slate-200 
                   transition-all duration-300 ease-in-out
                   hover:-translate-y-2 hover:shadow-2xl hover:shadow-indigo-500/10 
                   hover:ring-2 hover:ring-indigo-400 hover:ring-offset-2 hover:ring-offset-slate-50"
      >
        {/* Icon Container */}
        <div
          className="mb-5 flex h-16 w-16 items-center justify-center 
                     rounded-full bg-indigo-100/70 border border-indigo-200/50 shadow-inner"
        >
          {/* Apply text-indigo-600 to the icon itself */}
          <div className="text-indigo-600">{icon}</div>
        </div>

        {/* Text Content */}
        <div className="flex flex-col gap-2">
          <CardTitle className="text-xl font-bold text-gray-900">
            {title}
          </CardTitle>
          <CardContent className="p-0">
            {" "}
            {/* Remove default padding */}
            <p className="text-gray-600 leading-relaxed">{children}</p>
          </CardContent>
        </div>
      </Card>
    </div>
  );
}

// Using memo for performance optimization, preventing re-renders if props haven't changed.
export default memo(FeatureCardImpl);

