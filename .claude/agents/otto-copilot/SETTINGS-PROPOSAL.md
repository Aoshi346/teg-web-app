# Propuesta de wiring de Otto en settings.json — ⏳ REQUIERE APROBACIÓN DEL USUARIO (T4.5)

> Preparado en TPL-1 W4. NO aplicado. El cambio a `settings.json` es config crítica
> (governance.md) y el plan aprobado lo marca como decisión humana.

## Cambio propuesto en `hooks.SessionStart`

**Antes** (actual):
```json
"SessionStart": [
  { "hooks": [
    { "type": "command", "command": "bash $CLAUDE_PROJECT_DIR/.claude/hooks/validate-progress.sh", "async": true }
  ]}
]
```

**Después**:
```json
"SessionStart": [
  { "hooks": [
    { "type": "command", "command": "bash $CLAUDE_PROJECT_DIR/.claude/hooks/otto-briefing.sh", "timeout": 10 },
    { "type": "command", "command": "bash $CLAUDE_PROJECT_DIR/.claude/hooks/validate-progress.sh", "timeout": 10 }
  ]}
]
```

Dos cambios y por qué:
1. **`otto-briefing.sh` añadido, SÍNCRONO** (sin `async`): el stdout de un hook async se inyecta de
   forma poco fiable como contexto. El briefing tarda ~0.17s medido — muy dentro del timeout de 10 s
   (el campo va en SEGUNDOS: hasta el 2026-10-21 aquí ponía 2000, que son 33 minutos; AMC,
   cold_calling_coach, risk-couple y webs tienen esos mismos 2000 en los dos — MO-55).
2. **`validate-progress.sh` pasa de `async:true` a síncrono**: su WARNING de PROGRESS.json inválido
   hoy puede perderse por la misma razón. Mismo coste (<100ms).

## Opt-in documentado (NO activar por defecto) — UserPromptSubmit

Descartado como default en el diseño (latencia en CADA prompt + un bash no sabe juzgar "tarea
grande" → falsos positivos que queman el address-rate de Otto). El "modo guía" en tareas grandes
va por el **Gate 0 de plan-gates.md** (sin coste por prompt). Si algún proyecto lo quiere igualmente:

```json
"UserPromptSubmit": [
  { "hooks": [
    { "type": "command", "command": "bash $CLAUDE_PROJECT_DIR/.claude/hooks/otto-briefing.sh", "timeout": 5 }
  ]}
]
```

## Cómo aplicar (cuando el Usuario apruebe)

Editar `.claude/settings.json` → bloque `hooks.SessionStart` como arriba. Verificación: abrir
sesión nueva → el briefing "🅾️ Otto" aparece como contexto; `time .claude/hooks/otto-briefing.sh` < 0.5s.
