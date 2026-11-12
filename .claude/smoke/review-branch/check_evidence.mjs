#!/usr/bin/env node
// Prueba de GRF-6 en /review-branch: un hallazgo cuyo comando no da la salida que declara se
// descarta, y uno honesto se confirma. Re-ejecuta comandos de verdad sobre el fixture de la 3.02
// (sin modelo, coste 0). Extrae el bloque <pure> del workflow, así que prueba el código que corre.
//
//   node .claude/smoke/review-branch/check_evidence.mjs        # 0 pasa · 1 falla · 2 no se pudo medir

import { readFileSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repo = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const wfPath = resolve(repo, ".claude/workflows/review-branch.js");
const fixture = ".docs/plans/2026-10-17-revision-integral-template/lote-27-10/3.02-prueba/head";
const src = readFileSync(wfPath, "utf8");

// 1 · El workflow entero compila (el runtime lo ejecuta como cuerpo de función asíncrona).
try {
  const AsyncFunction = Object.getPrototypeOf(async () => {}).constructor;
  new AsyncFunction("agent", "pipeline", "parallel", "log", "args", "budget", src.replace(/^export /m, ""));
} catch (e) {
  console.log(`❌ review-branch.js no compila: ${e.message}`);
  process.exit(1);
}

const m = src.match(/\/\/ <pure>[^\n]*\n([\s\S]*?)\/\/ <\/pure>/);
if (!m || !existsSync(resolve(repo, fixture))) {
  console.log("⛔ NO SE PUDO MEDIR: falta el bloque <pure> del workflow o el fixture de la 3.02");
  process.exit(2);
}
const pure = new Function(`${m[1]}; return { isReadOnlyCommand, unrunnable, checkEvidence, decide };`)();

// Re-ejecución real, como haría un verificador honesto. Solo llega aquí lo que pasa el filtro.
const run = (cmd) => {
  if (!pure.isReadOnlyCommand(cmd)) throw new Error(`no debería re-ejecutarse: ${cmd}`);
  try {
    return execFileSync("sh", ["-c", cmd], { cwd: repo, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  } catch (e) {
    return e.stdout || "";
  }
};
const honestVerdict = (f) => ({
  isReal: true,
  observed: `${fixture}/core/managers.py:7 def for_company_request`,
  reran: f.evidence.map((ev) => ({ command: ev.command, output: run(ev.command) })),
});

const cmd = `grep -rn for_company_request ${fixture}`;
const realOutput = run(cmd);
const cases = [
  {
    name: "hallazgo honesto: salida real → se confirma",
    finding: { title: "helper paralelo", severity: "P1", file: "workers/helpers.py", evidence: [{ command: cmd, output: realOutput }] },
    expect: true,
  },
  {
    name: "comando falso: salida inventada → se descarta",
    finding: { title: "helper paralelo", severity: "P1", file: "workers/helpers.py",
      evidence: [{ command: cmd, output: `${fixture}/core/managers.py:99:    def for_company_request(self, request, strict=True):` }] },
    expect: false,
  },
  {
    name: "negativo falso: dice 0 coincidencias y las hay → se descarta",
    finding: { title: "no existe equivalente", severity: "P1", file: "workers/helpers.py", evidence: [{ command: cmd, output: "" }] },
    expect: false,
  },
  {
    name: "comando que no existe en el repo (grep de un símbolo inventado) con salida inventada → se descarta",
    finding: { title: "x", severity: "P0", file: "workers/helpers.py",
      evidence: [{ command: `grep -rn get_workers_safe ${fixture}`, output: `${fixture}/workers/utils.py:3:def get_workers_safe():` }] },
    expect: false,
  },
];

let fails = 0;
for (const c of cases) {
  const got = pure.decide(c.finding, honestVerdict(c.finding), true);
  const ok = got.confirmed === c.expect;
  fails += ok ? 0 : 1;
  console.log(`${ok ? "✅" : "❌"} ${c.name} — ${got.reason}`);
}

// Filtro de solo lectura: lo que escribe o encadena no se re-ejecuta ni llega al verificador.
const commands = [
  [`grep -rn x ${fixture} | head -5`, true],
  [`git -C ${fixture} diff develop...HEAD -- a.py`, true],
  ["git blame -L 1,+3 HEAD -- a.py", true],
  ["python3 .claude/scripts/new_symbols.py --base develop --run --json", true],
  ["sed -i s/a/b/ a.py", false],
  ["grep x a.py; rm -rf /tmp/x", false],
  ["grep x a.py > out.txt", false],
  ["git push origin develop", false],
  ["git diff --output=/tmp/x", false],
  ["find . -delete", false],
  ["cat $(echo a.py)", false],
  ["grep x a.py | sh", false],
  ["python3 otro_script.py", false],
  // Lo que emite new_symbols.py: patrones entre comillas con | y \s son argumentos, no sintaxis.
  [`grep -rn -E '--include=*.py' --exclude-dir=.git -e '@tool|StructuredTool' ${fixture}`, true],
  [`grep -rn -E -i -e '^\\s*(async\\s+)?(def|class)\\s+\\w*company\\w*' ${fixture}`, true],
  // Huecos que encontró el verificador de la 3.03: escriben o lanzan otro programa.
  ["cat a & touch /tmp/x", false],
  ["cat a\ntouch /tmp/x", false],
  ["grep x f | sort -o /tmp/y", false],
  ["grep x f | uniq - /tmp/y", false],
  ["rg --pre sh x", false],
  ["find . -fls /tmp/z", false],
  ["git -c core.pager=sh log", false],
  ["git grep -O x", false],
  ["grep x \"$(id)\"", false],
  ["grep 'a' | ", false],
  // Segunda pasada del verificador: abreviaturas y opciones que lanzan programas o leen fuera.
  ["git grep --open-f=/tmp/prog hi -- a", false],
  ["grep x f | sort -S 1k --compress-program=sh", false],
  ["grep x f | sort --files0-from=f", false],
  ["python3 /tmp/evil/.claude/scripts/new_symbols.py --base main", false],
  ["git diff --ext-d", false],
  ["git diff --out=/tmp/x", false],
  ["rg --hostname-bin=prog --hyperlink-format=x y", false],
  ["rg --search-zip x", false],
  ["git show --textconv HEAD", false],
  ["git blame --contents /etc/passwd f", false],
  ["git diff --no-index a /etc/shadow", false],
  // Tercera pasada: una opción que «consume» la siguiente y rutas fuera del repo.
  ["git diff -U --output=/tmp/F", false],
  ["git grep -n --open-files-in-pager=/tmp/prog hi", false],
  ["git grep -n -O/tmp/prog hi", false],
  ["git log -S --output=/tmp/F", false],
  ["git show -L 1,+3:a.py --textconv", false],
  ["git -C /tmp/otro log", false],
  ["git -C ../otro log", false],
  ["python3 .claude/scripts/new_symbols.py --base main --root /tmp/otro", false],
  ["python3 .claude/scripts/diff_metrics.py --base main --root ../otro", false],
  // Cuarta pasada: un glob sin comillas expande a un fichero llamado `--output=x`; `--` en find.
  ["git log -p *", false],
  ["git grep -e def ?.py", false],
  ["rg foo [a-z]*", false],
  ["find . -- -fprint x", false],
  ["grep -rn x '--include=*.py' .", true],
  ["git diff -U3 develop...HEAD -- a.py", true],
  ["git grep -n -e for_company_request", true],
  ["git log --oneline -5 -- a.py", true],
  ["git diff -M -C --stat develop...HEAD", true],
];
for (const [c, exp] of commands) {
  const ok = pure.isReadOnlyCommand(c) === exp;
  fails += ok ? 0 : 1;
  if (!ok) console.log(`❌ filtro de solo lectura: «${c}» debería ser ${exp ? "aceptado" : "rechazado"}`);
}
console.log(`${fails ? "❌" : "✅"} filtro de solo lectura: ${commands.length} comandos`);

// Sin falsos negativos: TODAS las búsquedas que emite new_symbols.py sobre el fixture se aceptan.
const emitted = JSON.parse(execFileSync("python3", [".claude/scripts/new_symbols.py", "--diff",
  `${fixture}/../diff.patch`, "--root", fixture, "--json"], { cwd: repo, encoding: "utf8" }))
  .symbols.flatMap((s) => s.searches.map((q) => q.command));
const refused = emitted.filter((c) => !pure.isReadOnlyCommand(c));
fails += refused.length || !emitted.length ? 1 : 0;
console.log(`${refused.length || !emitted.length ? "❌" : "✅"} búsquedas de new_symbols aceptadas: ${emitted.length - refused.length}/${emitted.length}${refused.length ? ` — rechaza: ${refused[0]}` : ""}`);

// Sin re-ejecución, o sin observed citable, no se confirma (aunque isReal sea true).
const f0 = cases[0].finding;
const noRerun = pure.decide(f0, { isReal: true, observed: "a.py:1", reran: [] }, true);
const noObserved = pure.decide({ title: "bug", severity: "P1" }, { isReal: true, observed: "lo he mirado" }, false);
const withObserved = pure.decide({ title: "bug", severity: "P1" }, { isReal: true, observed: "src/a.ts:12 if (x = 1)" }, false);
for (const [name, got, exp] of [
  ["sin re-ejecución → se descarta", noRerun, false],
  ["dimensión sin evidence: observed sin fichero:línea → se descarta (de oídas)", noObserved, false],
  ["dimensión sin evidence: observed con fichero:línea → se confirma", withObserved, true],
]) {
  const ok = got.confirmed === exp;
  fails += ok ? 0 : 1;
  console.log(`${ok ? "✅" : "❌"} ${name} — ${got.reason}`);
}

process.exit(fails ? 1 : 0);
