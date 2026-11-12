// /review-branch — Review del diff de la rama por dimensiones + verificación adversarial
//
// CUÁNDO: antes de un merge a develop/main; review repetible que quieres correr igual cada vez.
// COSTE: medio. APRUEBA antes de correr.
// ARGS: opcional — base ref a comparar (default "main"). Ej: args = "develop".
// Mapea a la skill `code-review-gate`, a `rita-pattern-keeper` (patterns) y a `roberto-clean-code`
// (mantenibilidad, fase 1: informa, no bloquea).
//
// Patrón: pipeline — cada dimensión verifica sus findings en cuanto termina (sin barrera).
//
// El verificador no juzga de oídas (GRF-6, `rules/verification.md` §Nivel 4):
//   · recibe la base y la orden de abrir el fichero y su diff, y su schema EXIGE `observed`
//     (fichero:línea de lo que vio él); un «es real» sin `observed` citable no cuenta.
//   · en `mantenibilidad` además RE-EJECUTA cada `evidence[].command` del hallazgo y devuelve su
//     salida; el JS (checkEvidence, abajo) compara la salida declarada con la observada y descarta el
//     hallazgo si no cuadra, si falta una re-ejecución o si el comando no es de solo lectura.
//     Prueba con un comando falso: `node .claude/smoke/review-branch/check_evidence.mjs`.
//   · Límites declarados del filtro: (1) los comandos corren en el repo revisado, así que git usa SU
//     config (`core.fsmonitor`, `diff.external`): revisa ramas de repos tuyos, no de terceros;
//     (2) `new_symbols.py`/`diff_metrics.py` se ejecutan desde el árbol de la rama: si la rama los
//     cambia, corre su versión (míralos en el diff antes de lanzar); (3) un `cat`/`grep` con ruta
//     absoluta lee fuera del repo (lee; no escribe ni ejecuta).

export const meta = {
  name: "review-branch",
  description:
    "Revisa el diff de la rama por dimensiones (bugs/seguridad/perf/patrones/mantenibilidad) y verifica cada finding contra el código, re-ejecutando la evidencia",
  phases: [{ title: "Review" }, { title: "Verify" }],
};

// Presupuesto (MO-74, sub-ola 2.18): `budget.total` es el «+Nk» que el Usuario pone al pedir el run, y es
// duro (al llegar, agent() lanza). Si no queda ni lo mínimo, no se arranca; sin él, mandan los topes
// de este script (sus .slice y el tamaño de sus entradas).
if (budget.total && budget.remaining() < 50_000) {
  log(`Presupuesto: quedan ${budget.remaining()} tokens; no arranco`)
  return { exit_code: 2, error: 'presupuesto insuficiente' }
}


const BASE = (typeof args === 'string' && args.trim()) ? args.trim() : 'main'

const DIMENSIONS = [
  {
    key: "bugs",
    prompt: `Revisa el diff de la rama actual vs ${BASE} (usa git diff ${BASE}...HEAD via Bash, o Read sobre los ficheros cambiados). Busca BUGS de correctitud: off-by-one, null/undefined, async mal manejado, edge cases. Devuelve findings concretos con file:line.`,
  },
  {
    key: "security",
    prompt: `Revisa el diff vs ${BASE} buscando problemas de SEGURIDAD: SQL raw sin parametrizar, secretos hardcodeados, auth/permisos faltantes, XSS/dangerouslySetInnerHTML, env vars expuestas. file:line + severidad.`,
  },
  {
    key: "perf",
    prompt: `Revisa el diff vs ${BASE} buscando problemas de PERFORMANCE: N+1 queries, loops sobre I/O, listados sin paginar, falta de select_related/prefetch. file:line.`,
  },
  {
    key: "patterns",
    prompt: `Eres rita-pattern-keeper (lee .claude/agents/rita-pattern-keeper.md y .claude/patterns/catalog.yaml ANTES). Corre bash .claude/hooks/pattern-check.sh y juzga SOLO los candidatos que salgan + los ejes no-deterministas del diff vs ${BASE} (léxico, contratos, reuso). Cada finding: infracción file:line + ≥2 PRECEDENTES file:line del repo + diff aplicable, o silencio. Máx 5. NUNCA bloqueas: severidad informativa. Si un patrón tiene dominancia <60%, NO es finding — repórtalo como "eje sin patrón" (decisión del owner).`,
  },
  {
    key: "mantenibilidad",
    evidenceRequired: true,
    prompt: `Eres roberto-clean-code (lee ENTERA .claude/agents/roberto-clean-code.md y su memory.md ANTES; sigue su protocolo y su tabla de severidad). Diff: git diff ${BASE}...HEAD más lo no commiteado. Tier 0, pega su salida: python3 .claude/scripts/new_symbols.py --base ${BASE} --run --json y python3 .claude/scripts/diff_metrics.py --base ${BASE} --json. Cada símbolo nuevo pasa por la pregunta «¿esto ya existía?» con sus búsquedas. Cada finding lleva evidence: [{command, output}] con el comando EXACTO que ejecutaste (solo lectura: grep, git diff/log/show/blame, cat, ls, los dos scripts de arriba; sin ;, &&, > ni $()) y su salida LITERAL (≤10 líneas): un verificador lo re-ejecutará y, si la salida no cuadra, el hallazgo se descarta. Presupuesto: todos los P0 y como mucho 5 P1/P2. Fase 1: informas, no bloqueas. No escribas ficheros: devuelve los findings.`,
  },
];

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'string' },
          severity: { type: 'string', enum: ['P0', 'P1', 'P2'] },
          evidence: { type: 'string' },
        },
        required: ['title', 'severity'],
      },
    },
  },
  required: ['findings'],
}

