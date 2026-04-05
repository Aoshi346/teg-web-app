"use client";

import React, { ReactNode } from "react";
import { usePathname } from "next/navigation";

interface PageTransitionProps {
  children: ReactNode;
  className?: string;
}

/**
 * CSS-only page transition wrapper.
 *
 * Previously used GSAP which added ~70KB to the dashboard shell critical path
 * and ran a 300ms JS animation on every navigation, making module swaps feel
 * sluggish. This implementation uses a tiny CSS keyframe fade that is
 * GPU-composited and starts on the same frame as the route commit.
 *
 * The `key={pathname}` remount triggers the CSS animation restart on each
 * navigation without any JS work. Total animation time is 180ms so it never
 * blocks perceived responsiveness.
 */
export default function PageTransition({ children, className = "" }: PageTransitionProps) {
  const pathname = usePathname();

  return (
    <div
      key={pathname}
      className={`flex flex-col flex-1 min-h-0 tf-page-enter ${className}`}
    >
      {children}
    </div>
  );
}
