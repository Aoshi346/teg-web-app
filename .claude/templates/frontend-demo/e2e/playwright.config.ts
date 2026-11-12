import { defineConfig } from "@playwright/test";

/**
 * Playwright del recorrido crítico. NO se lanza a pelo: `npm run e2e` (e2e/run-e2e.mjs) crea y siembra
 * la base desechable, levanta los servidores en 127.0.0.1 y pasa aquí sus URLs; al terminar los para y
 * borra la base. Por eso no hay `webServer`: quien arranca y limpia es el runner.
 */
const WEB = process.env.E2E_WEB_URL;
if (!WEB) {
  throw new Error(
    "Lanza el E2E con `npm run e2e`: prepara la base desechable y la borra al terminar.",
  );
}

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  outputDir: "test-results",
  // Un navegador, un trabajador: el navegador cuenta doble en RAM (rules/ram-pytest.md).
  workers: 1,
  fullyParallel: false,
  // Sin reintentos en local: un E2E que necesita reintento está roto (verification.md §E2E-4).
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: WEB,
    locale: "es-ES",
    timezoneId: "Europe/Madrid",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "off",
  },
});