const EVIDENCE_FINDINGS_SCHEMA = {
  type: "object",
  properties: {
    findings: {
      type: "array",
      items: {
        type: "object",
        properties: {
          title: { type: "string" },
          file: { type: "string" },
          line: { type: "string" },
          severity: { type: "string", enum: ["P0", "P1", "P2"] },
          dimension: {
            type: "string",
            enum: [
              "reuse",
              "layer",
              "scope",
              "validation-errors",
              "clean-code",
              "stack",
            ],
          },
          evidence: {
            type: "array",
            minItems: 1,
            items: {
              type: "object",
              properties: {
                command: { type: "string" },
                output: { type: "string" },
              },
              required: ["command", "output"],
            },
          },
        },
        required: ["title", "severity", "file", "evidence"],
      },
    },
  },
  required: ["findings"],
};

const VERDICT_SCHEMA = {
  type: "object",
  properties: {
    isReal: { type: "boolean" },
    observed: {
      type: "string",
      description: "fichero:línea de lo que viste TÚ en el código, y qué había",
    },
    reasoning: { type: "string" },
  },
  required: ["isReal", "observed"],
};

const RERUN_VERDICT_SCHEMA = {
  type: "object",
  properties: {
    isReal: { type: "boolean" },
    observed: {
      type: "string",
      description: "fichero:línea de lo que viste TÚ en el código, y qué había",
    },
    reran: {
      type: "array",
      items: {
        type: "object",
        properties: {
          command: {
            type: "string",
            description: "el comando, copiado letra a letra",
          },
          exit: { type: "number" },
          output: {
            type: "string",
            description: "su salida literal (primeras 20 líneas)",
          },
        },
        required: ["command", "output"],
      },
    },
    reasoning: { type: "string" },
  },
  required: ["isReal", "observed", "reran"],
};

