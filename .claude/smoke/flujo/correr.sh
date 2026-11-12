#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# correr.sh — los sabotajes del flujo de arranque. Cada gate se ve FALLAR antes de confiar en él.
#
# POR QUÉ. `rules/verification.md`: «un chequeo verde no está verificado; solo está sin ejecutar
# contra el caso que lo rompe». Al escribir estos gates, tres sabotajes encontraron bugs propios
# que leer el código NO habría encontrado:
#   · `\bTODO\b` y `\bPENDIENTE\b` con re.I casaban con las palabras españolas normales «todo» y
#     «pendiente» → CUALQUIER documento en español fallaba el gate.
#   · `flow_state --check` decía «✓ refleja el disco» con el state.json editado a mano a verde.
#   · `gen_proceso` pintaba Marca, Backend y QA cerrados sin haberse hecho.
#
# CONTROLES NEGATIVOS incluidos, y no son decorado: sin ellos no se distingue un gate que
# discrimina de uno que dice que no a todo. El del PRD encontró que el suelo de tamaño estaba
# mal calibrado y suspendía un documento correcto por 104 bytes.
#
# Todo corre sobre una COPIA en $TMPDIR. Nunca sobre el repo vivo.
#
#   bash .claude/smoke/flujo/correr.sh          # todos
#   bash .claude/smoke/flujo/correr.sh S-01     # uno
# ══════════════════════════════════════════════════════════════════════════════════════════════
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SOLO="${1:-}"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/smoke-flujo-XXXXXX")"
# Sin carpeta temporal, $TMP queda vacío y el fixture se monta en la RAÍZ (/proyecto, /fuera): pasó el
# 21-10 con un TMPDIR que no existía (verificador de la 2.18). El instrumento que no puede montar su
# sujeto aborta (rules/verification.md §El instrumento que no puede medir).
if [ -z "$TMP" ] || [ ! -d "$TMP" ]; then
  echo "✗ no se pudo crear la carpeta temporal en ${TMPDIR:-/tmp} (¿existe TMPDIR?): no corro nada" >&2
  exit 2
fi
trap 'rm -rf "$TMP"' EXIT
OK=0; KO=0; SALTADOS=0

# ── el fixture: un proyecto de juguete con el harness dentro ──────────────────────────────────
FIX="$TMP/proyecto"
mkdir -p "$FIX/.claude/scripts" "$FIX/.claude/templates" "$FIX/.docs/plans/2026-01-01-p/arranque" \
         "$FIX/.docs/flow" "$FIX/backend"
for s in gate_arranque.py spec_lint.py flow_state.py gen_modelo_datos.py; do
  cp "$REPO/.claude/scripts/$s" "$FIX/.claude/scripts/" 2>/dev/null
done
cp "$REPO/.claude/templates/"{prd,requisito}-template.md "$FIX/.claude/templates/" 2>/dev/null
PLAN="$FIX/.docs/plans/2026-01-01-p"
ARR="$PLAN/arranque"

prd_bueno(){ cat > "$ARR/01-prd.md" <<'EOF'
---
reviewed: 2026-01-01
reviewed_by: Ana Ruiz
---
# PRD · Gestor de citas
## El problema
Las recepcionistas apuntan las citas en un cuaderno y en el móvil del doctor. Cuando alguien llama
para cambiar una hora hay que mirar los dos sitios y a veces no coinciden. Pasa unas quince veces
por semana y cada llamada se lleva cuatro minutos de más.
## Quién decide
El alcance lo decide la doctora, que es quien paga. Mantenimiento: su hijo. Veto técnico: el
proveedor del programa de facturación.
## Qué será verdad cuando exista
Una recepcionista ve las citas del día en una pantalla y puede moverlas sin llamar a nadie.
Métrica objetivo: las cuarenta horas al mes de cuadrar agendas bajan a menos de diez. Hoy están
medidas en cuarenta y dos sobre un mes de registro manual.
## Qué queda fuera
La facturación no entra. Tampoco el historial clínico.
EOF
}

# Relleno determinista. Antes era `head -c N /dev/urandom | base64`, y eso podía generar por
# azar las marcas que el gate busca (TODO/XXX son secuencias válidas en base64): el smoke daba
# resultados distintos entre ejecuciones. Un fixture que no es reproducible no es una prueba.
relleno(){ python3 -c "print(('Texto de relleno para el fixture, sin marcas ni huecos. '*40)[:$1])"; }
export -f relleno   # `sh -c` no hereda funciones; con `bash -c` y export, sí

caso(){  # caso <id> <descripción> <exit_esperado> <comando…>
  local id="$1" desc="$2" esp="$3"; shift 3
  [ -n "$SOLO" ] && [ "$SOLO" != "$id" ] && { SALTADOS=$((SALTADOS+1)); return; }
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  if [ "$rc" = "$esp" ]; then
    OK=$((OK+1)); printf '  ✓ %-8s %s\n' "$id" "$desc"
  else
    KO=$((KO+1)); printf '  ✗ %-8s %s\n      esperaba exit %s, dio %s\n      %s\n' \
      "$id" "$desc" "$esp" "$rc" "$(printf '%s' "$out" | head -2 | tr '\n' ' ')"
  fi
}

G="python3 $FIX/.claude/scripts/gate_arranque.py"
F="python3 $FIX/.claude/scripts/flow_state.py"
H="$REPO/.claude/hooks/gate-arranque.sh"

