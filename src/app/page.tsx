import React from "react";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import FeaturesSection from "@/components/FeaturesSection";
import Footer from "@/components/Footer";

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
