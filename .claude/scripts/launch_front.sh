#!/usr/bin/env bash
# launch_front.sh <plan> <nombre> [--solo-guarda] — lanza una sesión-frente del plan en SU worktree,
# después de diez guardas. El comando NO se escribe aquí: sale de `<plan>/sesiones.json` vía
# `gen_sesiones.py --comando`, el mismo que enseña la pestaña «Sesiones». Con --solo-guarda solo
# comprueba (es lo que antepone el propio comando generado).
#
# POR QUÉ (AN-20, cosechado de la pizarra de elvion, 26-09). Abrir un frente en paralelo falla por lo
# que no se ve: un workspace sin confianza (`claude --bg` se niega), una sesión viva con el mismo
# nombre, un worktree que nace sin lo que no estaba commiteado o desde «Initial commit», un `.env` que
# no viaja al worktree, un puerto de la franja ya cogido. Cada guarda es uno de esos casos medidos.
#
# Las diez, en orden; aborta en la primera que falla (exit 1 y el porqué):
#   1 el nombre está en sesiones.json          6 el principal está en la rama tronco
#   2 el repo pasó el diálogo de confianza       7 el tronco no tiene cambios sin commitear
#   3 check-ram.sh da vía libre                  8 worktree.baseRef = "head" en .claude/settings.json
#   4 no hay sesión viva con ese nombre          9 cada .env* de la raíz está en .worktreeinclude
#   5 el worktree no existe ya                  10 (y) los puertos de su franja están libres
# La confianza la acepta el Usuario abriendo `claude` una vez en el repo; nunca se marca a mano.
#
# sesiones.json: lo de gen_sesiones.py (`repo`, `sesiones[].nombre`, `sesiones[].franja`) más
# `"tronco"` (por defecto develop). Los puertos de la franja son sus valores enteros.
# Variables para pruebas: TL_CLAUDE_JSON (~/.claude.json), TL_CHECK_RAM (el check-ram.sh del repo).
#
#   bash .claude/scripts/launch_front.sh .docs/plans/<plan> evo-catalogo --solo-guarda
#   bash .claude/scripts/launch_front.sh --self-test
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fail(){ echo "❌ $*" >&2; exit 1; }

self_test() {
  local T R P fails=0 out
  T=$(mktemp -d); R="$T/repo"; P="$R/.docs/plans/p"
  mkdir -p "$R/.claude" "$P" "$T/bin"
  git -C "$R" init -q -b develop && git -C "$R" config user.email t@t && git -C "$R" config user.name t
  printf '{"worktree": {"baseRef": "head"}}\n' > "$R/.claude/settings.json"
  printf 'x\n' > "$R/a.txt"; printf 'K=1\n' > "$R/.env"; printf '.env\n' > "$R/.worktreeinclude"
  git -C "$R" add a.txt .claude/settings.json .worktreeinclude && git -C "$R" commit -qm init
  printf '{"repo": "%s", "tronco": "develop", "sesiones": [{"nombre": "f1", "franja": {"runserver": 59871}}]}\n' "$R" > "$P/sesiones.json"
  printf '{"projects": {"%s": {"hasTrustDialogAccepted": true}}}\n' "$R" > "$T/claude.json"
  printf '#!/bin/sh\necho "[]"\n' > "$T/bin/claude"; chmod +x "$T/bin/claude"
  printf '#!/bin/sh\nexit 0\n' > "$T/ram.sh"
  run() { PATH="$T/bin:$PATH" TL_CLAUDE_JSON="$T/claude.json" TL_CHECK_RAM="$T/ram.sh" bash "$HERE/launch_front.sh" "$@" 2>&1; }
  expect_case() {  # <nombre> <rc esperado> <texto esperado> <args…>
    local n="$1" want="$2" txt="$3"; shift 3
    out=$(run "$@"); local rc=$?
    if [ "$rc" = "$want" ] && printf '%s' "$out" | grep -q -- "$txt"; then echo "  ✓ $n"; else
      echo "  ✗ $n (rc $rc, esperado $want): $out"; fails=$((fails+1)); fi
  }
  expect_case "todo en orden → guarda en verde" 0 "en verde" "$P" f1 --solo-guarda
  expect_case "nombre que no está en sesiones.json → rechaza" 1 "no está en sesiones.json" "$P" nadie --solo-guarda
  printf 'y\n' >> "$R/a.txt"
  expect_case "tronco sucio → rechaza" 1 "cambios sin commitear" "$P" f1 --solo-guarda
  git -C "$R" checkout -q -- a.txt
  printf '{"worktree": {"baseRef": "fresh"}}\n' > "$R/.claude/settings.json"; git -C "$R" commit -qam base
  expect_case "baseRef distinto de head → rechaza" 1 "baseRef" "$P" f1 --solo-guarda
  printf '{"worktree": {"baseRef": "head"}}\n' > "$R/.claude/settings.json"; git -C "$R" commit -qam base2
  printf 'K=2\n' > "$R/.env.franja"
  expect_case ".env.franja fuera de .worktreeinclude → rechaza" 1 ".worktreeinclude no lista .env.franja" "$P" f1 --solo-guarda
  rm -f "$R/.env.franja"
  printf '{"projects": {}}\n' > "$T/claude.json"
  expect_case "workspace sin confianza → rechaza" 1 "no es de confianza" "$P" f1 --solo-guarda
  rm -rf "$T"
  [ "$fails" = 0 ] && echo "self-test: OK" || echo "self-test: $fails FALLO(S)"
  [ "$fails" = 0 ]
}

