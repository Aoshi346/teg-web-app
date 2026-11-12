#!/bin/bash
# Hook: Validación antes de commit
# Bloquea si hay node_modules, .env, credentials o mock data hardcodeada en staged files
#
# Uso: enlazarlo como git hook real:
#   ln -s ../../.claude/hooks/pre-commit-check.sh .git/hooks/pre-commit

set -euo pipefail

# Solo lo que ENTRA en el commit (añadido, copiado, modificado, renombrado). Sacar algo del índice
# con `git rm --cached` no mete nada en el historial, y el fichero sigue en disco: contarlo bloqueaba
# justo las limpiezas que este hook quiere facilitar.
STAGED=$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)

if [ -z "$STAGED" ]; then
  exit 0
fi

# --- Secretos / files prohibidos ---

# Check for node_modules
if echo "$STAGED" | grep -q "node_modules/"; then
  echo "BLOCKED: node_modules/ detectado en staged files."
  echo "Ejecuta: git reset HEAD -- '**/node_modules/**'"
  exit 1
fi

# Check for .env files. `.env.example` NO es un secreto: es la plantilla que el propio .gitignore
# del template deja pasar (`!.env.example`), y los fixtures del comprobador de patrones llevan una
# a propósito. Medido el 2026-09-14: el primer commit de un derivado se bloqueaba por
# `patterns/stack/_fixtures/{conforme,infractor}/.env.example`.
if echo "$STAGED" | grep -vE '\.env\.example$' | grep -qE '\.env($|\.)'; then
  echo "BLOCKED: Archivo .env detectado en staged files."
  echo "Ejecuta: git reset HEAD -- '*.env*'"
  exit 1
fi

# Check for credentials/secrets
if echo "$STAGED" | grep -qE '(credentials|secrets|\.pem|\.key)'; then
  echo "BLOCKED: Archivo sensible detectado en staged files."
  echo "Revisa los archivos staged y elimina los sensibles."
  exit 1
fi

# --- Ficheros grandes y claves privadas (EVO-16) ---
# Por qué: en el repo de referencia entraron 89 MB de cuadernos y una clave privada, y la regla que
# se propuso para evitarlo medía la UBICACIÓN del fichero — se satisfacía moviéndolo de carpeta, con
# el 100% del daño intacto. Lo que caza el daño de verdad es el CONTENIDO, aquí y en cualquier ruta.
MAX_KB=500
BIG=""
# Un RENOMBRADO AL 100 % no cuenta: mover un fichero ya versionado reutiliza su blob y no mete ni un
# byte en el historial, que es lo que esta guarda protege. Sin esta excepción, archivar un plan viejo
# con un HTML de 650 KB pedía `--no-verify`, y un gate que se salta por rutina deja de ser gate
# (medido el 2026-10-19, LI-30: 8 ficheros ya versionados bloqueaban el `git mv`). Un renombrado CON
# cambios (R<100) sí entra: su contenido nuevo es un blob nuevo. Y por línea, no por palabra: así los
# nombres con espacios se miden en vez de saltarse. `core.quotePath=false`: sin él git entrecomilla
# los nombres con acentos ("presentaci\303\263n.bin") y el `[ -f ]` no los encuentra (verificador, 19-10).
while IFS= read -r f; do
  [ -n "$f" ] && [ -f "$f" ] || continue
  KB=$(( $(wc -c < "$f") / 1024 ))
  [ "$KB" -gt "$MAX_KB" ] && BIG="$BIG\n  $f (${KB} KB)"
done < <(git -c core.quotePath=false diff --cached --name-status -M --diff-filter=ACMR 2>/dev/null | awk -F'\t' '$1 != "R100" {print $NF}')
if [ -n "$BIG" ]; then
  echo "BLOQUEADO: fichero(s) de más de ${MAX_KB} KB en el commit:"
  printf "%b\n" "$BIG"
  echo "Un binario grande se queda en el historial PARA SIEMPRE: sacarlo después no lo borra,"
  echo "cada clon lo seguirá descargando. Si de verdad debe ir, usa git-lfs o --no-verify."
  exit 1
fi

# Cuadernos: pesan, y guardan la salida de las celdas (a veces con datos reales dentro)
if echo "$STAGED" | grep -q '\.ipynb$'; then
  echo "BLOQUEADO: cuaderno .ipynb en el commit."
  echo "Guardan la salida de las celdas —datos incluidos— y engordan el repo. Exporta el .py."
  exit 1
