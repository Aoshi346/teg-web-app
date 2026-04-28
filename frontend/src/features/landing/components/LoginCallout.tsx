"use client";

import React, { useState } from "react";
import { login } from "@features/auth/api/clientAuth";
import { useRouter } from "next/navigation";

export default function LoginCallout() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await login(email, password);
      if (result?.success) {
        router.push("/dashboard");
      } else {
        setError(result?.message || "No se pudo iniciar sesión");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setSubmitting(false);
    }
  }

  function openModal() {
    const btn = document.querySelector('[aria-label="Ingresar"]') as HTMLButtonElement | null;
    if (btn) btn.click();
  }

  return (
    <section className="lh-login-callout" data-testid="login-callout">
      <div className="copy">
        <span className="eyebrow">Acceso</span>
        <h3>
          Una sola cuenta. Todo <em>tu trabajo</em>.
        </h3>
        <p>
          Entras y la plataforma te lleva directo a lo que falta — una observación por leer, una entrega por subir, una defensa que evaluar. Nada más.
        </p>
        <div className="alts">
          <span>¿Primera vez?</span>
          <a onClick={openModal}>Solicita acceso →</a>
        </div>
      </div>

      <form className="lh-login-card" onSubmit={handleSubmit}>
        <div className="step">— Iniciar sesión</div>
        <h4>Bienvenido de vuelta</h4>
        <label className="field">
          <span className="lbl">Correo institucional</span>
          <input
            type="email"
            autoComplete="email"
            placeholder="tu.nombre@usm.edu.ve"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="field">
          <span className="lbl">Contraseña</span>
          <input
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <div className="meta">
          <label className="check">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              style={{ marginRight: 6 }}
            />
            Mantener sesión
          </label>
          <button type="button" className="forgot" onClick={openModal}>
            ¿Olvidaste tu contraseña?
          </button>
        </div>
        {error && (
          <div style={{ marginBottom: 10, padding: "8px 12px", background: "#fef2f2", color: "#b91c1c", borderRadius: 8, fontSize: 12 }}>
            {error}
          </div>
        )}
        <button type="submit" className="submit" disabled={submitting}>
          {submitting ? "Verificando..." : "Continuar"}
        </button>
      </form>
    </section>
  );
}
