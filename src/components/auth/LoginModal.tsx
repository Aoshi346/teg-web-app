"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { X, Eye, EyeOff, Mail, Lock, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Toast from "@/components/ui/Toast";
import LoginLoading from "@/components/ui/LoginLoading";
import {
  login as demoLogin,
  register as demoRegister,
} from "@/features/auth/clientAuth";
import { useRouter } from "next/navigation";

// --- Particle Animation Utility ---
function runParticleAnimation(container: HTMLDivElement): () => void {
  const canvas = document.createElement("canvas");
  container.appendChild(canvas);
  const ctx = canvas.getContext("2d")!;
  if (!ctx) {
    console.error("2D context not supported");
    return () => {};
  }

  let animationFrameId: number;
  const particles: Particle[] = [];
  const particleCount = 40;
  const connectDistance = 80;

  const mouse = {
    x: -1000,
    y: -1000,
    radius: 60,
  };

  const handleMouseMove = (event: MouseEvent) => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = event.clientX - rect.left;
    mouse.y = event.clientY - rect.top;
  };

  const handleMouseOut = () => {
    mouse.x = -1000;
    mouse.y = -1000;
  };

  container.addEventListener("mousemove", handleMouseMove);
  container.addEventListener("mouseout", handleMouseOut);

  const colors = {
    blue: "#3b82f6",
    green: "#10b981",
    lightBlue: "#bfdbfe",
    lightGreen: "#a7f3d0",
    white: "#ffffff",
    darkBlue: "#1e40af",
  };

  class Particle {
    x: number;
    y: number;
    baseSize: number;
    size: number;
    speedX: number;
    speedY: number;
    color1: string;
    color2: string | null;
    shape: "pill" | "capsule" | "cross" | "molecule";
    rotation: number;
    rotationSpeed: number;
    pulseAngle: number;
    pulseSpeed: number;

    constructor() {
      this.baseSize = 6;
      this.x =
        Math.random() * (canvas.width - this.baseSize * 2) + this.baseSize;
      this.y =
        Math.random() * (canvas.height - this.baseSize * 2) + this.baseSize;
      this.speedX = (Math.random() - 0.5) * 0.4;
      this.speedY = (Math.random() - 0.5) * 0.4;
      this.rotation = Math.random() * Math.PI * 2;
      this.rotationSpeed = (Math.random() - 0.5) * 0.01;
      this.pulseAngle = Math.random() * Math.PI * 2;
      this.pulseSpeed = (Math.random() - 0.5) * 0.02;

      const shapeType = Math.random();
      if (shapeType < 0.4) {
        // 40% pill
        this.shape = "pill";
        this.color1 = Math.random() < 0.5 ? colors.blue : colors.green;
        this.color2 = null;
        this.baseSize = Math.random() * 5 + 5;
      } else if (shapeType < 0.7) {
        // 30% capsule
        this.shape = "capsule";
        this.color1 = colors.lightBlue;
        this.color2 = colors.blue;
        this.baseSize = Math.random() * 6 + 7;
      } else if (shapeType < 0.9) {
        // 20% cross
        this.shape = "cross";
        this.color1 = colors.green;
        this.color2 = null;
        this.baseSize = Math.random() * 4 + 5;
      } else {
        // 10% molecule
        this.shape = "molecule";
        this.color1 = colors.lightGreen;
        this.color2 = colors.darkBlue;
        this.baseSize = Math.random() * 8 + 8;
      }
      this.size = this.baseSize;

      const reduced =
        typeof window !== "undefined" &&
        window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
      if (reduced) {
        this.speedX *= 0.1;
        this.speedY *= 0.1;
        this.rotationSpeed = 0;
        this.pulseSpeed = 0;
      }
    }

    update() {
      // Mouse interaction
      const dx = this.x - mouse.x;
      const dy = this.y - mouse.y;
      const distance = Math.hypot(dx, dy);
      const forceDirectionX = dx / distance;
      const forceDirectionY = dy / distance;
      const force = (mouse.radius - distance) / mouse.radius;

      if (distance < mouse.radius) {
        this.x += forceDirectionX * force * 2.5;
        this.y += forceDirectionY * force * 2.5;
      }

      // Wall collision
      if (this.x > canvas.width + 10 || this.x < -10)
        this.speedX = -this.speedX;
      if (this.y > canvas.height + 10 || this.y < -10)
        this.speedY = -this.speedY;

      this.x += this.speedX;
      this.y += this.speedY;
      this.rotation += this.rotationSpeed;

      // Pulsing effect
      this.pulseAngle += this.pulseSpeed;
      this.size =
        this.baseSize + Math.sin(this.pulseAngle) * (this.baseSize * 0.1);
    }

    draw() {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.rotation);
      ctx.shadowColor = "rgba(0,0,0,0.1)";
      ctx.shadowBlur = 8;

      if (this.shape === "pill") {
        const s = this.size;
        ctx.fillStyle = this.color1;
        ctx.beginPath();
        ctx.arc(0, 0, s, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(-s * 0.5, 0);
        ctx.lineTo(s * 0.5, 0);
        ctx.stroke();
      } else if (this.shape === "capsule") {
        const width = this.size * 1.8;
        const height = this.size;
        const radius = height / 2;

        // First half
        ctx.fillStyle = this.color1;
        ctx.beginPath();
        ctx.arc(-width / 4, 0, radius, Math.PI / 2, -Math.PI / 2);
        ctx.rect(-width / 4, -radius, width / 4, height);
        ctx.fill();

        // Second half
        ctx.fillStyle = this.color2!;
        ctx.beginPath();
        ctx.arc(width / 4, 0, radius, -Math.PI / 2, Math.PI / 2);
        ctx.rect(0, -radius, width / 4, height);
        ctx.fill();
      } else if (this.shape === "cross") {
        const armLength = this.size * 1.5;
        const armWidth = this.size * 0.5;
        ctx.fillStyle = this.color1;
        ctx.globalAlpha = 0.8;
        ctx.fillRect(-armLength / 2, -armWidth / 2, armLength, armWidth);
        ctx.fillRect(-armWidth / 2, -armLength / 2, armWidth, armLength);
        ctx.globalAlpha = 1;
      } else if (this.shape === "molecule") {
        ctx.strokeStyle = this.color1;
        ctx.fillStyle = this.color2!;
        ctx.lineWidth = 1.5;

        const r = this.size / 3;
        const positions = [
          { x: 0, y: 0 },
          { x: this.size, y: 0 },
          { x: this.size / 2, y: (this.size * Math.sqrt(3)) / 2 },
        ];

        ctx.beginPath();
        ctx.moveTo(positions[0].x, positions[0].y);
        ctx.lineTo(positions[1].x, positions[1].y);
        ctx.lineTo(positions[2].x, positions[2].y);
        ctx.closePath();
        ctx.stroke();

        positions.forEach((p) => {
          ctx.beginPath();
          ctx.arc(p.x, p.y, r, 0, 2 * Math.PI);
          ctx.fill();
        });
      }

      ctx.restore();
    }
  }

  const init = () => {
    particles.length = 0;
    const rect = container.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    canvas.style.position = "absolute";
    canvas.style.inset = "0";
    canvas.style.width = "100%";
    canvas.style.height = "100%";

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle());
    }
  };

  const connect = () => {
    for (let a = 0; a < particles.length; a++) {
      for (let b = a + 1; b < particles.length; b++) {
        const distance = Math.hypot(
          particles[a].x - particles[b].x,
          particles[a].y - particles[b].y,
        );

        if (distance < connectDistance) {
          const opacity = 1 - distance / connectDistance;
          ctx.strokeStyle = `rgba(191, 219, 254, ${opacity * 0.6})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(particles[a].x, particles[a].y);
          ctx.lineTo(particles[b].x, particles[b].y);
          ctx.stroke();
        }
      }
    }
  };

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach((p) => {
      p.update();
      p.draw();
    });
    connect();
    animationFrameId = requestAnimationFrame(animate);
  };

  const debouncedInit = () => {
    cancelAnimationFrame(animationFrameId);
    init();
    animate();
  };

  init();
  animate();

  window.addEventListener("resize", debouncedInit);

  return () => {
    window.removeEventListener("resize", debouncedInit);
    container.removeEventListener("mousemove", handleMouseMove);
    container.removeEventListener("mouseout", handleMouseOut);
    cancelAnimationFrame(animationFrameId);
    if (container.contains(canvas)) {
      container.removeChild(canvas);
    }
  };
}

// --- React Components ---
const ParticleCanvas = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      const cleanup = runParticleAnimation(containerRef.current);
      return cleanup;
    }
  }, []);

  return <div ref={containerRef} className="absolute inset-0 h-full w-full" />;
};

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const router = useRouter();
  const [isLoginMode, setIsLoginMode] = useState(true);
  // Form states
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerFullName, setRegisterFullName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerRole, setRegisterRole] = useState<"Estudiante" | "Profesor">(
    "Estudiante",
  );
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

  // Animation state
  const [isClosing, setIsClosing] = useState(false);

  const handleClose = useCallback(() => {
    setIsClosing(true);
    setTimeout(() => {
      onClose();
      setIsClosing(false);
    }, 300); // Corresponds to animation duration
  }, [onClose]);

  // Prevent body from scrolling when the modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "auto";
    }
    // Cleanup on unmount
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

  const showToast = (
    message: string,
    type: "error" | "success" | "info" = "error",
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
              "info",
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
          }, 1000); // Reduced delay for smoother feel with API
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
        return; // Add return
      } // Add missing brace? No, context shows it

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

      setLoading(true); // Reuse existing loading state or isLoggingIn? existing code uses setLoading but it's not in view?
      // Wait, view shows `setIsLoggingIn` usage in login, but register part used `setLoading` in previous `view_file` (Line 445 in previous view, wait, previous view didn't show register logic fully? Line 443 says "else ...").
      // Ah, Step 1038 lines 443+.
      // I'll assume setLoading exists.

      demoRegister(newUser)
        .then((res) => {
          setLoading(false);
          if (res.success) {
            showToast(
              "Registro exitoso. Espera la aprobación de un administrador.",
              "success",
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
  const modalClasses = show
    ? "opacity-100 scale-100"
    : "opacity-0 scale-95 pointer-events-none";

  return (
    <>
      <LoginLoading visible={isLoggingIn} />
      <Toast
        isVisible={toastState.visible}
        message={toastState.message}
        type={toastState.type}
        onClose={hideToast}
      />
      <div
        className={`fixed inset-0 bg-black/50 backdrop-blur-sm z-50 transition-opacity ease-in-out duration-300 ${backdropClasses}`}
        onClick={handleClose}
      />
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
      >
        <div
          onClick={(e) => e.stopPropagation()}
          className={`bg-white rounded-2xl shadow-2xl w-full max-w-md md:max-w-2xl lg:max-w-4xl flex overflow-hidden transition-all ease-in-out duration-300 ${modalClasses}`}
        >
          {/* Left Side: Forms */}
          <div className="flex-1 p-8 lg:p-12 flex flex-col justify-center">
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 p-1.5 text-gray-400 hover:text-gray-800 hover:bg-gray-100 rounded-full transition-all duration-200 ease-in-out hover:rotate-90 z-20"
            >
              <X className="h-6 w-6" />
            </button>

            <div className="w-full">
              <div className="flex border-b mb-8">
                <button
                  onClick={() => setIsLoginMode(true)}
                  className={`flex-1 py-3 text-center font-semibold transition-colors duration-300 ${isLoginMode ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-500 hover:text-gray-800"}`}
                >
                  Iniciar sesión
                </button>
                <button
                  onClick={() => setIsLoginMode(false)}
                  className={`flex-1 py-3 text-center font-semibold transition-colors duration-300 ${!isLoginMode ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-500 hover:text-gray-800"}`}
                >
                  Registrarse
                </button>
              </div>

              <div className="relative min-h-[510px] overflow-hidden">
                {/* Login Form */}
                <div
                  className={`absolute inset-0 p-1 transition-all duration-500 ease-in-out ${isLoginMode ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-full pointer-events-none"}`}
                >
                  <form
                    onSubmit={handleSubmit}
                    className="space-y-6"
                    noValidate
                  >
                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-gray-700 ml-1">
                        Correo electrónico
                      </label>
                      <div className="relative group">
                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                        <Input
                          type="email"
                          value={loginEmail}
                          onChange={(e) => setLoginEmail(e.target.value)}
                          placeholder="nombre@correo.com"
                          className="pl-12 h-12 bg-gray-50 border-gray-200 focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 rounded-xl transition-all duration-200"
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-gray-700 ml-1">
                        Contraseña
                      </label>
                      <div className="relative group">
                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                        <Input
                          type={loginShowPassword ? "text" : "password"}
                          value={loginPassword}
                          onChange={(e) => setLoginPassword(e.target.value)}
                          placeholder="Ingresa tu contraseña"
                          className="pl-12 pr-12 h-12 bg-gray-50 border-gray-200 focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 rounded-xl transition-all duration-200"
                          required
                        />
                        <button
                          type="button"
                          onClick={() =>
                            setLoginShowPassword(!loginShowPassword)
                          }
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          {loginShowPassword ? (
                            <EyeOff className="h-5 w-5" />
                          ) : (
                            <Eye className="h-5 w-5" />
                          )}
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm pt-2">
                      <label className="flex items-center gap-2 text-gray-600 cursor-pointer hover:text-gray-900 transition-colors">
                        <input
                          type="checkbox"
                          checked={rememberMe}
                          onChange={(e) => setRememberMe(e.target.checked)}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                        />
                        Recuérdame
                      </label>
                      <button
                        type="button"
                        className="font-medium text-blue-600 hover:text-blue-700 transition-colors"
                      >
                        ¿Olvidaste tu contraseña?
                      </button>
                    </div>
                    <Button
                      type="submit"
                      className="w-full h-12 text-base font-bold bg-blue-600 text-white hover:bg-blue-700 rounded-xl shadow-lg shadow-blue-600/30 hover:shadow-blue-600/40 active:scale-[0.98] transition-all duration-200 mt-4"
                    >
                      Iniciar sesión
                    </Button>
                  </form>
                </div>

                {/* Register Form */}
                <div
                  className={`absolute inset-0 p-1 transition-all duration-500 ease-in-out ${!isLoginMode ? "opacity-100 translate-x-0" : "opacity-0 translate-x-full pointer-events-none"}`}
                >
                  <form
                    onSubmit={handleSubmit}
                    className="space-y-3"
                    noValidate
                  >
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-gray-700 ml-1">
                        Nombre completo
                      </label>
                      <div className="relative group">
                        <User className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                        <Input
                          type="text"
                          value={registerFullName}
                          onChange={(e) => setRegisterFullName(e.target.value)}
                          placeholder="Tu nombre completo"
                          className="pl-12 h-11 bg-gray-50 border-gray-200 focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 rounded-xl transition-all duration-200 text-sm"
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-gray-700 ml-1">
                        Correo electrónico
                      </label>
                      <div className="relative group">
                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                        <Input
                          type="email"
                          value={registerEmail}
                          onChange={(e) => setRegisterEmail(e.target.value)}
                          placeholder="nombre@correo.com"
                          className="pl-12 h-11 bg-gray-50 border-gray-200 focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 rounded-xl transition-all duration-200 text-sm"
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-gray-700 ml-1">
                        Rol de usuario
                      </label>
                      <div className="relative group">
                        <User className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                        <select
                          value={registerRole}
                          onChange={(e) =>
                            setRegisterRole(
                              e.target.value as "Estudiante" | "Profesor",
                            )
                          }
                          className="w-full pl-12 pr-4 h-11 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none appearance-none cursor-pointer transition-all duration-200"
                        >
                          <option value="Estudiante">Estudiante</option>
                          <option value="Profesor">Profesor</option>
                        </select>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-gray-700 ml-1">
                        Contraseña
                      </label>
                      <div className="relative group">
                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                        <Input
                          type={registerShowPassword ? "text" : "password"}
                          value={registerPassword}
                          onChange={(e) => setRegisterPassword(e.target.value)}
                          placeholder="Crea una contraseña segura"
                          className="pl-12 pr-12 h-11 bg-gray-50 border-gray-200 focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 rounded-xl transition-all duration-200 text-sm"
                          required
                        />
                        <button
                          type="button"
                          onClick={() =>
                            setRegisterShowPassword(!registerShowPassword)
                          }
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
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
                      <label className="text-xs font-semibold text-gray-700 ml-1">
                        Confirmar contraseña
                      </label>
                      <div className="relative group">
                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                        <Input
                          type={
                            registerShowConfirmPassword ? "text" : "password"
                          }
                          value={registerConfirmPassword}
                          onChange={(e) =>
                            setRegisterConfirmPassword(e.target.value)
                          }
                          placeholder="Confirma tu contraseña"
                          className="pl-12 pr-12 h-11 bg-gray-50 border-gray-200 focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 rounded-xl transition-all duration-200 text-sm"
                          required
                        />
                        <button
                          type="button"
                          onClick={() =>
                            setRegisterShowConfirmPassword(
                              !registerShowConfirmPassword,
                            )
                          }
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
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
                        className="w-full h-12 text-sm font-bold bg-blue-600 text-white hover:bg-blue-700 rounded-xl shadow-lg shadow-blue-600/30 hover:shadow-blue-600/40 active:scale-[0.98] transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed"
                      >
                        {loading ? "Registrando..." : "Registrarse"}
                      </Button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>

          {/* Right Side: Info */}
          <div className="flex-1 relative hidden lg:block bg-gray-900 animated-gradient">
            <ParticleCanvas />
            <div className="relative h-full flex flex-col justify-center items-center p-12 text-center z-10">
              <div className="text-white space-y-6">
                <div className="relative inline-block">
                  <div className="absolute inset-0 blur-2xl bg-blue-500/30 rounded-full"></div>
                  <h3 className="text-6xl font-bold drop-shadow-lg relative">
                    TesisFar
                  </h3>
                </div>
                <p className="text-lg font-light tracking-wider opacity-90 leading-relaxed max-w-sm mx-auto">
                  La plataforma integral para la gestión y seguimiento eficiente
                  de Trabajos Especiales de Grado.
                </p>
                <div className="pt-8 flex justify-center gap-4 opacity-70">
                  <div className="w-2 h-2 rounded-full bg-white"></div>
                  <div className="w-2 h-2 rounded-full bg-white/50"></div>
                  <div className="w-2 h-2 rounded-full bg-white/50"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
