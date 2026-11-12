#!/usr/bin/env python3
"""plantar.py — construye los fixtures de calibración de los auditores.

`rules/qa-loop.md` §4b lleva desde agosto pidiendo esto y nunca se había hecho: un
artefacto con defectos CONOCIDOS y contados de antemano, para poder medir dos cosas que
hoy son literalmente desconocidas de Vera — su **recall** (cuántos ve) y sus **falsos
positivos** (cuántos se inventa).

Dos fixtures, y el primero importa tanto como el segundo:

  A-limpio   el diseño tal cual, SIN plantar nada. Es donde el falso positivo tiene sitio
             para aparecer. Sin un control así, un recall alto no dice nada.
  B-landing  el mismo, con 12 defectos plantados en tres franjas:
               30% obvios      (los ve cualquiera)
               40% de refilón  (los ve quien mira de verdad)
               30% QUE PARECEN DELIBERADOS — llevan al lado un comentario de workaround
                                con número de incidencia. **Condenarlos es un FALSO POSITIVO**,
                                y eso mide si el auditor busca el `Intent` antes de sentenciar
                                (`rules/verdict-contract.md`).

La clave —qué se plantó y dónde— se escribe FUERA del proyecto, en
`~/.claude/calibracion-diseno/`, y `settings.json` deniega su lectura. Si el auditor puede
leerla, la prueba no mide nada.

Uso:  python3 .claude/smoke/calibracion/plantar.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / "resources" / "referencias-diseno" / "bien" / "kalinayoga-v4.html"
DESTINO = RAIZ / "smoke" / "calibracion"
CLAVE = Path.home() / ".claude" / "calibracion-diseno"

# (id, franja, qué se busca, con qué se sustituye, qué defecto es, severidad esperada)
# ⚠️ LA RECETA NO VIVE AQUÍ, Y ESE ES EL PUNTO (corregido el 2026-09-18).
# La primera versión llevaba los 12 defectos escritos en este mismo fichero, dentro del repo.
# La clave estaba fuera y denegada… y la receta, al lado del auditor: cualquiera que leyera
# `plantar.py` sabía exactamente qué buscar, y la prueba dejaba de medir nada. Mover la clave sin
# mover la receta es poner la caja fuerte con la combinación escrita en la puerta.
#
# Ahora el repo se queda el MECANISMO y la receta vive con la clave:
#     ~/.claude/calibracion-diseno/receta-kalinayoga-v4.json
# (denegada en settings.json, igual que la clave).
RECETA = CLAVE / "receta-kalinayoga-v4.json"


def main() -> int:
    if not BASE.exists():
        print(f"⛔ NO SE PUDO CONSTRUIR: falta {BASE}", file=sys.stderr)
        return 2
    original = BASE.read_text(errors="ignore")
    if not RECETA.exists():
        print(f"⛔ NO SE PUDO CONSTRUIR: falta la receta {RECETA}.\n"
              f"   Vive fuera del repo A PROPÓSITO: si estuviera aquí, el auditor podría leerla.",
              file=sys.stderr)
        return 2
    defectos = [(d["id"], d["franja"], d["busca"], d["pon"], d["que_es"], d["severidad"])
                for d in json.loads(RECETA.read_text())]

    # ── A · el control, sin tocar ────────────────────────────────────────────
    (DESTINO / "A-limpio").mkdir(parents=True, exist_ok=True)
    (DESTINO / "A-limpio" / "index.html").write_text(original)

    # ── B · con los defectos plantados ───────────────────────────────────────
    texto, plantados, fallidos = original, [], []
    for pid, franja, busca, pon, que_es, sev in defectos:
        if busca not in texto:
            fallidos.append((pid, busca))
            continue
        pos = texto.index(busca)
        linea = texto[:pos].count("\n") + 1
        texto = texto.replace(busca, pon, 1)
        plantados.append({"id": pid, "franja": franja, "linea_aprox": linea,
                          "que_es": que_es, "severidad_esperada": sev,
                          "es_trampa": franja == "trampa"})
    (DESTINO / "B-landing").mkdir(parents=True, exist_ok=True)
    (DESTINO / "B-landing" / "index.html").write_text(texto)

    # ── la clave, FUERA del proyecto ─────────────────────────────────────────
    CLAVE.mkdir(parents=True, exist_ok=True)
    clave = {
        "generado": "2026-09-18",
        "base": str(BASE.relative_to(RAIZ)),
        "sha256_base": hashlib.sha256(original.encode()).hexdigest()[:16],
        "A-limpio": {
            "plantados": 0,
            "defectos_REALES_preexistentes": [
                "un <br> tras un span display:block deja una línea vacía de ~130px en el h1",
                "sin bloque prefers-reduced-motion",
                "outline quitado sin reponer el foco con :focus-visible",
            ],
            "como_se_lee": ("Un hallazgo que coincida con los defectos reales NO es falso positivo: "
                            "es un acierto. Falso positivo es todo lo demás que se reporte aquí."),
        },
        "B-landing": {"plantados": len(plantados), "defectos": plantados},
        "aviso_de_techo": ("Si el recall sale ≥90% dos veces seguidas, el fixture está EN TECHO y no "
                           "discrimina: hay que endurecerlo antes de volver a usarlo. Un 14,5/15 habla "
                           "del fixture, no del auditor (qa-loop §4b)."),
    }
    (CLAVE / "kalinayoga-v4.json").write_text(json.dumps(clave, ensure_ascii=False, indent=1) + "\n")

    print(f"A-limpio  · {DESTINO/'A-limpio'/'index.html'} (sin tocar)")
    print(f"B-landing · {len(plantados)}/{len(defectos)} defectos plantados "
          f"({sum(1 for p in plantados if p['es_trampa'])} son trampas)")
    if fallidos:
        print("\n⚠ NO se pudieron plantar (el patrón no está en el fichero base):")
        for pid, busca in fallidos:
            print(f"   {pid}: «{busca[:50]}»")
        print("   Un fixture con menos defectos de los declarados mide otra cosa: arréglalo antes de usarlo.")
    print(f"\nClave (fuera del proyecto, denegada en settings.json): {CLAVE/'kalinayoga-v4.json'}")
    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
