/**
 * normalizeError — converts any thrown error, API response, or raw value
 * into a single friendly, user-facing message (Spanish). Used by the
 * notification system so every surfaced error across the app reads the
 * same way, never exposes stack traces, and never says "undefined".
 */

// Human-friendly fallbacks keyed by loose server error signals.
const SIGNAL_TO_FRIENDLY: Array<[RegExp, string]> = [
  [/network|failed to fetch|load failed|ERR_NETWORK/i, "No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo."],
  [/timeout/i, "La solicitud tardó demasiado. Por favor, inténtalo de nuevo."],
  [/abort/i, "La solicitud fue cancelada."],
  [/unauthorized|not authenticated|401/i, "Tu sesión ha expirado. Inicia sesión de nuevo para continuar."],
  [/forbidden|permission|403/i, "No tienes permisos para realizar esta acción."],
  [/not found|404/i, "No encontramos lo que estás buscando."],
  [/conflict|already exists|duplicate|unique/i, "Ese registro ya existe."],
  [/validation|invalid|required/i, "Revisa los campos marcados; hay algo que no es válido."],
  [/csrf/i, "Tu sesión parece desactualizada. Recarga la página e inténtalo de nuevo."],
  [/server error|internal|500|502|503|504/i, "Algo salió mal de nuestro lado. Ya estamos en ello — inténtalo en un momento."],
];

function polish(raw: string): string {
  let msg = raw.trim();
  if (!msg) return "";
  // Strip trailing punctuation repeats, normalize
  msg = msg.replace(/\.{2,}$/, ".").replace(/\s+/g, " ");
  // Capitalize first letter if it's lowercase ascii
  if (/^[a-zñáéíóú]/.test(msg)) {
    msg = msg.charAt(0).toUpperCase() + msg.slice(1);
  }
  // Ensure sentence ends cleanly
  if (!/[.!?…]$/.test(msg)) msg += ".";
  return msg;
}

function fromSignal(raw: string): string | null {
  for (const [re, friendly] of SIGNAL_TO_FRIENDLY) {
    if (re.test(raw)) return friendly;
  }
  return null;
}

function extractFromObject(obj: Record<string, unknown>): string | null {
  // DRF shapes we know about
  const candidates = ["detail", "message", "error", "non_field_errors"];
  for (const key of candidates) {
    const v = obj[key];
    if (typeof v === "string" && v.trim()) return v;
    if (Array.isArray(v) && typeof v[0] === "string") return v[0];
  }
  // Otherwise take the first string-ish value (field errors)
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === "string" && value.trim()) {
      return key === "detail" ? value : `${prettyField(key)}: ${value}`;
    }
    if (Array.isArray(value) && typeof value[0] === "string") {
      return `${prettyField(key)}: ${value[0]}`;
    }
  }
  return null;
}

function prettyField(key: string): string {
  const map: Record<string, string> = {
    email: "Correo",
    password: "Contraseña",
    full_name: "Nombre",
    fullName: "Nombre",
    username: "Usuario",
    title: "Título",
    period: "Período",
    start_month: "Mes de inicio",
    end_month: "Mes de cierre",
  };
  if (map[key]) return map[key];
  return key
    .replace(/_/g, " ")
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (c) => c.toUpperCase())
    .trim();
}

/**
 * Convert an unknown error value into a user-facing string.
 *
 * @param err      The caught value (Error, string, API response, etc.)
 * @param fallback Optional context-specific fallback, used only if the
 *                 error itself yields no usable message.
 */
export function normalizeError(err: unknown, fallback?: string): string {
  let raw: string | null = null;

  if (err == null) {
    raw = null;
  } else if (typeof err === "string") {
    raw = err;
  } else if (err instanceof Error) {
    raw = err.message;
  } else if (typeof err === "object") {
    raw = extractFromObject(err as Record<string, unknown>);
  }

  if (raw) {
    const signal = fromSignal(raw);
    if (signal) return signal;
    // Server-returned message is probably already human. Polish it.
    return polish(raw);
  }

  return polish(fallback || "Algo salió mal. Por favor, inténtalo de nuevo.");
}

/**
 * Shorthand: given a caught error in a try/catch, return the friendly
 * message using a fallback specific to the operation.
 */
export const friendlyError = normalizeError;
