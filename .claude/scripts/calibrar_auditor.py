#!/usr/bin/env python3
"""calibrar_auditor.py — ¿se le puede hacer caso a este auditor?

`rules/qa-loop.md` §4b lo pide desde agosto y nunca se había hecho. Hoy, de Vera se sabe
su nota y **no se sabe ni su recall ni su tasa de falsos positivos**. Sin esos dos números,
su 7,35 no significa nada: puede ser un auditor severo o uno que se inventa la mitad.

Se comparan sus hallazgos contra la clave del fixture (que vive FUERA del proyecto y está
denegada en `settings.json`) y salen tres cosas:

  RECALL   cuántos de los defectos plantados vio.
           Medio punto si lo ve pero le pone la severidad equivocada.
  FP       cuántos hallazgos NO corresponden ni a un defecto plantado ni a uno real
           conocido. **Es el número que decide si se le puede hacer caso**: un auditor
           con recall alto y FP alto no filtra, hace ruido caro.
  TRAMPAS  cuántas de las «trampas» condenó. Son defectos aparentes con su razón escrita
           al lado (`workaround: … #412`). Condenarlas es un FALSO POSITIVO y mide si
           busca el `Intent` antes de sentenciar (`rules/verdict-contract.md`).

Dos familias de fixture:
  · diseño (`smoke/calibracion/A-limpio`, `B-landing`): clave por defecto
    `~/.claude/calibracion-diseno/kalinayoga-v4.json`.
  · código (`smoke/calibracion/auditores/`, Roberto y Pilar, sub-ola 3.07): cada defecto declara
    su `fichero`; un hallazgo solo casa con defectos de su mismo fichero. Clave en
    `~/.claude/calibracion-diseno/<agente>/clave.json` (`--clave`). Acepta `findings.json`
    (Roberto) e `impacto.json` (Pilar: cuenta como hallazgo lo que condena — migración que no es
    aditiva-segura, cambio fuera de alcance, fichero fuera del plan, `cambia-NO-esperado`). Un
    hallazgo que casa con un defecto del OTRO auditor (`otro_dominio`) no es FP ni suma recall.

Desenlaces:
    0  medido
    2  NO SE PUDO MEDIR (falta la clave o los hallazgos) — nunca «0% de fallos»

Uso:  python3 .claude/scripts/calibrar_auditor.py <fixture> <hallazgos.json> [--clave <ruta>] [--json]
      fixture: A-limpio | B-landing | cambio-a | cambio-b
"""
import json
import re
import sys
from pathlib import Path

CLAVE = Path.home() / ".claude" / "calibracion-diseno" / "kalinayoga-v4.json"
SEVERIDADES = ({"P0", "P1", "P2"}, {"alto", "medio", "bajo"})


def abortar(motivo: str) -> None:
    print(f"⛔ NO SE PUDO MEDIR: {motivo}", file=sys.stderr)
    print("   Sin los dos ficheros no hay calibración: no se imprime un 0% que parezca bueno.",
          file=sys.stderr)
    sys.exit(2)


def normaliza(t: str) -> str:
    return re.sub(r"[^a-záéíóúñ0-9 ]", " ", (t or "").lower())


def casa(hallazgo: dict, defecto: dict) -> bool:
    """Empareja por TÉRMINOS CLAVE declarados, no por parecido de frases.

    ── 2026-09-18 · la primera versión emparejaba contando palabras compartidas de ≥5 letras
    entre la descripción del defecto y la del hallazgo, y fallaba EN LOS DOS SENTIDOS, que es lo
    peor que puede hacer un corrector:
      · contaba como FALSO POSITIVO un acierto escrito con otras palabras («El contraste del
        acento baja a 2,1:1» no casaba con «contraste de 2,1:1: se sustituye el token…»);
      · y NO veía que un auditor había condenado dos trampas, porque tampoco casaban.
    O sea que habría dado por bueno al ruidoso y por ruidoso al bueno. Ahora cada defecto declara
    sus términos en la receta (que vive fuera del repo): basta con que aparezca UNO.
    """
    texto = normaliza(json.dumps(hallazgo, ensure_ascii=False))
    for termino in defecto.get("claves", []):
        if normaliza(termino).strip() and normaliza(termino).strip() in texto:
            return True
    linea = hallazgo.get("line") or hallazgo.get("linea")
    return bool(linea) and abs(int(linea) - defecto.get("linea_aprox", -999)) <= 3


