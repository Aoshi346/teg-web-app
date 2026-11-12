#!/bin/bash
# pattern-check.sh — Tier 0 del sistema de patrones (Rita). Determinista, 0 tokens.
# Uso:
#   .claude/hooks/pattern-check.sh                  # ficheros cambiados (staged+unstaged) vs catálogo
#   .claude/hooks/pattern-check.sh --all            # escaneo completo (medición/inventario)
#   como pre-push:  ln -s ../../.claude/hooks/pattern-check.sh .git/hooks/pre-push
# Política (rules del catálogo — .claude/patterns/catalog.yaml):
#   patrón ACTIVO  → violación NUEVA = bloquea (exit 1)
#   patrón DÉBIL   → aviso, nunca bloquea
#   baseline       → deuda aceptada, NUNCA se reporta salvo --all (y como "baseline", no violación)
#   excepción      → línea con "pattern-exempt: <id>" en el fichero ⇒ se respeta SIEMPRE
set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
MODE="${1:-changed}"
FAIL=0; WARN=0
BASE=""   # en pre-push: el commit contra el que se juzga lo que se va a subir

# ── Modo PRE-PUSH ─────────────────────────────────────────────────────────────
# Git llama al hook como `pre-push <remoto> <url>` y manda por stdin una línea por ref:
#   <ref local> <sha local> <ref remota> <sha remota>
# Hasta el 2026-10-03 esto no se distinguía: MODE valía "origin", caía en el modo de abajo
# («cambios sin commitear») y en un push —donde todo está ya commiteado— no había nada que
# mirar: «sin ficheros que comprobar», exit 0, SIEMPRE. Un gate ciego que daba verde.
# Ahora se juzga exactamente lo que se va a publicar: el diff entre lo que ya tiene el remoto
# y lo que se sube. Rama nueva: desde el primer commit que no está en ningún remoto.
if [ "$MODE" != "--all" ] && [ $# -ge 2 ] && [ "${1#--}" = "$1" ]; then
  MODE="pre-push"
  FILES=""
  while read -r _lref lsha _rref rsha; do
    echo "$lsha" | grep -qE '^0+$' && continue                     # se borra una rama: nada que juzgar
    if echo "$rsha" | grep -qE '^0+$' || ! git cat-file -e "${rsha}^{commit}" 2>/dev/null; then
      primero=$(git rev-list "$lsha" --not --remotes 2>/dev/null | tail -1)
      [ -z "$primero" ] && continue                                 # todo ya publicado
      b=$(git rev-parse -q --verify "${primero}^" 2>/dev/null) || b=$(git hash-object -t tree /dev/null)
    else
      b="$rsha"
    fi
    BASE="$b"
    FILES="$FILES
$(git diff --name-only --diff-filter=ACMR "$b" "$lsha" 2>/dev/null)"
  done
  FILES=$(echo "$FILES" | sed '/^$/d' | sort -u)
  [ -z "$FILES" ] && { echo "pattern-check (pre-push): nada nuevo que publicar"; exit 0; }
elif [ "$MODE" = "--all" ]; then
  FILES=$( { ls .claude/skills/*/SKILL.md; ls .claude/templates/html/*.html .claude/templates/report_kit/*.html; ls .claude/rules/*.md; } 2>/dev/null )
else
  FILES=$( { git diff --name-only HEAD 2>/dev/null; git diff --cached --name-only 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null; } | sort -u )
fi
[ -z "$FILES" ] && { echo "pattern-check: sin ficheros que comprobar"; exit 0; }

exempt(){ grep -q "pattern-exempt: $2" "$1" 2>/dev/null; }
in_baseline(){ grep -q "\"$1\"" .claude/patterns/baseline/rule-header.json 2>/dev/null; }

for f in $FILES; do
  [ -f "$f" ] || continue
  case "$f" in
    .claude/skills/*/SKILL.md)   # P1 skill-frontmatter-description (ACTIVO)
      if ! grep -q "^description:" "$f" && ! exempt "$f" skill-frontmatter-description; then
        echo "✗ [ACTIVO] $f — sin 'description:' en frontmatter (skill-frontmatter-description)"
        echo "   fix: añade frontmatter YAML con description de triggers · precedente: skills/verification-loops/SKILL.md:1"
        FAIL=1
      fi;;
    .claude/templates/*.html|.claude/templates/*/*.html)   # P2 html-self-contained (ACTIVO)
      if grep -q 'rel="stylesheet"\|<script src="http\|fonts.googleapis' "$f" && ! exempt "$f" html-self-contained; then
        echo "✗ [ACTIVO] $f — referencia externa (html-self-contained)"
        echo "   fix: CSS/JS inline · precedente: templates/html/base.html:8"
        FAIL=1
      fi;;
    .claude/rules/*.md)          # P3 rule-header (DÉBIL — solo avisa; baseline exenta)
      if ! grep -q "Cuándo aplicar" "$f" && ! in_baseline "$f" && ! exempt "$f" rule-header-cuando-aplicar; then
        echo "⚠ [débil] $f — sin cabecera '> **Cuándo aplicar:**' (rule-header-cuando-aplicar; no bloquea)"
        WARN=1
      fi;;
  esac
done

# ---------------------------------------------------------------------------
# Tier 0b — los patrones de CÓDIGO (pattern_check_{agente,backend,frontend}.py)
#
# Hasta el 2026-08-27 esto NO existía y era el agujero de fondo: `catalog.yaml`
# cubre 13 reglas sobre ficheros del HARNESS (skills, rules, plantillas HTML), y
# los 43 documentos de `patterns/stack/` sobre el CÓDIGO no los ejecutaba nadie.
# Dos sistemas, cero puentes (`grep -c pattern_check_ pattern-check.sh` daba 0).
#
# POLÍTICA, y es deliberadamente conservadora: estas reglas AVISAN, NUNCA
# BLOQUEAN. Conectarlas no puede convertir 40 reglas en bloqueantes de golpe —
# `refactor-progresivo.md` §4.5 exige que promover una regla lo firme un humano,
# con dominancia medida y la deuda bajando. Mientras eso no pase, son avisos.
#
# `--diff-scope` juzga SOLO las líneas que este cambio ha tocado, así que el
# baseline no hace falta silenciarlo: si tocas la línea, es tuya (boy-scout).
# ---------------------------------------------------------------------------
if [ "$MODE" != "--all" ] && [ "${PATTERN_CHECK_SIN_CODIGO:-0}" != "1" ]; then
  for CAPA in agente backend frontend; do
    CHK=".claude/patterns/stack/pattern_check_${CAPA}.py"
    [ -f "$CHK" ] || continue
    if [ "$MODE" = "pre-push" ]; then
      # Sin argumentos el comprobador mira «cambios contra HEAD», que en un push es nada. Se le
      # dan los ficheros que se publican (el de agente solo acepta una ruta: el repo entero) y
      # el diff-scope se calcula contra BASE, no contra HEAD.
      # Solo CÓDIGO del proyecto: lo de `.claude/` (corpus de diseño, scripts de skills) lo
      # juzgan las reglas del harness de arriba, no los patrones de código. Sin este filtro, el
      # primer pre-push simulado en aquila-erp avisaba del `script.js` del corpus de referencias.
      CODIGO=$(echo "$FILES" | grep -v '^\.claude/')
      [ -z "$CODIGO" ] && continue
      if [ "$CAPA" = "agente" ]; then ARGS="."; else ARGS=$(echo "$CODIGO" | tr '\n' ' '); fi
      # shellcheck disable=SC2086
      JSON=$(timeout 90 python3 "$CHK" --json $ARGS 2>/dev/null \
             | python3 .claude/scripts/pattern_baseline.py check --from - --diff-scope --base "$BASE" --json 2>/dev/null)
    else
      JSON=$(timeout 90 python3 "$CHK" --json 2>/dev/null \
             | python3 .claude/scripts/pattern_baseline.py check --from - --diff-scope --json 2>/dev/null)
    fi
    # QUIÉN BLOQUEA. Una regla de código bloquea SOLO si el catálogo del proyecto la tiene en
    # `estado: activo` — y eso lo firma un humano (refactor-progresivo.md §4.5). El estado que
    # trae el comprobador por defecto NO cuenta: antes de 2026-10-03 el hook no leía el catálogo
    # y todo avisaba; ahora el catálogo medido y firmado es el que decide. Solo se juzgan las
    # líneas que este cambio toca (diff-scope): la deuda vieja no bloquea hasta que se toca.
    [ -z "$JSON" ] && continue
    RES=$(printf '%s' "$JSON" | python3 -c '
import json, sys
try:
    import yaml
    cat = yaml.safe_load(open(".claude/patterns/catalog.yaml")) or {}
    activas = {p["id"] for p in cat.get("patterns") or [] if p.get("estado") == "activo"}
except FileNotFoundError:
    activas = set()
except Exception as e:
    activas = set()
    print(f"⚠ catalog.yaml ilegible ({type(e).__name__}): ninguna regla de código bloquea en este push")
capa = sys.argv[1]
d = json.load(sys.stdin)
bloq = 0
for f in d.get("nuevas", []):
    if f["rule"] in activas:
        bloq = 1
        print(f"✗ [ACTIVO·catálogo] {f["path"]}:{f["line"]} — {f["msg"]} ({f["rule"]})")
    elif f.get("estado") == "activo":
        print(f"⚠ [código·{capa}] {f["path"]}:{f["line"]} — {f["msg"]} ({f["rule"]})")
print(f"#BLOQUEA={bloq}")
' "$CAPA" 2>&1)
    echo "$RES" | grep -v '^#BLOQUEA=' | sed '/^$/d'
    echo "$RES" | grep -q '^#BLOQUEA=1' && FAIL=1
    echo "$RES" | grep -q '^⚠' && WARN=1
  done
  [ $WARN -eq 1 ] && echo "   (⚠ = regla que el catálogo aún no tiene en «activo»: avisa y no bloquea — promoverla lo firma un humano, refactor-progresivo.md §4.5)"
fi

[ $FAIL -eq 1 ] && { echo; echo "pattern-check: violaciones de patrones ACTIVOS — detalle en .claude/patterns/<id>.md"; exit 1; }
[ $WARN -eq 1 ] && echo "pattern-check: avisos de patrones débiles (no bloquean)"
echo "pattern-check: OK"
exit 0
