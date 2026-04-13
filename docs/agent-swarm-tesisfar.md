# Agent Swarm en TesisFar — Cómo lo usamos, qué resolvió y qué sigue

> Documento de contexto sobre la implementación del patrón **Hierarchical Orchestration (Orchestrator → Workers)** en el monorepo TesisFar.
> Fecha: 2026-04-13

---

## 1. Qué implementamos

### 1.1 Patrón elegido: Jerárquico con TDD estricto y checkpoint humano

De los cinco patrones que evaluamos (jerárquico, secuencial, peer-to-peer, debate y agent teams), elegimos **jerárquico** porque encaja naturalmente con la forma del proyecto:

- Dos dominios claros (Django backend + Next.js frontend).
- Tareas típicas descomponibles en capas (modelo → API → UI → tests).
- CRUD con reglas de negocio — no necesita debate adversarial ni coordinación peer-to-peer.
- Deuda técnica conocida (tests vacíos) que se beneficia de un especialista en testing.

### 1.2 Arquitectura concreta

```
        Orchestrator (Opus 4.6)
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
  backend-   frontend-   test-
  worker     worker      worker
  (Sonnet)   (Sonnet)    (Sonnet)
```

- **Orchestrator (Opus 4.6)** — planifica, delega y sintetiza. Nunca escribe código directamente si puede delegar.
- **Workers (Sonnet 4.6)** — especialistas con contexto mínimo y herramientas acotadas.
- **Razón del mix de modelos:** Opus para razonamiento y planificación compleja, Sonnet para ejecución porque es más rápido y barato sin perder calidad en tareas enfocadas.

### 1.3 Disciplinas que añadimos encima del patrón base

1. **TDD estricto.** Ningún código de producción se escribe sin un test fallando primero. El `test-worker` es el guardián de esta regla.
2. **Checkpoint humano obligatorio.** Antes de gastar tokens en workers, el Orchestrator escribe un *task brief* (`.claude/state/<task-id>/brief.md`) y espera aprobación explícita del usuario.
3. **Handoff basado en archivos.** Cada worker lee el brief y escribe un reporte estructurado en markdown. Esto es auditable, sobrevive reinicios, y permite revisar en PR.
4. **No git automatizado.** Commits y pushes quedan exclusivamente en manos del humano. El Orchestrator jamás toca git.

### 1.4 Infraestructura creada

- [`CLAUDE.md`](../CLAUDE.md) raíz — guía del Orchestrator, convenciones y workflow.
- [`.claude/agents/`](../.claude/agents/) — definiciones de los tres subagentes con frontmatter (nombre, descripción, herramientas, modelo).
- [`.claude/state/`](../.claude/state/) — directorio de handoff con template y README.
- [`.claude/hooks/post-edit-lint.sh`](../.claude/hooks/post-edit-lint.sh) — script que dispara `ruff` para `.py` y `eslint + tsc` para `.tsx` después de cada edición, vía `PostToolUse` hook en [`.claude/settings.json`](../.claude/settings.json).
- [`backend/pyproject.toml`](../backend/pyproject.toml) — configuración de `pytest-django` y `ruff`.
- [`backend/conftest.py`](../backend/conftest.py) — fixtures compartidas (usuarios por rol, `project_factory`).
- [`frontend/vitest.config.ts`](../frontend/vitest.config.ts) — configuración de Vitest con jsdom y `@testing-library/react`.

---

## 2. Qué resolvió (casos reales)

### 2.1 Tarea 001 — Tests de caracterización para `EvaluationViewSet`

**Problema:** el backend no tenía ni un solo test automatizado. `api/tests.py` estaba vacío. Refactorizar cualquier cosa era un salto de fe.

**Cómo lo resolvió el patrón:**
- El Orchestrator leyó el código del viewset y **detectó inconsistencias antes de escribir una sola línea de test**. Identificó tres comportamientos no obvios que había que pinnar: (a) el límite de 2 intentos solo aplica a `proyecto`, no a `tesis`; (b) los estudiantes solo ven evaluaciones como `student`, no como `partner`; (c) los tutores ven todas las evaluaciones sin filtrar por asignación.
- El brief documentó estas observaciones **y las marcó como posibles bugs, pidiendo NO ajustar las aserciones silenciosamente** si fallaban.
- Tras la aprobación humana, el `test-worker` escribió 20 tests en cuatro clases, los ejecutó contra el código sin modificar, y todos pasaron en verde.
- En el reporte final, el Orchestrator **escaló al humano dos hallazgos**: el bug de `User.objects.create_user()` (descubierto al configurar fixtures, roto por `username = None` sin `UserManager` custom) y la asimetría del `partner` que quedó pinneada por el test #16.

