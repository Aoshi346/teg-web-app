---
name: "verification-loops"
description: >-
  Usar antes de marcar cualquier tarea como DONE: tests del módulo afectado, que no haya datos mock
  en la UI, capturas con Playwright, type checker y build. Se activa en verificación pre-commit,
  testing, QA y chequeos anti-mock. Agnóstica de stack: ajusta los comandos al proyecto. NO usar
  para: escribir tests (escribir-tests), juzgar los tests (code-review-gate) ni el gate de UX
  (ux-reviewer).
user-invocable: false
metadata:
  source: "adapted from boris-verification (archivada 2026-08-22 — duplicaba rules/verification.md)"
  version: 1.0.0
  author: Tech Lead Template
  category: workflow
  updated: 2026-10-21
  tech-stack: "ajusta al stack del proyecto"
---

# Verification Loops — Pre-DONE gate (stack-agnostic)

## Principio

Sin verificación explícita, el agente reporta DONE y el supervisor encuentra errores básicos. Con este checklist, los errores se atrapan antes de reportar.

> **Nota:** Los comandos abajo son ejemplos. Ajusta al stack real del proyecto. Donde aparece `${TEST_CMD:-pytest}` o `cd frontend && npm run build`, sustituye por lo que use tu proyecto (jest, vitest, cargo test, pnpm build, etc.).

## Checklist obligatorio antes de reportar DONE

### Backend (ej: Django / FastAPI / Node)

```bash
# 1. Verificar RAM
free -h | awk '/Mem:/ {print "Libre: " $7}'

# 2. Tests del módulo (NO tests globales sin filtro)
# Ejemplo Django: pytest backend/apps/[app_afectada]/tests/ -v --maxfail=5
# Ejemplo Node:   npm test -- --testPathPattern=[module] --bail=5
${TEST_CMD:-pytest} path/al/modulo/tests/ -v --maxfail=5

# 3. Verificar sin errores de arranque
# Django: cd backend && python manage.py check --deploy
# FastAPI: python -c "from app.main import app; print('OK')"
# Node: npm run lint && npm run typecheck

# 4. Migraciones al día (si aplica)
# Django: cd backend && python manage.py showmigrations | grep "\[ \]" && echo "PENDING" || echo "OK"
# Alembic: alembic current && alembic heads
```

### Frontend (si aplica)

```bash
# 5. Build sin errores de tipos (ajusta path al proyecto)
cd frontend && npm run build 2>&1 | tail -20

# 6. No hay 'any' sin justificación (TypeScript)
grep -rn ": any\|as any" frontend/src --include="*.ts" --include="*.tsx" | grep -v "// eslint-disable\|// any-ok"

# 7. Anti-mock — no hay datos hardcodeados
grep -rn "mockData\|fakeData\|TODO.*real\|HARDCODED\|placeholder_" frontend/src --include="*.tsx" --include="*.ts"
```

### Verificación visual (si hay cambios de UI)

```bash
# 8. Screenshot con Playwright MCP
# Navegar a la página afectada y verificar que se renderiza correctamente
# Usar browser_navigate + browser_screenshot del MCP playwright
# 8b. O de extremo a extremo con lo que trae Claude Code: /verify (hay que invocarla: Claude no
#     la lanza solo) y /run; detalle en rules/verification.md §3
```

### Si el resultado lleva un número (9. cifras con condiciones)

Un «funciona» con cifra se reporta en el formato de `rules/verification.md` §Una cifra sin sus
condiciones no es evidencia: **resultado con N · frente a qué línea base · en qué condiciones ·
sobre qué objeto (y cómo se comprobó que es lo desplegado) · qué no se probó**. Si falta una de las
cinco, se dice; no se omite.

```bash
# 9. Lo medido es lo desplegado: el símbolo del cambio, DENTRO de lo que corre (no en el repo)
# Docker: docker compose exec -T <servicio> grep -n "<símbolo nuevo>" /app/<ruta>
# Web:    python3 .claude/scripts/certifica_objeto.py sellar --base <url> --bundle <ruta> …
```

## Paths de tests — personalizar por proyecto

Mantén en el CLAUDE.md del proyecto una tabla como esta:

| Área | Path de tests | Comando |
|------|--------------|---------|
| <módulo_1> | `backend/apps/<módulo_1>/tests/` | `pytest backend/apps/<módulo_1>/tests/ -v --maxfail=5` |
| <módulo_2> | `backend/apps/<módulo_2>/tests/` | `pytest backend/apps/<módulo_2>/tests/ -v --maxfail=5` |
| frontend | `frontend/src/**/*.test.tsx` | `cd frontend && npm test -- --run` |

## Checklist SpecKit pre-merge

Antes de reportar READY_MERGE al Supervisor:

- [ ] Todos los checkboxes de la wave marcados en `.specify/sessions/[ID]/tasks.md`
- [ ] Tests del módulo afectado → PASS
- [ ] Build frontend (si aplica) → 0 errores
- [ ] No hay `console.error` o `console.warn` en las páginas afectadas
- [ ] Si hay UI nueva → screenshot capturado y revisado

## Después del merge — ¿arranca y no hay conflicto semántico?

Tras un merge a `develop` o `main` (o de un worktree), antes de dar el merge por bueno:
`references/post-merge.md`, el protocolo de 6 pasos que era el agente `integrador-merge` (retirado en
la 3.01, EQ-8: 0 usos observados). Lo corre quien no hizo el merge (un subagente con contexto limpio
vale): RAM, punto de partida, fan-in de lo cambiado, arranque, tests del módulo y conflicto semántico;
si algo se rompe, `git revert -m 1`, nunca `reset --hard` sobre una rama compartida.

## Verificación de API — endpoints nuevos

```bash
# Con servidor corriendo (ajusta puerto al proyecto)
curl -s http://localhost:8000/api/v1/[endpoint]/ -H "Authorization: Bearer [token]" | python3 -m json.tool
```

## Anti-mock grep — backend

```bash
# Ajusta path a la raíz de apps del proyecto
grep -rn "mockData\|hardcoded\|fake_\|TODO.*implement\|raise NotImplementedError\|pass  #.*todo" \
  backend/apps/ --include="*.py" | grep -v test_
```

## Anti-patterns

- Reportar DONE sin correr tests del módulo afectado
- Confiar en "el código se ve bien" sin tests
- `npm run build` con errores TypeScript y reportar DONE
- No verificar con screenshot cuando hay cambios de UI
- Reportar una cifra sin línea base, condiciones ni N, o medir el repo y desplegar el contenedor
  (`rules/verification.md` §Una cifra sin sus condiciones)
