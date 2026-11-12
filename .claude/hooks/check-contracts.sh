#!/usr/bin/env bash
# check-contracts.sh — gancho de PRE-COMMIT de git (no de settings.json). OPCIONAL (AN-19, cosechado
# de cold_calling_coach). Que el contrato no se desincronice del código:
#   1. si el commit toca la superficie de la API Django (serializers, views, urls), el schema OpenAPI
#      versionado (`schema.yml`, o `$TL_OPENAPI_FILE`) tiene que estar regenerado (drf-spectacular);
#   2. todo JSON Schema del commit (`*.schema.json` o bajo `schemas/`) tiene que ser JSON válido.
# `patterns/stack/frontend-contrato-con-el-backend.md` define el contrato; esto solo lo hace cumplir.
# Degrada en silencio sin backend, sin manage.py o sin drf-spectacular: no bloquea por no saber.
# Lo de origen propio del dominio (subir `evaluator_version` al cambiar el schema del hallazgo) no viaja.
#
# Instalar (encadenado al pre-commit de casa):
#   echo 'bash .claude/hooks/check-contracts.sh || exit 1' >> .git/hooks/pre-commit
set -uo pipefail
FAIL=0
STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
[ -z "$STAGED" ] && exit 0
SCHEMA="${TL_OPENAPI_FILE:-schema.yml}"

if printf '%s\n' "$STAGED" | grep -qE '(^|/)apps/.*/(serializers|views|urls)\.py$' \
   && [ -f manage.py ] && [ -f "$SCHEMA" ] && python3 -c 'import drf_spectacular' 2>/dev/null; then
  TMP=$(mktemp --suffix=.yml)
  if ! python3 manage.py spectacular --file "$TMP" >/dev/null 2>&1; then
    echo "⚠️  No se pudo regenerar el schema OpenAPI; revísalo a mano." >&2
  elif ! diff -q "$SCHEMA" "$TMP" >/dev/null 2>&1; then
    echo "BLOQUEADO: tocaste la API y $SCHEMA no está regenerado:" >&2
    echo "  python3 manage.py spectacular --file $SCHEMA && git add $SCHEMA" >&2
    echo "  (y si el frontend consume tipos: npx openapi-typescript $SCHEMA -o <ruta de los tipos>)" >&2
    FAIL=1
  fi
  rm -f "$TMP"
fi

while IFS= read -r f; do
  [ -n "$f" ] && [ -f "$f" ] || continue
  if ! python3 -c 'import json,sys; json.load(open(sys.argv[1], encoding="utf-8"))' "$f" 2>/dev/null; then
    echo "BLOQUEADO: '$f' no es JSON válido." >&2
    FAIL=1
  fi
done < <(printf '%s\n' "$STAGED" | grep -E '(\.schema\.json$|(^|/)schemas/.*\.json$)' || true)

exit $FAIL