**Resultado:**
- 20 tests de integración verdes, ejecutables en 64s.
- Tres decisiones de diseño documentadas y validadas con el humano.
- `conftest.py` con fixtures reutilizables para las próximas tareas.
- Un bug pre-existente (`create_user`) descubierto y solucionado para los tests sin tocar producción.

### 2.2 Tarea 002 — Corrección de `EvaluationViewSet.get_queryset`

**Problema:** el humano confirmó que los hallazgos #2 (partners invisibles) y #3 (tutores sin filtrar) eran bugs reales, no decisiones intencionales.

**Cómo lo resolvió el patrón:**
1. **RED (test-worker).** Renombró los dos tests de caracterización existentes con sus aserciones invertidas (ahora pidiendo el comportamiento correcto) y añadió cinco tests nuevos para cubrir `list`, `retrieve` y filtro `?project=` en los escenarios tutor/partner. Ejecutó pytest y confirmó que seis tests fallaban por la razón correcta (el séptimo era un invariant guard que ya pasaba).
2. **GREEN (backend-worker).** Leyó el reporte del RED, aplicó una reescritura de seis líneas en `EvaluationViewSet.get_queryset` (añadiendo filtrado por `advisors=user` para tutores y `Q(student) | Q(partner)` para estudiantes), y ejecutó la suite para confirmar 25/25 en verde.
3. **GREEN (verificación del Orchestrator).** Re-corrió la suite de forma independiente como doble chequeo.

**Resultado:**
- Dos bugs de producción arreglados con una reescritura mínima y quirúrgica.
- 25 tests verdes, cero regresiones en los 18 tests no tocados.
- Scope respetado: solo `views.py` y `test_evaluations.py` modificados. `IsReviewerRole`, `create`, serializers, urls y frontend no se tocaron.
- Trazabilidad completa en `.claude/state/20260413-002-evaluation-queryset-fixes/` — brief, RED, GREEN y summary.

### 2.3 Beneficios observados en estas dos tareas

| Beneficio | Evidencia concreta |
|---|---|
| **Detección temprana de bugs** | El Orchestrator encontró los dos bugs en la fase de planificación de la tarea 001, antes de escribir un solo test. |
| **Escalada limpia al humano** | Cuando los tests pinnearon comportamientos ambiguos, el Orchestrator se detuvo y pidió decisión al humano en lugar de improvisar. |
| **Aislamiento de scope** | Cada worker tenía permisos acotados. El `test-worker` físicamente no podía modificar `api/views.py`, y el `backend-worker` no podía tocar tests. Esto hace imposible saltarse el TDD por accidente. |
| **Refactor seguro** | El fix de la tarea 002 cambió solo seis líneas en producción, con 25 tests como red de seguridad. La confianza de merge es alta. |
| **Auditabilidad** | Todo el razonamiento, cada decisión, cada resultado quedó escrito en `.claude/state/`. El humano puede revisar el proceso, no solo el diff final. |

---

## 3. Qué podemos hacer a futuro con este patrón

### 3.1 Siguientes pasos inmediatos (bajo riesgo)

1. **Arreglar `User.objects.create_user()`** — añadir un `UserManager` custom al modelo `User`. Tarea pequeña, backend-only, con TDD estricto. `create_test_users.py` dejaría de estar roto silenciosamente.
2. **Tests de integración para el resto de los ViewSets.** El patrón ya demostró su valor en `EvaluationViewSet`. Repetir para `ProjectViewSet`, `SemesterViewSet`, `UserViewSet` y `CommentViewSet` es trabajo directo y paralelo. Cada viewset puede ser su propia tarea independiente.
3. **Tests frontend iniciales con Vitest.** La infraestructura (`vitest.config.ts`, `vitest.setup.ts`) ya está lista pero no se ha usado. Un buen primer caso: la lógica de `useEvaluationDraft` (persistencia en localStorage) y el cálculo de `scoring.ts`. No tocan UI, solo funciones puras — bajo riesgo, alto valor.

### 3.2 Features cross-cutting (todos los workers a la vez)

El verdadero poder del patrón se libera cuando una feature toca backend + frontend + tests de forma coordinada. Ejemplos candidatos:

- **Notificaciones en la app** — nuevo modelo `Notification`, viewset con permisos por rol, hook en `EvaluationViewSet.perform_create` para disparar eventos, componente frontend que haga polling o use Server-Sent Events, badge en el sidebar. El Orchestrator decomposaría esto en ~8 subtareas secuenciales con checkpoints intermedios.
- **Export PDF de evaluaciones** — endpoint backend que renderiza la evaluación, botón frontend, tests de integración del endpoint y tests del componente.
- **Historial de cambios en proyectos** — auditoría con `django-simple-history`, vista read-only en frontend, tests de que los cambios se loggean correctamente.

