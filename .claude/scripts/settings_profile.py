#!/usr/bin/env python3
"""settings_profile.py — aplica un PERFIL DE AUTONOMÍA al settings.json de un proyecto.

EL HUECO QUE CIERRA. `update-agent` copia ficheros y nunca pregunta **cuánta cuerda** quiere ese
proyecto. Y no es el mismo caso un repo de cliente donde cada commit se revisa, que un proyecto
propio que se deja corriendo toda la noche con el `/qa-loop`. Hoy los dos heredan el mismo
`settings.json` del template.

LOS PERFILES SON DE AUTONOMÍA, NO DE STACK. Los de `documentation/settings-examples/` responden
«¿qué herramientas necesita un backend?»; estos responden «¿qué se le deja hacer solo?». Son ejes
distintos y se combinan.

═══ EL MATIZ QUE CAMBIA EL DISEÑO ═══
En modo desatendido, **`ask` no sirve de nada**: no hay nadie para responder. El agente se queda
esperando o —peor— el harness acaba anulando el bloqueo y sigue. Así que lo que de día es `ask`,
de noche tiene que ser **`deny`**. Un perfil nocturno que se limite a "quitar las preguntas" está
mal hecho: convierte un punto de control en una puerta abierta.

═══ MODOS (CL-D1, decisión del Usuario 2026-10-18; sub-ola 2.01) ═══
`estandar` y `yolo` NO fijan `defaultMode`: una sesión interactiva arranca en `auto` (el defecto de
terminal y VS Code desde la v2.1.283; un "auto" escrito en el settings del proyecto no surtiría
efecto). En auto, el clasificador decide lo que no es lectura ni edición, y se apagan los `allow` que
dan ejecución arbitraria (`Bash(*)` del yolo incluido); el `deny` sigue mandando. `nocturno` se queda
en `acceptEdits` (desatendido), y `observador`/`asistido` en `default` (preguntan). Un `claude -p`
desatendido pasa el modo en la orden: `--permission-mode acceptEdits` (rules/harness-gotchas.md).
"""
import argparse, json, os, sys
from datetime import date, datetime

# Acciones que NUNCA se relajan, en ningún perfil. Vienen de governance.md §2.
JAMAS = ["Bash(git push --force*)", "Bash(git push -f*)", "Bash(rm -rf /*)",
         "Bash(terraform destroy*)", "Bash(git reset --hard origin*)",
         "Read(**/.env*)", "Read(**/id_rsa*)", "Read(**/.aws/**)"]

# Despliegues REALES, por verbo y herramienta. El `Bash(*deploy*)` de antes casaba la palabra donde
# fuese y bloqueaba `manage.py check --deploy` (el chequeo de seguridad de Django) y cualquier grep o
# documento que la mencionara (MO-8). Un `deny` no admite excepciones, así que la única forma de dejar
# pasar el chequeo es estrecharlo. Es la misma lista que `.claude/settings.json` del template.
DENY_DESPLIEGUES = [
    "Bash(*ansible-playbook*deploy*)",
    "Bash(*cdk deploy*)",
    "Bash(*deploy.py*)",
    "Bash(*deploy.sh*)",
    "Bash(*firebase deploy*)",
    "Bash(*fly deploy*)",
    "Bash(*flyctl deploy*)",
    "Bash(*gcloud * deploy*)",
    "Bash(*helm * install*)",
    "Bash(*helm * upgrade*)",
    "Bash(*kamal deploy*)",
    "Bash(*kubectl * apply*)",
    "Bash(*make deploy*)",
    "Bash(*netlify deploy*)",
    "Bash(*pnpm deploy*)",
    "Bash(*run deploy*)",
    "Bash(*serverless deploy*)",
    "Bash(*sh ./deploy*)",
    "Bash(*sh deploy*)",
    "Bash(*sls deploy*)",
    "Bash(*vercel deploy*)",
    "Bash(*vercel --prod*)",
    "Bash(*wrangler deploy*)",
    "Bash(*yarn deploy*)",
    "Bash(./deploy*)",
    "Bash(eb deploy*)",
    "Bash(helm install*)",
    "Bash(helm upgrade*)",
    "Bash(kubectl apply*)",
]

