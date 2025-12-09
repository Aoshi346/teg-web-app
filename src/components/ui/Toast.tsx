"use client";

import React, { useEffect, useState, useCallback } from "react";
import { X, CheckCircle, AlertTriangle, Info } from "lucide-react";

type ToastProps = {
  visible: boolean;
  message: string;
  type?: "error" | "success" | "info";
  duration?: number; // ms
  onClose: () => void; // onClose is required to handle component unmounting after animations.
};

const typeStyles = {
  success: {
    icon: <CheckCircle className="w-6 h-6 text-green-500" />,
    barClass: "bg-green-500",
    name: "Success",
  },
  error: {
    icon: <AlertTriangle className="w-6 h-6 text-red-500" />,
    barClass: "bg-red-500",
    name: "Error",
  },
  info: {
    icon: <Info className="w-6 h-6 text-blue-500" />,
    barClass: "bg-blue-500",
    name: "Information",
  },
};

export default function Toast({ visible, message, type = "info", duration = 4000, onClose }: ToastProps) {
  const [isExiting, setIsExiting] = useState(false);

  const handleClose = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      onClose();
      setIsExiting(false);
    }, 300); // Animation duration
  }, [onClose]);

  useEffect(() => {
    if (visible) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [visible, duration, handleClose]);

  if (!visible && !isExiting) {
    return null;
  }

  const { icon, barClass, name } = typeStyles[type];
  
  const animationClasses = visible && !isExiting
    ? "translate-x-0 opacity-100"
    : "translate-x-full opacity-0";

  return (
    <div
      className={`fixed top-6 right-6 z-[9999] w-full max-w-sm bg-white rounded-lg shadow-2xl pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden transform transition-all duration-300 ease-in-out ${animationClasses}`}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="relative">
        <div className="p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">{icon}</div>
            <div className="ml-3 w-0 flex-1 pt-0.5">
              <p className="text-sm font-semibold text-gray-900">{name}</p>
              <p className="mt-1 text-sm text-gray-600">
                {message}
              </p>
            </div>
            <div className="ml-4 flex-shrink-0 flex">
              <button
                onClick={handleClose}
                className="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <span className="sr-only">Close</span>
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
        {!isExiting && (
          <div className="absolute bottom-0 left-0 h-1 w-full bg-gray-200">
            <div
              className={`h-1 ${barClass}`}
              style={{ animation: `shrink-width ${duration}ms linear forwards` }}
            />
          </div>
        )}
      </div>
       <style jsx>{`
        @keyframes shrink-width {
          from {
            width: 100%;
          }
          to {
            width: 0%;
          }
        }
      `}</style>
    </div>
  );
}