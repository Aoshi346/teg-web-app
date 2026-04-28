import React from "react";
import Header from "@widgets/header/Header";
import Hero from "@features/landing/components/Hero";
import HeroExplainer from "@features/landing/components/HeroExplainer";
import FeaturesSection from "@features/landing/components/FeaturesSection";
import RolesSection from "@features/landing/components/RolesSection";
import LoginCallout from "@features/landing/components/LoginCallout";
import Footer from "@widgets/header/Footer";

export default function Home() {
  return (
    <>
      <Header />
      <main className="bg-white">
        <Hero />
        <HeroExplainer />
        <FeaturesSection />
        <RolesSection />
        <LoginCallout />
      </main>
      <Footer />
    </>
  );
}