// <pure> — funciones sin efectos; las prueba .claude/smoke/review-branch/check_evidence.mjs
//
// Lista BLANCA de opciones por programa: lo que no está aquí se rechaza. Una lista negra no basta
// (git acepta abreviaturas: `--open-f=` es `--open-files-in-pager`; `sort` lanza
// `--compress-program`). `short`: letras que se pueden juntar (`-rn`); `long`: opciones largas
// exactas, sin abreviar; `withArg`: opciones que consumen el token siguiente.
const OPTION_SPECS = {
  grep: {
    short: "rnEFGwilcvhHoqsxIL",
    long: ["--include", "--exclude", "--exclude-dir", "--color", "--max-count"],
    withArg: ["-e", "-m", "-A", "-B", "-C"],
  },
  rg: {
    short: "niwFlcHIuS",
    long: ["--glob", "--type", "--fixed-strings", "--line-number", "--ignore-case", "--hidden", "--no-heading", "--color"],
    withArg: ["-e", "-g", "-t", "-m", "-A", "-B", "-C"],
  },
  cat: { short: "nA", long: [], withArg: [] },
  head: { short: "", long: [], withArg: ["-n"] },
  tail: { short: "", long: [], withArg: ["-n"] },
  wc: { short: "lcwm", long: [], withArg: [] },
  ls: { short: "lahR1dt", long: [], withArg: [] },
  find: {
    short: "",
    long: [],
    withArg: ["-name", "-iname", "-path", "-ipath", "-type", "-maxdepth", "-mindepth"],
    words: ["-print", "-not", "-o", "-a"],
  },
  sort: { short: "nrufVhb", long: [], withArg: ["-k", "-t"] },
  uniq: { short: "cdui", long: [], withArg: [] },
  cut: { short: "", long: [], withArg: ["-d", "-f", "-c"] },
};
const PIPE_ONLY = ["sort", "uniq", "cut"];
const GIT_SPEC = {
  short: "pswn",
  long: [
    "--stat",
    "--numstat",
    "--shortstat",
    "--name-only",
    "--name-status",
    "--oneline",
    "--no-color",
    "--format",
    "--pretty",
    "--porcelain",
    "--summary",
    "--no-patch",
    "--follow",
    "--cached",
    "--staged",
    "--error-unmatch",
    "--others",
    "--exclude-standard",
    "--verify",
    "--short",
    "--diff-filter",
    "--since",
    "--until",
    "--author",
    "--color-moved",
    "--line-number",
    "--ignore-case",
    "--extended-regexp",
    "--fixed-strings",
    "--count",
    "--files-with-matches",
    "--word-regexp",
  ],
  // `-n` y `-U` no llevan argumento separado en git (`-n` es una opción de git grep; `-U3` va
  // pegado): si lo llevaran, se tragarían la opción siguiente sin mirarla.
  withArg: ["-L", "-S", "-G", "-e"],
  attached: /^-(\d+$|L\d|U\d*$|S.|G.|n\d*$|M\d*$|C\d*$)/,
};
const SCRIPT_SPEC = {
  short: "",
  long: ["--base", "--diff", "--root", "--run", "--json", "--only", "--workers", "--timeout"],
  withArg: ["--base", "--diff", "--root", "--only", "--workers", "--timeout"],
};
const READ_ONLY_GIT = [
  "diff",
  "log",
  "show",
  "blame",
  "grep",
  "ls-files",
  "rev-parse",
  "merge-base",
];
const READ_ONLY_SCRIPTS = [
  ".claude/scripts/new_symbols.py",
  ".claude/scripts/diff_metrics.py",
];
const PIPE_TARGETS = ["grep", "head", "tail", "wc", "sort", "uniq", "cut"];

// Tokeniza como sh, pero solo lo inocuo: comillas simples literales, dobles sin `$`/`\`/backtick y
// tuberías simples. Cualquier otro metacarácter fuera de comillas (encadenar, fondo, redirigir,
// sustituir, escapar) devuelve null. Lo que va entre comillas es un argumento, no sintaxis.
function shellStages(cmd) {
  if (/[\n\r]/.test(cmd)) return null;
  const stages = [[]];
  let tok = null;
  let quote = null;
  for (let i = 0; i < cmd.length; i++) {
    const c = cmd[i];
    if (quote === "'") {
      if (c === "'") quote = null;
      else tok += c;
    } else if (quote === '"') {
      if (c === '"') quote = null;
      else if ("$`\\".includes(c)) return null;
      else tok += c;
    } else if (c === "'" || c === '"') {
      quote = c;
      tok = tok ?? "";
    } else if (/\s/.test(c)) {
      if (tok !== null) stages.at(-1).push(tok);
      tok = null;
    } else if (c === "|") {
      if (tok !== null) stages.at(-1).push(tok);
      tok = null;
      if (cmd[i + 1] === "|" || !stages.at(-1).length) return null;
      stages.push([]);
      // Sin globs sin comillas: un fichero de la rama llamado `--output=x` se volvería una opción.
    } else if (";&<>`$\\(){}*?[".includes(c)) return null;
    else tok = (tok ?? "") + c;
  }
  if (quote) return null;
  if (tok !== null) stages.at(-1).push(tok);
  return stages.every((s) => s.length) ? stages : null;
}

