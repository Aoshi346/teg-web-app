---
name: ui-ux-pro-max-design
description: >-
  Usar a mano, y solo con decisión expresa del Usuario, para generar logo, identidad corporativa
  (CIP) o iconos con IA. Manda la marca, y con --logo la imagen, a Google Gemini sin DPA: el hook
  pregunta antes de CADA envío.
  NO usar para: la identidad de la casa (marca), los tokens ni consultar paletas (resources).
disable-model-invocation: true
metadata:
  vendored:
    repo: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
    commit: a38d04c3d5c298c851dbe5e6ee1965ee3de42cb5
    license: MIT
    date: 2026-10-31
    sends_out: [scripts/logo/generate.py, scripts/cip/generate.py, scripts/icon/generate.py]
---

> Vendorizada de nextlevelbuilder/ui-ux-pro-max-skill@a38d04c (tag v2.15.0, su carpeta de skill
> «design») el 31-10-2026 (MIT, `LICENSE`); parches marcados «tech-lead-template (3.66)». El SKILL.md
> del autor no se copia (rutas de su instalación y sub-skills que no se traen): esta página lo sustituye.

# Generadores de UI/UX Pro Max — logo, identidad e iconos con IA

**Decisión del Usuario (18-10, UX-D2):** se guardan los generadores, pero **con aviso CADA VEZ** que se
vayan a usar, porque envían material del cliente a un tercero sin contrato de encargo (DPA). Por eso:

1. **Antes de nada, `marca`.** La identidad la decide la skill `marca` con el Usuario; un logo generado
   que nadie eligió es la ruta que `motores-de-diseno.md` §F1b no admite. Esto es, como mucho, una
   dirección más para `direcciones-de-arte`, y entra en el escalón 8 (§1).
2. **Cada envío pregunta.** `.claude/envios-externos.json` declara los tres generadores con
   `always_ask: true`: el hook `aviso-envio-externo.sh` pide confirmación en cualquier proyecto, sea o no
   delicado. Sin nadie delante (`claude -p`) la pregunta se queda en denegación y no sale nada.
   Confirmar solo si el dueño de la marca ha aceptado por escrito que salga a Google.
3. **Clave y dependencia.** Necesitan `GEMINI_API_KEY` (o `GOOGLE_API_KEY` en `cip`) en el `.env` de
   esta carpeta, y el paquete `google-genai`. Ninguno de los dos viene puesto: instalarlo y la clave (que
   es gasto de API) los decide el Usuario. Parche: el script ya no lee `~/.claude/.env` ni
   `~/.claude/skills/.env`, y de su `.env` solo carga esas dos claves.
4. **Si un generador falla, se para y se avisa.** No se reescriben sus scripts para que funcionen.

## Qué manda fuera cada script (leído entero el 31-10)

| Script | Sale a | Qué sale | Sin red |
|---|---|---|---|
| `.claude/skills/ui-ux-pro-max-design/scripts/logo/generate.py` | Google Gemini (`google-genai`) | el texto: marca, contexto, estilo, sector | solo `--list-styles`, `--list-industries` |
| `.claude/skills/ui-ux-pro-max-design/scripts/cip/generate.py` | Google Gemini | el texto y, con `--logo`, **la imagen del logo** | solo `--prompt-only` |
| `.claude/skills/ui-ux-pro-max-design/scripts/icon/generate.py` | Google Gemini | el texto del icono | solo `--list-styles`, `--list-categories` |
| `.claude/skills/ui-ux-pro-max-design/scripts/{logo,cip}/search.py` · `…/cip/render-html.py` | nada | búsqueda BM25 sobre `data/` · HTML local | sí |

Escriben en el directorio actual o en `--output`/`--output-dir`: pásalo siempre, dentro del proyecto.

## Uso (rutas de esta carpeta, no las `~/.claude/skills/design/…` del original)

```bash
D=.claude/skills/ui-ux-pro-max-design/scripts
python3 $D/logo/search.py "tech startup modern" --design-brief -p "Marca"   # sin red
python3 $D/logo/generate.py --brand "Marca" --style minimalist --industry tech --output-dir .docs/marca/logos   # PREGUNTA
python3 $D/cip/generate.py --brand "Marca" --logo logo.png --deliverable "business card" --output .docs/marca/cip.png   # PREGUNTA
```

Las guías de `references/` (logo, CIP, iconos) se leen como consulta. No se trajeron las de slides,
banners ni fotos sociales: duplican `marca` y `html-suelto` (`motores-de-diseno.md` §7).
