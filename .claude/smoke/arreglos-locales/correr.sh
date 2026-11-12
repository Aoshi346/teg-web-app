#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# correr.sh — los arreglos que aoshi-develop tiene y develop NO. Cada uno, demostrado.
#
# POR QUÉ. La política es paridad con develop (memoria `develop-is-read-only`). El 2026-09-23 el
# Usuario aceptó divergir en estos tres fallos, que develop también tiene. Una divergencia sin
# prueba es deuda invisible: si un día se re-sincroniza desde develop y se pisan, esto grita.
#
#   D-1 suggest-compact: la ventana sale del modelo, no de «1M si pasa de 200k»  → smoke/contexto/
#   D-2 SpecKit crea las sesiones en .specify/sessions/, donde las miden los gates (no en specs/)
#   D-3 pattern_check_agente: sin código LangGraph dice «nada que medir» y sale 2, no «✓»
#
# Aceptadas el 2026-09-28 (Aoshi, una a una, al montar aiatech-web):
#   D-4 template_diff / audit_sistema_ia ABORTAN (exit 2) si el template falta o es el proyecto
#   D-5 sembrar_v0.py deja en v0 lo medido tras copiar el template, y es idempotente
#   D-6 audit_sistema_ia: una pieza archivada y vuelta a la vida no sale como «ya retirada»
#   D-7 boris-plan-mode / boris-insights / codex / plan-dashboard fuera de las listas vivas
#   D-8 timeouts de hooks en SEGUNDOS (develop tiene 2000/3000 = 33/50 min) y PreToolUse con límite
#   D-9 los 30 agentes con `## What You Do Not Do` (rúbrica 5a de check-agent)
#
# Aceptada el 2026-10-03 (Aoshi, sync 2):
#   D-10 smoke/flujo N-03 declara `fuente:` en la entidad. develop (608b4d36) hizo obligatorio el
#        campo en gate_arranque.py y no actualizó el fixture: allí el smoke sale 29/30
#   D-11 pasos_de_actualizacion.py no da verdes falsos: template = su repo (no /home/tech-lead-
#        template), CONFIGURACION.yaml con RESPONDE_AQUI es «sin responder», check_mechanisms se
#        corre en la copia DEL PROYECTO, y sin template aborta con exit 2. (Lo de no exigir
#        notify-telegram.sh por proyecto cayó en la sync 3: Aoshi adoptó el hook de develop.)
#   D-12 template_diff ve el cementerio DEL PROYECTO (improvements #21): lo podado allí sale como
#        PODADO, no como MISSING — con estructura (`_archive/<fecha>/skills/x/`) y plano
#        (`skills/_retiradas/x/`). (El canal de Telegram ya se propone por proyecto: sync 3.)
#   D-13 task_progress ABORTA (exit 2) ante una marca desconocida (`[/]`, `[~]`) en vez de dejar la
#        línea fuera del recuento — cosechado de aquila-erp (049ca83), donde ERP-2 decía «doing 0»
#        con tres tareas en curso
#   D-14 check_mechanisms: lo que el proyecto PODÓ y el cuestionario sigue ofreciendo es AVISO, no
#        «roto» (aquila-erp daba 24 rotos por su poda aprobada). Lo que desapareció sin más, sigue roto
#   D-15 pattern-check.sh como pre-push juzga lo que SE PUBLICA (diff remoto..local). Antes miraba
#        «cambios sin commitear», que en un push es nada: decía «sin ficheros» y exit 0 siempre
#   D-16 medir_catalogo.py: el catálogo de un proyecto se MIDE (sembrar_v0 lo deja en []). Mide,
#        deja todo en `sombra` con propuesta, y tiene sus tres desenlaces: 0 medido · 1 sin código ·
#        2 comprobador roto
#   D-17 una regla de código BLOQUEA el push solo si el catálogo del proyecto la tiene en `activo`
#        (lo firma un humano), y solo en líneas que el push toca. La misma violación con la regla en
#        `sombra` avisa y deja pasar
#   D-20 estado_flujo.py sin SpecKit lee el plan de superpowers (la task con su commit en el historial cuenta
#        hecha; Decision-Maker, 2026-10-27)
#   D-18 estado_flujo.py (nuevo, lo pinta el tablero TL): cuenta bien, lista lo que falta por wave
#        con su id, elige la wave abierta, sin
#        sesión → null, marca desconocida → exit 2; --todos ignora copias -prod
#   D-19 template_diff no cuenta lo PODADO por el proyecto como core que falta (si no, un proyecto
#        podado nunca sale «al día»)
#
#   bash .claude/smoke/arreglos-locales/correr.sh
# ══════════════════════════════════════════════════════════════════════════════════════════════
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/smoke-arreglos-XXXXXX")"; trap 'rm -rf "$TMP"' EXIT
OK=0; KO=0
bien(){ OK=$((OK+1)); echo "  ✓ $1"; }; mal(){ KO=$((KO+1)); echo "  ✗ $1"; }