echo "SABOTAJES DEL FLUJO — cada gate tiene que FALLAR cuando le plantas la violación"
echo
echo "· gate de arranque"
caso S-01 "la plantilla del PRD copiada sin tocar"            1 bash -c "cp '$FIX/.claude/templates/prd-template.md' '$ARR/01-prd.md'; $G '$FIX' --fase prd"
caso S-02 "plantilla con los huecos rellenados, cuerpo igual" 1 bash -c "python3 - '$FIX' <<'PY'
import re,sys,pathlib
r=pathlib.Path(sys.argv[1]); t=(r/'.claude/templates/prd-template.md').read_text()
t=re.sub(r'<[^>]{2,60}>','Gestor',t); t=re.sub(r'\[PERSONALIZAR\]|\[rellenar\]','X',t)
t=re.sub(r'\bTODO\b|\bPENDIENTE\b|\bXXX\b|\bTBD\b','ok',t).replace('YYYY-MM-DD','2026-01-01')
t+='\nreviewed: 2026-01-01\nreviewed_by: A\nMétrica: 40 horas\n'
(r/'.docs/plans/2026-01-01-p/arranque/01-prd.md').write_text(t)
PY
$G '$FIX' --fase prd"
caso S-03 "PRD sin ninguna métrica con su valor"              1 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# PRD\n%s\n' \"\$(relleno 900)\" > '$ARR/01-prd.md'; $G '$FIX' --fase prd"
caso S-04 "sin plan de arranque: ABORTA, no aprueba"          3 bash -c "$G '$TMP' --fase prd"
caso S-05 "requisitos sin ningún verbo normativo"             1 bash -c "mkdir -p '$ARR'; printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# Requisitos\n## R-1\nEl sistema puede guardar cosas y estaría bien que avisara.\nDado que hay algo cuando pasa entonces se ve.\n%s\n' \"\$(relleno 1400)\" > '$ARR/02-requisitos.md'; $G '$FIX' --fase requisitos"
caso S-06 "requisitos sin ningún Dado/Cuando/Entonces"        1 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# Requisitos\n## R-1\nEl sistema DEBE guardar la cita y DEBE avisar al cliente.\n%s\n' \"\$(relleno 1400)\" > '$ARR/02-requisitos.md'; $G '$FIX' --fase requisitos"
caso S-07 "máquina de estados SIN estado final"               1 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# Requisitos\n## R-1\nEl sistema DEBE guardar la cita.\nDado que hay hueco cuando reservo entonces se guarda.\n### El recorrido, como máquina de estados\n| sin empezar | inicio |\n| en curso | trabajo |\n%s\n' \"\$(relleno 1300)\" > '$ARR/02-requisitos.md'; $G '$FIX' --fase requisitos"
caso S-08 "campo sin 'personal: true|false' en entidades"     1 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\nmodelo de datos\n%s\n' \"\$(relleno 700)\" > '$ARR/03-modelo-datos.md'; printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\nflujos\n%s\n' \"\$(relleno 500)\" > '$ARR/04-flujos.md'; printf '{\"entidades\":[{\"nombre\":\"Cliente\",\"campos\":[{\"nombre\":\"nif\",\"tipo\":\"texto\"}]}],\"reviewed\":\"2026-01-01\",\"reviewed_by\":\"A\"}' > '$ARR/entidades.json'; $G '$FIX' --fase datos"
# Un JSON roto pero de tamaño razonable. El fixture anterior tenía 16 B y fallaba por el suelo
# de tamaño antes de llegar al parseo — el gate acertaba y la PRUEBA estaba mal planteada.
caso S-09 "entidades.json roto → NO MEDIBLE, no incumplimiento" 2 bash -c "python3 -c \"open('$ARR/entidades.json','w').write('{\\\"entidades\\\": [' + '{\\\"nombre\\\": \\\"Cliente\\\"},'*6 + ' ESTO ROMPE EL JSON ]}')\"; $G '$FIX' --fase datos"
caso S-10 "stack sin declarar base de datos ni despliegue"    1 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# Stack\nUsamos Python con Django.\n%s\n' \"\$(relleno 600)\" > '$ARR/05-stack.md'; $G '$FIX' --fase stack"
caso S-11 "datos personales sin base legal"                   1 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# Ética\nTratamos datos personales de los pacientes.\n%s\n' \"\$(relleno 600)\" > '$ARR/06-etica-privacidad.md'; $G '$FIX' --fase etica"
caso S-12 "seguridad: solo límite por IP, sin 2FA"            1 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# Superficie\nQuién entra: las recepcionistas.\nPonemos fail2ban y límite por IP en el login.\nLímite de intentos: 5.\nNo se publica ningún puerto, va tras el proxy.\nLos logs no guardan contraseñas.\n%s\n' \"\$(relleno 400)\" > '$ARR/07-superficie.md'; $G '$FIX' --fase seguridad"

echo
echo "· hook bloqueante"
caso S-13 "sin TL_ARRANQUE no hace nada (opt-in)"             0 bash -c "bash '$H' --file '$FIX/backend/models.py'"
caso S-14 "un .md nunca bloquea"                              0 bash -c "TL_ARRANQUE=1 CLAUDE_PROJECT_DIR='$FIX' bash '$H' --file '$FIX/README.md'"
caso S-15 "un fichero del harness nunca bloquea"              0 bash -c "TL_ARRANQUE=1 CLAUDE_PROJECT_DIR='$FIX' bash '$H' --file '$FIX/.claude/scripts/x.py'"
caso S-16 "BLOQUEA de verdad un .py de producto (exit 2)"     2 bash -c "rm -f '$FIX/.docs/arranque/.block-count'; TL_ARRANQUE=1 CLAUDE_PROJECT_DIR='$FIX' bash '$H' --file '$FIX/backend/models.py'"
caso S-17 "exención con motivo corto no vale"                 2 bash -c "mkdir -p '$FIX/.docs/arranque'; printf 'autorizado_por: M\ncaduca: 2099-01-01\nalcance: spike\nmotivo: >\n  ok\n' > '$FIX/.docs/arranque/EXENCION.md'; rm -f '$FIX/.docs/arranque/.block-count'; TL_ARRANQUE=1 CLAUDE_PROJECT_DIR='$FIX' bash '$H' --file '$FIX/backend/models.py'"
caso S-18 "exención CADUCADA vuelve a bloquear"               2 bash -c "printf 'autorizado_por: M\ncaduca: 2020-01-01\nalcance: spike\nmotivo: >\n  Prueba de la libreria con el fichero real, se tira el viernes\n' > '$FIX/.docs/arranque/EXENCION.md'; rm -f '$FIX/.docs/arranque/.block-count'; TL_ARRANQUE=1 CLAUDE_PROJECT_DIR='$FIX' bash '$H' --file '$FIX/backend/models.py'"

echo
echo "· tablero de cumplimiento"
caso S-19 "sin manifiesto: ABORTA (exit 3)"                   3 bash -c "$F '$TMP'"
caso S-20 "state.json editado a mano a verde"                 1 bash -c "$F '$FIX' --init >/dev/null; $F '$FIX' --write >/dev/null 2>&1; python3 - '$FIX' <<'PY'
import json,sys,pathlib
p=pathlib.Path(sys.argv[1],'.docs/flow/state.json'); d=json.loads(p.read_text())
d['veredicto']='cumple'
for g in d.get('gates',[]): g['estado']='cumple'
p.write_text(json.dumps(d))
PY
$F '$FIX' --check"
caso S-21 "waiver con alcance '*' se rechaza"                 1 bash -c "printf '%s\n' '{\"gate\":\"G-SPEC\",\"razon\":\"una razon larga de mas de cuarenta caracteres para pasar\",\"alcance\":\"*\",\"caduca\":\"2099-01-01\",\"quien\":\"M\"}' > '$FIX/.docs/flow/waivers.jsonl'; $F '$FIX' --verify-waivers"
caso S-22 "waiver con caducidad de 90 días se rechaza"        1 bash -c "printf '%s\n' '{\"gate\":\"G-SPEC\",\"razon\":\"una razon larga de mas de cuarenta caracteres para pasar\",\"alcance\":\"plan-x\",\"caduca\":\"2099-01-01\",\"quien\":\"M\"}' > '$FIX/.docs/flow/waivers.jsonl'; $F '$FIX' --verify-waivers"

