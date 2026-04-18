"use client";

import React, { ReactNode, memo, useRef, useState, useCallback, useEffect } from "react";

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
  const cardRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [isTouch, setIsTouch] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setIsTouch(window.matchMedia("(hover: none)").matches);
    }
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (isTouch || !cardRef.current) return;

    const rect = cardRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const mouseX = e.clientX;
    const mouseY = e.clientY;

    const rotateX = ((mouseY - centerY) / (rect.height / 2)) * -12;
    const rotateY = ((mouseX - centerX) / (rect.width / 2)) * 12;

    setTilt({
      x: Math.max(-12, Math.min(12, rotateX)),
      y: Math.max(-12, Math.min(12, rotateY)),
    });
  }, [isTouch]);

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    setTilt({ x: 0, y: 0 });
  }, []);

  const cardBg = isOrange
    ? "glass-card-orange"
    : "glass-card-blue";
  const borderClass = isOrange
    ? "corner-border-card is-orange"
    : "corner-border-card";
  const iconBg = isOrange
    ? "bg-gradient-to-br from-usm-orange to-orange-400"
    : "bg-gradient-to-br from-usm-blue to-blue-400";

  return (
    <div className="tilt-perspective">
      <div
        ref={cardRef}
        className={`h-full ${borderClass} ${cardBg} rounded-2xl overflow-hidden cursor-pointer
                   transition-shadow duration-300 ease-out tilt-card-3d`}
        style={{
          transform: !isTouch ? `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)` : undefined,
        }}
        onMouseMove={handleMouseMove}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div className="tilt-inner p-6 flex flex-col h-full relative z-10">
          {/* Icon */}
          <div className="mb-5">
            <div
              className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${iconBg}
                         shadow-md transition-transform duration-300 ${isHovered ? 'scale-110 -translate-y-0.5' : ''}`}
            >
              <div className="text-white">{icon}</div>
            </div>
          </div>

          {/* Title */}
          <h3 className="text-lg font-bold text-usm-navy mb-3 leading-snug">
            {title}
          </h3>

          {/* Accent line */}
          <div className="mb-4">
            <div
              className={`h-0.5 w-10 bg-gradient-to-r ${isOrange ? "from-usm-orange to-orange-400" : "from-usm-blue to-blue-400"} rounded-full transition-all duration-300 ${isHovered ? 'w-14' : ''}`}
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
