#!/usr/bin/env bash
# pytest_turn.sh <ruta-del-módulo> [args de pytest] — pytest de UN módulo con turno: como mucho N a
# la vez en la MÁQUINA (no por repo: la RAM es de todos), y check-ram.sh antes de cada uno.
#
# POR QUÉ (AN-20, cosechado de la pizarra de elvion). Con varios frentes vivos, cada sesión cumple
# «pytest por módulo» y aun así la máquina se queda sin memoria: tres módulos a la vez son tres
# suites. `rules/ram-pytest.md` pone el tope; esto lo hace cumplir con `flock`, que el sistema
# suelta solo aunque el proceso muera (no quedan candados huérfanos).
#
# Variables: TL_PYTEST_TURNS (2) · TL_PYTEST_LOCK_DIR (/tmp/tl-pytest-turn, compartida por todos
# los repos) · TL_PYTEST_CMD (por defecto: `poetry run pytest` si el pyproject es de poetry, si no
# `.venv/bin/pytest`, si no `python3 -m pytest`) · TL_PYTEST_NOWAIT=1 (sale con 75 si no hay turno).
#
#   bash .claude/scripts/pytest_turn.sh apps/billing -q --maxfail=3
#   bash .claude/scripts/pytest_turn.sh --self-test
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

self_test() {
  local T fails=0 rc
  T=$(mktemp -d)
  export TL_PYTEST_LOCK_DIR="$T/locks" TL_PYTEST_TURNS=1 TL_PYTEST_CMD="true" TL_CHECK_RAM="$T/ram.sh"
  printf '#!/bin/sh\nexit 0\n' > "$T/ram.sh"
  bash "$HERE/pytest_turn.sh" apps/x >/dev/null 2>&1; rc=$?
  [ $rc = 0 ] && echo "  ✓ turno libre → corre" || { echo "  ✗ turno libre → rc $rc"; fails=$((fails+1)); }
  mkdir -p "$T/locks"
  ( exec 9>"$T/locks/pytest-1.lock"; flock 9; sleep 5 ) &
  local holder=$!
  sleep 0.5
  TL_PYTEST_NOWAIT=1 bash "$HERE/pytest_turn.sh" apps/x >/dev/null 2>&1; rc=$?
  [ $rc = 75 ] && echo "  ✓ turno ocupado con NOWAIT → 75" || { echo "  ✗ turno ocupado → rc $rc"; fails=$((fails+1)); }
  kill "$holder" 2>/dev/null; wait "$holder" 2>/dev/null
  printf '#!/bin/sh\nexit 1\n' > "$T/ram.sh"
  bash "$HERE/pytest_turn.sh" apps/x >/dev/null 2>&1; rc=$?
  [ $rc = 1 ] && echo "  ✓ check-ram en rojo → no corre (1)" || { echo "  ✗ check-ram rojo → rc $rc"; fails=$((fails+1)); }
  rm -rf "$T"
  [ "$fails" = 0 ] && echo "self-test: OK" || echo "self-test: $fails FALLO(S)"
  [ "$fails" = 0 ]
}
[ "${1:-}" = "--self-test" ] && { self_test; exit $?; }

MOD="${1:?uso: pytest_turn.sh <ruta-del-módulo> [args]}"; shift
TURNS="${TL_PYTEST_TURNS:-2}"
LOCKS="${TL_PYTEST_LOCK_DIR:-/tmp/tl-pytest-turn}"
RAM="${TL_CHECK_RAM:-.claude/hooks/check-ram.sh}"
mkdir -p "$LOCKS" && chmod 1777 "$LOCKS" 2>/dev/null
if [ -n "${TL_PYTEST_CMD:-}" ]; then CMD="$TL_PYTEST_CMD"
elif grep -q '^\[tool\.poetry\]' pyproject.toml 2>/dev/null && command -v poetry >/dev/null; then CMD="poetry run pytest"
elif [ -x .venv/bin/pytest ]; then CMD=".venv/bin/pytest"
else CMD="python3 -m pytest"; fi

run_tests() {
  bash "$RAM" || { echo "❌ check-ram.sh no da vía libre: no se corre pytest" >&2; exit 1; }
  # shellcheck disable=SC2086
  $CMD "$MOD" "$@"
  exit $?
}
for n in $(seq 1 "$TURNS"); do
  exec {fd}>"$LOCKS/pytest-$n.lock"
  if flock -n "$fd"; then run_tests "$@"; fi
  exec {fd}>&-
done
[ "${TL_PYTEST_NOWAIT:-}" = 1 ] && { echo "· los $TURNS turnos de pytest están ocupados" >&2; exit 75; }
echo "· los $TURNS turnos de pytest están ocupados: esperando el 1…" >&2
exec {fd}>"$LOCKS/pytest-1.lock"; flock "$fd"; run_tests "$@"
