import React from "react";
import Header from "@/components/layout/Header";
import Hero from "@/components/landing/Hero";
import FeaturesSection from "@/components/landing/FeaturesSection";
import Footer from "@/components/layout/Footer";

export default function Home() {
  return (
    <>
      <Header />
      <main className="bg-white">
        <Hero />
        <FeaturesSection />
      </main>
      <Footer />
    </>
  );
}