bash "$REPO/.claude/smoke/contexto/correr.sh" >/dev/null 2>&1 \
  && bien "D-1 suggest-compact: smoke/contexto en verde" || mal "D-1 suggest-compact: smoke/contexto en rojo"

mkdir -p "$TMP/sk" && cp -r "$REPO/.specify" "$TMP/sk/" && rm -rf "$TMP/sk/.specify/sessions"/* && (cd "$TMP/sk" && git init -q)
(cd "$TMP/sk" && bash .specify/scripts/bash/create-new-feature.sh --json "Aviso de cita" >/dev/null 2>&1)
if ls -d "$TMP/sk/.specify/sessions"/001-* >/dev/null 2>&1 && [ ! -d "$TMP/sk/specs" ]; then
  bien "D-2 /speckit.specify crea la sesión en .specify/sessions/ (y no en specs/)"
else mal "D-2 la sesión NO está en .specify/sessions/: los gates G-WAVE/G-SPEC no la verán"; fi
grep -q 'specs/' "$REPO"/.claude/commands/speckit.*.md \
  && mal "D-2 algún comando /speckit.* sigue mandando a specs/" || bien "D-2 ningún comando /speckit.* manda a specs/"

CHK="$REPO/.claude/patterns/stack/pattern_check_agente.py"
mkdir -p "$TMP/sin-agente" && printf 'def dispatcher(x):\n    return x\n' > "$TMP/sin-agente/app.py"
python3 "$CHK" "$TMP/sin-agente" >/dev/null 2>&1; rc=$?
[ $rc -eq 2 ] && bien "D-3 sin código LangGraph: exit 2, «nada que medir»" || mal "D-3 sin código LangGraph: exit $rc (el ✓ falso ha vuelto)"
mkdir -p "$TMP/con-agente" && printf 'from langgraph.graph import StateGraph\nfrom langchain_core.tools import tool\n\n@tool\ndef buscar(q: str) -> str:\n    """Busca."""\n    return q\n\ng = StateGraph(dict)\ng.add_node("buscar", buscar)\n' > "$TMP/con-agente/agente.py"
python3 "$CHK" "$TMP/con-agente" >/dev/null 2>&1 && bien "D-3 control: con un agente LangGraph sigue midiendo (exit 0)" || mal "D-3 control: con LangGraph ya no sale 0"
[ "$(python3 "$CHK" --json "$TMP/sin-agente" 2>/dev/null)" = "[]" ] && bien "D-3 --json (lo que lee pattern-check.sh) no cambia: []" || mal "D-3 --json ha cambiado: el hook se rompe"

bash "$REPO/.claude/smoke/instrumentos/template-ausente.sh" >/dev/null 2>&1 \
  && bien "D-4 template_diff y audit_sistema_ia abortan si no pueden medir (4/4)" || mal "D-4 algún instrumento vuelve a dar verde sin template"

mkdir -p "$TMP/copia" && cp -r "$REPO/.claude" "$TMP/copia/"
python3 "$REPO/.claude/scripts/sembrar_v0.py" "$TMP/copia" --app copia >/dev/null 2>&1
grep -q '^project: copia' "$TMP/copia/.claude/patterns/catalog.yaml" \
  && bien "D-5 sembrar_v0: el catálogo copiado ya no dice project: tech-lead-template" || mal "D-5 sembrar_v0 no resembró el catálogo"
python3 "$REPO/.claude/scripts/sembrar_v0.py" "$TMP/copia" --app copia 2>/dev/null | grep -q ': 0 ficheros a v0' \
  && bien "D-5 sembrar_v0 es idempotente (2ª pasada: 0)" || mal "D-5 sembrar_v0 vuelve a tocar ficheros en la 2ª pasada"

python3 "$REPO/.claude/scripts/audit_sistema_ia.py" "$TMP/copia" 2>&1 | grep -q 'YA RETIRÓ' \
  && mal "D-6 las piezas vivas vuelven a salir como «ya retiradas»" || bien "D-6 ninguna pieza viva sale como «ya retirada»"
mkdir -p "$TMP/copia/.claude/skills/boris-plan-mode" && printf -- '---\nname: boris-plan-mode\ndescription: x\n---\n' > "$TMP/copia/.claude/skills/boris-plan-mode/SKILL.md"
python3 "$REPO/.claude/scripts/audit_sistema_ia.py" "$TMP/copia" 2>&1 | grep -A1 'YA RETIRÓ' | grep -q boris-plan-mode \
  && bien "D-6 control: una retirada de verdad (boris-plan-mode) sí se caza" || mal "D-6 control: ya no caza una retirada real"

if grep -qE '"(codex-adversarial-review|plan-dashboard|boris-plan-mode)"' "$REPO/.claude/scripts/gen_agent_system.py" \
   || grep -qE '^- \[ \] boris-plan-mode|^- boris-plan-mode' "$REPO"/.claude/skills/{check-agent,create-agent,update-agent}/SKILL.md "$REPO"/.claude/skills/project-setup/references/*.md; then
  mal "D-7 una pieza archivada ha vuelto a una lista viva"; else bien "D-7 ninguna pieza archivada en las listas vivas"; fi

python3 - "$REPO/.claude/settings.json" <<'PY' && bien "D-8 timeouts de hooks en segundos y PreToolUse con límite" || mal "D-8 timeouts en ms o PreToolUse sin límite (33-50 min colgado)"
import json, sys
s = json.load(open(sys.argv[1]))
malos = [(ev, x["command"][-40:]) for ev, arr in s["hooks"].items() for h in arr for x in h["hooks"]
         if (x.get("timeout") or 0) >= 60 or (ev == "PreToolUse" and x.get("timeout") is None)]
sys.exit(1 if malos else 0)
PY

sin=0; for f in "$REPO"/.claude/agents/*.md; do [ "$(basename "$f")" = README.md ] && continue
  grep -qiE '^#+ *(What You Do Not Do|Lo que NO (hago|hace)|Prohibi)' "$f" || sin=$((sin+1)); done
[ $sin -eq 0 ] && bien "D-9 todos los agentes con sección de prohibiciones" || mal "D-9 $sin agente(s) sin sección «What You Do Not Do»"

grep -q 'caso N-03 .*\\"fuente\\":\\"propia\\"' "$REPO/.claude/smoke/flujo/correr.sh" \
  && bash "$REPO/.claude/smoke/flujo/correr.sh" >/dev/null 2>&1 \
  && bien "D-10 smoke/flujo 30/30, con N-03 declarando la fuente del dato" \
  || mal "D-10 smoke/flujo en rojo o N-03 sin \`fuente\`: la sync pisó el fixture"

P="$TMP/d11/.claude"; mkdir -p "$P/hooks" "$P/scripts"
printf 'respuestas:\n  stack: RESPONDE_AQUI\n  ui: si\n' > "$P/CONFIGURACION.yaml"
echo '{"hooks":{}}' > "$P/settings.json"
printf 'print("  ✗ roto de prueba")\nraise SystemExit(1)\n' > "$P/scripts/check_mechanisms.py"
PA="$REPO/.claude/scripts/pasos_de_actualizacion.py"
J=$(env -u TL_TEMPLATE_DIR python3 "$PA" "$TMP/d11" --json 2>/dev/null)   # sale 1 a propósito: hay pasos sin hacer
echo "$J" | python3 -c '
import json,sys; d={p["paso"][0]: p for p in json.load(sys.stdin)["pasos"]}
ok = d["2"]["estado"]=="falta" and "stack" in d["2"]["detalle"] \
     and d["7"]["estado"]=="falta"
sys.exit(0 if ok else 1)' && TL_TEMPLATE_DIR=/no/existe python3 "$PA" "$TMP/d11" >/dev/null 2>&1; [ $? -eq 2 ] \
  && bien "D-11 pasos_de_actualizacion: sin verdes falsos (config vacía, mecanismos del proyecto, sin template = 2)" \
  || mal "D-11 pasos_de_actualizacion vuelve a dar verdes falsos o no aborta sin template"

Q="$TMP/d12/.claude"; mkdir -p "$Q/_archive/2026-01-01-poda/skills/marca" "$Q/skills/_retiradas/nueva-pantalla"
echo x > "$Q/_archive/2026-01-01-poda/skills/marca/SKILL.md"; echo x > "$Q/skills/_retiradas/nueva-pantalla/SKILL.md"
python3 "$REPO/.claude/scripts/template_diff.py" "$TMP/d12" --template "$REPO" --json 2>/dev/null | python3 -c '
import json,sys; d=json.load(sys.stdin); pod=d.get("podado",{}); mis=d["missing"]
ok = "skills/marca/" in pod and "skills/nueva-pantalla/" in pod \
     and "skills/marca/" not in mis and "skills/nueva-pantalla/" not in mis
sys.exit(0 if ok else 1)' \
  && bien "D-12 template_diff: lo podado por el proyecto sale PODADO (estructurado y plano), no MISSING" \
  || mal "D-12 template_diff vuelve a proponer reinstalar lo que el proyecto podó"

# D-19 lo podado no cuenta como core que falta: si no, un proyecto podado nunca sale «al día».
gap(){ python3 "$REPO/.claude/scripts/template_diff.py" "$TMP/d19" --template "$REPO" --core --json 2>/dev/null \
  | python3 -c 'import json,sys,re; m=re.search(r"\((\d+) ficheros", json.load(sys.stdin)["core_state"]); print(m.group(1) if m else 0)'; }
mkdir -p "$TMP/d19/.claude"; G0=$(gap)
# Una pieza que siga siendo CORE (desde la sync 3 el core sale de los packs: patterns/stack/ ya no
# lo es, así que el fixture viejo no movía el contador y daba rojo sin que el arreglo fallara).
mkdir -p "$TMP/d19/.claude/_archive/2026-01-01-poda/skills/pattern-gate"; echo x > "$TMP/d19/.claude/_archive/2026-01-01-poda/skills/pattern-gate/SKILL.md"
G1=$(gap)
[ -n "$G0" ] && [ "$G0" -gt 0 ] && [ "$G1" -lt "$G0" ] \
  && bien "D-19 template_diff: lo podado no cuenta como core que falta ($G0 → $G1)" \
  || mal "D-19 template_diff cuenta lo podado en el CORE (sin podar $G0, podado $G1)"

printf '## Wave 1\n- [x] T1 hecha\n- [/] T2 a medias\n' > "$TMP/d13.md"
python3 "$REPO/.claude/scripts/task_progress.py" "$TMP/d13.md" >/dev/null 2>&1; [ $? -eq 2 ] \
  && bien "D-13 task_progress aborta (2) ante «[/]» en vez de no contarla" \
  || mal "D-13 task_progress vuelve a saltarse las marcas que no conoce"

R="$TMP/d14/.claude"; mkdir -p "$R/scripts" "$R/templates" "$R/agents" "$R/skills" "$R/_archive/poda/agents"
cp "$REPO/.claude/scripts/check_mechanisms.py" "$R/scripts/"; echo x > "$R/_archive/poda/agents/agente-podado.md"
printf 'preguntas:\n  - id: x\n    configura:\n      si:\n        agentes: [agente-podado, agente-fantasma]\n' > "$R/templates/configuracion-de-proyecto.yaml"
O=$(python3 "$R/scripts/check_mechanisms.py" 2>&1)
echo "$O" | grep -q "agente-podado.*PODÓ" && ! echo "$O" | grep -q "declara 'agente-podado'" \
  && echo "$O" | grep -q "declara 'agente-fantasma' y no existe" \
  && bien "D-14 check_mechanisms: lo podado es aviso y el fantasma sigue roto" \
  || mal "D-14 check_mechanisms vuelve a contar la poda del proyecto como mecanismo roto"

V="$TMP/d15"; git init -q --bare "$V/remoto.git" && git init -q "$V/repo" && cd "$V/repo"
git config user.email t@t; git config user.name t; mkdir -p .claude/hooks .claude/skills/buena .claude/skills/mala
cp "$REPO/.claude/hooks/pattern-check.sh" .claude/hooks/; ln -s ../../.claude/hooks/pattern-check.sh .git/hooks/pre-push
printf -- '---\nname: buena\ndescription: x\n---\n' > .claude/skills/buena/SKILL.md
git add -A && git commit -qm uno && git remote add origin "$V/remoto.git"
PATTERN_CHECK_SIN_CODIGO=1 git push -q origin HEAD:refs/heads/main >/dev/null 2>&1; LIMPIO=$?
printf -- '---\nname: mala\n---\n' > .claude/skills/mala/SKILL.md; git add -A && git commit -qm dos
PATTERN_CHECK_SIN_CODIGO=1 git push -q origin HEAD:refs/heads/main >/dev/null 2>&1; SUCIO=$?
cd "$REPO"
[ $LIMPIO -eq 0 ] && [ $SUCIO -ne 0 ] \
  && bien "D-15 pre-push: deja pasar el push limpio y bloquea la skill sin description que va en el commit" \
  || mal "D-15 pre-push ciego otra vez (limpio=$LIMPIO, sucio=$SUCIO; se esperaba 0 y ≠0)"

W="$TMP/d16"; mkdir -p "$W/.claude/patterns/stack" "$W/front/src"
cp "$REPO/.claude/patterns/stack/pattern_check_frontend.py" "$W/.claude/patterns/stack/"
echo '{"dependencies":{"react":"18"}}' > "$W/front/package.json"
printf 'export function AvisosProvider(){ return null }\n' > "$W/front/src/Avisos.tsx"
MC="$REPO/.claude/scripts/medir_catalogo.py"
python3 "$MC" "$W" --escribir >/dev/null 2>&1; E0=$?
python3 -c '
import yaml,sys; d=yaml.safe_load(open(sys.argv[1]))
f={p["id"]:p for p in d["patterns"]}; r=f["fe-un-componente-por-fichero"]
sys.exit(0 if r["estado"]=="sombra" and "1 sitios" in r["dominancia"] and all(p["estado"]=="sombra" for p in d["patterns"]) else 1)' "$W/.claude/patterns/catalog.yaml" 2>/dev/null; MIDE=$?
python3 - "$W/.claude/patterns/catalog.yaml" <<'PY' 2>/dev/null
import yaml,sys; f=sys.argv[1]; d=yaml.safe_load(open(f))
for p in d["patterns"]:
    if p["id"]=="fe-un-componente-por-fichero": p["estado"]="activo"; p["firmado"]="prueba"
open(f,"w").write(yaml.safe_dump(d,allow_unicode=True,sort_keys=False))
PY
python3 "$MC" "$W" --escribir >/dev/null 2>&1
python3 -c '
import yaml,sys; f={p["id"]:p for p in yaml.safe_load(open(sys.argv[1]))["patterns"]}
sys.exit(0 if f["fe-un-componente-por-fichero"].get("estado")=="activo" and f["fe-un-componente-por-fichero"].get("firmado")=="prueba" else 1)' "$W/.claude/patterns/catalog.yaml" 2>/dev/null || MIDE=1
mkdir -p "$TMP/d16b/.claude"; python3 "$MC" "$TMP/d16b" >/dev/null 2>&1; E1=$?
echo 'raise SystemExit(3)' > "$W/.claude/patterns/stack/pattern_check_frontend.py"; python3 "$MC" "$W" >/dev/null 2>&1; E2=$?
[ $E0 -eq 0 ] && [ $MIDE -eq 0 ] && [ $E1 -eq 1 ] && [ $E2 -eq 2 ] \
  && bien "D-16 medir_catalogo: mide (todo en sombra), re-medir conserva lo firmado, 1 sin código, 2 roto" \
  || mal "D-16 medir_catalogo (esperado 0/0/1/2, salió $E0/$MIDE/$E1/$E2)"

X="$TMP/d17"; git init -q --bare "$X/remoto.git" && git init -q "$X/repo" && cd "$X/repo"
git config user.email t@t; git config user.name t
mkdir -p .claude/hooks .claude/scripts .claude/patterns/stack .claude/patterns/baseline front/src
cp "$REPO/.claude/hooks/pattern-check.sh" .claude/hooks/; cp "$REPO/.claude/scripts/pattern_baseline.py" .claude/scripts/
cp "$REPO/.claude/patterns/stack/pattern_check_frontend.py" .claude/patterns/stack/
ln -s ../../.claude/hooks/pattern-check.sh .git/hooks/pre-push
echo 'export const ok = 1' > front/src/base.ts; git add -A && git commit -qm base && git remote add origin "$X/remoto.git"
git push -q origin HEAD:refs/heads/main >/dev/null 2>&1
printf 'export function pinta(el: HTMLElement){ el.innerHTML = "<b>x</b>" }\n' > front/src/pinta.ts
git add -A && git commit -qm innerhtml
printf 'patterns:\n  - id: fe-sin-innerhtml\n    estado: sombra\n' > .claude/patterns/catalog.yaml
git push -q --dry-run origin HEAD:refs/heads/main >/dev/null 2>&1; EN_SOMBRA=$?
printf 'patterns:\n  - id: fe-sin-innerhtml\n    estado: activo\n' > .claude/patterns/catalog.yaml
git push -q --dry-run origin HEAD:refs/heads/main >/dev/null 2>&1; EN_ACTIVO=$?
cd "$REPO"
[ $EN_SOMBRA -eq 0 ] && [ $EN_ACTIVO -ne 0 ] \
  && bien "D-17 el catálogo decide: fe-sin-innerhtml en sombra deja pasar, en activo bloquea el push" \
  || mal "D-17 el catálogo no decide (sombra=$EN_SOMBRA, activo=$EN_ACTIVO; se esperaba 0 y ≠0)"

# D-18 estado_flujo.py: el tablero TL lee el flujo de aquí, así que tiene que contar bien,
# elegir la wave sin cerrar y ABORTAR ante una marca que no sabe leer (no darla por cerrada).
Y="$TMP/d18"; mkdir -p "$Y/.claude/scripts" "$Y/.specify/sessions/ABC-1 - Prueba"
cp "$REPO/.claude/scripts/estado_flujo.py" "$REPO/.claude/scripts/task_progress.py" "$REPO/.claude/scripts/tasks_registry.py" "$Y/.claude/scripts/"
cat > "$Y/.specify/sessions/ABC-1 - Prueba/tasks.md" <<'MD'
## Wave 1 — Base
- [x] T1 hecho
- [x] T2 hecho
## Wave 2 — Medio
- [x] T3 hecho
- [!] T4 espera al cliente
- [ ] T5 siguiente
## Deuda
- [ ] D1 suelta
MD
J=$(python3 "$Y/.claude/scripts/estado_flujo.py" "$Y" --json 2>&1); E0=$?
echo "$J" | python3 -c '
import json,sys; d=json.load(sys.stdin); a=d["actual"]
ok = d["sesion"]["id"]=="ABC-1" and d["sesion"]["total"]==6 and [w["id"] for w in d["waves"]]==["1","2"] \
  and a["id"]=="2" and a["hecho"]==1 and a["total"]==3 and len(a["bloqueos"])==1 and a["siguiente"].startswith("T5") \
  and d["fuera"][0]["pend"]==1 and d["waves"][0]["abiertas"]==[] \
  and [(x["id"],x["estado"]) for x in d["waves"][1]["abiertas"]]==[("T4","bloq"),("T5","pend")]
sys.exit(0 if ok else 1)' 2>/dev/null; FORMA=$?
echo "- [/] T6 a medias" >> "$Y/.specify/sessions/ABC-1 - Prueba/tasks.md"
python3 "$Y/.claude/scripts/estado_flujo.py" "$Y" --json >/dev/null 2>&1; E2=$?
mkdir -p "$TMP/d18b"; S=$(python3 "$Y/.claude/scripts/estado_flujo.py" "$TMP/d18b" --json 2>/dev/null)
echo "$S" | python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin)["sesion"] is None else 1)' 2>/dev/null; NULA=$?
RZ="$TMP/d18r"; for d in uno dos tres-prod; do mkdir -p "$RZ/$d/.specify/sessions/ABC-2 - P"; printf '## Wave 1\n- [x] a\n- [ ] b\n' > "$RZ/$d/.specify/sessions/ABC-2 - P/tasks.md"; done
python3 "$Y/.claude/scripts/estado_flujo.py" --todos "$RZ" --json 2>/dev/null | python3 -c '
import json,sys; d=json.load(sys.stdin); n=sorted(p["proyecto"] for p in d["proyectos"])
sys.exit(0 if n==["dos","uno"] and d["consejo"] and "vigilancia" in d else 1)' 2>/dev/null; TODOS=$?
[ $E0 -eq 0 ] && [ $FORMA -eq 0 ] && [ $E2 -eq 2 ] && [ $NULA -eq 0 ] && [ $TODOS -eq 0 ] \
  && bien "D-18 estado_flujo: cuenta, elige la wave abierta, sin sesión → null, marca rara → exit 2, --todos ignora -prod" \
  || mal "D-18 estado_flujo (esperado 0/0/2/0/0, salió $E0/$FORMA/$E2/$NULA/$TODOS)"

# D-20 estado_flujo sin SpecKit lee el plan de superpowers más reciente. La Task cuyo commit ya está en
# el historial cuenta HECHA aunque sus casillas sigan en [ ] (superpowers no las marca: en Decision-
# Maker un plan terminado salía 0/77); la otra, por sus casillas. Y un commit de OTRA task del mismo
# ámbito no la cierra.
Z="$TMP/d20"; mkdir -p "$Z/docs/superpowers/plans" && git init -q "$Z" && git -C "$Z" config user.email t@t && git -C "$Z" config user.name t
cat > "$Z/docs/superpowers/plans/2026-01-02-demo.md" <<'MD'
# Demo — plan de implementacion
### Task 1: Primera
- [ ] **Step 1:** test
- [ ] **Step 2: Commit** `feat(demo): la primera cosa queda hecha`
### Task 2: Segunda
- [x] **Step 1:** test
- [ ] **Step 2:** implementar el resto
- [ ] **Step 3: Commit** `feat(demo): la segunda cosa distinta del todo`
MD
printf '# viejo\n### Task 1: x\n- [ ] **Step 1:** nada\n' > "$Z/docs/superpowers/plans/2025-01-01-viejo.md"
git -C "$Z" add -A && git -C "$Z" commit -qm "feat(demo): la primera cosa queda hecha" && git -C "$Z" commit -q --allow-empty -m "feat(demo): otra cosa que no es la segunda"
python3 "$REPO/.claude/scripts/estado_flujo.py" "$Z" --json 2>/dev/null | python3 -c '
import json,sys; d=json.load(sys.stdin); s=d["sesion"] or {}; w={x["id"]: (x["hecho"], x["total"]) for x in d.get("waves", [])}
ok = s.get("tipo")=="superpowers" and s.get("id")=="plan 01-02" and s.get("nombre")=="Demo" \
     and w=={"1": (2, 2), "2": (1, 3)} and d["actual"]["id"]=="2" and d["actual"]["siguiente"]=="Step 2: implementar el resto"
sys.exit(0 if ok else 1)' \
  && bien "D-20 estado_flujo lee el plan de superpowers: la task con su commit cuenta hecha, la otra por casillas" \
  || mal "D-20 estado_flujo no lee bien el plan de superpowers (task con commit, casillas, plan más reciente)"

echo "═══ $OK/$((OK+KO)) correctos"; [ "$KO" -eq 0 ]