# ── sub-ola 2.17 (MO-61 · PV-76): la firma, el stack ELEGIDO y las rutas del hook ─────────────────
# Casos medidos en fitapp (y en elvion): con el gate de antes, los S- pasaban (exit 0) y N-09
# bloqueaba. Los controles N- de aquí van antes de los de abajo porque tienen que correr con el
# arranque A MEDIAS: un «no bloquea» con el arranque cerrado no prueba nada. Un S- del gate no basta
# con que salga 1: tiene que salir POR SU MOTIVO (`falla_por`), y hay uno por mecanismo, para que
# apagar cualquiera ponga algo en rojo (code-review-gate de la 2.17: 7 de 10 se podían apagar sin que
# el smoke se enterara).
prd_con(){  # prd_con '<frontmatter sin las ---, con \n>': el PRD bueno con otra firma
  prd_bueno
  python3 - "$ARR/01-prd.md" "$1" <<'PY'
import re, sys, pathlib
p = pathlib.Path(sys.argv[1]); fm = sys.argv[2].replace('\\n', '\n')
p.write_text(re.sub(r'\A---\n.*?\n---\n', lambda _: '---\n' + fm + '\n---\n', p.read_text(), flags=re.S))
PY
}
stack_con(){  # stack_con '<cuerpo, con \n>': un 05-stack.md firmado con ese cuerpo
  printf -- '---\nreviewed: 2026-01-01\nreviewed_by: Ana Ruiz\n---\n# Stack\n%b\n%s\n' "$1" "$(relleno 500)" > "$ARR/05-stack.md"
}
falla_por(){  # falla_por <fase> <texto>: 1 solo si el gate sale con 1 y POR ese motivo
  local out rc
  out="$(python3 "$FIX/.claude/scripts/gate_arranque.py" "$FIX" --fase "$1" --json 2>&1)"; rc=$?
  [ "$rc" = 1 ] && printf '%s' "$out" | grep -qF -- "$2" && return 1
  return 0
}
avisa(){  # avisa <fase> <texto>: 0 solo si el gate pasa (0) y deja ese aviso
  local out rc
  out="$(python3 "$FIX/.claude/scripts/gate_arranque.py" "$FIX" --fase "$1" --json 2>&1)"; rc=$?
  [ "$rc" = 0 ] && printf '%s' "$out" | grep -qF -- "$2"
}
export ARR FIX; export -f prd_bueno prd_con stack_con falla_por avisa

echo
echo "· la firma, el stack elegido y las rutas del hook (2.17)"
caso S-23 "firma vacía: «reviewed_by:» sin nadie (PV-76)"     1 bash -c "prd_con 'reviewed: 2026-01-01\nreviewed_by:'; falla_por prd 'está vacío'"
caso S-24 "fecha de firma imposible: 2026-13-45 (PV-76)"      1 bash -c "prd_con 'reviewed: 2026-13-45\nreviewed_by: Ana Ruiz'; falla_por prd 'no es una fecha que exista'"
caso S-25 "fecha de firma futura"                             1 bash -c "prd_con 'reviewed: 2099-01-01\nreviewed_by: Ana Ruiz'; falla_por prd 'fecha futura'"
caso S-26 "la firma es de un agente"                          1 bash -c "prd_con 'reviewed: 2026-01-01\nreviewed_by: Tech Lead (agente)'; falla_por prd 'es un agente'"
caso S-27 "«autor:» de agente y sin «reviewed_by:» (fitapp)"  1 bash -c "prd_con 'autor: \"Tech Lead (agente) · borrador para que lo confirme el Usuario\"\nrevisado: 2026-01-01'; falla_por prd 'es un agente'"
caso S-31 "firma de relleno: «pendiente de firmar»"           1 bash -c "prd_con 'reviewed: 2026-01-01\nreviewed_by: pendiente de firmar'; falla_por prd 'no es quién lo revisó'"
caso S-32 "«Tech Lead» a secas firma (es el agente)"          1 bash -c "prd_con 'reviewed: 2026-01-01\nreviewed_by: Tech Lead'; falla_por prd 'es un agente'"
caso S-37 "firma una sesión de agente"                        1 bash -c "prd_con 'reviewed: 2026-01-01\nreviewed_by: la sesión plataforma-x de la directora'; falla_por prd 'es un agente'"
caso S-38 "«confirmado_por_usuario: no» firmado: AVISA, no bloquea" 0 bash -c "prd_con 'reviewed: 2026-01-01\nreviewed_by: Ana Ruiz\nconfirmado_por_usuario: no'; avisa prd 'confirmado_por_usuario'"
caso S-28 "un .py de producto en un WORKTREE bloquea (exit 2)" 2 bash -c "rm -f '$FIX/.docs/arranque/.block-count'; TL_ARRANQUE=1 CLAUDE_PROJECT_DIR='$FIX' bash '$H' --file '$FIX/.claude/worktrees/agente-1/backend/models.py'"
caso S-39 "un .py en una carpeta-enlace del proyecto bloquea" 2 bash -c "mkdir -p '$TMP/fuera'; ln -sfn '$TMP/fuera' '$FIX/compartido'; rm -f '$FIX/.docs/arranque/.block-count'; TL_ARRANQUE=1 CLAUDE_PROJECT_DIR='$FIX' bash '$H' --file '$FIX/compartido/app.py'"
caso N-09 "el .py del scratchpad, FUERA del proyecto, no bloquea" 0 bash -c "rm -f '$FIX/.docs/arranque/.block-count'; TL_ARRANQUE=1 CLAUDE_PROJECT_DIR='$FIX' bash '$H' --file '$TMP/scratchpad/montar_lienzo.py'"
caso S-29 "la BD solo en alternativas y negada (fitapp)"      1 bash -c "stack_con 'Python con Django, desplegado en un VPS con Docker.\n| Pieza | Decisión | Alternativas miradas |\n|---|---|---|\n| Base de datos | la de siempre, única y sin Mongo | MongoDB · MySQL |'; falla_por stack 'base de datos'"
caso S-30 "el lenguaje no sale de «Django» («go» de dentro)"   1 bash -c "stack_con 'Framework Django, base de datos Postgres, desplegado en un VPS con Docker.'; falla_por stack 'lenguaje'"
caso S-33 "la única BD va «(descartado)»"                     1 bash -c "stack_con 'Python con Django, desplegado en un VPS con Docker. MongoDB (descartado).'; falla_por stack 'base de datos'"
caso S-34 "la única BD va ~~tachada~~"                        1 bash -c "stack_con 'Python con Django, desplegado en un VPS con Docker. ~~PostgreSQL~~'; falla_por stack 'base de datos'"
caso S-35 "la única BD está en «## Alternativas»"             1 bash -c "stack_con 'Python con Django, desplegado en un VPS con Docker.\n## Alternativas\nPostgreSQL o MySQL.'; falla_por stack 'base de datos'"
caso S-36 "la única BD está en «- Alternativas miradas: …»"   1 bash -c "stack_con 'Python con Django, desplegado en un VPS con Docker.\n- Alternativas miradas: MongoDB, MySQL'; falla_por stack 'base de datos'"
caso N-10 "alternativas descartadas y la BD elegida PASA"     0 bash -c "stack_con 'Python con Django y PostgreSQL, desplegado con Docker en un VPS.\n| Pieza | Decisión | Alternativas miradas |\n|---|---|---|\n| Base de datos | PostgreSQL, sin Mongo | MongoDB · MySQL |\n## Alternativas descartadas\nFastAPI, por el admin.'; $G '$FIX' --fase stack"
caso N-14 "versión pegada al nombre: Python3, SQLite3 PASA"   0 bash -c "stack_con 'Python3 con Django y SQLite3, desplegado con Docker en un VPS.'; $G '$FIX' --fase stack"
caso N-15 "«En lugar de MongoDB usamos PostgreSQL», «sin Docker en Coolify» PASA" 0 bash -c "stack_con '## Stack elegido y alternativas descartadas\nPython con Django. En lugar de MongoDB usamos PostgreSQL. Desplegado sin Docker en Coolify.'; $G '$FIX' --fase stack"
caso N-11 "«autor:» agente + «reviewed_by:» persona PASA"     0 bash -c "prd_con 'autor: \"Tech Lead (agente)\"\nreviewed: 2026-01-01\nreviewed_by: Usuario — confirmó por tandas el 1 de enero'; $G '$FIX' --fase prd"
caso N-12 "firma con su cargo y «con ayuda de Claude» PASA"   0 bash -c "prd_con 'reviewed: 2026-01-01\nreviewed_by: Ana Ruiz, Tech Lead de Proxera, con ayuda de Claude'; $G '$FIX' --fase prd"
caso N-16 "firma de persona que nombra al agente detrás PASA" 0 bash -c "prd_con 'reviewed: 2026-01-01\nreviewed_by: Usuario (Proxera) — entrevista con Claude del 1 de enero'; $G '$FIX' --fase prd"
caso N-13 "firma con valor plegado («reviewed_by: >») PASA"   0 bash -c "prd_con 'reviewed: 2026-01-01\nreviewed_by: >\n  Ana Ruiz, en la entrevista del 1 de enero'; $G '$FIX' --fase prd"
caso N-17 "fecha con hora y firmante en lista YAML PASA"      0 bash -c "prd_con 'reviewed: 2026-01-01T10:00\nreviewed_by:\n  - Ana Ruiz'; $G '$FIX' --fase prd"
caso N-18 "«Ana Ruiz con ayuda de Claude» PASA (firma Ana)"   0 bash -c "prd_con 'reviewed: 2026-01-01\nreviewed_by: Ana Ruiz con ayuda de Claude'; $G '$FIX' --fase prd"
caso N-19 "«## Alternativas miradas y stack elegido» no se quita" 0 bash -c "stack_con '## Alternativas miradas y stack elegido\nPython con Django y PostgreSQL, desplegado con Docker en un VPS.'; $G '$FIX' --fase stack"
caso S-40 "«go-live» no es el lenguaje Go"                    1 bash -c "stack_con 'Framework Django, base de datos PostgreSQL, Docker en un VPS; el go-live es en marzo.'; falla_por stack 'lenguaje'"
# Los bordes de stack, «¿es un agente?» y firma que sacaron los auditores, contra las funciones del
# gate una a una (77 casos; un mutante que apague un mecanismo pone alguno en rojo).
caso B-01 "los bordes de stack, agente y firma (bordes_gate_arranque.py)" 0 python3 "$REPO/.claude/smoke/flujo/bordes_gate_arranque.py" "$FIX/.claude/scripts"
# ── fin del bloque de la 2.17 ─────────────────────────────────────────────────────────────────

