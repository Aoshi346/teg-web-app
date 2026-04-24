import { useEffect } from "react";

export function useDirtyForm(isDirty: boolean, message = "Tienes cambios sin guardar. ¿Continuar?") {
  useEffect(() => {
    if (!isDirty) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = message;
      return message;
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty, message]);
}
