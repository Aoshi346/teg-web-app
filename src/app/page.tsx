"use client";

import React, { ReactNode, memo } from "react";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import FeaturesSection from "@/components/FeaturesSection";
import Footer from "@/components/Footer";
import { motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Twitter,
  Linkedin,
  Facebook,
  BookOpen,
  Users,
  ClipboardCheck,
  LayoutDashboard,
  MessageSquare,
  GraduationCap,
  ArrowDown,
} from "lucide-react";

// -------------------- Motion Variants --------------------
const fadeInUp = (delay = 0) => ({
  offscreen: { y: 30, opacity: 0 },
  onscreen: {
    y: 0,
    opacity: 1,
    transition: { delay, duration: 0.6, ease: "easeOut" },
  },
});

// -------------------- FeatureCard --------------------
type FeatureCardProps = {
  icon: ReactNode;
  title: string;
  children: ReactNode;
  delay?: number;
};

function FeatureCardImpl({ icon, title, children, delay = 0 }: FeatureCardProps) {
  const reduceMotion = useReducedMotion();
  const variants = reduceMotion ? {} : fadeInUp(delay);

  return (
    <motion.div variants={variants}>
      <Card className="h-full transform transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl bg-white/60 border border-slate-200 hover:border-indigo-300">
        <CardHeader className="flex flex-col items-center text-center">
          <div
            className="mb-4 rounded-full bg-indigo-100 p-4 text-indigo-600 shadow-inner"
            aria-hidden="true"
          >
            {icon}
          </div>
          <CardTitle className="text-xl font-bold text-gray-800">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-gray-600">{children}</p>
        </CardContent>
      </Card>
    </motion.div>
  );
}
const FeatureCard = memo(FeatureCardImpl);

// -------------------- Data --------------------
const studentFeatures = [
  {
    title: "Track Assignments",
    icon: <ClipboardCheck size={32} aria-hidden="true" />,
    text: "Never miss a deadline. View all your assignments and due dates in one place.",
    delay: 0.1,
  },
  {
    title: "Collaborate on Projects",
    icon: <Users size={32} aria-hidden="true" />,
    text: "Work together with classmates in real-time, share files, and track progress effortlessly.",
    delay: 0.2,
  },
  {
    title: "Access Resources",
    icon: <BookOpen size={32} aria-hidden="true" />,
    text: "Find all your course materials, lecture notes, and important links organized for you.",
    delay: 0.3,
  },
];

const teacherFeatures = [
  {
    title: "Manage Courses",
    icon: <LayoutDashboard size={32} aria-hidden="true" />,
    text: "Organize your curriculum, upload materials, and manage student enrollment with ease.",
    delay: 0.1,
  },
  {
    title: "Grade Submissions",
    icon: <GraduationCap size={32} aria-hidden="true" />,
    text: "Provide timely feedback with our intuitive grading interface and track student performance.",
    delay: 0.2,
  },
  {
    title: "Communicate Effectively",
    icon: <MessageSquare size={32} aria-hidden="true" />,
    text: "Send announcements, chat with students, and foster a collaborative learning environment.",
    delay: 0.3,
  },
];

// -------------------- Page --------------------
  export default function Home() {
    return (
      <div className="flex min-h-screen flex-col bg-slate-50">
        <Header />
        <main className="flex-1">
          <Hero />
          <FeaturesSection />
          {/* Teacher section can be added as another component later */}
        </main>
        <Footer />
      </div>
    );
  }