# Acciones contra producción. Era un `Bash(*production*)` que casaba la palabra donde fuese y bloqueaba
# `--settings config.settings.production`, que es como se lanza el gate G3 (MO-8, decisión del Usuario
# del 22-10). Misma lista que `.claude/settings.json` del template.
DENY_PRODUCCION = [
    "Bash(*cap production*)",
    "Bash(*production deploy*)",
    "Bash(*deploy production*)",
    "Bash(*--env production*)",
    "Bash(*--env=production*)",
    "Bash(*--environment production*)",
    "Bash(*--environment=production*)",
    "Bash(*RAILS_ENV=production*)",
    "Bash(*compose*production*)",
    "Bash(*kubectl*production*)",
    "Bash(*terraform*production*)",
    "Bash(*heroku*production*)",
    "Bash(*ssh *production*)",
    "Bash(*scp *production*)",
    "Bash(*rsync *production*)",
    "Bash(*manage.py migrate*production*)",
    "Bash(*manage.py flush*production*)",
    "Bash(*manage.py loaddata*production*)",
    "Bash(*production*manage.py migrate*)",
    "Bash(*production*manage.py flush*)",
    "Bash(*production*manage.py loaddata*)",
]

# Tools del propio harness que no son ficheros ni Bash. Sin ellas en `allow`, una sesión que no está
# en `auto` (`claude --bg`, `claude -p`, un workflow) se queda parada pidiendo permiso para invocar
# una skill o un subagente: una sesión en segundo plano de fitapp estuvo 19 h así (MO-3, 2026-10-04).
TOOLS_HARNESS = ["Skill", "Agent", "SendMessage", "ToolSearch", "Monitor", "TaskStop", "TodoWrite"]
TOOLS_RED = ["WebFetch", "WebSearch"]          # solo en yolo: salen de la máquina, el estándar las pregunta