[ "${1:-}" = "--self-test" ] && { self_test; exit $?; }
PLAN="$(cd "${1:?uso: launch_front.sh <plan> <nombre> [--solo-guarda]}" 2>/dev/null && pwd)" || fail "no existe el plan $1"
N="${2:?uso: launch_front.sh <plan> <nombre> [--solo-guarda]}"
SJ="$PLAN/sesiones.json"
[ -f "$SJ" ] || fail "no hay $SJ"
read -r REPO TRONCO PORTS < <(python3 - "$SJ" "$N" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
s = next((x for x in d.get("sesiones", []) if x.get("nombre") == sys.argv[2]), None)
if not s:
    sys.exit(3)
ports = ",".join(str(v) for v in (s.get("franja") or {}).values() if isinstance(v, int))
print(d.get("repo") or ".", d.get("tronco") or "develop", ports or "-")
PY
) || fail "«$N» no está en sesiones.json"
[ -n "${REPO:-}" ] || fail "«$N» no está en sesiones.json"
cd "$REPO" 2>/dev/null || fail "no existe el repo $REPO"
REPO="$(pwd)"
CJ="${TL_CLAUDE_JSON:-$HOME/.claude.json}"
python3 -c "import json,sys;d=json.load(open(sys.argv[1]));sys.exit(0 if d.get('projects',{}).get(sys.argv[2],{}).get('hasTrustDialogAccepted') else 1)" "$CJ" "$REPO" 2>/dev/null \
  || fail "el workspace $REPO no es de confianza: el Usuario abre \`claude\` allí UNA vez, acepta el aviso y sale"
RAM="${TL_CHECK_RAM:-$REPO/.claude/hooks/check-ram.sh}"
bash "$RAM" >/dev/null 2>&1 || fail "check-ram.sh no da vía libre: no se lanza una sesión más"
command -v claude >/dev/null 2>&1 || fail "sin \`claude\` no se puede mirar si ya hay una sesión «$N» viva"
if claude agents --json 2>/dev/null | python3 -c "import json,sys;n=sys.argv[1];d=json.load(sys.stdin);sys.exit(0 if any(a.get('name')==n and (a.get('status') or a.get('state')) not in ('completed','stopped','done') for a in d) else 1)" "$N"; then
  fail "ya hay una sesión viva «$N»: reanúdala (claude agents / claude attach), no abras otra encima"
fi
git worktree list --porcelain | grep -q "worktrees/$N\$" && fail "el worktree .claude/worktrees/$N ya existe: reanuda, no lo dupliques"
[ "$(git branch --show-current)" = "$TRONCO" ] || fail "el checkout principal no está en $TRONCO"
[ -z "$(git status --porcelain --untracked-files=no)" ] || fail "el principal tiene cambios sin commitear: el worktree nacería sin ellos (baseRef=head)"
python3 -c "import json,sys;s=json.load(open('.claude/settings.json'));sys.exit(0 if s.get('worktree',{}).get('baseRef')=='head' else 1)" 2>/dev/null \
  || fail "worktree.baseRef no es 'head' en .claude/settings.json: el worktree nacería desde origin/HEAD"
for f in .env*; do
  [ -f "$f" ] || continue
  case "$f" in *.example|*.sample|*.template) continue ;; esac
  grep -qx "$f" .worktreeinclude 2>/dev/null || fail ".worktreeinclude no lista $f: el worktree nacería sin él"
done
if [ "$PORTS" != "-" ]; then
  for p in ${PORTS//,/ }; do
    ss -tlnH "sport = :$p" 2>/dev/null | grep -q . && fail "el puerto $p de la franja de $N está ocupado"
  done
fi
echo "✅ guarda de «$N» en verde"
[ "${3:-}" = "--solo-guarda" ] && exit 0
GEN="$REPO/.claude/templates/report_kit/gen_sesiones.py"
[ -f "$GEN" ] || GEN="$HERE/../templates/report_kit/gen_sesiones.py"
CMD=$(python3 "$GEN" --comando "$PLAN" "$N") || fail "gen_sesiones --comando falló"
echo "→ $CMD"
eval "$CMD"