# ── fixtures de código ───────────────────────────────────────────────────────────────────

def aplanar_impacto(datos: dict) -> list[dict]:
    """De un impacto.json, solo lo que Pilar CONDENA (lo que diría al Usuario «esto no»)."""
    post = datos.get("post") or {}
    hallazgos = []
    for m in post.get("db_changes") or []:
        if m.get("class") != "aditiva-segura" or m.get("risk") in ("medio", "alto"):
            hallazgos.append({"id": m.get("migration"), "file": m.get("migration"),
                              "severity": m.get("risk"), "texto": m})
    # Un cambio condenado sale una vez: `out_of_scope_changes` y las mediciones que lo cubren lo
    # citan por id, y contarlos aparte daba un FP por cada cita (ronda 1 de Pilar, 02-11).
    cambios = {c.get("id"): c for c in post.get("behavior_changes") or []}
    condenados = set()
    for c in cambios.values():
        if c.get("declared_in_scope") is False:
            condenados.add(c.get("id"))
            hallazgos.append({"id": c.get("id"), "file": c.get("ref"), "texto": c})
    fidelidad = post.get("scope_fidelity") or {}
    for f in fidelidad.get("files_outside_plan") or []:
        hallazgos.append({"id": f"fuera-del-plan:{f}", "file": f, "solo_fichero": True})
    for t in fidelidad.get("out_of_scope_changes") or []:
        t = str(t)
        if t in cambios:
            if t not in condenados:
                condenados.add(t)
                hallazgos.append({"id": t, "file": cambios[t].get("ref"), "texto": cambios[t]})
        else:
            hallazgos.append({"id": f"fuera-de-alcance:{t[:40]}", "file": t, "solo_fichero": "/" in t,
                              "texto": t})
    for r in post.get("comparison") or []:
        if r.get("result") != "cambia-NO-esperado":
            continue
        dueno = next((c for c in cambios.values() if r.get("measurement") in (c.get("measurements") or [])), None)
        if dueno and dueno.get("id") in condenados:
            continue
        hallazgos.append({"id": r.get("measurement"), "file": (dueno or {}).get("ref", ""), "texto": [r, dueno]})
    return hallazgos


def aciertos(texto: str, defecto: dict) -> int:
    return sum(1 for t in defecto.get("claves", [])
               if normaliza(t).strip() and re.search(rf"\b{re.escape(normaliza(t).strip())}\b", texto))


def defectos_que_casa(h: dict, defectos: list[dict]) -> list[dict]:
    """Los defectos reales de los ficheros que nombra el hallazgo con algún término clave suyo.

    Un hallazgo puede cubrir varios defectos («dos helpers paralelos», ficheros en `line` o en
    `bug_class.instances`): se le acreditan todos (ronda 1 de Roberto, 02-11: con uno solo, un
    acierto doble contaba como un fallo). Si no casa ningún real, la trampa con más términos.
    Sin término clave no casa por cercanía de línea: en un fichero de 30 líneas, ±2 regalaba el
    acierto a un hallazgo sobre otra cosa (prueba del 01-11). La única excepción es el hallazgo
    que solo nombra un fichero (`files_outside_plan`): casa con el primer defecto real.
    """
    instancias = (h.get("bug_class") or {}).get("instances") or []
    ref = " ".join([*(str(h.get(k) or "") for k in ("file", "line", "ref", "migration")),
                    *map(str, instancias)])
    texto = normaliza(json.dumps(h, ensure_ascii=False))
    mismos = [d for d in defectos if d["fichero"] in ref or Path(d["fichero"]).name in ref]
    if not mismos and not ref.strip():                   # sin fichero (p. ej. una medición)
        mismos = defectos
    reales = [d for d in mismos if not d.get("es_trampa") and aciertos(texto, d) > 0]
    if reales:
        return reales
    trampas = sorted((d for d in mismos if d.get("es_trampa") and aciertos(texto, d) > 0),
                     key=lambda d: aciertos(texto, d), reverse=True)
    if trampas:
        return trampas[:1]
    if mismos and h.get("solo_fichero"):
        return [d for d in mismos if not d.get("es_trampa")][:1]
    return []


