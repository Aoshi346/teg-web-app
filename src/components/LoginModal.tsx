"use client";

import React, { useState, useEffect, useRef } from "react";
import { gsap } from "gsap";
import { X, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const modalRef = useRef<HTMLDivElement>(null);
  const backdropRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLDivElement>(null);
  const loginFormRef = useRef<HTMLDivElement>(null);
  const registerFormRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      // Set initial states
      gsap.set([modalRef.current, backdropRef.current], { opacity: 0 });
      gsap.set(modalRef.current, { scale: 0.8, y: 50 });
      gsap.set([formRef.current, imageRef.current], { opacity: 0, y: 30 });

      // Create timeline for entrance animation
      const tl = gsap.timeline();
      
      tl.to(backdropRef.current, {
        opacity: 1,
        duration: 0.3,
        ease: "power2.out"
      })
      .to(modalRef.current, {
        opacity: 1,
        scale: 1,
        y: 0,
        duration: 0.4,
        ease: "back.out(1.7)"
      }, "-=0.2")
      .to([formRef.current, imageRef.current], {
        opacity: 1,
        y: 0,
        duration: 0.5,
        stagger: 0.1,
        ease: "power2.out"
      }, "-=0.3");
    }
  }, [isOpen]);

  const handleClose = () => {
    if (modalRef.current && backdropRef.current) {
      const tl = gsap.timeline({
        onComplete: onClose
      });
      
      tl.to([formRef.current, imageRef.current], {
        opacity: 0,
        y: -30,
        duration: 0.2,
        stagger: 0.05,
        ease: "power2.in"
      })
      .to(modalRef.current, {
        opacity: 0,
        scale: 0.8,
        y: 50,
        duration: 0.3,
        ease: "power2.in"
      }, "-=0.1")
      .to(backdropRef.current, {
        opacity: 0,
        duration: 0.2,
        ease: "power2.in"
      }, "-=0.2");
    }
  };

  const switchFormMode = () => {
    const currentForm = isLoginMode ? loginFormRef.current : registerFormRef.current;
    const nextForm = isLoginMode ? registerFormRef.current : loginFormRef.current;
    
    if (currentForm && nextForm) {
      const tl = gsap.timeline();
      
      // Slide out current form
      tl.to(currentForm, {
        x: isLoginMode ? -50 : 50,
        opacity: 0,
        duration: 0.3,
        ease: "power2.in"
      })
      // Set next form initial position
      .set(nextForm, {
        x: isLoginMode ? 50 : -50,
        opacity: 0
      })
      // Slide in next form
      .to(nextForm, {
        x: 0,
        opacity: 1,
        duration: 0.3,
        ease: "power2.out"
      });
      
      setIsLoginMode(!isLoginMode);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Add button animation on submit
    const submitButton = e.currentTarget.querySelector('button[type="submit"]');
    if (submitButton) {
      gsap.to(submitButton, {
        scale: 0.95,
        duration: 0.1,
        yoyo: true,
        repeat: 1,
        ease: "power2.inOut"
      });
    }
    
    if (isLoginMode) {
      console.log("Login attempt:", { email, password, rememberMe });
    } else {
      if (password !== confirmPassword) {
        alert("Passwords do not match!");
        return;
      }
      console.log("Register attempt:", { fullName, email, password });
    }
  };

  const handleInputFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    gsap.to(e.target, {
      scale: 1.02,
      duration: 0.2,
      ease: "power2.out"
    });
  };

  const handleInputBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    gsap.to(e.target, {
      scale: 1,
      duration: 0.2,
      ease: "power2.out"
    });
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        ref={backdropRef}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div
        ref={modalRef}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl h-[600px] flex overflow-hidden">
          {/* Left Section - Forms */}
          <div ref={formRef} className="flex-1 p-8 flex flex-col justify-center relative overflow-hidden">
            {/* Close Button */}
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors z-10"
              onMouseEnter={(e) => {
                gsap.to(e.currentTarget, {
                  scale: 1.1,
                  rotation: 90,
                  duration: 0.2,
                  ease: "power2.out"
                });
              }}
              onMouseLeave={(e) => {
                gsap.to(e.currentTarget, {
                  scale: 1,
                  rotation: 0,
                  duration: 0.2,
                  ease: "power2.out"
                });
              }}
            >
              <X className="h-6 w-6" />
            </button>

            {/* Login Form */}
            <div ref={loginFormRef} className={`absolute inset-0 p-8 flex flex-col justify-center ${isLoginMode ? 'block' : 'hidden'}`}>
              {/* Title */}
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-black uppercase tracking-wide">
                  SIGN IN
                </h2>
                <div className="w-12 h-0.5 bg-yellow-400 mt-2"></div>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Email Field */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-black uppercase">
                    E-MAIL ADDRESS<span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onFocus={handleInputFocus}
                    onBlur={handleInputBlur}
                    placeholder="enter your email address"
                    className="w-full h-12 border-gray-300 focus:border-black focus:ring-black"
                    required
                  />
                </div>

                {/* Password Field */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-black uppercase">
                    PASSWORD<span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onFocus={handleInputFocus}
                      onBlur={handleInputBlur}
                      className="w-full h-12 border-gray-300 focus:border-black focus:ring-black pr-12"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                {/* Remember Me & Forgot Password */}
                <div className="flex items-center justify-between">
                  <label className="flex items-center space-x-2 text-gray-600">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 text-black border-gray-300 rounded focus:ring-black"
                    />
                    <span className="text-sm">Remember me!</span>
                  </label>
                  <button
                    type="button"
                    className="text-orange-500 hover:text-orange-600 text-sm font-medium"
                  >
                    Forgot password?
                  </button>
                </div>

                {/* Sign In Button */}
                <Button
                  type="submit"
                  className="w-full h-12 bg-black text-white hover:bg-gray-800 font-medium uppercase tracking-wide"
                >
                  SIGN IN
                </Button>

                {/* Switch to Register */}
                <div className="text-center">
                  <button
                    type="button"
                    onClick={switchFormMode}
                    className="text-gray-600 hover:text-black text-sm font-medium"
                  >
                    Don't have an account? <span className="text-orange-500 hover:text-orange-600">Register here</span>
                  </button>
                </div>
              </form>
            </div>

            {/* Register Form */}
            <div ref={registerFormRef} className={`absolute inset-0 p-8 flex flex-col justify-center ${!isLoginMode ? 'block' : 'hidden'}`}>
              {/* Title */}
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-black uppercase tracking-wide">
                  REGISTER
                </h2>
                <div className="w-12 h-0.5 bg-yellow-400 mt-2"></div>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Full Name Field */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-black uppercase">
                    FULL NAME<span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    onFocus={handleInputFocus}
                    onBlur={handleInputBlur}
                    placeholder="enter your full name"
                    className="w-full h-12 border-gray-300 focus:border-black focus:ring-black"
                    required
                  />
                </div>

                {/* Email Field */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-black uppercase">
                    E-MAIL ADDRESS<span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onFocus={handleInputFocus}
                    onBlur={handleInputBlur}
                    placeholder="enter your email address"
                    className="w-full h-12 border-gray-300 focus:border-black focus:ring-black"
                    required
                  />
                </div>

                {/* Password Field */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-black uppercase">
                    PASSWORD<span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onFocus={handleInputFocus}
                      onBlur={handleInputBlur}
                      className="w-full h-12 border-gray-300 focus:border-black focus:ring-black pr-12"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                {/* Confirm Password Field */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-black uppercase">
                    CONFIRM PASSWORD<span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Input
                      type={showConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      onFocus={handleInputFocus}
                      onBlur={handleInputBlur}
                      className="w-full h-12 border-gray-300 focus:border-black focus:ring-black pr-12"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                {/* Register Button */}
                <Button
                  type="submit"
                  className="w-full h-12 bg-black text-white hover:bg-gray-800 font-medium uppercase tracking-wide"
                >
                  REGISTER
                </Button>

                {/* Switch to Login */}
                <div className="text-center">
                  <button
                    type="button"
                    onClick={switchFormMode}
                    className="text-gray-600 hover:text-black text-sm font-medium"
                  >
                    Already have an account? <span className="text-orange-500 hover:text-orange-600">Sign in here</span>
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Right Section - Promotional Image */}
          <div ref={imageRef} className="flex-1 relative">
                <div
                  className="w-full h-full bg-cover bg-center bg-no-repeat"
                  style={{
                    backgroundImage: "url('/usm_hero.jpg')",
                  }}
                >
                  {/* Overlay */}
                  <div className="absolute inset-0 bg-black/40"></div>
                  
                  {/* Text Overlays */}
                  <div className="absolute inset-0 flex flex-col justify-center items-center text-white p-8">
                    <h3 className="text-4xl font-bold uppercase tracking-wider mb-2">
                      MENS WEAR
                    </h3>
                    <h4 className="text-4xl font-bold uppercase tracking-wider mb-4 text-yellow-400">
                      FAS
                    </h4>
                    <p className="text-lg uppercase tracking-wide text-center">
                      SUITS & COATS FOR MEN
                    </p>
                  </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