PERFILES = {
 "observador": dict(
   titulo="Observador — solo mira",
   para="Auditar un repo ajeno, o una primera pasada antes de dar acceso de escritura.",
   mode="default",
   allow=["Read(**)", "Grep(**)", "Glob(**)", "Bash(git log*)", "Bash(git diff*)",
          "Bash(git status*)", "Bash(ls*)", "Bash(cat*)", "Bash(rg*)"],
   ask=[],
   deny=["Edit(**)", "Write(**)", "Bash(git commit*)", "Bash(git add*)",
         "Bash(npm install*)", "Bash(pip install*)"] + JAMAS,
   nota="No escribe NADA. Si necesita proponer un cambio, lo escribe en el informe, no en el repo."),

 "asistido": dict(
   titulo="Asistido — escribe, pero cada commit se aprueba",
   para="Repo de cliente, código sensible, o un agente que aún no se ha ganado la confianza.",
   mode="default",
   allow=["Read(**)", "Grep(**)", "Glob(**)", "Edit(**)", "Write(**)",
          "Bash(git status*)", "Bash(git diff*)", "Bash(git log*)", "Bash(pytest*)"],
   ask=["Bash(git commit*)", "Bash(git add*)", "Bash(npm install*)", "Bash(pip install*)"],
   deny=["Bash(git push*)", "Bash(git merge*)", "Bash(gh pr merge*)"] + JAMAS,
   nota="El agente trabaja pero no consolida nada sin ti. Útil cuando el coste de un commit malo "
        "es alto o el repo lo comparten varias personas."),

 "estandar": dict(
   titulo="Estándar — commits libres en la rama; push y merge se aprueban",
   para="El día a día. Es el perfil del template y el que sirve para casi todo.",
   mode=None,                    # sin defaultMode → interactivo en auto (CL-D1; ver MODOS arriba)
   allow=["Read(**)", "Grep(**)", "Glob(**)", "Edit(**)", "Write(**)",
          "Bash(git add*)", "Bash(git commit*)", "Bash(git diff*)", "Bash(git status*)",
          "Bash(pytest*)", "Bash(npm run*)", "Bash(python3*)"] + TOOLS_HARNESS,
   ask=["Bash(git push*)", "Bash(git merge*)", "Bash(gh pr merge*)",
        "Bash(terraform apply*)", "Bash(apt*)", "Bash(docker*)"],
   deny=JAMAS,
   nota="governance.md §2 en forma de fichero: lo autónomo es autónomo, y lo que sale de la máquina "
        "o toca el sistema, se pregunta."),

 "yolo": dict(
   titulo="Yolo — no pregunta por nada salvo lo prohibido",
   para="Workflows con fan-out, waves largas, cualquier cosa donde parar 50 veces a decir «sí» no aporta nada.",
   mode=None,                    # sin defaultMode → interactivo en auto (CL-D1; ver MODOS arriba)
   # `Bash(*)` en allow NO es «todo vale»: las reglas se evalúan **deny → ask → allow** y el
   # primer match manda (verificado en la doc de permisos, ver rules/agent-security.md §2). Así
   # que el `deny` de abajo sigue bloqueando force-push, rm -rf, terraform destroy y la lectura
   # de secretos, aunque Bash(*) esté permitido. Eso es lo que separa esto de bypassPermissions,
   # que se salta TODO — deny incluido — y deja al agente sin ninguna red.
   allow=["Read(**)", "Grep(**)", "Glob(**)", "Edit(**)", "Write(**)", "Bash(*)"]
         + TOOLS_HARNESS + TOOLS_RED,
   ask=[],
   deny=["Bash(git push*)", "Bash(git merge*)", "Bash(gh pr merge*)",
         "Bash(terraform apply*)", "Bash(apt*)", "Bash(sudo*)", "Bash(npm publish*)",
         "Bash(docker push*)"] + DENY_DESPLIEGUES + DENY_PRODUCCION + JAMAS,
   nota="Todo permitido MENOS lo del deny, que sigue mandando porque se evalúa antes. Lo que "
        "salía de la máquina (push, merge, deploy, publish) pasa de `ask` a `deny`: en un fan-out "
        "no hay nadie para responder un `ask` 50 veces, así que lo que no se puede aprobar se "
        "deniega y la tarea lo reporta como bloqueada."),

 "nocturno": dict(
   titulo="Nocturno — corre solo hasta cumplir la condición",
   para="Dejar un /qa-loop o un /goal trabajando sin nadie delante.",
   mode="acceptEdits",
   allow=["Read(**)", "Grep(**)", "Glob(**)", "Edit(**)", "Write(**)",
          "Bash(git add*)", "Bash(git commit*)", "Bash(git diff*)", "Bash(git status*)",
          "Bash(pytest*)", "Bash(npm run*)", "Bash(python3*)", "Bash(curl -s*)"]
         # Skill y Agent, sin WebFetch ni WebSearch (MO-3, decisión del Usuario del 22-10): de noche
         # un /qa-loop invoca skills y subagentes, y sin ellas en allow se denegaban en silencio.
         + TOOLS_HARNESS,
   ask=[],                       # ← vacío A PROPÓSITO: ver la nota
   deny=["Bash(git push*)", "Bash(git merge*)", "Bash(gh pr merge*)",
         "Bash(terraform apply*)", "Bash(apt*)", "Bash(sudo*)",
         "Bash(docker*)", "Bash(psql*)", "Bash(mysql*)"] + JAMAS,
   nota="⚠️ `ask` va VACÍO y todo lo que de día se preguntaría está en `deny`. No es un descuido: "
        "de noche no hay nadie que responda una pregunta, así que un `ask` deja al agente colgado "
        "o acaba abriéndose. Lo que no se puede aprobar, se deniega."),
}

AVISOS_NOCTURNO = """
⚠️  ANTES DE DEJARLO CORRIENDO — tres límites que conviene saber:

1. **El criterio de parada tiene que ser demostrable.** `/goal` juzga sobre lo que el agente
   MUESTRA en la conversación: «hasta que pytest salga verde y pegue la salida» sirve; «hasta que
   quede bien» no. Y `/loop` no converge solo — sus tareas recurrentes caducan a los 7 días.

2. **Un Stop hook se anula tras 8 bloqueos consecutivos — sin ninguna tool entre medias.** El
   contador vuelve a cero cada vez que el agente llama a una tool (doc `hooks` §Stop input), así que
   un agente que sigue intentándolo contra un gate imposible NO sale a los 8: gira hasta el tope de
   presupuesto o de turnos. El mensaje de bloqueo tiene que decir qué falta y cómo arreglarlo, y el
   gate tiene que ser alcanzable.

3. **Commit sí, push no — y de madrugada menos.** Es cuando más barato sale saltarse el control, y
   por eso el perfil lo deniega en vez de preguntarlo.

   Y para el `/qa-loop` en concreto: tiene tope de 5 iteraciones y si no converge escala. No corre
   indefinidamente por diseño — un bucle de calidad sin tope gasta la noche sin mejorar nada.
"""

