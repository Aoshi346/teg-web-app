"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { X, Eye, EyeOff, Mail, Lock, User, ArrowRight, HelpCircle } from "lucide-react";
import Toast from "@shared/ui/Toast";
import LoginLoading from "@shared/ui/LoginLoading";
import {
  login as demoLogin,
  register as demoRegister,
} from "@features/auth/api/clientAuth";
import { useRouter } from "next/navigation";
import { gsap } from "gsap";
import RoleGrid from "./RoleGrid";
import CedulaField, { Nationality } from "./CedulaField";

const REMEMBER_EMAIL_KEY = "tf_remembered_email";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const router = useRouter();
  const modalRef = useRef<HTMLDivElement>(null);
  const formContainerRef = useRef<HTMLDivElement>(null);

  const [isLoginMode, setIsLoginMode] = useState(true);
  const [isForgotMode, setIsForgotMode] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotSent, setForgotSent] = useState(false);

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerFullName, setRegisterFullName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerCedula, setRegisterCedula] = useState("");
  const [registerNationality, setRegisterNationality] = useState<Nationality>("V");
  const [registerRole, setRegisterRole] = useState<"Estudiante" | "Tutor" | "Jurado">("Estudiante");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerConfirmPassword, setRegisterConfirmPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loginShowPassword, setLoginShowPassword] = useState(false);
  const [registerShowPassword, setRegisterShowPassword] = useState(false);
  const [registerShowConfirmPassword, setRegisterShowConfirmPassword] = useState(false);

  const [toastState, setToastState] = useState<{
    visible: boolean;
    message: string;
    type: "error" | "success" | "info";
  }>({ visible: false, message: "", type: "error" });

  useEffect(() => {
    if (typeof window !== "undefined" && localStorage.getItem(REMEMBER_EMAIL_KEY)) {
      const remembered = localStorage.getItem(REMEMBER_EMAIL_KEY);
      if (remembered) {
        setLoginEmail(remembered);
        setRememberMe(true);
      }
    }
  }, []);

  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  const reducedMotion = typeof window !== "undefined"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    if (isOpen && modalRef.current && !reducedMotion) {
      gsap.fromTo(
        modalRef.current,
        { scale: 0.94, opacity: 0, y: 24 },
        { scale: 1, opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }
      );
    }
  }, [isOpen, reducedMotion]);

  const handleClose = useCallback(() => {
    setIsClosing(true);
    if (modalRef.current && !reducedMotion) {
      gsap.to(modalRef.current, {
        scale: 0.94, opacity: 0, y: 16,
        duration: 0.28, ease: "power2.in",
        onComplete: () => { onClose(); setIsClosing(false); },
      });
    } else {
      setTimeout(() => { onClose(); setIsClosing(false); }, reducedMotion ? 0 : 280);
    }
  }, [onClose, reducedMotion]);

  useEffect(() => {
    if (isOpen) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "auto";
    return () => { document.body.style.overflow = "auto"; };
  }, [isOpen]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (isForgotMode) {
        setIsForgotMode(false);
        setForgotSent(false);
      } else {
        handleClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleClose, isForgotMode]);

  useEffect(() => {
    if (formContainerRef.current && !reducedMotion) {
      gsap.fromTo(
        formContainerRef.current,
        { opacity: 0, x: isLoginMode ? -16 : 16 },
        { opacity: 1, x: 0, duration: 0.32, ease: "power2.out" }
      );
    }
  }, [isLoginMode, isForgotMode, reducedMotion]);

  const showToast = (message: string, type: "error" | "success" | "info" = "error") => {
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
            showToast("Tu cuenta aún está pendiente de aprobación por un administrador.", "info");
            return;
          }
          showToast("Inicio de sesión exitoso.", "success");
          try {
            sessionStorage.setItem("justLoggedIn", "1");
            if (rememberMe) localStorage.setItem(REMEMBER_EMAIL_KEY, loginEmail);
            else localStorage.removeItem(REMEMBER_EMAIL_KEY);
          } catch {}
          setTimeout(() => {
            try { router.push("/dashboard"); }
            catch { window.location.href = "/dashboard"; }
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
        cedula: registerCedula || undefined,
        nationality: registerNationality,
        status: "pending" as const,
      };

      setLoading(true);
      demoRegister(newUser)
        .then((res) => {
          setLoading(false);
          if (res.success) {
            showToast("Registro exitoso. Espera la aprobación de un administrador.", "success");
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

  const handleForgotSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!forgotEmail.trim()) {
      showToast("Ingresa tu correo institucional.", "error");
      return;
    }
    // Note: real wiring pending future brief 010-forgot-password.
    setForgotSent(true);
    showToast("Si la cuenta existe, te enviaremos un enlace.", "success");
  };

  if (!isOpen && !isClosing) return null;

  const numeral = isForgotMode ? "?" : isLoginMode ? "01" : "02";
  const eyebrow = isForgotMode ? "Recuperación" : isLoginMode ? "Acceso" : "Solicita acceso";

  return (
    <>
      <LoginLoading visible={isLoggingIn} />
      <Toast
        isVisible={toastState.visible}
        message={toastState.message}
        type={toastState.type}
        onClose={hideToast}
      />

      <div className="lm-overlay" onClick={handleClose} role="presentation">
        <div
          ref={modalRef}
          className="lm-modal"
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-modal="true"
          aria-labelledby="lm-band-title"
        >
          <div className="lm-utility">
            <a className="help" href="#" onClick={(e) => e.preventDefault()}>
              <HelpCircle size={12} style={{ display: "inline", marginRight: 4, verticalAlign: "-2px" }} />
              ¿Necesitas ayuda?
            </a>
            <button
              type="button"
              className="x"
              aria-label="Cerrar"
              onClick={handleClose}
            >
              <X size={18} />
            </button>
          </div>

          <div className="lm-band">
            <span className="lm-band-corner tl" />
            <span className="lm-band-corner br" />
            <div className="lm-band-row">
              <span className="lm-band-num">{numeral}</span>
              <div className="lm-band-info">
                <span className="lm-band-eyebrow">{eyebrow}</span>
                <h3 id="lm-band-title" className="lm-band-title">
                  {isForgotMode ? (
                    <>¿Olvidaste tu <em>contraseña</em>?</>
                  ) : isLoginMode ? (
                    <>Bienvenido <em>de vuelta</em>.</>
                  ) : (
                    <>Crea tu <em>cuenta</em>.</>
                  )}
                </h3>
                <p className="lm-band-lede">
                  {isForgotMode
                    ? "Te enviaremos un enlace para restablecerla."
                    : isLoginMode
                    ? "Entra y la plataforma te lleva directo a lo pendiente."
                    : "Solicita acceso con tus datos institucionales."}
                </p>
              </div>
            </div>
            <span className="lm-band-strip" />
          </div>

          <div className="lm-body">
            {!isForgotMode && (
              <div className="lm-seg" role="tablist" aria-label="Modo de acceso">
                <button
                  type="button"
                  role="tab"
                  aria-selected={isLoginMode}
                  onClick={() => setIsLoginMode(true)}
                >
                  Iniciar sesión
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={!isLoginMode}
                  onClick={() => setIsLoginMode(false)}
                >
                  Crear cuenta
                </button>
              </div>
            )}

            <div ref={formContainerRef}>
              {isForgotMode ? (
                <form id="lm-forgot-form" onSubmit={handleForgotSubmit} className="lm-fields" noValidate>
                  <label className="lm-field">
                    <span className="lm-field-lbl">Correo institucional</span>
                    <div className="lm-field-row">
                      <Mail className="icon" size={18} />
                      <input
                        type="email"
                        autoComplete="email"
                        placeholder="tu.nombre@usm.edu.ve"
                        value={forgotEmail}
                        onChange={(e) => setForgotEmail(e.target.value)}
                        required
                        disabled={forgotSent}
                      />
                    </div>
                    <span className="lm-field-help">
                      {forgotSent
                        ? "Revisa tu bandeja de entrada en los próximos minutos."
                        : "Te enviaremos un enlace de recuperación."}
                    </span>
                  </label>
                </form>
              ) : isLoginMode ? (
                <form id="lm-login-form" onSubmit={handleSubmit} className="lm-fields" noValidate>
                  <label className="lm-field">
                    <span className="lm-field-lbl">Correo institucional</span>
                    <div className="lm-field-row">
                      <Mail className="icon" size={18} />
                      <input
                        type="email"
                        autoComplete="email"
                        placeholder="tu.nombre@usm.edu.ve"
                        value={loginEmail}
                        onChange={(e) => setLoginEmail(e.target.value)}
                        required
                      />
                    </div>
                  </label>
                  <label className="lm-field">
                    <span className="lm-field-lbl">Contraseña</span>
                    <div className="lm-field-row">
                      <Lock className="icon" size={18} />
                      <input
                        type={loginShowPassword ? "text" : "password"}
                        autoComplete="current-password"
                        placeholder="••••••••"
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        required
                      />
                      <button
                        type="button"
                        className="toggle"
                        aria-label={loginShowPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                        onClick={() => setLoginShowPassword(!loginShowPassword)}
                      >
                        {loginShowPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </label>
                  <div className="lm-meta">
                    <label className="check">
                      <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => {
                          setRememberMe(e.target.checked);
                          if (!e.target.checked) localStorage.removeItem(REMEMBER_EMAIL_KEY);
                        }}
                      />
                      Mantener sesión
                    </label>
                    <button
                      type="button"
                      className="forgot"
                      onClick={() => { setIsForgotMode(true); setForgotSent(false); setForgotEmail(loginEmail); }}
                    >
                      ¿Olvidaste tu contraseña?
                    </button>
                  </div>
                </form>
              ) : (
                <form id="lm-register-form" onSubmit={handleSubmit} className="lm-fields" noValidate>
                  <label className="lm-field">
                    <span className="lm-field-lbl">Nombre completo</span>
                    <div className="lm-field-row">
                      <User className="icon" size={18} />
                      <input
                        type="text"
                        autoComplete="name"
                        placeholder="María Fernández"
                        value={registerFullName}
                        onChange={(e) => setRegisterFullName(e.target.value)}
                        required
                      />
                    </div>
                  </label>
                  <label className="lm-field">
                    <span className="lm-field-lbl">Correo institucional</span>
                    <div className="lm-field-row">
                      <Mail className="icon" size={18} />
                      <input
                        type="email"
                        autoComplete="email"
                        placeholder="tu.nombre@usm.edu.ve"
                        value={registerEmail}
                        onChange={(e) => setRegisterEmail(e.target.value)}
                        required
                      />
                    </div>
                  </label>
                  <CedulaField
                    nationality={registerNationality}
                    cedula={registerCedula}
                    onChange={({ nationality, cedula }) => {
                      setRegisterNationality(nationality);
                      setRegisterCedula(cedula);
                    }}
                  />
                  <RoleGrid value={registerRole} onChange={setRegisterRole} />
                  <label className="lm-field">
                    <span className="lm-field-lbl">Contraseña</span>
                    <div className="lm-field-row">
                      <Lock className="icon" size={18} />
                      <input
                        type={registerShowPassword ? "text" : "password"}
                        autoComplete="new-password"
                        placeholder="Mínimo 8 caracteres"
                        value={registerPassword}
                        onChange={(e) => setRegisterPassword(e.target.value)}
                        required
                      />
                      <button
                        type="button"
                        className="toggle"
                        aria-label={registerShowPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                        onClick={() => setRegisterShowPassword(!registerShowPassword)}
                      >
                        {registerShowPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </label>
                  <label className="lm-field">
                    <span className="lm-field-lbl">Confirmar contraseña</span>
                    <div className="lm-field-row">
                      <Lock className="icon" size={18} />
                      <input
                        type={registerShowConfirmPassword ? "text" : "password"}
                        autoComplete="new-password"
                        placeholder="Repite la contraseña"
                        value={registerConfirmPassword}
                        onChange={(e) => setRegisterConfirmPassword(e.target.value)}
                        required
                      />
                      <button
                        type="button"
                        className="toggle"
                        aria-label={registerShowConfirmPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                        onClick={() => setRegisterShowConfirmPassword(!registerShowConfirmPassword)}
                      >
                        {registerShowConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </label>
                </form>
              )}
            </div>
          </div>

          <div className="lm-foot">
            {isForgotMode ? (
              <>
                <button
                  type="submit"
                  form="lm-forgot-form"
                  className="lm-stamp"
                  disabled={forgotSent}
                >
                  <span className="num">?</span>
                  {forgotSent ? "Enlace enviado" : "Enviar enlace"}
                  <ArrowRight className="arrow" size={16} />
                </button>
                <p className="lm-alt-foot">
                  <button
                    type="button"
                    onClick={() => { setIsForgotMode(false); setForgotSent(false); }}
                  >
                    ← Volver a iniciar sesión
                  </button>
                </p>
              </>
            ) : isLoginMode ? (
              <>
                <button
                  type="submit"
                  form="lm-login-form"
                  className="lm-stamp"
                  disabled={isLoggingIn}
                >
                  <span className="num">01</span>
                  {isLoggingIn ? "Verificando..." : "Continuar"}
                  <ArrowRight className="arrow" size={16} />
                </button>
                <p className="lm-alt-foot">
                  ¿Eres nuevo?{" "}
                  <button type="button" onClick={() => setIsLoginMode(false)}>
                    Solicita acceso →
                  </button>
                </p>
              </>
            ) : (
              <>
                <button
                  type="submit"
                  form="lm-register-form"
                  className="lm-stamp"
                  disabled={loading}
                >
                  <span className="num">02</span>
                  {loading ? "Registrando..." : "Crear cuenta"}
                  <ArrowRight className="arrow" size={16} />
                </button>
                <p className="lm-alt-foot">
                  ¿Ya tienes cuenta?{" "}
                  <button type="button" onClick={() => setIsLoginMode(true)}>
                    Inicia sesión →
                  </button>
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
