#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# red-flags.sh — Detección automática de anti-patrones visuales/copy
# Usado por: vera-art-director, lidia-naive-tester, ignacio-roig
# Fuente: deep research 2026-04-22 (ELV-5 Calibration research, 2374 lines)
# ─────────────────────────────────────────────────────────────────────────────

set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# ── Vera, iter-11 · el default apuntaba a un directorio que no existe ─────────────────────────
# Era `TARGET="${1:-src}"` y en este repo NO hay `src/` — el frontend vive en `frontend/src`. Las
# tres fichas que usan este script lo llaman SIN argumento, así que `grep` fallaba en todas las
# comprobaciones y cada una imprimía «(clean)».
#
# Medido: sin argumento, 4 «(clean)». Con `frontend/src`, 3 «(clean)» **y un hallazgo real de
# AI-slop** que llevaba escondido quién sabe cuánto. No es que no encontrara nada: es que no
# miraba, y decía que estaba limpio.
#
# Dos arreglos, y el segundo importa más que el primero:
#   1. el default se busca entre los sitios donde de verdad vive el frontend;
#   2. si el destino NO existe, esto **ABORTA** en vez de imprimir «(clean)». Un instrumento que
#      no puede mirar tiene que decirlo, no dar una buena noticia.
if [ $# -ge 1 ]; then
    TARGET="$1"
else
    TARGET=""
    for CANDIDATO in frontend/src src app assets templates; do
        [ -d "$CANDIDATO" ] && { TARGET="$CANDIDATO"; break; }
    done
    if [ -z "$TARGET" ]; then
        echo "⛔ red-flags.sh: no encuentro dónde mirar." >&2
        echo "   Probé: frontend/src · src · app · assets · templates — ninguno existe aquí." >&2
        echo "   Pásale el directorio: bash $0 <ruta>" >&2
        echo "   NO se imprime «(clean)»: no haber mirado no es estar limpio." >&2
        exit 2
    fi
fi

if [ ! -d "$TARGET" ]; then
    echo "⛔ red-flags.sh: el destino '$TARGET' no existe." >&2
    echo "   Sin esto, cada grep falla en silencio y las 10 comprobaciones dicen «(clean)»." >&2
    exit 2
fi

# ── 2026-09-18 · SEIS comprobaciones salían MUDAS, y el silencio se leía como «limpio» ────────
# R5, R6, R7, R8, R9 y R10 terminaban en `| head -N || echo "  (clean)"`. **`head` sale 0
# siempre**, también con la entrada vacía, así que el `||` no disparaba nunca: no imprimían el
# hallazgo (porque no lo había) NI el «(clean)». Seis de diez checks no decían absolutamente
# nada.
#
# Es el mismo fallo que el de iter-11, una capa más abajo: allí el instrumento no podía mirar;
# aquí no podía hablar. Y los dos fallan en la misma dirección — hacia la buena noticia.
#
# Arreglo: `reportar` captura la salida y decide. Imprime «(clean)» SOLO cuando de verdad no hay
# coincidencias, y lleva la cuenta para el resumen final. El contador vive en un fichero porque
# una función dentro de una tubería corre en subshell y una variable no sobreviviría.
CONTADOR="$(mktemp)"; echo 0 > "$CONTADOR"
trap 'rm -f "$CONTADOR"' EXIT

reportar() {
    local salida
    salida="$(cat)"
    if [ -n "$salida" ]; then
        printf '%s\n' "$salida"
        echo $(( $(cat "$CONTADOR") + 1 )) > "$CONTADOR"
    else
        echo "  (clean)"
    fi
}

echo "════════════════════════════════════════════════════════════════"
echo " red-flags.sh · target: ${TARGET}"
echo "════════════════════════════════════════════════════════════════"

# ─── 1. Tailwind opacity classes NOT in default scale ──────────────────────
# Default Tailwind opacity scale: 0/5/10/20/25/30/40/50/60/70/75/80/90/95/100
# Cualquier /15, /35, /45, /55, /65, /85 → JIT no genera → transparente silencioso
echo ""
echo "── [R1] Tailwind opacity inválida (bg-X/85, text-X/45, etc.) ──"
# ── 2026-09-18 · R1 NO PODÍA CAZAR SU PROPIO CASO ────────────────────────────────────────────
# La regex era `-[a-z]+/(15|35|…)`, y `[a-z]+` no casa con `blue-500`: solo cazaba colores sin
# escala numérica (`bg-white/85`), que son la minoría. O sea que la clase real de Tailwind que
# esta comprobación existe para encontrar —`bg-blue-500/85`— le pasaba por delante.
# Descubierto plantándole una violación a propósito, que es la única forma de saberlo.
grep -rnE "(bg|text|border|ring|from|to|via|fill|stroke|divide|placeholder)-[a-z]+(-[0-9]{2,3})?/(15|35|45|55|65|85)\b" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.js' --include='*.ts' \
  --include='*.html' --include='*.css' 2>/dev/null | reportar

# ─── 2. Clickbait CSS patterns ─────────────────────────────────────────────
echo ""
echo "── [R2] Clickbait CSS (shine/gradient-border animados) ──"
grep -rnE "(shine|shimmer|sheen|gradient-border|cta-premium|border.*rotating|conic.*animat)" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.css' --include='*.scss' 2>/dev/null | reportar

# ─── 3. AI-slop copy patterns ──────────────────────────────────────────────
echo ""
echo "── [R3] AI-slop copy (phrases LLM genéricas) ──"
grep -rniE "revolucionar|revolutionary|next-level|game-changing|cutting-edge|transform.*business|potencia tu|transforma tu|seamlessly|effortlessly|unlock the power|elevate your" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.js' --include='*.ts' \
  --include='*.md' 2>/dev/null | reportar

# ─── 4. Sombra en negro puro (debería ir teñida con el oscuro de marca) ────
# ── 2026-09-18 · R4 decía lo contrario de lo que hay que decir ────────────────────────────────
# Era: «box-shadow de una sola capa (premium = ≥2 capas)», y marcaba toda sombra sin comas. Eso
# **premia el look de tarjeta SaaS** — la sombra multicapa suave es literalmente uno de los
# clusters que el skill oficial `frontend-design` lista como señal de IA. Un red flag que empuja
# hacia lo genérico no es un red flag.
#
# Lo que sí está medido en el corpus (`resources/referencias-diseno/`, T5): las sombras buenas
# NUNCA son negro puro — van teñidas con el oscuro de la marca
# (`0 8px 32px rgba(45,36,32,.10)`), y por eso la sombra se funde con el fondo en vez de
# ensuciarlo. Lo que se marca ahora es el negro puro.
echo ""
echo "── [R4] Sombra en negro puro (debería teñirse con el oscuro de marca) ──"
grep -rnE "box-shadow:[^;]*(rgba\(\s*0\s*,\s*0\s*,\s*0|#000\b|#000000\b)" "$TARGET" \
  --include='*.css' --include='*.scss' --include='*.jsx' --include='*.tsx' --include='*.html' 2>/dev/null \
  | grep -v "tailwind.config\|//.*ok\|/\*.*ok" | reportar

# ─── 5. Arbitrary spacing values (not 4/8 scale) ───────────────────────────
echo ""
echo "── [R5] Padding/margin fuera de escala 4/8pt ──"
grep -rnE "(padding|margin|gap):\s*[0-9]+(px|rem)" "$TARGET" \
  --include='*.css' --include='*.scss' 2>/dev/null \
  | grep -vE ":\s*(0|4|8|12|16|20|24|28|32|36|40|44|48|52|56|60|64|72|80|96|112|128)(px|rem)" \
  | head -30 | reportar

# ─── 6. Emojis en UI (no profesional) ──────────────────────────────────────
echo ""
echo "── [R6] Emojis en elementos UI (CTAs, headlines) ──"
# Limitamos a archivos de componentes no-testeable
grep -rnE "(className|class)=[\"'][^\"']*[\"']>.*[📊🚀💡✨🔥💎⚡🎯🎉👀🤖🔒🎓💬💳🛡]" "$TARGET" \
  --include='*.jsx' --include='*.tsx' 2>/dev/null \
  | head -20 | reportar

# ─── 7. Hex hardcoded fuera del sistema tokens ─────────────────────────────
echo ""
echo "── [R7] Hex colors hardcoded (debería usar tokens Tailwind) ──"
grep -rnE "#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.js' --include='*.ts' \
  --include='*.css' 2>/dev/null \
  | grep -v 'tailwind.config\|tokens\|design-system\|ok-hex\|/\*.*design\b\|storybook' \
  | head -30 | reportar

# ─── 8. Duración de animaciones excesiva ───────────────────────────────────
echo ""
echo "── [R8] Animaciones con duration > 500ms en hover/click (excesivo) ──"
grep -rnE "(duration-(700|1000|1500|2000)|transition-duration:\s*(700|800|900|1000|1500|2000)ms|duration:\s*(0\.[7-9]|[1-9]))" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.css' 2>/dev/null \
  | head -20 | reportar

# ─── 9. Urgency badges con pulse agresivo ──────────────────────────────────
echo ""
echo "── [R9] Urgency badges/scarcity copy ──"
grep -rnE "Solo [0-9]+ plazas|plazas disponibles|Oferta expira|expires (in|today)|Last chance|Última oportunidad|¡Apúrate!|Limited time" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.js' 2>/dev/null \
  | head -10 | reportar

# ─── 10. TODOs/placeholders ────────────────────────────────────────────────
echo ""
echo "── [R10] TODOs, placeholders, lorem ipsum ──"
grep -rniE "TODO[^(]|FIXME|XXX|lorem ipsum|PLACEHOLDER|<!-- TODO" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.js' --include='*.ts' \
  --include='*.md' 2>/dev/null \
  | grep -v 'contact\.js\|CHECKLIST\|\.test\.\|\.spec\.' \
  | head -20 | reportar

TOTAL="$(cat "$CONTADOR")"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo " Finalizado · ${TOTAL} de 10 comprobaciones con hallazgos."
echo " Cada match = posible P1+. Un «(clean)» aquí SÍ significa que se miró."
echo "════════════════════════════════════════════════════════════════"