function isReadOnlyCommand(cmd) {
  if (typeof cmd !== "string" || !cmd.trim()) return false;
  const stages = shellStages(cmd);
  if (!stages) return false;
  const [first, ...rest] = stages;
  const head = first[0];
  let ok = false;
  if (head === "git") {
    let i = 1;
    while (first[i] === "-C" || first[i] === "--no-pager") {
      // Otro repo traería su propia config (core.fsmonitor, diff.external): solo dentro de este.
      if (first[i] === "-C" && !isInsidePath(first[i + 1])) return false;
      i += first[i] === "-C" ? 2 : 1;
    }
    // Lo que escribe o lanza un programa no pasa ni como valor de otra opción.
    if (first.some(isDangerousGitToken)) return false;
    ok =
      READ_ONLY_GIT.includes(first[i]) &&
      allowedArgs(first.slice(i + 1), GIT_SPEC) !== null;
  } else if (head === "python3" || head === "python") {
    const script = (first[1] || "").replace(/^\.\//, "");
    const argv = first.slice(2);
    const pathOk = argv.every((t, k) =>
      !["--root", "--diff"].includes(argv[k - 1]) && !/^--(root|diff)=/.test(t)
        ? true
        : isInsidePath(t.includes("=") ? t.split("=")[1] : t),
    );
    ok =
      READ_ONLY_SCRIPTS.includes(script) &&
      pathOk &&
      allowedArgs(argv, SCRIPT_SPEC) !== null;
  } else if (OPTION_SPECS[head] && !PIPE_ONLY.includes(head)) {
    ok = allowedArgs(first.slice(1), OPTION_SPECS[head]) !== null;
  }
  // Tras la tubería, filtros de la entrada estándar y sin ficheros (`uniq a b` escribe b); grep solo
  // con su patrón.
  return (
    ok &&
    rest.every((st) => {
      if (!PIPE_TARGETS.includes(st[0])) return false;
      const pos = allowedArgs(st.slice(1), OPTION_SPECS[st[0]]);
      return (
        pos !== null &&
        pos.length <= (st[0] === "grep" && !st.includes("-e") ? 1 : 0)
      );
    })
  );
}

// Ruta relativa que no sale del repo (sin `/` inicial, `~` ni `..`).
function isInsidePath(p) {
  return typeof p === "string" && p !== "" && !/^[/~]/.test(p) && !p.split("/").includes("..");
}

// Opciones de git que escriben o lanzan un programa, también abreviadas (`--open-f`, `--ext-d`).
const DANGEROUS_GIT = ["--output", "--open-files-in-pager", "--ext-diff", "--textconv", "--exec-path", "--config-env"];
function isDangerousGitToken(t) {
  if (/^-O/.test(t) || t === "-c") return true;
  const name = t.split("=")[0];
  return name.startsWith("--") && name.length >= 4 && DANGEROUS_GIT.some((d) => d.startsWith(name));
}

// Los argumentos posicionales si todas las opciones están en la lista blanca; si no, null.
function allowedArgs(argv, spec) {
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const t = argv[i];
    // En find, `--` no cierra las opciones: lo que va detrás seguiría siendo una primaria.
    if (t === "--" && spec.words) return null;
    if (t === "--") {
      positional.push(...argv.slice(i + 1));
      break;
    }
    if (!t.startsWith("-") || t === "-") {
      positional.push(t);
      continue;
    }
    if (spec.words?.includes(t)) continue;
    if (spec.withArg.includes(t)) {
      if (++i >= argv.length) return null;
      continue;
    }
    if (t.startsWith("--")) {
      if (!spec.long.includes(t.split("=")[0])) return null;
      continue;
    }
    if (spec.attached?.test(t)) continue;
    if (/^-\d+$/.test(t) && spec.withArg.includes("-n")) continue;
    if (t.length > 2 && spec.withArg.includes(t.slice(0, 2))) continue;
    if (![...t.slice(1)].every((c) => spec.short.includes(c))) return null;
  }
  return positional;
}

function outputLines(text) {
  return String(text ?? "")
    .split("\n")
    .map((l) => l.replace(/\s+/g, " ").trim())
    .filter((l) => l && !/^… \(\+\d+ líneas\)$/.test(l) && !/^\.\.\.$/.test(l));
}

// Cada línea que el hallazgo declara como salida tiene que aparecer en la salida re-ejecutada.
// Declarar «0 coincidencias» (salida vacía) exige que la re-ejecución tampoco encuentre nada.
function unrunnable(finding) {
  const evidence = Array.isArray(finding?.evidence) ? finding.evidence : [];
  if (!evidence.length) return "sin evidence[]: no hay nada que re-ejecutar";
  const bad = evidence.find((ev) => !isReadOnlyCommand(ev.command));
  return bad
    ? `comando no re-ejecutable (no es de solo lectura): ${bad.command}`
    : null;
}