En estos flujos, el orden típico sería: test-worker (RED backend) → backend-worker → test-worker (GREEN backend) → test-worker (RED frontend) → frontend-worker → test-worker (GREEN frontend) → Orchestrator sintetiza.

### 3.3 Evoluciones del patrón

**Corto plazo:**
- **Hooks más inteligentes.** Actualmente el `post-edit-lint.sh` solo reporta. Podríamos añadir un hook que ejecute los tests del módulo afectado automáticamente tras editar un archivo de producción (mini-GREEN automático).
- **Commits automatizados con gate humano.** Cuando madure la confianza, permitir que el Orchestrator proponga un commit (sin push) al terminar una tarea, mostrando el mensaje sugerido para que el humano lo apruebe con un click.
- **Task briefs versionados.** Guardar los briefs aprobados en git (ya lo hacemos) sirve como documentación viva de decisiones de diseño. Podríamos enlazarlos desde los PRs.

**Medio plazo:**
- **Subagentes adicionales.**
  - `migration-reviewer` — un worker especialista que solo revisa migraciones de Django generadas, buscando operaciones destructivas o locks peligrosos en producción.
  - `security-auditor` — corre tras cambios en `permissions.py` o `views.py` para detectar fugas de datos o endpoints desprotegidos.
  - `doc-writer` — genera/actualiza las secciones relevantes de `CLAUDE.md`/`AGENT.md` cuando se añade código nuevo.
- **Integración con CI.** Los reportes en `.claude/state/` pueden convertirse en comentarios de PR automáticos. GitHub Actions ejecutaría la misma suite que corrió localmente y pegaría el summary del Orchestrator en el PR.

**Largo plazo (si escala):**
- **Paralelización de workers independientes.** Cuando una feature tiene subtareas verdaderamente independientes (ej: migrar 10 componentes a un nuevo estilo), el Orchestrator podría spawnar workers en paralelo con git worktrees aislados. Esto convierte el patrón jerárquico en algo más parecido a un **Agent Team** para ese caso particular.
- **Debate pattern para decisiones arquitectónicas.** Si llegamos a un punto donde hay que elegir entre, por ejemplo, dos approaches para la auth (JWT vs session), se puede spawnar un `proposer-a`, `proposer-b` y un `judge` para producir un ADR (Architecture Decision Record) razonado.

### 3.4 Límites conocidos del patrón actual

Hay que ser honestos sobre dónde no brilla:

- **Tareas muy pequeñas.** Arreglar un typo o renombrar una variable no justifica el overhead de brief + checkpoint + worker + summary. El propio `CLAUDE.md` raíz documenta las excepciones.
- **Exploración abierta.** "¿Qué puedo mejorar en este módulo?" no es una tarea; es una conversación. El patrón se activa cuando hay un objetivo concreto.
- **Debugging interactivo.** Si un bug requiere 20 minutos de prueba y error en el navegador, el Orchestrator no puede hacerlo solo — el humano es parte del loop. En ese caso, el Orchestrator propone hipótesis y el humano las valida.
- **Costos.** Opus 4.6 para el Orchestrator cuesta más que Sonnet. Para tareas grandes el ROI es claro; para tareas triviales conviene saltarse el patrón.

---

## 4. Resumen ejecutivo

- El patrón **jerárquico con TDD estricto y checkpoint humano** encajó en TesisFar por su topología (monorepo backend/frontend) y su estado (sin tests automatizados).
- En dos tareas reales demostró valor concreto: 25 tests de integración escritos desde cero y 2 bugs de producción arreglados con refactor mínimo, todo con trazabilidad completa en `.claude/state/`.
- El próximo paso natural es replicar el patrón en otros viewsets, arrancar tests frontend, y eventualmente ejecutar features cross-cutting que usen los tres workers coordinados.
- El sistema está diseñado para evolucionar: hooks más inteligentes, nuevos subagentes especializados, integración con CI y — cuando haga falta — paralelización real con worktrees.

---

## 5. Enlaces rápidos

- [Guía del Orchestrator](../CLAUDE.md)
- [Definición del backend-worker](../.claude/agents/backend-worker.md)
- [Definición del frontend-worker](../.claude/agents/frontend-worker.md)
- [Definición del test-worker](../.claude/agents/test-worker.md)
- [Template de task brief](../.claude/state/template.md)
- [Tarea 001 — tests de `EvaluationViewSet`](../.claude/state/20260413-001-evaluation-viewset-tests/summary.md)
- [Tarea 002 — fix de `get_queryset`](../.claude/state/20260413-002-evaluation-queryset-fixes/summary.md)
- [Diagramas de patrones](orchestration-patterns/)