fi

# Contenido de clave privada, mire donde mire la extensión
for f in $STAGED; do
  [ -f "$f" ] || continue
  if head -c 4096 "$f" 2>/dev/null | grep -qE 'BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY'; then
    echo "BLOQUEADO: $f contiene una CLAVE PRIVADA."
    echo "Y si ya se subió alguna vez: no basta con borrarla — una clave publicada SE ROTA."
    exit 1
  fi
done

# --- Secretos en el CONTENIDO (SE-31, 2026-10-22) ---
# Todo lo de arriba mira NOMBRES de fichero. Un `sk-ant-…` pegado dentro de settings.py entraba sin
# aviso, y los agentes hacen `git add -A`. El escáner mira las líneas que AÑADE el commit, no
# imprime el valor y respeta `# tl-secret-ok: <razón>`. Exit 1 = secreto (bloquea); 2 = no se pudo
# medir (git roto): un gate que no puede medir no dice «limpio», avisa y deja pasar para no dejar
# el repo sin poder commitear.
AQUI_PC="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
SCAN_SECRETOS="$AQUI_PC/../scripts/scan_secretos_diff.py"
if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN_SECRETOS" ]; then
  RC_SEC=0
  python3 "$SCAN_SECRETOS" || RC_SEC=$?       # sin el `||`, `set -e` cortaría aquí con el rc 2 y sin aviso
  if [ "$RC_SEC" -eq 1 ]; then exit 1; fi
  if [ "$RC_SEC" -ne 0 ]; then echo "AVISO: el escáner de secretos no pudo medir (rc=$RC_SEC); revisa a mano." >&2; fi
else
  echo "AVISO: sin python3 o sin scan_secretos_diff.py: este commit NO se ha escaneado en busca de secretos." >&2
fi

# --- Anti-mock: detectar datos hardcodeados ---
# Solo aplica a archivos de código fuente (frontend/backend); ignora tests y docs.

MOCK_TARGETS=$(echo "$STAGED" | grep -E '\.(ts|tsx|js|jsx|py)$' | grep -viE '(test|spec|stories|__tests__|fixtures)' || true)

if [ -n "$MOCK_TARGETS" ]; then
  MOCK_HITS=""
  for f in $MOCK_TARGETS; do
    [ -f "$f" ] || continue
    # Código vendorizado de terceros (rules/vendoring.md): no es nuestro producto ni se parchea por un
    # grep. Cuenta como tal lo que cuelga de `.claude/resources/referencias-diseno/terceros/` y la
    # carpeta de una skill cuyo SKILL.md declara `metadata.vendored`. Nada más se excluye.
    case "$f" in
      .claude/resources/referencias-diseno/terceros/*) continue ;;
      .claude/skills/*/*|.claude/templates/skills-opcionales/*/*)
        skill_dir=$(printf '%s' "$f" | cut -d/ -f1-3)
        [ "${f#.claude/templates/}" != "$f" ] && skill_dir=$(printf '%s' "$f" | cut -d/ -f1-4)
        if [ -f "$skill_dir/SKILL.md" ] && grep -qE '^[[:space:]]+vendored:' "$skill_dir/SKILL.md"; then
          continue
        fi ;;
    esac
    # Patrones anti-mock: mockData, fakeData, dummyData, TODO.*real, // fake, demo_data
    # Solo en las líneas que AÑADE este commit: mirar el fichero entero bloqueaba por comentarios que ya
    # estaban (elvion, 19-10-2026) y obligaba a --no-verify, que se salta TODOS los controles.
    if git diff --cached -U0 -- "$f" 2>/dev/null | grep -E '^\+[^+]' | grep -nE '(mockData|fakeData|dummyData|TODO.*real|//[[:space:]]*fake|demo_data|hardcoded)' | head -3; then
      MOCK_HITS="$MOCK_HITS\n$f"
    fi
  done
  if [ -n "$MOCK_HITS" ]; then
    echo ""
    echo "BLOCKED: Se detectó posible mock/fake data en archivos de producción."
    echo "Revisa las líneas arriba y elimina o muévelas a tests/fixtures."
    echo "Si es intencional, usa 'git commit --no-verify' (queda loggeado)."
    exit 1
  fi
fi

# Check PROGRESS.json exists (opcional, no bloquea)
if [ ! -f "PROGRESS.json" ]; then
  echo "WARNING: PROGRESS.json no existe. Considera crearlo antes de commitear."
fi

exit 0
