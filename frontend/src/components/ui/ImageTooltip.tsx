"use client";

import React, { useState, useRef, useCallback } from "react";
import { createPortal } from "react-dom";

interface ImageTooltipProps {
    imageUrl: string;
    title?: string;
    children: React.ReactNode;
}

/**
 * A hover tooltip component that displays an image preview.
 * Uses a portal to render above all other content.
 */
export function ImageTooltip({ imageUrl, title, children }: ImageTooltipProps) {
    const [isVisible, setIsVisible] = useState(false);
    const [position, setPosition] = useState({ top: 0, left: 0 });
    const triggerRef = useRef<HTMLSpanElement>(null);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);

    const showTooltip = useCallback(() => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);

        if (triggerRef.current) {
            const rect = triggerRef.current.getBoundingClientRect();
            const tooltipWidth = 320;
            const tooltipHeight = 240;

            // Calculate position - prefer right side, fallback to left if not enough space
            let left = rect.right + 12;
            if (left + tooltipWidth > window.innerWidth - 20) {
                left = rect.left - tooltipWidth - 12;
            }

            // Vertical centering with bounds checking
            let top = rect.top + (rect.height / 2) - (tooltipHeight / 2);
            if (top < 20) top = 20;
            if (top + tooltipHeight > window.innerHeight - 20) {
                top = window.innerHeight - tooltipHeight - 20;
            }

            setPosition({ top, left });
        }

        setIsVisible(true);
    }, []);

    const hideTooltip = useCallback(() => {
        timeoutRef.current = setTimeout(() => {
            setIsVisible(false);
        }, 150);
    }, []);

    const tooltipContent = isVisible && typeof window !== "undefined" ? (
        createPortal(
            <div
                className="fixed z-[9999] animate-in fade-in zoom-in-95 duration-200"
                style={{ top: position.top, left: position.left }}
                onMouseEnter={() => {
                    if (timeoutRef.current) clearTimeout(timeoutRef.current);
                }}
                onMouseLeave={hideTooltip}
            >
                <div className="w-80 bg-white rounded-xl shadow-2xl overflow-hidden ring-1 ring-gray-200/50">
                    {/* Gradient header */}
                    <div className="px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600">
                        <p className="text-[10px] font-bold text-blue-100 uppercase tracking-widest">
                            📷 Referencia Visual
                        </p>
                        {title && (
                            <p className="text-sm font-bold text-white truncate mt-0.5">
                                {title}
                            </p>
                        )}
                    </div>

                    {/* Image */}
                    <div className="aspect-video bg-gray-100 relative group">
                        <img
                            src={imageUrl}
                            alt={title || "Referencia visual"}
                            className="w-full h-full object-cover"
                            loading="eager"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>

                    {/* Footer hint */}
                    <div className="px-4 py-2.5 bg-gradient-to-r from-gray-50 to-gray-100 border-t border-gray-100">
                        <p className="text-[10px] text-gray-500 text-center font-medium">
                            Ejemplo de cómo debe verse este elemento
                        </p>
                    </div>
                </div>
            </div>,
            document.body
        )
    ) : null;

    return (
        <>
            <span
                ref={triggerRef}
                onMouseEnter={showTooltip}
                onMouseLeave={hideTooltip}
                className="cursor-pointer"
            >
                {children}
            </span>
            {tooltipContent}
        </>
    );
}
