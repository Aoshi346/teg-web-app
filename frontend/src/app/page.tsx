import React from "react";
import Header from "@widgets/header/Header";
import Hero from "@features/landing/components/Hero";
import FeaturesSection from "@features/landing/components/FeaturesSection";
import Footer from "@widgets/header/Footer";

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
