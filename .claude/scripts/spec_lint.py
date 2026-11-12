#!/usr/bin/env python3
"""spec_lint.py — validación DETERMINISTA de specs SpecKit con umbrales duros (SPEC-2).

Reglas estructurales no-LLM sobre una sesión SpecKit (spec.md / plan.md / tasks.md), robadas de
validation/constants.ts de OpenSpec y adaptadas a nuestro formato. `/speckit.analyze` (LLM) queda
para lo semántico; esto es un grep con umbrales: gratis, reproducible, apto para pre-DONE.

Reglas (ERROR rompe con exit 1; WARN solo avisa):
  E1  spec.md existe y tiene >= MIN_SPEC_LINES líneas de contenido
  E2  cada requisito (bullet bajo un heading de requisitos) lleva verbo NORMATIVO
      (DEBE/DEBERÁ/NO DEBE/SHALL/MUST) — sin verbo no hay contrato, hay deseo
  E3  spec.md tiene sección de criterios de aceptación (o escenarios Dado/Cuando/Entonces)
  W1  requisito de > MAX_REQ_CHARS chars → trocéalo
  W2  una wave de tasks.md con > MAX_ITEMS_WAVE items sin hacer → scope creep, divide
  W3  spec.md > MAX_SPEC_LINES líneas → probablemente son 2 features
  W4  tasks.md sin puntos de comunicación (**→ NOTIFICAR** / ⏳ ESPERAR) → speckit-workflow los exige

Uso:
  python3 spec_lint.py <dir-sesion-speckit>     # p.ej. ".specify/sessions/TPL-1 - …/"
  python3 spec_lint.py <dir> --json
"""
import json
import os
import re
import sys

MIN_SPEC_LINES = 15
MAX_SPEC_LINES = 400
MAX_REQ_CHARS = 500
MAX_ITEMS_WAVE = 10
NORMATIVE = re.compile(r"\b(DEBE(R[ÁA])?N?|NO DEBE|SHALL|MUST)\b", re.I)
REQ_HEAD = re.compile(r"^#{2,4}\s.*(requisito|requirement|funcional|scope|alcance)", re.I)
ACCEPT = re.compile(r"(criterios? de aceptaci|acceptance criteria|dado que|given\b)", re.I)
BOX = re.compile(r"^\s*[-*]\s*\[([ >])\]")
H2 = re.compile(r"^##+\s+(.+)")


def lint(session: str):
    errors, warns = [], []
    spec = os.path.join(session, "spec.md")
    tasks = os.path.join(session, "tasks.md")

    if not os.path.isfile(spec):
        errors.append("E1 spec.md no existe")
    else:
        lines = [l for l in open(spec, encoding="utf-8").read().splitlines()]
        content = [l for l in lines if l.strip()]
        if len(content) < MIN_SPEC_LINES:
            errors.append(f"E1 spec.md demasiado corto ({len(content)} líneas < {MIN_SPEC_LINES}) — eso no es una spec")
        if len(lines) > MAX_SPEC_LINES:
            warns.append(f"W3 spec.md tiene {len(lines)} líneas (> {MAX_SPEC_LINES}) — ¿son dos features?")
        text = "\n".join(lines)
        if not ACCEPT.search(text):
            errors.append("E3 spec.md sin criterios de aceptación (ni sección ni Dado/Cuando/Entonces)")
        # E2/W1: bullets bajo headings de requisitos
        in_req, n_req, n_norm = False, 0, 0
        for l in lines:
            if l.startswith("#"):
                in_req = bool(REQ_HEAD.match(l))
                continue
            m = re.match(r"^\s*[-*]\s+(.{5,})", l)
            if in_req and m:
                n_req += 1
                if NORMATIVE.search(m.group(1)):
                    n_norm += 1
                if len(m.group(1)) > MAX_REQ_CHARS:
                    warns.append(f"W1 requisito de {len(m.group(1))} chars (> {MAX_REQ_CHARS}) — trocéalo: «{m.group(1)[:60]}…»")
        if n_req and n_norm == 0:
            errors.append(f"E2 {n_req} requisitos y NINGUNO lleva verbo normativo (DEBE/SHALL/MUST) — sin verbo no hay contrato")
        elif n_req and n_norm < n_req / 2:
            warns.append(f"E2~ solo {n_norm}/{n_req} requisitos llevan verbo normativo")

    if os.path.isfile(tasks):
        text = open(tasks, encoding="utf-8").read()
        wave, counts = "(sin sección)", {}
        for l in text.splitlines():
            h = H2.match(l)
            if h:
                wave = h.group(1).strip()
                continue
            if BOX.match(l):
                counts[wave] = counts.get(wave, 0) + 1
        for w, c in counts.items():
            if c > MAX_ITEMS_WAVE:
                warns.append(f"W2 «{w}»: {c} items sin hacer (> {MAX_ITEMS_WAVE}) — scope creep, divide la wave")
        if "NOTIFICAR" not in text and "ESPERAR" not in text:
            warns.append("W4 tasks.md sin puntos de comunicación con el Supervisor (speckit-workflow los exige)")
    else:
        warns.append("tasks.md no existe aún (ok si la sesión está en fase de spec)")

    return errors, warns


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    session = args[0]
    if not os.path.isdir(session):
        sys.exit(f"ERROR: {session} no es un directorio de sesión SpecKit")
    errors, warns = lint(session)
    if "--json" in sys.argv:
        print(json.dumps({"session": session, "errors": errors, "warnings": warns,
                          "ok": not errors}, ensure_ascii=False, indent=1))
    else:
        for e in errors:
            print("ERROR ", e)
        for w in warns:
            print("warn  ", w)
        print("OK — spec estructuralmente válida" if not errors else f"{len(errors)} errores, {len(warns)} avisos")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