def aplicar(proyecto, perfil, dry=False):
    p = PERFILES[perfil]
    sp = os.path.join(proyecto, ".claude", "settings.json")
    if not os.path.exists(sp):
        print(f"✗ no hay {sp}"); return 2
    d = json.load(open(sp, encoding="utf-8"))
    perms = d.setdefault("permissions", {})
    antes = {k: len(perms.get(k, [])) for k in ("allow", "ask", "deny")}

    # El deny NUNCA se recorta: solo crece. Quitar una denegación es una decisión humana, no el
    # efecto secundario de cambiar de perfil.
    perms["deny"] = sorted(set(perms.get("deny", [])) | set(p["deny"]))
    perms["allow"] = sorted(set(p["allow"]))
    perms["ask"] = sorted(set(p["ask"]))
    if p["mode"] is None:
        perms.pop("defaultMode", None)
    else:
        perms["defaultMode"] = p["mode"]
    d["_perfil_autonomia"] = {"perfil": perfil, "aplicado": date.today().isoformat(),
                              "nota": p["nota"]}

    if dry:
        print(json.dumps(perms, ensure_ascii=False, indent=2)[:1200]); return 0
    open(sp + ".bak", "w", encoding="utf-8").write(open(sp, encoding="utf-8").read())
    open(sp, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))
    print(f"  perfil «{p['titulo']}» aplicado a {sp}")
    print(f"    allow {antes['allow']}→{len(perms['allow'])} · "
          f"ask {antes['ask']}→{len(perms['ask'])} · deny {antes['deny']}→{len(perms['deny'])} (nunca baja)")
    print(f"    {p['nota']}")
    if perfil == "nocturno":
        print(AVISOS_NOCTURNO)
    print(f"  copia previa en {sp}.bak")
    return 0

# ═══ EL INTERRUPTOR YOLO (T-101) — entrar y SALIR sin dejar residuos ═══
# `--perfil` no sirve para ir y volver: el deny nunca baja, así que yolo → estándar deja push y
# merge DENEGADOS en vez de preguntados (medido: el deny de yolo lleva 10 reglas que estándar no
# tiene). El interruptor guarda el bloque `permissions` tal como lo dejó una persona y, al apagarlo,
# lo RESTAURA entero. No contradice «el deny nunca se recorta»: no se recorta nada por efecto
# colateral, se vuelve exactamente a lo que alguien eligió. El resto del settings.json no se toca.
SNAP = ".antes-yolo"

def estado(proyecto):
    """Perfil vigente y si el interruptor está puesto. Lo usa server.py en /api/health."""
    sp = os.path.join(proyecto, ".claude", "settings.json")
    if not os.path.exists(sp):
        return {"settings": False, "perfil": None, "yolo": False}
    try:
        d = json.load(open(sp, encoding="utf-8"))
    except Exception:
        return {"settings": True, "perfil": None, "yolo": False, "error": "settings.json ilegible"}
    return {"settings": True, "perfil": (d.get("_perfil_autonomia") or {}).get("perfil"),
            "yolo": os.path.exists(sp + SNAP)}

def _perdido_al_apagar(actual, guardado):
    """Entradas de permisos que alguien añadió MIENTRAS el interruptor estaba puesto: lo que
    `--yolo off` no vuelve a poner, porque restaura el bloque guardado entero. La línea base es lo que
    dejó `aplicar(yolo)`: el allow/ask del perfil y el deny del perfil unido al que ya había."""
    y = PERFILES["yolo"]
    base = {"allow": set(y["allow"]), "ask": set(y["ask"]),
            "deny": set(y["deny"]) | set(guardado.get("deny", []))}
    return {k: sorted(set(actual.get(k, [])) - base[k] - set(guardado.get(k, []))) for k in base}

