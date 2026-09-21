# PROGRESS.json y PROGRESS.log — formato canónico

> **Cuándo aplicar:** en TODA sesión de trabajo (PROGRESS.json es obligatorio al inicio).
> Consolidada aquí desde CLAUDE.md (poda TPL-1, 2026-08-07). `PROGRESS.json` es la **única fuente
> de verdad de estado** para el Supervisor (`rules/governance.md` §4); el hook
> `validate-progress.sh` (SessionStart) avisa si falta.

## PROGRESS.json — obligatorio, en la raíz del proyecto

Crear AL INICIO de la sesión; actualizar EN VIVO (no en batch):

```json
{
  "task": "Nombre de la tarea principal",
  "status": "in_progress",
  "startedAt": "2026-03-27T09:00:00Z",
  "checklist": [
    {"id": 1, "item": "Analizar código actual", "done": false},
    {"id": 2, "item": "Implementar cambio X", "done": false},
    {"id": 3, "item": "Escribir tests", "done": false},
    {"id": 4, "item": "Verificar con screenshot", "done": false},
    {"id": 5, "item": "Commit y push", "done": false}
  ],
  "completedAt": null,
  "notes": []
}
```

- Marca `"done": true` al completar cada item; añade items si descubres más trabajo.
- Al terminar todo: `"status": "completed"` + `"completedAt"`.
- Esto permite supervisión automática sin parsear logs: `cat PROGRESS.json | jq '{task,status}'`.

## `pending-tasks.md` — lo que ha PEDIDO el Usuario (automático)

Vive en el plan activo (`.docs/plans/<plan>/pending-tasks.md`) y lo escribe el hook
`capture-task.sh` en **cada** petición. No hay que acordarse de nada: el hook corre siempre y
además **reinyecta las pendientes** en el contexto de cada turno.

**Por qué existe.** Palabras del Usuario: *«se te está olvidando todo, yo voy diciéndote cosas y se
van perdiendo»*. Y tenía razón: no había ningún sitio donde quedara escrita cada petición, así que
recordarlas dependía del agente entre veinte tareas — y eso falla siempre, no a veces.

**Es un hook y no una skill a propósito.** Una skill hay que acordarse de invocarla, que es el
mismo fallo otra vez (criterio de capas del template: si el coste de ignorarlo es alto, baja de capa).

| Estado | Significa |
|---|---|
| `[ ]` | pendiente |
| `[>]` | en curso |
| `[~]` | delegada a background — **con el id de la tarea** |
| `[x]` | hecha, con nota de qué se hizo |
| `[!]` | bloqueada o descartada, **con su razón** |

### Los DOS sitios, y no es redundancia

Toda petición del Usuario va **a los dos**, siempre — en este repo y en cualquier proyecto derivado:

| | Dónde se ve | Qué aporta | Qué le falta al otro |
|---|---|---|---|
| **`pending-tasks.md`** | el fichero, en el plan | **persiste entre sesiones**; lo abre una persona | los TODOs mueren con la conversación |
| **Tasks (`TaskCreate`)** | `Ctrl+T` en la terminal | se ve **mientras el agente trabaja**, sin abrir nada | el fichero hay que ir a mirarlo |

**Por eso los dos.** El fichero lo escribe el hook automáticamente; la tarea la crea el TL con
`TaskCreate` al ponerse con ella, y la cierra con `TaskUpdate` (`completed`). Si solo se hace uno
de los dos, se pierde justo la mitad que hacía falta: o no hay rastro mañana, o no se ve hoy.

⚠️ Las tools de Task **vienen desactivadas por defecto** en los modelos recientes. Se activan con
`CLAUDE_CODE_ENABLE_TODO_TOOLS=1` en el `env` de `settings.json`, y `ensure_hooks.py` lo asegura en
cada proyecto — porque `settings.json` no se copia con el template y ponerlo solo aquí no llegaba
a ninguna parte.

**Las tres obligaciones del TL:**

1. **Refinar** al ponerse con ella: el hook guarda el texto crudo (rápido y a prueba de fallos),
   pero una petición con erratas y tres cosas mezcladas se lee mal a los dos días.
   `tasks_registry.py refine <id> "<qué se pide, en claro>"` — conserva el original en un
   comentario, por si el refinado se equivoca.
2. **Marcar al terminar**, con nota: `done <id> --nota "<qué se hizo>"`.
3. **Nunca borrar una línea para "limpiar"**: una tarea que desaparece sin marcarse es una tarea
   perdida, que es justo lo que el fichero impide.

⚠️ **No confundir con `dashboard.md`**, que está en la misma carpeta: aquel son los items del
informe (los escribe el agente desde el análisis); éste son las peticiones del Usuario.

## PROGRESS.log — opcional (notas detalladas)

```
[YYYY-MM-DD HH:MM] TIPO: Descripción
```

Tipos: `INICIO | PROGRESO | BLOQUEADO | ERROR | FIN | NOTA | PLAN | PARALELIZACIÓN`.
El plan de una tarea grande va aquí con tag `[PLAN]` (archivos exactos + por qué + riesgo + orden).

## Con SpecKit

El progreso granular vive en `tasks.md` de la sesión (checkboxes ` />x!` EN VIVO —
`rules/speckit-progress-tracking.md`, gate: `scripts/task_progress.py --gate`). PROGRESS.json
mantiene la vista de tarea/estado global; PROGRESS.log la actividad.

## Anti-patterns

- ❌ Crear PROGRESS.json al final de la sesión "para cumplir" — nace al inicio o no sirve.
- ❌ Actualizarlo en batch al terminar — el Supervisor lo lee DURANTE la sesión.
- ❌ Estado en la conversación pero no en el JSON ("ya casi está") — si no está en el JSON, no existe.