function checkEvidence(finding, verdict) {
  const blocked = unrunnable(finding);
  if (blocked) return { ok: false, reason: blocked };
  const evidence = finding.evidence;
  const reran = Array.isArray(verdict?.reran) ? verdict.reran : [];
  for (const ev of evidence) {
    const r = reran.find((x) => (x.command || "").trim() === ev.command.trim());
    if (!r)
      return {
        ok: false,
        reason: `el verificador no re-ejecutó: ${ev.command}`,
      };
    const claimed = outputLines(ev.output);
    const observed = outputLines(r.output);
    if (!claimed.length && observed.length)
      return {
        ok: false,
        reason: `declaraba 0 coincidencias y hay ${observed.length}: ${ev.command}`,
      };
    const missing = claimed.filter((l) => !observed.some((o) => o.includes(l)));
    if (missing.length)
      return {
        ok: false,
        reason: `la salida no cuadra al re-ejecutar (${missing.length} líneas no salen): ${ev.command} → «${missing[0]}»`,
      };
  }
  return {
    ok: true,
    reason: `${evidence.length} comando(s) re-ejecutado(s); la salida cuadra`,
  };
}

function hasObserved(verdict) {
  return (
    typeof verdict?.observed === "string" &&
    /[\w./-]+:\d+/.test(verdict.observed)
  );
}

function decide(finding, verdict, evidenceRequired) {
  if (!verdict?.isReal)
    return { confirmed: false, reason: "el verificador lo refuta" };
  if (!hasObserved(verdict))
    return {
      confirmed: false,
      reason: "sin observed fichero:línea: confirmación de oídas",
    };
  if (!evidenceRequired)
    return { confirmed: true, reason: "confirmado contra el código" };
  const ev = checkEvidence(finding, verdict);
  return { confirmed: ev.ok, reason: ev.reason };
}
// </pure>

function verifyPrompt(f, dim) {
  const material = `Base: ${BASE}. Abre ${f.file || "los ficheros que cite"} y corre git diff ${BASE}...HEAD -- ${f.file || "."}. Juzga contra el código, no contra lo que se te cuenta. En "observed" pon fichero:línea de lo que viste TÚ.`;
  const rerun = dim.evidenceRequired
    ? ` Después re-ejecuta, letra a letra y sin cambiarlos, CADA comando de evidence[] (todos son de solo lectura) y devuelve en "reran" el comando copiado y su salida literal. No los arregles ni los adaptes: si un comando falla, devuelve el fallo.`
    : "";
  return `Verifica adversarialmente este finding (¿es REAL o falso positivo? sé escéptico, default a refutar si dudas). ${material}${rerun}\n\nFinding: ${JSON.stringify(f)}`;
}

const results = await pipeline(
  DIMENSIONS,
  (d) =>
    agent(d.prompt, {
      label: `review:${d.key}`,
      phase: "Review",
      schema: d.evidenceRequired ? EVIDENCE_FINDINGS_SCHEMA : FINDINGS_SCHEMA,
    }),
  (review, dim) =>
    parallel(
      (review?.findings || []).map((f) => () => {
        // Lo que no se puede re-ejecutar ni se manda al verificador.
        const blocked = dim.evidenceRequired ? unrunnable(f) : null;
        if (blocked) {
          return Promise.resolve({
            ...f,
            dimension: dim.key,
            verdict: null,
            decision: { confirmed: false, reason: blocked },
          });
        }
        return agent(verifyPrompt(f, dim), {
          label: `verify:${dim.key}`,
          phase: "Verify",
          schema: dim.evidenceRequired ? RERUN_VERDICT_SCHEMA : VERDICT_SCHEMA,
        }).then((v) => ({
          ...f,
          dimension: dim.key,
          verdict: v,
          decision: decide(f, v, dim.evidenceRequired),
        }));
      }),
    ),
);

const all = results.flat().filter(Boolean);
const confirmed = all.filter((f) => f.decision?.confirmed);
const discarded = all
  .filter((f) => !f.decision?.confirmed)
  .map((f) => ({
    title: f.title,
    dimension: f.dimension,
    reason: f.decision?.reason,
  }));
// Roberto está en fase 1: sus P0 se enseñan pero no bloquean.
const blockers = confirmed.filter(
  (f) => f.severity === "P0" && f.dimension !== "mantenibilidad",
);
log(
  `Confirmados: ${confirmed.length} · Descartados: ${discarded.length} · Bloqueantes P0: ${blockers.length}`,
);
return {
  base: BASE,
  confirmed,
  discarded,
  blockers,
  verdict: blockers.length ? "BLOQUEAR" : "PASS",
};
