// src/app/Header.tsx

"use client";

import { LogIn, Menu, X } from "lucide-react";
import React, { useState, useEffect, useRef } from "react";
import { gsap } from "gsap";
import LoginModal from "./LoginModal";

export default function Header() {
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const headerRef = useRef<HTMLElement>(null);
  const logoRef = useRef<HTMLAnchorElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (headerRef.current && logoRef.current && buttonRef.current) {
      // Set identical initial states for both elements - NO vertical movement
      gsap.set([logoRef.current, buttonRef.current], { 
        opacity: 0, 
        scale: 0.9
      });
      
      // Create a timeline for synchronized animations
      const tl = gsap.timeline({ delay: 0.1 });
      
      // Animate both elements with identical properties - NO vertical movement
      tl.to([logoRef.current, buttonRef.current], {
        opacity: 1,
        scale: 1,
        duration: 0.8,
        ease: "power2.out",
        stagger: 0.1
      });
    }
  }, []);
  const handleButtonHover = (e: React.MouseEvent<HTMLButtonElement>) => {
    gsap.to(e.currentTarget, {
      scale: 1.05,
      duration: 0.2,
      ease: "power2.out"
    });
  };

  const handleButtonLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
    gsap.to(e.currentTarget, {
      scale: 1,
      duration: 0.2,
      ease: "power2.out"
    });
  };

  const handleButtonClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    gsap.to(e.currentTarget, {
      scale: 0.95,
      duration: 0.1,
      yoyo: true,
      repeat: 1,
      ease: "power2.inOut",
      onComplete: () => setIsLoginModalOpen(true)
    });
  };

  return (
    <>
      <header
        ref={headerRef}
        className="sticky top-0 z-40 w-full bg-white/95 backdrop-blur-xl border-b border-slate-200/50 shadow-sm"
      >
        <div className="container mx-auto flex h-20 items-center justify-between px-4">
          {/* Logo and Brand Name */}
          <a
            ref={logoRef}
            href="/"
            className="flex items-center gap-4 no-underline"
            aria-label="EVTEG home"
          >
            <div className="flex-shrink-0 rounded-full bg-white p-1.5 shadow-md">
              <img
                src="/usmlogo.png"
                alt="EVTEG logo"
                className="h-12 w-12 object-contain rounded-full"
              />
            </div>

            <div className="flex flex-col leading-tight">
              <span className="text-2xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-blue-500">
                EVTEG
              </span>
              <span className="block text-sm text-gray-500">
                Gestión del Trabajo Especial de Grado
              </span>
            </div>
          </a>

          {/* Desktop Action Button */}
          <div className="hidden md:flex items-center">
            <button
              ref={buttonRef}
              onMouseEnter={handleButtonHover}
              onMouseLeave={handleButtonLeave}
              onClick={handleButtonClick}
              className="inline-flex items-center gap-2 px-6 py-3 text-white text-sm font-medium
                    bg-indigo-600 hover:bg-indigo-700
                    rounded-lg shadow-md hover:shadow-lg
                    focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-300
                    transition-all duration-200"
              aria-label="Ingresar"
              title="Ingresar"
            >
              <LogIn className="h-4 w-4" aria-hidden />
              Ingresar
            </button>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200/50 bg-white/95 backdrop-blur-xl">
            <div className="px-4 py-4">
              <button
                onClick={() => {
                  setIsMobileMenuOpen(false);
                  setIsLoginModalOpen(true);
                }}
                className="w-full inline-flex items-center justify-center gap-2 px-6 py-3 text-white text-sm font-medium
                      bg-indigo-600 hover:bg-indigo-700
                      rounded-lg shadow-md hover:shadow-lg
                      transition-all duration-200"
              >
                <LogIn className="h-4 w-4" />
                Ingresar
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Login Modal */}
      <LoginModal 
        isOpen={isLoginModalOpen} 
        onClose={() => setIsLoginModalOpen(false)} 
      />
    </>
  );
}
