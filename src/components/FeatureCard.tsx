"use client";

import React, { ReactNode, memo } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

type FeatureCardProps = {
  icon: ReactNode;
  title: string;
  children: ReactNode;
  delay?: number;
};

function FeatureCardImpl({
  icon,
  title,
  children,
  delay = 0,
}: FeatureCardProps) {
  const reduceMotion = useReducedMotion();

  const cardVariants = reduceMotion
    ? { offscreen: { y: 0, opacity: 1 }, onscreen: { y: 0, opacity: 1 } }
    : {
        offscreen: { y: 30, opacity: 0 },
        onscreen: {
          y: 0,
          opacity: 1,
          transition: { stiffness: 90, damping: 18, delay, duration: 0.6 },
        },
      };

  return (
    <motion.div variants={cardVariants} className="h-full">
      <Card className="h-full flex flex-col justify-between transition-transform duration-300 hover:-translate-y-2 hover:shadow-2xl bg-white/60 border border-slate-200 hover:border-indigo-300 p-6">
        <div className="flex flex-col items-center text-center">
          <div className="mb-4 rounded-full bg-indigo-50 p-5 text-indigo-600 shadow-inner flex items-center justify-center w-16 h-16">
            {icon}
          </div>
          <CardTitle className="text-xl font-semibold text-gray-800 mb-3">
            {title}
          </CardTitle>
          <CardContent>
            <p className="text-center text-gray-600 leading-relaxed">
              {children}
            </p>
          </CardContent>
        </div>
      </Card>
    </motion.div>
  );
}

export default memo(FeatureCardImpl);