def yolo(proyecto, on, dry=False):
    sp = os.path.join(proyecto, ".claude", "settings.json")
    snap = sp + SNAP
    if not os.path.exists(sp):
        print(f"✗ no hay {sp}"); return 2
    if on:
        if os.path.exists(snap):
            print("  el interruptor YOLO ya estaba puesto: no se pisa la copia de lo anterior"); return 0
        if dry:                   # ensayo: ni copia de lo anterior, ni .bak, ni settings.json tocado
            print("  [--dry-run] con --yolo on se guardaría la copia de los permisos y quedaría esto:")
            return aplicar(proyecto, "yolo", dry=True)
        d = json.load(open(sp, encoding="utf-8"))
        guardado = {"permissions": d.get("permissions", {}),
                    "_perfil_autonomia": d.get("_perfil_autonomia"),
                    "guardado": datetime.now().isoformat(timespec="seconds")}
        open(snap, "w", encoding="utf-8").write(json.dumps(guardado, ensure_ascii=False, indent=2))
        rc = aplicar(proyecto, "yolo")
        if rc:
            os.remove(snap)       # si no se pudo aplicar, no queda un interruptor «puesto» a medias
        return rc
    if not os.path.exists(snap):
        print("  el interruptor YOLO no estaba puesto: nada que restaurar"); return 0
    s = json.load(open(snap, encoding="utf-8"))
    d = json.load(open(sp, encoding="utf-8"))
    perdido = _perdido_al_apagar(d.get("permissions", {}), s.get("permissions", {}))
    if any(perdido.values()):
        print("  ⚠ se perderá lo que se añadió a los permisos mientras yolo estaba puesto "
              "(la copia previa queda en settings.json.bak):")
        for k, v in perdido.items():
            for x in v:
                print(f"      {k}: {x}")
        print("    Lo propio de este proyecto va en .claude/settings.local.json: no lo toca este script.")
    if dry:
        print("  [--dry-run] con --yolo off se restaurarían los permisos guardados el "
              f"{s.get('guardado', '?')}; no se ha escrito nada.")
        return 0
    d["permissions"] = s.get("permissions", {})
    if s.get("_perfil_autonomia") is None:
        d.pop("_perfil_autonomia", None)
    else:
        d["_perfil_autonomia"] = s["_perfil_autonomia"]
    open(sp + ".bak", "w", encoding="utf-8").write(open(sp, encoding="utf-8").read())
    open(sp, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))
    os.remove(snap)
    print(f"  interruptor YOLO apagado: permisos restaurados tal como estaban el {s.get('guardado', '?')}")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("proyecto", nargs="?", default=".")
    ap.add_argument("--perfil", choices=list(PERFILES))
    ap.add_argument("--yolo", choices=["on", "off"],
                    help="interruptor: on guarda los permisos actuales y pone yolo; off los restaura enteros")
    ap.add_argument("--estado", action="store_true", help="perfil vigente y si el interruptor YOLO está puesto (JSON)")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.estado:
        print(json.dumps(estado(os.path.abspath(a.proyecto)), ensure_ascii=False)); return 0
    if a.yolo:
        return yolo(os.path.abspath(a.proyecto), a.yolo == "on", a.dry_run)
    if a.listar or not a.perfil:
        print("\n  PERFILES DE AUTONOMÍA — cuánta cuerda se le da al agente en este proyecto\n")
        for k, v in PERFILES.items():
            print(f"  ── {k} · {v['titulo']}")
            print(f"     {v['para']}")
            print(f"     allow {len(v['allow'])} · ask {len(v['ask'])} · deny {len(v['deny'])}\n")
        print("  Se elige con --perfil <nombre>. El `deny` nunca se recorta: solo crece.")
        print("  Para ir y VOLVER de yolo sin residuos: --yolo on / --yolo off (restaura los permisos enteros).\n")
        return 0
    return aplicar(os.path.abspath(a.proyecto), a.perfil, a.dry_run)

if __name__ == "__main__":
    sys.exit(main())
