"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { X, Eye, EyeOff, Mail, Lock, User, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Toast from "@/components/ui/Toast";
import LoginLoading from "@/components/ui/LoginLoading";
import {
  login as demoLogin,
  register as demoRegister,
} from "@/features/auth/clientAuth";
import { useRouter } from "next/navigation";
import { gsap } from "gsap";

// --- Animated Canvas Background with floating geometric shapes ---
const BrandCanvas = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let width = 0;
    let height = 0;

    const colors = {
      blue: "rgba(0, 102, 255, 0.5)",
      blueFaint: "rgba(0, 102, 255, 0.12)",
      orange: "rgba(255, 107, 53, 0.45)",
      orangeFaint: "rgba(255, 107, 53, 0.10)",
      yellow: "rgba(255, 210, 63, 0.35)",
      white: "rgba(255, 255, 255, 0.15)",
      whiteLine: "rgba(255, 255, 255, 0.06)",
    };

    type Shape = {
      x: number;
      y: number;
      size: number;
      type: "circle" | "ring" | "square" | "triangle" | "dot" | "cross";
      color: string;
      vx: number;
      vy: number;
      rotation: number;
      rotSpeed: number;
      pulsePhase: number;
      pulseSpeed: number;
      opacity: number;
    };

    const shapes: Shape[] = [];
    const shapeCount = 28;
    const connectDist = 120;

    const resize = () => {
      const rect = canvas.parentElement!.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = width * window.devicePixelRatio;
      canvas.height = height * window.devicePixelRatio;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    };

    const createShape = (): Shape => {
      const typeRoll = Math.random();
      let type: Shape["type"];
      if (typeRoll < 0.2) type = "circle";
      else if (typeRoll < 0.35) type = "ring";
      else if (typeRoll < 0.5) type = "square";
      else if (typeRoll < 0.65) type = "triangle";
      else if (typeRoll < 0.85) type = "dot";
      else type = "cross";

      const colorPick = [colors.blue, colors.orange, colors.yellow, colors.white];
      return {
        x: Math.random() * width,
        y: Math.random() * height,
        size: type === "dot" ? 2 + Math.random() * 3 : 6 + Math.random() * 14,
        type,
        color: colorPick[Math.floor(Math.random() * colorPick.length)],
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        rotation: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 0.008,
        pulsePhase: Math.random() * Math.PI * 2,
        pulseSpeed: 0.01 + Math.random() * 0.02,
        opacity: 0.4 + Math.random() * 0.6,
      };
    };

    const init = () => {
      resize();
      shapes.length = 0;
      for (let i = 0; i < shapeCount; i++) {
        shapes.push(createShape());
      }
    };

    const drawShape = (s: Shape, pulse: number) => {
      ctx.save();
      ctx.translate(s.x, s.y);
      ctx.rotate(s.rotation);
      ctx.globalAlpha = s.opacity * (0.7 + pulse * 0.3);

      const sz = s.size * (0.9 + pulse * 0.1);

      switch (s.type) {
        case "circle":
          ctx.fillStyle = s.color;
          ctx.beginPath();
          ctx.arc(0, 0, sz, 0, Math.PI * 2);
          ctx.fill();
          break;
        case "ring":
          ctx.strokeStyle = s.color;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(0, 0, sz, 0, Math.PI * 2);
          ctx.stroke();
          break;
        case "square":
          ctx.fillStyle = s.color;
          ctx.fillRect(-sz / 2, -sz / 2, sz, sz);
          break;
        case "triangle":
          ctx.fillStyle = s.color;
          ctx.beginPath();
          ctx.moveTo(0, -sz);
          ctx.lineTo(sz * 0.866, sz * 0.5);
          ctx.lineTo(-sz * 0.866, sz * 0.5);
          ctx.closePath();
          ctx.fill();
          break;
        case "dot":
          ctx.fillStyle = s.color;
          ctx.beginPath();
          ctx.arc(0, 0, sz, 0, Math.PI * 2);
          ctx.fill();
          break;
        case "cross": {
          ctx.strokeStyle = s.color;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(-sz, 0);
          ctx.lineTo(sz, 0);
          ctx.moveTo(0, -sz);
          ctx.lineTo(0, sz);
          ctx.stroke();
          break;
        }
      }

      ctx.restore();
    };

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      // Connection lines
      for (let a = 0; a < shapes.length; a++) {
        for (let b = a + 1; b < shapes.length; b++) {
          const dx = shapes[a].x - shapes[b].x;
          const dy = shapes[a].y - shapes[b].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < connectDist) {
            const opacity = (1 - dist / connectDist) * 0.3;
            ctx.strokeStyle = colors.whiteLine.replace("0.06", String(opacity * 0.15));
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(shapes[a].x, shapes[a].y);
            ctx.lineTo(shapes[b].x, shapes[b].y);
            ctx.stroke();
          }
        }
      }

      // Update and draw shapes
      for (const s of shapes) {
        s.x += s.vx;
        s.y += s.vy;
        s.rotation += s.rotSpeed;
        s.pulsePhase += s.pulseSpeed;
        const pulse = (Math.sin(s.pulsePhase) + 1) / 2;

        // Wrap around edges
        if (s.x < -20) s.x = width + 20;
        if (s.x > width + 20) s.x = -20;
        if (s.y < -20) s.y = height + 20;
        if (s.y > height + 20) s.y = -20;

        drawShape(s, pulse);
      }

      animId = requestAnimationFrame(animate);
    };

    init();
    animate();

    const onResize = () => {
      cancelAnimationFrame(animId);
      init();
      animate();
    };
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full"
      style={{ pointerEvents: "none" }}
    />
  );
};

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const router = useRouter();
  const modalRef = useRef<HTMLDivElement>(null);
  const formContainerRef = useRef<HTMLDivElement>(null);

  const [isLoginMode, setIsLoginMode] = useState(true);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerFullName, setRegisterFullName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerRole, setRegisterRole] = useState<
    "Estudiante" | "Tutor" | "Jurado"
  >("Estudiante");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerConfirmPassword, setRegisterConfirmPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loginShowPassword, setLoginShowPassword] = useState(false);
  const [registerShowPassword, setRegisterShowPassword] = useState(false);
  const [registerShowConfirmPassword, setRegisterShowConfirmPassword] =
    useState(false);

  const [toastState, setToastState] = useState<{
    visible: boolean;
    message: string;
    type: "error" | "success" | "info";
  }>({
    visible: false,
    message: "",
    type: "error",
  });

  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  // GSAP entrance animation
  useEffect(() => {
    if (isOpen && modalRef.current) {
      gsap.fromTo(
        modalRef.current,
        { scale: 0.92, opacity: 0, y: 30 },
        {
          scale: 1,
          opacity: 1,
          y: 0,
          duration: 0.45,
          ease: "power3.out",
        }
      );
    }
  }, [isOpen]);

  const handleClose = useCallback(() => {
    setIsClosing(true);
    if (modalRef.current) {
      gsap.to(modalRef.current, {
        scale: 0.92,
        opacity: 0,
        y: 20,
        duration: 0.3,
        ease: "power2.in",
        onComplete: () => {
          onClose();
          setIsClosing(false);
        },
      });
    } else {
      setTimeout(() => {
        onClose();
        setIsClosing(false);
      }, 300);
    }
  }, [onClose]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "auto";
    }
    return () => {
      document.body.style.overflow = "auto";
    };
  }, [isOpen]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleClose]);

  // Animate form switch
  useEffect(() => {
    if (formContainerRef.current) {
      gsap.fromTo(
        formContainerRef.current,
        { opacity: 0, x: isLoginMode ? -20 : 20 },
        { opacity: 1, x: 0, duration: 0.35, ease: "power2.out" }
      );
    }
  }, [isLoginMode]);

  const showToast = (
    message: string,
    type: "error" | "success" | "info" = "error"
  ) => {
    setToastState({ visible: true, message, type });
  };

  const hideToast = () => setToastState((t) => ({ ...t, visible: false }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoginMode) {
      if (!loginEmail.trim() || !loginPassword.trim()) {
        showToast("Por favor ingresa correo y contraseña.", "error");
        return;
      }
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(loginEmail)) {
        showToast("Por favor ingresa una dirección de correo válida.", "error");
        return;
      }

      setIsLoggingIn(true);

      demoLogin(loginEmail, loginPassword)
        .then((result) => {
          if (!result.success) {
            setIsLoggingIn(false);
            showToast(result.message || "Credenciales incorrectas.", "error");
            return;
          }

          if (result.user && result.user.status === "pending") {
            setIsLoggingIn(false);
            showToast(
              "Tu cuenta aún está pendiente de aprobación por un administrador.",
              "info"
            );
            return;
          }

          showToast("Inicio de sesión exitoso.", "success");
          try {
            sessionStorage.setItem("justLoggedIn", "1");
          } catch {}
          setTimeout(() => {
            try {
              router.push("/dashboard");
            } catch {
              window.location.href = "/dashboard";
            }
          }, 1000);
        })
        .catch(() => {
          setIsLoggingIn(false);
          showToast("Error de conexión", "error");
        });
    } else {
      if (
        !registerFullName.trim() ||
        !registerEmail.trim() ||
        !registerPassword.trim() ||
        !registerConfirmPassword.trim()
      ) {
        showToast("Por favor completa todos los campos de registro.", "error");
        return;
      }

      if (registerPassword !== registerConfirmPassword) {
        showToast("Las contraseñas no coinciden", "error");
        return;
      }

      const newUser = {
        email: registerEmail,
        fullName: registerFullName,
        password: registerPassword,
        role: registerRole,
        status: "pending" as const,
      };

      setLoading(true);

      demoRegister(newUser)
        .then((res) => {
          setLoading(false);
          if (res.success) {
            showToast(
              "Registro exitoso. Espera la aprobación de un administrador.",
              "success"
            );
            setTimeout(() => {
              setIsLoginMode(true);
              setLoginEmail(registerEmail);
            }, 1500);
          } else {
            showToast(res.message || "Error al registrarse", "error");
          }
        })
        .catch(() => {
          setLoading(false);
          showToast("Error de conexión", "error");
        });
    }
  };

  if (!isOpen && !isClosing) return null;

  const show = isOpen && !isClosing;
  const backdropClasses = show
    ? "opacity-100"
    : "opacity-0 pointer-events-none";

  // Shared input styling
  const inputClass =
    "pl-12 h-12 bg-slate-50/80 border-slate-200 focus:bg-white focus:ring-2 focus:ring-usm-blue/20 focus:border-usm-blue rounded-xl transition-all duration-200";
  const inputClassSm =
    "pl-12 h-11 bg-slate-50/80 border-slate-200 focus:bg-white focus:ring-2 focus:ring-usm-blue/20 focus:border-usm-blue rounded-xl transition-all duration-200 text-sm";
  const labelClass = "text-sm font-semibold text-slate-700 ml-1";
  const labelClassSm = "text-xs font-semibold text-slate-700 ml-1";
  const iconClass =
    "absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 group-focus-within:text-usm-blue transition-colors duration-200";
  const iconClassSm =
    "absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-usm-blue transition-colors duration-200";

  return (
    <>
      <LoginLoading visible={isLoggingIn} />
      <Toast
        isVisible={toastState.visible}
        message={toastState.message}
        type={toastState.type}
        onClose={hideToast}
      />

      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-usm-navy/60 backdrop-blur-sm z-50 transition-opacity ease-in-out duration-300 ${backdropClasses}`}
        onClick={handleClose}
      />

      {/* Modal wrapper */}
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-0 md:p-4"
        role="dialog"
        aria-modal="true"
      >
        <div
          ref={modalRef}
          onClick={(e) => e.stopPropagation()}
          className="bg-white shadow-2xl w-full max-w-md md:max-w-2xl lg:max-w-4xl flex overflow-hidden
                     modal-mobile-full md:rounded-2xl md:h-auto"
        >
          {/* Left Side: Forms */}
          <div className="flex-1 p-6 sm:p-8 lg:p-12 flex flex-col justify-center relative overflow-y-auto max-h-[100dvh] md:max-h-[85vh]">
            {/* Close button */}
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-800 hover:bg-slate-100 rounded-full transition-all duration-200 ease-out hover:rotate-90 z-20"
            >
              <X className="h-5 w-5" />
            </button>

            {/* Mobile brand header (visible only on small screens) */}
            <div className="md:hidden mb-6 text-center">
              <h2 className="text-2xl font-bold text-usm-navy">TesisFar</h2>
              <p className="text-sm text-slate-500 mt-1">
                Gestión del Trabajo Especial de Grado
              </p>
            </div>

            <div className="w-full">
              {/* Tab switcher */}
              <div className="flex bg-slate-100 rounded-xl p-1 mb-8">
                <button
                  onClick={() => setIsLoginMode(true)}
                  className={`flex-1 py-2.5 text-center text-sm font-semibold rounded-lg transition-all duration-300 ${
                    isLoginMode
                      ? "bg-white text-usm-navy shadow-sm"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  Iniciar sesión
                </button>
                <button
                  onClick={() => setIsLoginMode(false)}
                  className={`flex-1 py-2.5 text-center text-sm font-semibold rounded-lg transition-all duration-300 ${
                    !isLoginMode
                      ? "bg-white text-usm-navy shadow-sm"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  Registrarse
                </button>
              </div>

              <div ref={formContainerRef}>
                {isLoginMode ? (
                  /* Login Form */
                  <form
                    onSubmit={handleSubmit}
                    className="space-y-5"
                    noValidate
                  >
                    <div className="space-y-2">
                      <label className={labelClass}>Correo electrónico</label>
                      <div className="relative group">
                        <Mail className={iconClass} />
                        <Input
                          type="email"
                          value={loginEmail}
                          onChange={(e) => setLoginEmail(e.target.value)}
                          placeholder="nombre@correo.com"
                          className={inputClass}
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className={labelClass}>Contraseña</label>
                      <div className="relative group">
                        <Lock className={iconClass} />
                        <Input
                          type={loginShowPassword ? "text" : "password"}
                          value={loginPassword}
                          onChange={(e) => setLoginPassword(e.target.value)}
                          placeholder="Ingresa tu contraseña"
                          className={`${inputClass} pr-12`}
                          required
                        />
                        <button
                          type="button"
                          onClick={() =>
                            setLoginShowPassword(!loginShowPassword)
                          }
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                        >
                          {loginShowPassword ? (
                            <EyeOff className="h-5 w-5" />
                          ) : (
                            <Eye className="h-5 w-5" />
                          )}
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm pt-1">
                      <label className="flex items-center gap-2 text-slate-600 cursor-pointer hover:text-slate-900 transition-colors">
                        <input
                          type="checkbox"
                          checked={rememberMe}
                          onChange={(e) => setRememberMe(e.target.checked)}
                          className="w-4 h-4 text-usm-blue border-slate-300 rounded focus:ring-usm-blue cursor-pointer"
                        />
                        Recuérdame
                      </label>
                      <button
                        type="button"
                        className="font-medium text-usm-blue hover:text-blue-700 transition-colors"
                      >
                        ¿Olvidaste tu contraseña?
                      </button>
                    </div>
                    <Button
                      type="submit"
                      className="w-full h-12 text-base font-bold bg-gradient-to-r from-usm-blue to-blue-600 text-white hover:from-blue-700 hover:to-blue-800 rounded-xl shadow-lg shadow-usm-blue/25 hover:shadow-usm-blue/35 active:scale-[0.98] transition-all duration-200 mt-4"
                    >
                      Iniciar sesión
                    </Button>

                    {/* Mobile: show switch prompt */}
                    <p className="text-center text-sm text-slate-500 md:hidden pt-2">
                      ¿No tienes cuenta?{" "}
                      <button
                        type="button"
                        onClick={() => setIsLoginMode(false)}
                        className="font-semibold text-usm-blue hover:text-blue-700"
                      >
                        Regístrate
                      </button>
                    </p>
                  </form>
                ) : (
                  /* Register Form */
                  <form
                    onSubmit={handleSubmit}
                    className="space-y-3"
                    noValidate
                  >
                    <div className="space-y-1">
                      <label className={labelClassSm}>Nombre completo</label>
                      <div className="relative group">
                        <User className={iconClassSm} />
                        <Input
                          type="text"
                          value={registerFullName}
                          onChange={(e) => setRegisterFullName(e.target.value)}
                          placeholder="Tu nombre completo"
                          className={inputClassSm}
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className={labelClassSm}>
                        Correo electrónico
                      </label>
                      <div className="relative group">
                        <Mail className={iconClassSm} />
                        <Input
                          type="email"
                          value={registerEmail}
                          onChange={(e) => setRegisterEmail(e.target.value)}
                          placeholder="nombre@correo.com"
                          className={inputClassSm}
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className={labelClassSm}>Rol de usuario</label>
                      <div className="relative group">
                        <User className={iconClassSm} />
                        <select
                          value={registerRole}
                          onChange={(e) =>
                            setRegisterRole(
                              e.target.value as
                                | "Estudiante"
                                | "Tutor"
                                | "Jurado"
                            )
                          }
                          className="w-full pl-12 pr-4 h-11 bg-slate-50/80 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-usm-blue/20 focus:border-usm-blue outline-none appearance-none cursor-pointer transition-all duration-200"
                        >
                          <option value="Estudiante">Estudiante</option>
                          <option value="Tutor">Tutor</option>
                          <option value="Jurado">Jurado</option>
                        </select>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className={labelClassSm}>Contraseña</label>
                      <div className="relative group">
                        <Lock className={iconClassSm} />
                        <Input
                          type={registerShowPassword ? "text" : "password"}
                          value={registerPassword}
                          onChange={(e) => setRegisterPassword(e.target.value)}
                          placeholder="Crea una contraseña segura"
                          className={`${inputClassSm} pr-12`}
                          required
                        />
                        <button
                          type="button"
                          onClick={() =>
                            setRegisterShowPassword(!registerShowPassword)
                          }
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                        >
                          {registerShowPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className={labelClassSm}>
                        Confirmar contraseña
                      </label>
                      <div className="relative group">
                        <Lock className={iconClassSm} />
                        <Input
                          type={
                            registerShowConfirmPassword ? "text" : "password"
                          }
                          value={registerConfirmPassword}
                          onChange={(e) =>
                            setRegisterConfirmPassword(e.target.value)
                          }
                          placeholder="Confirma tu contraseña"
                          className={`${inputClassSm} pr-12`}
                          required
                        />
                        <button
                          type="button"
                          onClick={() =>
                            setRegisterShowConfirmPassword(
                              !registerShowConfirmPassword
                            )
                          }
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                        >
                          {registerShowConfirmPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>
                    <div className="pt-2">
                      <Button
                        type="submit"
                        disabled={loading}
                        className="w-full h-12 text-sm font-bold bg-gradient-to-r from-usm-orange to-orange-500 text-white hover:from-orange-600 hover:to-orange-700 rounded-xl shadow-lg shadow-usm-orange/25 hover:shadow-usm-orange/35 active:scale-[0.98] transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed"
                      >
                        {loading ? "Registrando..." : "Registrarse"}
                      </Button>
                    </div>

                    {/* Mobile: show switch prompt */}
                    <p className="text-center text-sm text-slate-500 md:hidden pt-2">
                      ¿Ya tienes cuenta?{" "}
                      <button
                        type="button"
                        onClick={() => setIsLoginMode(true)}
                        className="font-semibold text-usm-blue hover:text-blue-700"
                      >
                        Inicia sesión
                      </button>
                    </p>
                  </form>
                )}
              </div>
            </div>
          </div>

          {/* Right Side: Brand Panel — visible on md+ (not just lg) */}
          <div className="flex-1 relative hidden md:flex brand-gradient-animated overflow-hidden">
            <BrandCanvas />
            <div className="relative h-full w-full flex flex-col justify-center items-center p-10 lg:p-12 text-center z-10">
              <div className="text-white space-y-6">
                {/* Glowing logo */}
                <div className="relative inline-block">
                  <div className="absolute inset-0 blur-3xl bg-usm-blue/30 rounded-full scale-150" />
                  <h3 className="text-5xl lg:text-6xl font-bold drop-shadow-lg relative">
                    TesisFar
                  </h3>
                </div>

                <p className="text-base lg:text-lg font-light tracking-wide opacity-90 leading-relaxed max-w-xs mx-auto">
                  La plataforma integral para la gestión y seguimiento eficiente
                  de Trabajos Especiales de Grado.
                </p>

                {/* Feature pills */}
                <div className="flex flex-wrap justify-center gap-2 pt-4">
                  {["Entregas", "Evaluaciones", "Seguimiento"].map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 text-xs font-medium text-white/80"
                    >
                      <Sparkles className="h-3 w-3 text-usm-yellow" />
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Decorative dots */}
                <div className="pt-6 flex justify-center gap-2 opacity-60">
                  <div className="w-2 h-2 rounded-full bg-white" />
                  <div className="w-2 h-2 rounded-full bg-white/40" />
                  <div className="w-2 h-2 rounded-full bg-white/40" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
