// src/components/FeatureCard.tsx

"use client";

import React, { ReactNode, memo } from "react";
import { motion, useReducedMotion, Variants } from "framer-motion";
import { Card, CardTitle, CardContent } from "@/components/ui/card";

type FeatureCardProps = {
  icon: ReactNode;
  title: string;
  children: ReactNode;
  delay?: number;
};

// Use the memoized component for export
function FeatureCardImpl({
  icon,
  title,
  children,
  delay = 0,
}: FeatureCardProps) {
  const reduceMotion = useReducedMotion();

  // Explicitly type variants for better TypeScript inference and safety
  const cardVariants: Variants = reduceMotion
    ? { offscreen: { opacity: 1 }, onscreen: { opacity: 1 } } // Simplified variant for reduced motion
    : {
        offscreen: { y: 40, opacity: 0 },
        onscreen: {
          y: 0,
          opacity: 1,
          transition: {
            type: "spring",
            stiffness: 100,
            damping: 20,
            delay,
          },
        },
      };

  return (
    <motion.div variants={cardVariants} className="h-full">
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
    </motion.div>
  );
}

// Using memo for performance optimization, preventing re-renders if props haven't changed.
export default memo(FeatureCardImpl);