def medir_codigo(bloque: dict, hallazgos: list[dict]) -> dict:
    plantados = bloque.get("defectos", [])
    otros = bloque.get("otro_dominio", [])
    vistos, trampas, fp, fuera, etiquetas = {}, [], [], [], []
    for h in hallazgos:
        casados = defectos_que_casa(h, plantados)
        # Un hallazgo correcto del otro dominio que cita de paso el fichero de una trampa no la
        # condena (ronda 1 de Roberto: active() de managers listaba tools.py entre sus consumidores).
        if not casados or casados[0].get("es_trampa"):
            if otros and defectos_que_casa(h, otros):
                fuera.append(h.get("id") or str(h)[:60])
                continue
        if not casados:
            fp.append(h.get("id") or str(h)[:60])
            etiquetas.append(h.get("label") or "sin-etiqueta")
            continue
        if casados[0].get("es_trampa"):
            trampas.append(f"{casados[0]['id']}←{h.get('id')}")
            continue
        sev = str(h.get("severity") or h.get("severidad") or "")
        for d in casados:
            esperada = d["severidad_esperada"]
            misma_escala = any(sev in s and esperada in s for s in SEVERIDADES)
            punto = 1.0 if (not misma_escala or sev == esperada) else 0.5
            vistos[d["id"]] = max(vistos.get(d["id"], 0), punto)
    reales = [d for d in plantados if not d.get("es_trampa")]
    return {"plantados_reales": len(reales), "puntos": sum(vistos.values()),
            "recall": round(sum(vistos.values()) / len(reales), 3) if reales else None,
            "vistos": sorted(vistos), "no_vistos": [d["id"] for d in reales if d["id"] not in vistos],
            "falsos_positivos": len(fp), "detalle_fp": fp[:10],
            # Un `nit` o un `pre-existing` fuera de la clave no pesa como un `important`: se separa,
            # y lo que cuenta para el paso de fase lo adjudica una persona leyéndolos.
            "fp_por_etiqueta": {e: etiquetas.count(e) for e in sorted(set(etiquetas))},
            "fuera_de_dominio": fuera,
            "trampas": len(plantados) - len(reales), "trampas_condenadas": trampas}


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--json"]
    clave_path = CLAVE
    if "--clave" in args:
        i = args.index("--clave")
        if i + 1 >= len(args):
            abortar("--clave necesita una ruta")
        clave_path = Path(args[i + 1])
        del args[i:i + 2]
    if len(args) < 2:
        print(__doc__)
        return 2
    fixture, ruta = args[0], Path(args[1])
    if not clave_path.exists():
        abortar(f"no existe la clave {clave_path} — la del diseño la crea smoke/calibracion/plantar.py")
    if not ruta.exists():
        abortar(f"no existe {ruta} (los hallazgos del auditor)")

    clave = json.loads(clave_path.read_text())
    if fixture not in clave:
        abortar(f"la clave no conoce el fixture «{fixture}»")
    bloque = clave[fixture]
    plantados = bloque.get("defectos", [])
    reales = bloque.get("defectos_REALES_preexistentes", [])

    datos = json.loads(ruta.read_text())
    if isinstance(datos, dict) and isinstance(datos.get("post"), dict):
        hallazgos = aplanar_impacto(datos)
    else:
        hallazgos = datos if isinstance(datos, list) else (datos.get("findings") or datos.get("hallazgos") or [])
    if not isinstance(hallazgos, list):
        abortar("no encuentro una lista de hallazgos en ese fichero")

    if "otro_dominio" in bloque or any("fichero" in d for d in plantados):
        salida = {"estado_instrumento": "medido", "fixture": fixture, "hallazgos": len(hallazgos),
                  **medir_codigo(bloque, hallazgos), "aviso_techo": clave.get("aviso_de_techo")}
        recall = salida["recall"]
        puntos = salida["puntos"]
        sin_ver, fp, trampas_condenadas = salida["no_vistos"], salida["detalle_fp"], salida["trampas_condenadas"]
        fp = [None] * salida["falsos_positivos"] if not fp else fp
    else:
        vistos, sin_ver, fp, trampas_condenadas = [], [], [], []
        emparejados = set()
        for d in plantados:
            hit = next((h for h in hallazgos if casa(h, d)), None)
            if hit is None:
                if not d["es_trampa"]:
                    sin_ver.append(d["id"])
                continue
            emparejados.add(id(hit))
            if d["es_trampa"]:
                trampas_condenadas.append(d["id"])          # verla es un ERROR
            else:
                sev = str(hit.get("severity") or hit.get("severidad") or "").upper()
                vistos.append((d["id"], 1.0 if sev.startswith(d["severidad_esperada"]) else 0.5))
        for h in hallazgos:
            if id(h) in emparejados:
                continue
            texto = normaliza(json.dumps(h, ensure_ascii=False))
            if any(sum(1 for w in normaliza(r).split() if len(w) >= 5 and w in texto) >= 2 for r in reales):
                continue                                    # coincide con un defecto REAL: es acierto
            fp.append(h.get("id") or h.get("titulo") or str(h)[:60])
        reales_plantados = [d for d in plantados if not d["es_trampa"]]
        puntos = sum(p for _, p in vistos)
        recall = puntos / len(reales_plantados) if reales_plantados else None
        salida = {"estado_instrumento": "medido", "fixture": fixture,
                  "plantados_reales": len(reales_plantados),
                  "recall": round(recall, 3) if recall is not None else None,
                  "vistos": [v[0] for v in vistos], "no_vistos": sin_ver,
                  "falsos_positivos": len(fp), "detalle_fp": fp[:10],
                  "trampas": len(plantados) - len(reales_plantados),
                  "trampas_condenadas": trampas_condenadas,
                  "aviso_techo": clave.get("aviso_de_techo")}

    if "--json" in sys.argv:
        print(json.dumps(salida, ensure_ascii=False, indent=1))
    else:
        print(f"calibrar_auditor · fixture {fixture} · {len(hallazgos)} hallazgos del auditor")
        if recall is not None:
            print(f"  RECALL  {recall:.0%} ({puntos:g} de {salida['plantados_reales']} defectos plantados)")
            if sin_ver:
                print(f"          no vio: {', '.join(sin_ver)}")
        print(f"  FP      {len(fp)}" + (f" → {', '.join(map(str, fp[:5]))}" if any(fp) else ""))
        if salida.get("fp_por_etiqueta"):
            print("          por etiqueta: " + ", ".join(f"{k} {v}" for k, v in salida["fp_por_etiqueta"].items()))
        if salida.get("fuera_de_dominio"):
            print(f"  otro dominio (ni FP ni recall): {len(salida['fuera_de_dominio'])}")
        if trampas_condenadas:
            print(f"  ⚠ TRAMPAS CONDENADAS: {', '.join(trampas_condenadas)} — son defectos APARENTES")
            print(f"    con su razón escrita al lado. Condenarlas es falso positivo: no buscó el Intent.")
        else:
            print(f"  ✓ no condenó ninguna trampa: respetó el Intent")
        if recall is not None and recall >= 0.9:
            print(f"\n  ⚠ {clave.get('aviso_de_techo')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
