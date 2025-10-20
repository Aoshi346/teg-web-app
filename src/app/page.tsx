"use client";

import Header from "@/components/Header";
import Hero from "@/components/Hero";
import FeaturesSection from "@/components/FeaturesSection";
import Footer from "@/components/Footer";
import React, { useEffect, useState } from "react";

export default function Home() {
  const [debugOn, setDebugOn] = useState(false);

  useEffect(() => {
    // Force body overflow to auto to ensure page can scroll (debug helper)
    document.body.style.overflow = 'auto';

    const log = () => {
      // Log helpful diagnostic info to the console
      console.log('DEBUG: body.overflow=', document.body.style.overflow,
        'doc.scrollHeight=', document.documentElement.scrollHeight,
        'vw=', window.innerWidth, 'vh=', window.innerHeight);
    };

    log();
    window.addEventListener('resize', log);
    return () => window.removeEventListener('resize', log);
  }, []);

  useEffect(() => {
    if (debugOn) document.body.classList.add('outline-debug');
    else document.body.classList.remove('outline-debug');
  }, [debugOn]);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Header />
      <main className="flex-1 overflow-y-auto">
        <Hero />
        <FeaturesSection />
      </main>
      <Footer />

      {/* Debug toggle - will not render in production if you remove it later */}
      <button
        onClick={() => setDebugOn((s) => !s)}
        title="Toggle debug outlines"
        className="fixed right-4 bottom-4 z-50 rounded-full bg-indigo-600 text-white px-3 py-2 text-xs shadow-lg"
      >
        Debug Outlines
      </button>
    </div>
  );
}
