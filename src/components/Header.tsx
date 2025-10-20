"use client";

import { LogIn, X } from "lucide-react";
import React, { useState, useEffect, useRef, useLayoutEffect } from "react";
import Link from 'next/link';
import Image from 'next/image';
import { gsap } from 'gsap';
import LoginModal from "@/components/LoginModal";


/**
 * A custom animated menu icon that transitions between a hamburger and an X.
 * It uses GSAP for smooth animations.
 */
const AnimatedMenuIcon = ({ isOpen }: { isOpen: boolean; }) => {
  const iconRef = useRef<SVGSVGElement>(null);
  const tl = useRef<gsap.core.Timeline | null>(null);

  useLayoutEffect(() => {
    if (typeof gsap === 'undefined') return;
    const ctx = gsap.context(() => {
      const top = iconRef.current?.querySelector(".line-top");
      const middle = iconRef.current?.querySelector(".line-middle");
      const bottom = iconRef.current?.querySelector(".line-bottom");

      gsap.set([top, middle, bottom], { transformOrigin: "50% 50%" });

      tl.current = gsap.timeline({ paused: true })
        .to(top!, { y: 6, rotate: 45, duration: 0.3, ease: "power2.inOut" }, 0)
        .to(middle!, { opacity: 0, duration: 0.2, ease: "power2.inOut" }, 0)
        .to(bottom!, { y: -6, rotate: -45, duration: 0.3, ease: "power2.inOut" }, 0);
    }, iconRef);

    return () => ctx.revert();
  }, []);

  useEffect(() => {
    if (isOpen) {
      tl.current?.play();
    } else {
      tl.current?.reverse();
    }
  }, [isOpen]);

  return (
    <svg
      ref={iconRef}
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="overflow-visible"
      aria-hidden="true"
      role="img"
    >
      <line className="line-top" x1="3" y1="6" x2="21" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line className="line-middle" x1="3" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line className="line-bottom" x1="3" y1="18" x2="21" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
};

export default function Header() {
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const componentRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLElement>(null);
  const mobileMenuRef = useRef<HTMLDivElement>(null);
  const mobileMenuTimeline = useRef<gsap.core.Timeline | null>(null);
  
  // We import GSAP directly; no CDN injection required. Keep animations available immediately.
  const gsapLoaded = true;

  // Set up all animations in a useLayoutEffect to prevent flashes of unstyled content
  useLayoutEffect(() => {
    if (!gsapLoaded) return;
    
    const ctx = gsap.context(() => {
      // --- Initial entrance animation for header elements ---
      gsap.from([".logo-anim", ".desktop-btn-anim", ".mobile-btn-anim"], {
        opacity: 0,
        y: -30,
        scale: 0.95,
        duration: 0.6,
        ease: "power3.out",
        stagger: 0.15,
        delay: 0.2,
      });
      
      // --- Mobile menu reveal animation timeline ---
      mobileMenuTimeline.current = gsap.timeline({ paused: true })
        .fromTo(mobileMenuRef.current,
          { clipPath: 'polygon(0% 0%, 100% 0%, 100% 0%, 0% 0%)', visibility: 'hidden' },
          { clipPath: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', visibility: 'visible', duration: 0.4, ease: 'power3.inOut' }
        )
        .from(".mobile-menu-btn-anim", {
          opacity: 0,
          y: 20,
          duration: 0.3,
          ease: 'power3.out'
        }, "-=0.2");

    }, componentRef);

    return () => ctx.revert(); // Cleanup GSAP animations on component unmount
  }, [gsapLoaded]);

  // Effect to control the mobile menu animation based on state
  useEffect(() => {
    if (isMobileMenuOpen) {
      mobileMenuTimeline.current?.play();
    } else {
      mobileMenuTimeline.current?.reverse();
    }
  }, [isMobileMenuOpen]);

  // Centralized body overflow control so the page doesn't get permanently locked when
  // modal or mobile menu unmounts during animations
  useEffect(() => {
    const shouldHide = isMobileMenuOpen || isLoginModalOpen;
    // use explicit 'auto' when not hiding so scrolling works across browsers
    document.body.style.overflow = shouldHide ? 'hidden' : 'auto';
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [isMobileMenuOpen, isLoginModalOpen]);

  // Effect for scroll-based header changes
  useEffect(() => {
    if (!gsapLoaded) return;
    const onScroll = () => {
      if (window.scrollY > 20) {
        gsap.to(headerRef.current, {
          height: 72,
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          duration: 0.3,
          ease: 'power2.out',
        });
      } else {
        gsap.to(headerRef.current, {
          height: 88,
          boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
          backgroundColor: 'rgba(255, 255, 255, 0.85)',
          duration: 0.3,
          ease: 'power2.out',
        });
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, [gsapLoaded]);


  const handleButtonHover = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!gsapLoaded) return;
    gsap.to(e.currentTarget, {
        y: -2,
        scale: 1.02,
        duration: 0.18,
        ease: "power2.out"
    });
  };

  const handleButtonLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!gsapLoaded) return;
    gsap.to(e.currentTarget, {
        y: 0,
        scale: 1,
        duration: 0.18,
        ease: "power2.out"
    });
  };

  const handleButtonClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    // Always open the login modal; play a subtle micro-interaction
    setIsLoginModalOpen(true);
    if (!gsapLoaded) return;
    gsap.fromTo(
      e.currentTarget,
      { scale: 1 },
      { scale: 0.97, duration: 0.08, yoyo: true, repeat: 1, ease: 'power2.inOut' }
    );
  };

  // Ensure body overflow isn't stuck from previous runs
  useEffect(() => {
    document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, []);

  // Smooth-scroll to the features section and optionally close mobile menu
  const handleScrollToFeatures = (e: React.MouseEvent, closeMobile = false) => {
    e.preventDefault();
    const el = document.getElementById('features');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      try {
        // update URL hash without causing an instant jump
        history.replaceState(null, '', '#features');
      } catch {
        // ignore
      }
    }
    if (closeMobile) setIsMobileMenuOpen(false);
  };

  return (
    <>
      <div ref={componentRef}>
        <header
          ref={headerRef}
          className="fixed top-0 z-40 w-full bg-white/85 backdrop-blur-lg shadow-sm"
          style={{ height: 88 }}
        >
          <div className="container mx-auto flex h-full items-center justify-between px-4 sm:px-6 lg:px-8">
            {/* Logo and Brand Name */}
            <Link href="/" className="logo-anim flex items-center gap-2 no-underline" aria-label="TesisFar home">
              <Image
                src="/tesisfar_logo.png"
                alt="TesisFar logo"
                width={48}
                height={48}
                className="object-contain rounded-full"
              />
              <div className="flex flex-col leading-tight">
                <span className="text-xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-blue-500">
                  TesisFar
                </span>
                <span className="block text-xs text-gray-500">
                  Gestión del Trabajo Especial de Grado
                </span>
              </div>
            </Link>

            {/* Desktop Action Button */}
            <nav className="hidden md:flex items-center gap-6">
              <Link href="#features" onClick={(e) => handleScrollToFeatures(e, false)} className="text-sm text-gray-700 hover:text-gray-900">Funciones</Link>
              <Link href="#contact" className="text-sm text-gray-700 hover:text-gray-900">Contacto</Link>
              <div className="desktop-btn-anim">
                <button
                  onMouseEnter={handleButtonHover}
                  onMouseLeave={handleButtonLeave}
                  onClick={handleButtonClick}
                  className="inline-flex items-center gap-3 px-5 py-2.5 text-sm font-semibold text-white
                        bg-gradient-to-r from-indigo-600 to-blue-500 hover:from-indigo-700 hover:to-blue-600
                        rounded-full shadow-md hover:shadow-indigo-500/20
                        focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-500
                        transition-transform duration-200 will-change-transform"
                  aria-label="Ingresar"
                  title="Ingresar"
                >
                  <LogIn className="h-4 w-4" aria-hidden />
                  <span>Ingresar</span>
                </button>
              </div>
            </nav>

            {/* Mobile Menu Button */}
            <div className="md:hidden mobile-btn-anim">
                <button
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  aria-expanded={isMobileMenuOpen}
                  aria-controls="mobile-menu"
                  className="p-2 rounded-full text-gray-700 hover:text-indigo-600 hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-500"
                >
                    <AnimatedMenuIcon isOpen={isMobileMenuOpen} />
                </button>
            </div>
          </div>
        </header>

        {/* Mobile Menu Panel */}
        <div 
          ref={mobileMenuRef} 
          className="md:hidden fixed top-[72px] left-0 w-full h-[calc(100vh-72px)] bg-white/95 backdrop-blur-lg z-30"
          style={{ visibility: 'hidden' }}
        >
          <div className="container mx-auto px-6 pt-6">
            <div className="flex items-center justify-end mb-4">
              <button
                onClick={() => setIsMobileMenuOpen(false)}
                className="p-2 rounded-md text-gray-700 hover:bg-gray-100 focus:outline-none"
                aria-label="Cerrar menú"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <Link href="#features" onClick={(e) => handleScrollToFeatures(e, true)} className="block text-lg font-medium text-gray-800">Funciones</Link>
              <Link href="#contact" className="block text-lg font-medium text-gray-800">Contacto</Link>
            </div>

            <div className="mt-8">
              <button
                onClick={() => { setIsMobileMenuOpen(false); setIsLoginModalOpen(true); }}
                className="w-full inline-flex items-center justify-center gap-3 px-5 py-3 bg-indigo-600 text-white rounded-lg shadow-md"
              >
                <LogIn className="h-4 w-4" />
                Ingresar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Login Modal */}
      <LoginModal 
        isOpen={isLoginModalOpen} 
        onClose={() => setIsLoginModalOpen(false)} 
      />
    </>
  );
}