# ── sub-ola 2.10 (SE-D12, CL-6, CL-11, MO-73): la guarda de destructivos, 0.0.0.0 y `git add -A` ──────
# El hook PreToolUse guarda-destructivos.sh: alerta (ask o exit 2) ante rm -r, force-push, un servidor en
# 0.0.0.0 y `git add -A` con OTRA sesión viva con ficheros ajenos; silencio ante lo benigno. La «otra
# sesión» es un proceso `claude` de juguete (sleep con argv0 «claude») con cwd en el repo del fixture.
echo
echo "· guarda de destructivos (2.10): bloquea o avisa lo peligroso, calla ante lo benigno"
GD="$REPO/.claude/hooks/guarda-destructivos.sh"
GR="$TMP/guarda_repo"; mkdir -p "$GR"
( cd "$GR" && git init -q && git config user.email a@b && git config user.name x && echo 1 > a.py && git add a.py \
  && git commit -qm i && echo ajeno > ajeno.txt ) >/dev/null 2>&1
gd(){  # gd <cwd> <comando> → exit 1 si la guarda alerta (ask o exit 2), 0 si calla
  local out rc
  out="$(python3 -c 'import json,sys;print(json.dumps({"tool_name":"Bash","cwd":sys.argv[1],"tool_input":{"command":sys.argv[2]}}))' "$1" "$2" | bash "$GD" 2>&1)"; rc=$?
  { [ "$rc" = 2 ] || printf '%s' "$out" | grep -q '"permissionDecision": "ask"'; } && return 1
  return 0
}
gd_sab(){ TL_GUARDA_SABOTAJE=excepcion gd "$@"; }
caso G-01 "rm -r fuera de /tmp alerta"                         1 gd "$TMP" "rm -r src/old"
caso G-02 "git push --force alerta"                            1 gd "$TMP" "git push --force origin develop"
caso G-03 "un servidor en 0.0.0.0 alerta"                      1 gd "$TMP" "python3 -m http.server 8080 --bind 0.0.0.0"
caso G-04 "http.server SIN --bind (0.0.0.0 implícito) alerta"  1 gd "$TMP" "python3 -m http.server 8080"
caso G-05 "docker compose down -v alerta (borra volúmenes)"    1 gd "$TMP" "docker compose down -v"
caso G-06 "git add -A sin otra sesión: silencio"               0 gd "$GR" "git add -A"
( cd "$GR" && exec -a claude sleep 120 ) >/dev/null 2>&1 &
GD_SESION=$!; sleep 0.3
caso G-07 "git add -A con OTRA sesión viva y un fichero ajeno alerta" 1 gd "$GR" "git add -A"
caso G-08 "git add -n -A (simulacro) NO alerta, aunque haya otra sesión" 0 gd "$GR" "git add -n -A"
caso G-09 "git add -- <ruta> con otra sesión: silencio"        0 gd "$GR" "git add -- a.py"
kill "$GD_SESION" 2>/dev/null; wait "$GD_SESION" 2>/dev/null
caso G-10 "lo benigno calla: rm -r en /tmp, bind 127.0.0.1, clean -n" 0 gd "$TMP" "rm -r /tmp/x && python3 -m http.server 8080 --bind 127.0.0.1 && git status && git clean -n"
caso G-11 "la guarda ROTA falla cerrada: rm -r sigue frenado"  1 gd_sab "$TMP" "rm -r src/old"
caso G-12 "la guarda ROTA no bloquea lo benigno"               0 gd_sab "$TMP" "ls -la && git status"
caso G-13 "prosa con \`git branch -D\` en un heredoc entrecomillado NO alerta" 0 gd "$TMP" "cat > nota.md <<'EOF'
no uses \`git branch -D\` ni \`rm -rf x\` ni sqlflush | dbshell
EOF"
# ── fin del bloque de la 2.10 ─────────────────────────────────────────────────────────────────

# ── sub-ola 2.11 (CL-24, CL-30, CL-39): TaskCompleted, PreCompact, PermissionDenied, InstructionsLoaded ──
# Los envoltorios de hooks/ y scripts/eventos_harness.py, alimentados con la entrada real que Claude Code
# manda (capturada con `claude -p` 2.1.307 en la 2.11). El vivo contra `claude -p` está en
# _archive/2026-10-20/medicion-2.11/; aquí, lo determinista y sin gasto.
echo
echo "· hooks nuevos (2.11): el gate de waves, el archivo previo a compactar y el registro de rules"
P211="$TMP/p211"; E211="$TMP/estado211"; mkdir -p "$P211/.specify/sessions/S1" "$P211/.claude/rules" "$E211"
printf '# T\n## Wave 1 — demo\n- [x] a\n- [ ] b abierta\n## Wave 2 — otra\n- [x] c\n' > "$P211/.specify/sessions/S1/tasks.md"
printf -- '---\npaths:\n  - "src/**/*.py"\n---\n# r\n' > "$P211/.claude/rules/py.md"
printf -- '---\npaths:\n  - "web/**/*.ts"\n---\n# r\n' > "$P211/.claude/rules/ts.md"
printf '{"x":1}\n' > "$TMP/transcript211.jsonl"
mkdir -p "$P211/.claude/scripts" "$P211/src"; cp "$REPO"/.claude/scripts/{eventos_harness,task_progress}.py "$P211/.claude/scripts/"
eh(){  # eh <wrapper.sh> <json> → corre el envoltorio con el estado aislado
  printf '%s' "$2" | CLAUDE_PROJECT_DIR="$P211" CLAUDE_STATE_DIR="$E211" bash "$REPO/.claude/hooks/$1"; }
tc(){ printf '{"task_subject":"%s","cwd":"%s"}' "$1" "$P211"; }
caso H-01 "TaskCompleted «Wave 1» con casillas abiertas: exit 2"  2 eh task-completed-gate.sh "$(tc 'Wave 1 demo')"
caso H-02 "control: «Wave 2», sin casillas abiertas, pasa"        0 eh task-completed-gate.sh "$(tc 'Wave 2 otra')"
caso H-03 "una tarea que no es de wave pasa sin mirar"            0 eh task-completed-gate.sh "$(tc 'Escribir tests')"
caso H-04 "una wave que el tasks.md no tiene pasa"                0 eh task-completed-gate.sh "$(tc 'Wave 9 inexistente')"
caso H-05 "entrada basura: falla ABIERTO (límite declarado)"      0 eh task-completed-gate.sh "esto no es json"
caso H-06 "PreCompact archiva el transcript"                      0 bash -c "$(declare -f eh); REPO='$REPO' E211='$E211'; eh pre-compact-archive.sh '{\"transcript_path\":\"$TMP/transcript211.jsonl\",\"session_id\":\"abcdef12\",\"trigger\":\"manual\"}' && ls '$E211'/*/precompact/*abcdef12-manual.jsonl >/dev/null"
caso H-07 "InstructionsLoaded registra rule, motivo y trigger"    0 bash -c "$(declare -f eh); REPO='$REPO' E211='$E211'; eh instructions-loaded-log.sh '{\"session_id\":\"abcdef12\",\"file_path\":\"$P211/.claude/rules/py.md\",\"memory_type\":\"Project\",\"load_reason\":\"path_glob_match\",\"globs\":[\"src/**/*.py\"],\"trigger_file_path\":\"$P211/src/a.py\"}' && grep -q 'path_glob_match' '$E211'/*/instructions-loaded.jsonl"
caso H-08 "el informe nombra la rule con paths: que NO cargó"     0 bash -c "CLAUDE_PROJECT_DIR='$REPO' CLAUDE_STATE_DIR='$E211' python3 '$REPO/.claude/scripts/eventos_harness.py' informe-rules --dir '$P211' | grep -q 'NO han cargado nunca en el registro: 1' "
caso H-09 "y la que SÍ cargó sale como cargada, no como ausente"  0 bash -c "CLAUDE_PROJECT_DIR='$REPO' CLAUDE_STATE_DIR='$E211' python3 '$REPO/.claude/scripts/eventos_harness.py' informe-rules --dir '$P211' | grep -q '+ .claude/rules/py.md' "
pd(){ printf '{"session_id":"s1abcdefgh","tool_name":"Bash","tool_input":{"command":"%s"},"reason":"x"}' "$1"; }
caso H-10 "PermissionDenied: una orden benigna se puede reintentar" 0 bash -c "$(declare -f eh pd); REPO='$REPO' E211='$E211'; eh permission-denied-log.sh \"\$(pd 'ls /tmp')\" | grep -q '\"retry\": true'"
caso H-11 "...pero la MISMA orden otra vez ya no (sin bucles)"     0 bash -c "$(declare -f eh pd); REPO='$REPO' E211='$E211'; eh permission-denied-log.sh \"\$(pd 'pwd -P')\" >/dev/null; o=\$(eh permission-denied-log.sh \"\$(pd 'pwd -P')\"); echo \"\$o\" | grep -q systemMessage && ! echo \"\$o\" | grep -q retry"
caso H-12 "...y lo destructivo nunca (rm -rf)"                     0 bash -c "$(declare -f eh pd); REPO='$REPO' E211='$E211'; o=\$(eh permission-denied-log.sh \"\$(pd 'rm -rf /x')\"); echo \"\$o\" | grep -q systemMessage && ! echo \"\$o\" | grep -q retry"
caso H-13 "editar un CLAUDE.md avisa de que no rige hasta /clear"  0 bash -c "$(declare -f eh); REPO='$REPO' E211='$E211'; eh aviso-claude-md.sh '{\"tool_input\":{\"file_path\":\"/x/CLAUDE.md\"}}' | grep -q '/clear'"
caso H-14 "...y editar otro fichero NO avisa"                      0 bash -c "$(declare -f eh); REPO='$REPO' E211='$E211'; [ -z \"\$(eh aviso-claude-md.sh '{\"tool_input\":{\"file_path\":\"/x/a.py\"}}')\" ]"
caso H-15 "cambio de modelo avisa de la caché; reanudar no"        0 bash -c "$(declare -f eh); REPO='$REPO' E211='$E211'; eh aviso-modelo.sh '{\"from_model\":\"a\",\"to_model\":\"b\",\"source\":\"command\"}' | grep -q 'caché' && [ -z \"\$(eh aviso-modelo.sh '{\"to_model\":\"b\",\"source\":\"resume\"}')\" ]"
caso H-16 "settings.json registra los seis eventos nuevos"         0 python3 -c "
import json,sys;h=json.load(open('$REPO/.claude/settings.json'))['hooks']
falta=[e for e in ('TaskCompleted','PreCompact','PermissionDenied','InstructionsLoaded','PostModelSwitch') if e not in h]
pt=[g for g in h.get('PostToolUse',[]) if any('aviso-claude-md' in x['command'] for x in g['hooks'])]
sys.exit(1 if falta or len(pt)<2 else 0)"
caso H-17 "el mod tl-visibilidad pasa sus pruebas (claude plugin test)" 0 bash -c "command -v claude >/dev/null || exit 0; claude plugin test '$REPO/.claude/mods/tl-visibilidad' 2>&1 | grep -q ' 0 fail'"
h18(){ printf '## Wave 1 — a\n- [x] a\n## Wave 10 — b\n- [ ] b\n' > "$P211/.specify/sessions/S1/tasks.md"; eh task-completed-gate.sh "$(tc 'Wave 1 a')"; local r=$?
  printf '# T\n## Wave 1 — demo\n- [x] a\n- [ ] b abierta\n## Wave 2 — otra\n- [x] c\n' > "$P211/.specify/sessions/S1/tasks.md"; return $r; }
h19(){ eh task-completed-gate.sh "{\"task_subject\":\"Wave 1 demo\",\"cwd\":\"$P211/src\"}"; }
h20(){ local w; for w in task-completed-gate pre-compact-archive permission-denied-log instructions-loaded-log aviso-modelo aviso-claude-md; do
  echo '{}' | CLAUDE_PROJECT_DIR="$TMP/sin-script" bash "$REPO/.claude/hooks/$w.sh" >/dev/null 2>&1 || return 1; done; }
caso H-18 "«Wave 1» no arrastra a «Wave 10» (la 10 abierta no frena la 1)" 0 h18
caso H-19 "el gate sigue frenando tras un cd (cwd del evento en un subdirectorio)" 2 h19
caso H-20 "script ausente: los envoltorios fallan ABIERTO (exit 0, no 2)" 0 h20
# ── fin del bloque de la 2.11 ─────────────────────────────────────────────────────────────────

# ── sub-ola 2.14 (MO-16, MO-28, MO-45, MO-56, MO-59, MO-D5): git, commits y flujo ─────────────────
# Cada mecanismo nuevo con su sabotaje y su control. Los fixtures son repos git de juguete en $TMP.
echo
echo "· git y flujo (2.14): .gitignore, formateo por líneas, política de commits, status, speckit"
gitrepo(){ mkdir -p "$1" && ( cd "$1" && git init -q && git config user.email a@b && git config user.name x ) >/dev/null 2>&1; }
GI="$TMP/gi214"; gitrepo "$GI"
mkdir -p "$GI/backend/core/media" "$GI/media" "$GI/tests/fixtures" "$GI/node_modules/x" "$GI/src"
echo 'def v(): pass' > "$GI/backend/core/media/views.py"; echo voz > "$GI/media/voz.wav"
echo n43 > "$GI/tests/fixtures/extracto.n43"; echo x > "$GI/node_modules/x/index.js"; echo ok > "$GI/src/app.ts"
CG="python3 $REPO/.claude/scripts/check_gitignore.py"
gi_bad(){ printf 'media/\n*.n43\nnode_modules/\n' > "$GI/.gitignore"; }
gi_good(){ printf '/media/\n*.n43\n!tests/fixtures/*.n43\nnode_modules/\n' > "$GI/.gitignore"; }
gi_catches(){ gi_bad; local o; o="$($CG "$GI")"; local r=$?
  printf '%s' "$o" | grep -q 'backend/core/media/views.py' && printf '%s' "$o" | grep -q 'tests/fixtures/extracto.n43' \
    && ! printf '%s' "$o" | grep -q 'voz.wav' && ! printf '%s' "$o" | grep -q 'node_modules' || return 9; return $r; }
gi_allow(){ gi_bad; mkdir -p "$GI/.claude"; printf 'backend/core/media/**\ntests/fixtures/*\n' > "$GI/.claude/gitignore-allow.txt"
  $CG "$GI"; local r=$?; rm -f "$GI/.claude/gitignore-allow.txt"; return $r; }
caso GI-01 "\`media/\` sin anclar se come código y \`*.n43\` un fixture: lo caza (y calla la voz y node_modules)" 1 gi_catches
caso GI-02 "lo ignorado a propósito en gitignore-allow.txt no se cuenta"  0 gi_allow
caso GI-03 "fuera de un repo git: ABORTA (exit 2), no dice «limpio»"     2 bash -c "mkdir -p '$TMP/sin-git'; $CG '$TMP/sin-git'"
GB="$TMP/gb214"; gitrepo "$GB"; mkdir -p "$GB/backend/auth" "$GB/src/diseño"
echo 'x = 1' > "$GB/backend/auth/credentials.py"; echo 'y = 2' > "$GB/backend/auth/secrets.py"; echo 'z = 3' > "$GB/src/diseño/vista.py"
gi_base_clean(){ cp "$REPO/.claude/templates/gitignore-base" "$GB/.gitignore"; $CG "$GB"; }
gi_non_ascii(){ printf 'diseño/\n' > "$GB/.gitignore"; local o; o="$($CG "$GB")"; local r=$?
  printf '%s' "$o" | grep -q 'src/diseño/vista.py' || return 9; return $r; }
caso GI-04 "gitignore-base NO se come credentials.py ni secrets.py"       0 gi_base_clean
caso GI-05 "una carpeta no ASCII ignorada (diseño/) se ve y se nombra"   1 gi_non_ascii

# auto-format.sh: un fichero heredado mal formateado, commiteado; se toca UNA línea y se mide el diff.
AF="$TMP/af214"; gitrepo "$AF"; mkdir -p "$AF/.claude" "$AF/.venv/bin" "$AF/node_modules/.bin"
RUFF_BIN="${RUFF_BIN:-$(command -v ruff || ls /home/*/.venv/bin/ruff /home/*/*/.venv/bin/ruff 2>/dev/null | head -1)}"
PRETTIER_BIN="${PRETTIER_BIN:-$(command -v prettier || ls /home/*/*/frontend/node_modules/.bin/prettier /home/*/*/node_modules/.bin/prettier 2>/dev/null | head -1)}"
[ -n "$RUFF_BIN" ] && ln -sf "$RUFF_BIN" "$AF/.venv/bin/ruff"
[ -n "$PRETTIER_BIN" ] && ln -sf "$PRETTIER_BIN" "$AF/node_modules/.bin/prettier"
af_prep(){  # af_prep <ext>: fichero de 6 líneas mal formateadas, commiteado, y se cambia la 3.ª
  local f="$AF/legado.$1"
  if [ "$1" = py ]; then printf 'a=1\nb  =  2\nc=3\nd  =  {  "k":1 }\ne=5\nf  =  [1,2]\n' > "$f"
  else printf 'const a=1\nconst b  =  2\nconst c=3\nconst d  =  {  k:1 }\nconst e=5\nconst f  =  [1,2]\n' > "$f"; fi
  ( cd "$AF" && git add "legado.$1" && git commit -qm "legado $1" ) >/dev/null 2>&1
  sed -i '3s/=3/  =   33/' "$f"; }
af_run(){ CLAUDE_PROJECT_DIR="$AF" bash "$REPO/.claude/hooks/auto-format.sh" "$AF/legado.$1" </dev/null; }
af_lines(){ ( cd "$AF" && git diff --numstat -- "legado.$1" | awk '{print $1+$2}' ); }
af_only_touched(){  # el diff es la línea 3 cambiada (1 añadida + 1 quitada) y está formateada
  rm -f "$AF/.claude/CONFIGURACION.yaml"; af_prep "$1"; af_run "$1"
  [ "$(af_lines "$1")" = 2 ] && grep -qE '^(const )?c = 33;?$' "$AF/legado.$1"; }
af_whole(){  # control: con `auto_format: fichero-entero` (lo de antes) el diff crece → exit 1
  printf 'respuestas:\n  auto_format: fichero-entero\n' > "$AF/.claude/CONFIGURACION.yaml"; af_prep "$1"; af_run "$1"
  local n; n="$(af_lines "$1")"; rm -f "$AF/.claude/CONFIGURACION.yaml"; [ "$n" -gt 2 ] && return 1; return 0; }
af_off(){ printf 'respuestas:\n  auto_format: "no"\n' > "$AF/.claude/CONFIGURACION.yaml"; af_prep py; af_run py
  local r; grep -q '^c  =   33$' "$AF/legado.py"; r=$?; rm -f "$AF/.claude/CONFIGURACION.yaml"; return $r; }
af_new(){ printf 'x  =  1\n' > "$AF/nuevo.py"
  CLAUDE_PROJECT_DIR="$AF" bash "$REPO/.claude/hooks/auto-format.sh" "$AF/nuevo.py" </dev/null; grep -qx 'x = 1' "$AF/nuevo.py"; }
skip_case(){ SALTADOS=$((SALTADOS+1)); printf '  - %-8s %s (sin %s en la máquina: NO medido)\n' "$1" "$2" "$3"; }
if [ -n "$RUFF_BIN" ]; then
  caso AF-01 "ruff: tocar 1 línea de un .py heredado cambia SOLO esa línea"        0 af_only_touched py
  caso AF-02 "ruff con \`auto_format: fichero-entero\`: el diff crece (el control ve la diferencia)" 1 af_whole py
  caso AF-06 "un fichero nuevo (sin versionar) se formatea entero"                 0 af_new
else skip_case AF-01 "ruff, líneas tocadas" "ruff (RUFF_BIN=<ruta>)"; skip_case AF-02 "ruff, fichero entero" ruff; skip_case AF-06 "fichero nuevo" ruff; fi
if [ -n "$PRETTIER_BIN" ]; then
  caso AF-03 "prettier: tocar 1 línea de un .ts heredado cambia SOLO esa línea"    0 af_only_touched ts
  caso AF-04 "prettier con \`auto_format: fichero-entero\`: el diff crece"            1 af_whole ts
else skip_case AF-03 "prettier, líneas tocadas" "prettier (PRETTIER_BIN=<ruta>)"; skip_case AF-04 "prettier, fichero entero" prettier; fi
caso AF-05 "\`auto_format: \"no\"\`: el hook no toca nada"                           0 af_off
af_no_head(){ local R="$TMP/af214-nohead"; gitrepo "$R"; mkdir -p "$R/.venv/bin"; ln -sf "$RUFF_BIN" "$R/.venv/bin/ruff"
  printf 'x  =  1\n' > "$R/a.py"; ( cd "$R" && git add a.py ) >/dev/null 2>&1
  CLAUDE_PROJECT_DIR="$R" bash "$REPO/.claude/hooks/auto-format.sh" "$R/a.py" </dev/null; grep -qx 'x = 1' "$R/a.py"; }
af_emoji(){  # prettier cuenta en UTF-16: una línea de emojis encima no debe arrastrar la de al lado
  local f="$AF/emoji.ts"; printf 'const e = "%s"\nconst a  =  {x:1}\nconst c=3\n' "$(printf '😀%.0s' $(seq 20))" > "$f"
  ( cd "$AF" && git add emoji.ts && git commit -qm emoji ) >/dev/null 2>&1; sed -i '3s/=3/  =   33/' "$f"
  CLAUDE_PROJECT_DIR="$AF" bash "$REPO/.claude/hooks/auto-format.sh" "$f" </dev/null
  grep -qx 'const a  =  {x:1}' "$f" && grep -qE '^const c = 33;?$' "$f"; }
if [ -n "$RUFF_BIN" ]; then caso AF-07 "repo sin ningún commit: el fichero del índice se formatea entero" 0 af_no_head
else skip_case AF-07 "repo sin commits" ruff; fi
if [ -n "$PRETTIER_BIN" ]; then caso AF-08 "prettier con emojis encima: solo cambia la línea tocada" 0 af_emoji
else skip_case AF-08 "emojis" prettier; fi

# session-stop.sh: con `git_commit: usuario` no sugiere commitear (EvoPreven lo desregistró por eso).
SS="$TMP/ss214"; gitrepo "$SS"; mkdir -p "$SS/.claude"; echo cambio > "$SS/sucio.txt"
ss_suggests(){ ( cd "$SS" && CLAUDE_PROJECT_DIR="$SS" bash "$REPO/.claude/hooks/session-stop.sh" ) | grep -q 'Considera hacer commit'; }
ss_user(){ printf 'respuestas:\n  git_commit: usuario\n' > "$SS/.claude/CONFIGURACION.yaml"; ss_suggests; }
ss_default(){ rm -f "$SS/.claude/CONFIGURACION.yaml"; ss_suggests; }
caso SS-01 "con \`git_commit: usuario\` NO sugiere commitear"         1 ss_user
caso SS-02 "sin el dato (default: commitea el agente) sí lo sugiere" 0 ss_default

# tasks_to_items.py: el status lo manda el fichero salvo cambio a mano (7 casos; con el de antes, 5/7).
caso TS-01 "status: manda tasks.md salvo cambio a mano en el dashboard (tasks_status_cases.py)" 0 \
  python3 "$REPO/.claude/smoke/flujo/tasks_status_cases.py" "$REPO/.claude/templates/report_kit/tasks_to_items.py"

# check_mechanisms.py: /speckit.* sin .specify/scripts/ es mecanismo roto (seis derivados lo tenían).
SK="$TMP/sk214"; mkdir -p "$SK/.claude/commands"; echo '{}' > "$SK/.claude/settings.json"
printf -- '---\nscripts:\n  sh: scripts/bash/check-prerequisites.sh --json\n---\n# x\n' > "$SK/.claude/commands/speckit.plan.md"
sk_broken(){  # la salida se guarda antes de buscar: con pipefail, `| grep -q` corta la tubería y el
  # SIGPIPE de python se lee como fallo del caso
  local o; o="$(python3 "$REPO/.claude/scripts/check_mechanisms.py" --root "$SK" --json)"
  printf '%s' "$o" | grep -q '"donde": ".specify/scripts/bash/check-prerequisites.sh"'; }
sk_with_script(){ mkdir -p "$SK/.specify/scripts/bash"; touch "$SK/.specify/scripts/bash/check-prerequisites.sh"; sk_broken; }
caso SK-01 "/speckit.* sin .specify/scripts/: check_mechanisms lo marca roto" 0 sk_broken
caso SK-02 "con el script en su sitio, calla"                                1 sk_with_script

# code-review-gate §Comentarios con cita: la regex se lee DEL SKILL (si alguien la cambia, esto la prueba).
CITA_RE="$(sed -n "s/^CITA_RE='\(.*\)'$/\1/p" "$REPO/.claude/skills/code-review-gate/SKILL.md")"
cite(){ [ -n "$CITA_RE" ] || return 7; printf '%s\n' "$1" | grep -qE "$CITA_RE"; }
cite_variants(){ cite '+ * ver src/lib/api.ts:12' && cite '+  return 1 // copiado de utils.js:7' \
  && cite '+    """Copiado de apps/core/views.py:42."""' && cite '+-- ver migrations/0003.sql:10'; }
cite_silent(){ cite '+URL = "http://127.0.0.1:8000/"  # servidor local' || cite '+path = "views.py:42"' \
  || cite '+++ b/apps/x.py' || cite '-    # antes en apps/core/views.py:42'; }
caso CR-01 "un comentario con cita fichero:línea en una línea añadida se marca" 0 cite '+    x = 1  # mismo patrón que apps/core/views.py:42'
caso CR-02 "//, JSDoc, docstring y -- de SQL con cita también"                                     0 cite_variants
caso CR-03 "URL con puerto, cita en código, cabecera +++ o línea quitada: calla" 1 cite_silent
# ── fin del bloque de la 2.14 ─────────────────────────────────────────────────────────────────

# ── sub-ola 3.52 (NE-9): tanda 2.5, ¿el producto escribe por iniciativa propia? ─────────────────
echo
echo "· mensajes propios (3.52): sin declararlo, o declarado sin D-1/D-2/D-6, no pasa"
caso S-52a "entidades sin mensajes_propios" 1 bash -c "printf '{\"entidades\":[{\"nombre\":\"Cliente\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"nif\",\"tipo\":\"texto\",\"personal\":true}]}]}' > '$ARR/entidades.json'; $G '$FIX' --fase datos"
caso S-52b "mensajes_propios: true sin consentimiento, exclusión ni exposición" 1 bash -c "printf '{\"mensajes_propios\":true,\"entidades\":[{\"nombre\":\"Cliente\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"nif\",\"tipo\":\"texto\",\"personal\":true}]}]}' > '$ARR/entidades.json'; $G '$FIX' --fase datos"
caso S-52c "mensajes_propios: true con D-1 y D-2 pero sin D-6" 1 bash -c "printf '{\"mensajes_propios\":true,\"entidades\":[{\"nombre\":\"Cliente\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"nif\",\"tipo\":\"texto\",\"personal\":true}]},{\"nombre\":\"ConsentLedger\",\"patron\":\"D-1\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"id\",\"tipo\":\"id\",\"personal\":false}]},{\"nombre\":\"Suppression\",\"patron\":\"D-2\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"id\",\"tipo\":\"id\",\"personal\":false}]}]}' > '$ARR/entidades.json'; $G '$FIX' --fase datos"
caso S-52d "mensajes_propios como texto, no booleano" 1 bash -c "printf '{\"mensajes_propios\":\"si\",\"entidades\":[{\"nombre\":\"Cliente\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"nif\",\"tipo\":\"texto\",\"personal\":true}]}]}' > '$ARR/entidades.json'; $G '$FIX' --fase datos"
# ── fin del bloque de la 3.52 ─────────────────────────────────────────────────────────────────

echo
echo "· CONTROLES NEGATIVOS — lo correcto NO puede fallar"
prd_bueno
caso N-01 "un PRD real, corto y completo, PASA"               0 bash -c "$G '$FIX' --fase prd"
caso N-02 "requisitos con verbo normativo, Gherkin y fin"     0 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# Requisitos\n## R-1 Reservar una cita\nEl sistema DEBE guardar la cita y DEBE avisar al cliente por correo.\nDado que hay un hueco libre cuando la recepcionista reserva entonces la cita aparece en la agenda del día.\n### El recorrido, como máquina de estados\n| sin confirmar | inicio |\n| confirmada | fin |\n%s\n' \"\$(relleno 1200)\" > '$ARR/02-requisitos.md'; $G '$FIX' --fase requisitos"
caso N-03 "entidades con todos los campos clasificados"       0 bash -c "printf '{\"mensajes_propios\":false,\"entidades\":[{\"nombre\":\"Cliente\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"nif\",\"tipo\":\"texto\",\"personal\":true}]}]}' > '$ARR/entidades.json'; $G '$FIX' --fase datos"
caso N-04 "stack completo: lenguaje, framework, BD, deploy"   0 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# Stack\nPython con Django, base de datos Postgres, desplegado en un VPS con Docker.\n%s\n' \"\$(relleno 500)\" > '$ARR/05-stack.md'; $G '$FIX' --fase stack"
caso N-05 "ética con base legal declarada"                    0 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# Ética\nTratamos datos personales de los pacientes. La base legal es el contrato de prestación del servicio.\n%s\n' \"\$(relleno 500)\" > '$ARR/06-etica-privacidad.md'; $G '$FIX' --fase etica"
caso N-06 "seguridad con las 4 defensas y 2FA"                0 bash -c "printf -- '---\nreviewed: 2026-01-01\nreviewed_by: A\n---\n# Superficie\n2FA obligatorio en la cuenta de administración.\nLímite de intentos por cuenta: 5 y bloqueo con aviso.\nNo se publica ningún puerto en 0.0.0.0, todo tras el proxy.\nLos logs no guardan contraseñas ni tokens.\n%s\n' \"\$(relleno 400)\" > '$ARR/07-superficie.md'; $G '$FIX' --fase seguridad"
caso N-07 "exención VÁLIDA deja pasar"                        0 bash -c "printf 'autorizado_por: Miller\ncaduca: 2099-01-01\nalcance: spike\nmotivo: >\n  Prueba de la libreria de N43 con el fichero real de AMC, se tira el viernes\n' > '$FIX/.docs/arranque/EXENCION.md'; rm -f '$FIX/.docs/arranque/.block-count'; TL_ARRANQUE=1 CLAUDE_PROJECT_DIR='$FIX' bash '$H' --file '$FIX/backend/models.py'"
caso N-08 "state.json recién escrito refleja el disco"        0 bash -c "rm -f '$FIX/.docs/flow/waivers.jsonl'; $F '$FIX' --write >/dev/null 2>&1; $F '$FIX' --check"
caso N-52 "mensajes_propios: true con D-1, D-2 y D-6" 0 bash -c "printf '{\"mensajes_propios\":true,\"entidades\":[{\"nombre\":\"Cliente\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"nif\",\"tipo\":\"texto\",\"personal\":true}]},{\"nombre\":\"ConsentLedger\",\"patron\":\"D-1\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"id\",\"tipo\":\"id\",\"personal\":false}]},{\"nombre\":\"Suppression\",\"patron\":\"D-2\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"id\",\"tipo\":\"id\",\"personal\":false}]},{\"nombre\":\"CampaignExposure\",\"patron\":\"d-6\",\"fuente\":\"propia\",\"campos\":[{\"nombre\":\"id\",\"tipo\":\"id\",\"personal\":false}]}]}' > '$ARR/entidades.json'; $G '$FIX' --fase datos"

echo
TOT=$((OK+KO))
echo "═══ $OK/$TOT correctos · $KO fallidos$([ "$SALTADOS" -gt 0 ] && echo " · $SALTADOS saltados")"
[ "$KO" -eq 0 ] && echo "    Los gates cazan lo que tienen que cazar y dejan pasar lo correcto." \
                || echo "    ⚠ Un gate que no caza su sabotaje no está verificado: está sin ejecutar."
exit $([ "$KO" -eq 0 ] && echo 0 || echo 1)
