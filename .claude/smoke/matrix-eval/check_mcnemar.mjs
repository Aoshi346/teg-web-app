#!/usr/bin/env node
// Prueba de CB-81 (3.39) en /matrix-eval-harness: el McNemar del panel lo calcula el JS, coincide con
// el de `templates/bot-evals/experiments.py` y llega al resultado. Sin modelo, coste 0: los agentes son
// dobles que devuelven scores fijos. Extrae el bloque <pure>, así que prueba el código que corre.
//
//   node .claude/smoke/matrix-eval/check_mcnemar.mjs        # 0 pasa · 1 falla · 2 no se pudo medir

import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repo = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = readFileSync(resolve(repo, ".claude/workflows/matrix-eval-harness.js"), "utf8");
const m = src.match(/\/\/ <pure>[^\n]*\n([\s\S]*?)\/\/ <\/pure>/);
if (!m) {
  console.log("⛔ NO SE PUDO MEDIR: falta el bloque <pure> del workflow");
  process.exit(2);
}
const pure = new Function(`${m[1]}; return { mcnemar, comparePaired };`)();
let fails = 0;
const check = (name, ok, extra = "") => {
  fails += ok ? 0 : 1;
  console.log(`${ok ? "✅" : "❌"} ${name}${extra ? ` — ${extra}` : ""}`);
};

// 1 · Paridad con Python (el mismo número en el panel y en el informe de agent-evals).
const pairs = [[10, 0], [3, 2], [12, 12], [30, 10], [5, 40]];
let py;
try {
  py = JSON.parse(
    execFileSync("python3", ["-I", "-c",
      "import json,sys; sys.path.insert(0, sys.argv[1]); import experiments as e; " +
      "print(json.dumps([e.mcnemar(b, c)[0] for b, c in json.loads(sys.argv[2])]))",
      resolve(repo, ".claude/templates/bot-evals"), JSON.stringify(pairs)], { encoding: "utf8" }));
} catch (e) {
  console.log(`⛔ NO SE PUDO MEDIR: python3 no carga experiments.py (${e.message.split("\n")[0]})`);
  process.exit(2);
}
pairs.forEach(([b, c], i) => {
  const js = pure.mcnemar(b, c).p;
  check(`McNemar(${b}, ${c}) igual en JS y en Python`, Math.abs(js - py[i]) < 1e-6, `${js.toFixed(6)} vs ${py[i].toFixed(6)}`);
});

// 2 · Emparejado por caso: una tasa igual con casos distintos no es «sin cambios» si no lo es.
const rows = (passed) => passed.map((p, i) => ({ case_id: `c${i}`, passed: p }));
const base = { case_results: rows(Array(40).fill(true)) };
const worse = { case_results: rows([...Array(10).fill(false), ...Array(30).fill(true)]) };
const r = pure.comparePaired(base, worse);
check("10 casos que empeoran → el candidato empeora", r.verdict === "el candidato empeora" && r.worse === 10, `p=${r.p}`);
check("sin case_results → sin medir, no un veredicto", pure.comparePaired(base, {}).measured === false);

// 3 · El workflow entero con dobles: el McNemar llega al resultado y a la instrucción del panel.
const AsyncFunction = Object.getPrototypeOf(async () => {}).constructor;
const scores = {
  "A-baseline": { config_id: "A-baseline", primary_metric: 1.0, notes: "", case_results: base.case_results },
  "B-variant": { config_id: "B-variant", primary_metric: 0.75, notes: "", case_results: worse.case_results },
};
let dashboardPrompt = "";
const agent = async (prompt, opts) => {
  if (opts.label === "dashboard") {
    dashboardPrompt = prompt;
    return "<html></html>";
  }
  const id = opts.label.split(":")[1];
  return scores[id];
};
const pipeline = async (items, run, verify) =>
  Promise.all(items.map(async (it) => verify(await run(it), it)));
const wf = new AsyncFunction("agent", "pipeline", "phase", "log", "args", "budget", src.replace(/^export /m, ""));
const out = await wf(agent, pipeline, () => {}, () => {},
  { paso0: { omitir: "smoke sin banco" }, langfuse: { dataset: "regresion-v1", run_prefix: "smoke" } }, {});
const b = out.mcnemar?.find((x) => x.config_id === "B-variant");
check("el resultado trae McNemar contra la referencia", b?.verdict === "el candidato empeora");
check("la nota del ganador lo dice", out.winner_note === "gana la referencia", out.winner_note);
check("el panel recibe los valores calculados", dashboardPrompt.includes('"verdict":"el candidato empeora"'));

process.exit(fails ? 1 : 0);
