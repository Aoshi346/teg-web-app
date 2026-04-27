"use client";

import React from "react";

interface FactibilidadToggleProps {
  isFactible: boolean | null;
  includesModelo: boolean | null;
  onChange: (next: { isFactible: boolean | null; includesModelo: boolean | null }) => void;
  disabled?: boolean;
}

export default function FactibilidadToggle({
  isFactible,
  includesModelo,
  onChange,
  disabled = false,
}: FactibilidadToggleProps) {
  const sec62Disabled = disabled || isFactible !== true;
  const showPenaltyHint = isFactible === true && includesModelo === false;

  function handleFactible(value: boolean) {
    if (value === false) {
      // Seleccionar No en 6.1 limpia includesModelo para evitar penalización residual
      onChange({ isFactible: false, includesModelo: null });
    } else {
      onChange({ isFactible: true, includesModelo });
    }
  }

  function handleModelo(value: boolean) {
    onChange({ isFactible, includesModelo: value });
  }

  return (
    <div className="factibilidad-toggle">
      {/* Sección 6.1 */}
      <div className="qcard" data-section="s6-1">
        <div className="qcard-header">
          <span className="qcard-num font-display">6.1</span>
          <div className="qcard-body">
            <div className="qcard-label-row">
              <h5 className="qcard-label">
                ¿El estudio constituye un proyecto factible?
              </h5>
            </div>
          </div>
          <span className="qcard-status">
            {isFactible === null ? "Pendiente" : "Respondida"}
          </span>
        </div>
        <div className="qcard-input">
          <div className="inp-seg v-yesno">
            <button
              type="button"
              disabled={disabled}
              aria-pressed={isFactible === true}
              className={isFactible === true ? "active success" : ""}
              onClick={() => handleFactible(true)}
            >
              Sí
            </button>
            <button
              type="button"
              disabled={disabled}
              aria-pressed={isFactible === false}
              className={isFactible === false ? "active danger" : ""}
              onClick={() => handleFactible(false)}
            >
              No
            </button>
          </div>
        </div>
      </div>

      {/* Sección 6.2 */}
      <div className="qcard" data-section="s6-2">
        <div className="qcard-header">
          <span className="qcard-num font-display">6.2</span>
          <div className="qcard-body">
            <div className="qcard-label-row">
              <h5 className="qcard-label">
                ¿Se adjunta el modelo operativo en el Capítulo 6?
              </h5>
            </div>
          </div>
          <span className="qcard-status">
            {!sec62Disabled && includesModelo !== null ? "Respondida" : "Pendiente"}
          </span>
        </div>
        <div className="qcard-input">
          <div className="inp-seg v-yesno">
            <button
              type="button"
              disabled={sec62Disabled}
              aria-pressed={includesModelo === true}
              className={includesModelo === true && !sec62Disabled ? "active success" : ""}
              onClick={() => handleModelo(true)}
            >
              Sí
            </button>
            <button
              type="button"
              disabled={sec62Disabled}
              aria-pressed={includesModelo === false}
              className={includesModelo === false && !sec62Disabled ? "active danger" : ""}
              onClick={() => handleModelo(false)}
            >
              No
            </button>
          </div>
        </div>
      </div>

      {/* Hint de penalización: solo cuando 6.1=Sí y 6.2=No */}
      {showPenaltyHint && (
        <div className="err-banner" role="alert">
          <span className="err-banner-msg">
            Se restarán <strong>-2</strong> puntos por no incluir el modelo operativo siendo un proyecto factible.
          </span>
        </div>
      )}
    </div>
  );
}
