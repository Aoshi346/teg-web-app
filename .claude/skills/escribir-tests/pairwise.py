#!/usr/bin/env python3
"""Pairwise (all-pairs) sin dependencias: greedy sobre pares no cubiertos.

Uso:  python3 pairwise.py vars.json          # imprime los casos + verificación
      python3 pairwise.py vars.json --csv    # salida CSV
vars.json = {"navegador": ["chrome","firefox","safari"], "rol": [...], ...}
"""
import itertools
import json
import random
import sys


def all_pairs(variables):
    """Todos los pares (var_i, val, var_j, val) que hay que cubrir."""
    names = list(variables)
    pairs = set()
    for a, b in itertools.combinations(names, 2):
        for va in variables[a]:
            for vb in variables[b]:
                pairs.add((a, va, b, vb))
    return pairs


def covered_by(case, names):
    out = set()
    for a, b in itertools.combinations(names, 2):
        out.add((a, case[a], b, case[b]))
    return out


def _key(names, a, va, b, vb):
    return (a, va, b, vb) if names.index(a) < names.index(b) else (b, vb, a, va)


def _fill(variables, names, seed_case, pending, order):
    case = dict(seed_case)
    for n in order:
        if n in case:
            continue
        best, best_score = None, -1
        for v in variables[n]:
            score = sum(1 for m, mv in case.items() if _key(names, n, v, m, mv) in pending)
            if score > best_score:
                best, best_score = v, score
        case[n] = best
    return case


def generate(variables, seed=0, candidates=24):
    """Greedy con pool de candidatos (estilo PICT/AllPairs). Determinista con `seed`."""
    names = list(variables)
    rnd = random.Random(seed)
    pending = all_pairs(variables)
    cases = []
    while pending:
        best_case, best_new = None, -1
        for _ in range(candidates):
            a, va, b, vb = rnd.choice(sorted(pending))
            order = names[:]
            rnd.shuffle(order)
            case = _fill(variables, names, {a: va, b: vb}, pending, order)
            n_new = len(covered_by(case, names) & pending)
            if n_new > best_new:
                best_case, best_new = case, n_new
        pending -= covered_by(best_case, names)
        cases.append({n: best_case[n] for n in names})
    return cases


def verify(variables, cases):
    """Devuelve los pares NO cubiertos (debe ser vacío)."""
    names = list(variables)
    covered = set()
    for c in cases:
        covered |= covered_by(c, names)
    return all_pairs(variables) - covered


if __name__ == "__main__":
    variables = json.load(open(sys.argv[1]))
    cases = generate(variables)
    missing = verify(variables, cases)
    full = 1
    for v in variables.values():
        full *= len(v)
    names = list(variables)
    if "--csv" in sys.argv:
        print(",".join(names))
        for c in cases:
            print(",".join(str(c[n]) for n in names))
    else:
        for i, c in enumerate(cases, 1):
            print(f"{i:3d}  " + "  ".join(f"{n}={c[n]}" for n in names))
    print(f"\n# casos pairwise: {len(cases)}  ·  producto cartesiano: {full}"
          f"  ·  pares sin cubrir: {len(missing)}")
    sys.exit(1 if missing else 0)
