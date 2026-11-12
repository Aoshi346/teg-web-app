import { useRegisterSW } from "virtual:pwa-register/react";

/**
 * «Hay una versión nueva · Actualizar» de una PWA con vite-plugin-pwa (`registerType: 'prompt'`).
 * Un service worker mal actualizado deja al usuario en una versión vieja sin que nadie lo vea: el
 * aviso le da el control, y el botón activa la versión nueva y recarga.
 *
 * Las cuatro piezas, todas necesarias (si falta una, el aviso no sale o sale tarde):
 *   1. vite.config.ts: `VitePWA({ registerType: 'prompt', ... })` — con 'autoUpdate' no hay aviso.
 *   2. Este componente, montado SOLO en producción: `{import.meta.env.PROD && <UpdateNotice />}`
 *      (en desarrollo y en los tests no hay service worker).
 *   3. Los textos por i18n (aquí, en claro para la plantilla): «Hay una versión nueva» · «Ahora no» ·
 *      «Actualizar».
 *   4. El servidor sirve `sw.js`, `registerSW.js`, `manifest.webmanifest` e `index.html` con
 *      `Cache-Control: no-cache` (nginx/demo.conf). Si el navegador cachea `sw.js`, nunca ve la nueva.
 *
 * Los estilos son los del design-system del proyecto: sustituye las clases por sus tokens.
 */
export function UpdateNotice() {
  const {
    needRefresh: [hasNewVersion, setHasNewVersion],
    updateServiceWorker,
  } = useRegisterSW();

  if (!hasNewVersion) return null;
  return (
    <div
      role="status"
      data-testid="pwa-update-notice"
      className="fixed inset-x-4 bottom-6 z-50 mx-auto flex max-w-md items-center gap-3 rounded-lg p-4"
    >
      <p className="m-0 flex-1 text-sm font-semibold">Hay una versión nueva</p>
      <button type="button" onClick={() => setHasNewVersion(false)}>
        Ahora no
      </button>
      <button
        type="button"
        data-testid="pwa-update-apply"
        onClick={() => void updateServiceWorker(true)}
      >
        Actualizar
      </button>
    </div>
  );
}
