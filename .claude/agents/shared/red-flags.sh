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
    echo "   Sin esto, cada grep falla en silencio y las 8 comprobaciones dicen «(clean)»." >&2
    exit 2
fi

echo "════════════════════════════════════════════════════════════════"
echo " red-flags.sh · target: ${TARGET}"
echo "════════════════════════════════════════════════════════════════"

# ─── 1. Tailwind opacity classes NOT in default scale ──────────────────────
# Default Tailwind opacity scale: 0/5/10/20/25/30/40/50/60/70/75/80/90/95/100
# Cualquier /15, /35, /45, /55, /65, /85 → JIT no genera → transparente silencioso
echo ""
echo "── [R1] Tailwind opacity inválida (bg-X/85, text-X/45, etc.) ──"
grep -rnE "(bg|text|border|ring|from|to|via|fill|stroke|divide|placeholder)-[a-z]+/(15|35|45|55|65|85|15\b|35\b|45\b|55\b|65\b|85\b)" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.js' --include='*.ts' \
  --include='*.html' --include='*.css' 2>/dev/null || echo "  (clean)"

# ─── 2. Clickbait CSS patterns ─────────────────────────────────────────────
echo ""
echo "── [R2] Clickbait CSS (shine/gradient-border animados) ──"
grep -rnE "(shine|shimmer|sheen|gradient-border|cta-premium|border.*rotating|conic.*animat)" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.css' --include='*.scss' 2>/dev/null || echo "  (clean)"

# ─── 3. AI-slop copy patterns ──────────────────────────────────────────────
echo ""
echo "── [R3] AI-slop copy (phrases LLM genéricas) ──"
grep -rniE "revolucionar|revolutionary|next-level|game-changing|cutting-edge|transform.*business|potencia tu|transforma tu|seamlessly|effortlessly|unlock the power|elevate your" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.js' --include='*.ts' \
  --include='*.md' 2>/dev/null || echo "  (clean)"

# ─── 4. Single-layer shadows on UI elements ────────────────────────────────
echo ""
echo "── [R4] box-shadow de una sola capa (premium = ≥2 capas) ──"
# Busca box-shadow sin comas (= 1 capa). Excluye tokens en tailwind.config
grep -rnE "box-shadow:\s*[0-9][^,;]+;" "$TARGET" \
  --include='*.css' --include='*.scss' --include='*.jsx' --include='*.tsx' 2>/dev/null \
  | grep -v "tailwind.config\|inset 0\|//.*ok" || echo "  (clean)"

# ─── 5. Arbitrary spacing values (not 4/8 scale) ───────────────────────────
echo ""
echo "── [R5] Padding/margin fuera de escala 4/8pt ──"
grep -rnE "(padding|margin|gap):\s*[0-9]+(px|rem)" "$TARGET" \
  --include='*.css' --include='*.scss' 2>/dev/null \
  | grep -vE ":\s*(0|4|8|12|16|20|24|28|32|36|40|44|48|52|56|60|64|72|80|96|112|128)(px|rem)" \
  | head -30 || echo "  (clean)"

# ─── 6. Emojis en UI (no profesional) ──────────────────────────────────────
echo ""
echo "── [R6] Emojis en elementos UI (CTAs, headlines) ──"
# Limitamos a archivos de componentes no-testeable
grep -rnE "(className|class)=[\"'][^\"']*[\"']>.*[📊🚀💡✨🔥💎⚡🎯🎉👀🤖🔒🎓💬💳🛡]" "$TARGET" \
  --include='*.jsx' --include='*.tsx' 2>/dev/null \
  | head -20 || echo "  (clean)"

# ─── 7. Hex hardcoded fuera del sistema tokens ─────────────────────────────
echo ""
echo "── [R7] Hex colors hardcoded (debería usar tokens Tailwind) ──"
grep -rnE "#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.js' --include='*.ts' \
  --include='*.css' 2>/dev/null \
  | grep -v 'tailwind.config\|tokens\|design-system\|ok-hex\|/\*.*design\b\|storybook' \
  | head -30 || echo "  (clean)"

# ─── 8. Duración de animaciones excesiva ───────────────────────────────────
echo ""
echo "── [R8] Animaciones con duration > 500ms en hover/click (excesivo) ──"
grep -rnE "(duration-(700|1000|1500|2000)|transition-duration:\s*(700|800|900|1000|1500|2000)ms|duration:\s*(0\.[7-9]|[1-9]))" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.css' 2>/dev/null \
  | head -20 || echo "  (clean)"

# ─── 9. Urgency badges con pulse agresivo ──────────────────────────────────
echo ""
echo "── [R9] Urgency badges/scarcity copy ──"
grep -rnE "Solo [0-9]+ plazas|plazas disponibles|Oferta expira|expires (in|today)|Last chance|Última oportunidad|¡Apúrate!|Limited time" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.js' 2>/dev/null \
  | head -10 || echo "  (clean)"

# ─── 10. TODOs/placeholders ────────────────────────────────────────────────
echo ""
echo "── [R10] TODOs, placeholders, lorem ipsum ──"
grep -rniE "TODO[^(]|FIXME|XXX|lorem ipsum|PLACEHOLDER|<!-- TODO" "$TARGET" \
  --include='*.jsx' --include='*.tsx' --include='*.js' --include='*.ts' \
  --include='*.md' 2>/dev/null \
  | grep -v 'contact\.js\|CHECKLIST\|\.test\.\|\.spec\.' \
  | head -20 || echo "  (clean)"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo " Finalizado. Revisa findings arriba. Cada match = posible P1+."
echo "════════════════════════════════════════════════════════════════"
