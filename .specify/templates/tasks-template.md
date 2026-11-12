# Tasks: [NOMBRE DE LA SESIÓN]

**Sesión:** [ID]
**Última actualización:** YYYY-MM-DD HH:MM

---

## 🔧 Setup (Tech Lead Principal)

### Preparación Worktrees
- [ ] Verificar RAM disponible (`bash .claude/hooks/check-ram.sh` en verde; límites: `--explain`)
- [ ] Crear worktrees necesarios:
  ```bash
  git worktree add worktrees/[nombre] feature/[nombre]
  ```
- [ ] Copiar PROGRESS.log a cada worktree
- [ ] Verificar estructura .claude/ en worktrees

### Instalación Dependencias (si necesario)
- [ ] Playwright: `pip install playwright && playwright install`
- [ ] Otras: [especificar]

---

## Wave 1 — [Nombre]

**Ejecuta:** Tech Lead Principal (TL-1)
**Worktree:** - (develop directo)
**Subagentes:** [listar si aplica]

### [XXX-01] [Nombre del item]
**Paralelizable:** No
**Skills/MCPs:** django-orm, context7

- [ ] Subtarea 1
- [ ] Subtarea 2
- [ ] Test: `pytest apps/[module]/ -k "test_xxx" -v`
- [ ] Verificar en PROGRESS.log

### [XXX-02] [Nombre del item]
**Paralelizable:** Sí (con subagente)
**Subagente:** Backend Dev
**Skills/MCPs:** postgresql

- [ ] Subtarea 1
- [ ] Subtarea 2
- [ ] Test: `pytest apps/[module]/ -v`

### ✅ Wave 1 Checkpoint
- [ ] Todos los tests de Wave 1 pasan
- [ ] Build pasa
- [ ] PROGRESS.log actualizado
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Wave 1 completada, tests OK"

---

## Wave 2 — [Nombre] (PARALELO)

### 🔀 TL-2: Backend (worktree: wave2-backend)

**Branch:** `feature/wave2-backend`
**Crear con:**
```bash
git worktree add worktrees/wave2-backend feature/wave2-backend
cp .claude/PROGRESS.log worktrees/wave2-backend/.claude/
```

#### [XXX-03] [Nombre]
**Skills/MCPs:** django-orm, postgresql

- [ ] Subtarea 1
- [ ] Subtarea 2
- [ ] Test: `pytest apps/[module]/ -v`

#### TL-2 Checkpoint
- [ ] Tests backend pasan
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "TL-2 backend listo para merge"
- [ ] **⏳ ESPERAR APROBACIÓN** del Supervisor o Usuario

---

### 🔀 TL-3: Frontend (worktree: wave2-frontend)

**Branch:** `feature/wave2-frontend`
**Crear con:**
```bash
git worktree add worktrees/wave2-frontend feature/wave2-frontend
cp .claude/PROGRESS.log worktrees/wave2-frontend/.claude/
```

#### [XXX-04] [Nombre]
**Skills/MCPs:** context7
**Plugins:** frontend-design

- [ ] Subtarea 1
- [ ] Subtarea 2
- [ ] Test visual / manual
- [ ] Build: `npm run build`

#### TL-3 Checkpoint
- [ ] Build pasa sin errores TypeScript
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "TL-3 frontend listo para merge"
- [ ] **⏳ ESPERAR APROBACIÓN** del Supervisor o Usuario

---

## 🔄 Merge Protocol

### Pre-Merge (por worktree)

#### Merge TL-2 (wave2-backend)
- [ ] **⏳ CONFIRMACIÓN RECIBIDA** del Supervisor o Usuario
- [ ] `git checkout develop && git merge feature/wave2-backend`
- [ ] Resolver conflictos si hay
- [ ] Tests post-merge: `pytest apps/[module]/ -v`
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Merge TL-2 completado, tests OK"

#### Merge TL-3 (wave2-frontend)
- [ ] **⏳ CONFIRMACIÓN RECIBIDA** del Supervisor o Usuario
- [ ] `git checkout develop && git merge feature/wave2-frontend`
- [ ] Resolver conflictos si hay
- [ ] Build: `npm run build`
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Merge TL-3 completado, build OK"

---

## 🧪 Testing Final

### Tests Unitarios
- [ ] Backend: `pytest apps/ -v --ignore=tests/e2e/`
- [ ] Verificar: 0 failures

### Tests E2E
- [ ] `pytest tests/e2e/ -v` (si existe)
- [ ] Verificar: 0 failures

### Tests Playwright (Frontend)
- [ ] `cd frontend && npx playwright test`
- [ ] O: `playwright test --project=chromium`
- [ ] Verificar: 0 failures
- [ ] Screenshots guardados para review

### Testing Checkpoint
- [ ] **TODOS** los tests pasan
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Testing final OK. ¿Commit a develop?"
- [ ] **⏳ ESPERAR APROBACIÓN** para commit final

---

## 📝 Commit Final

- [ ] Commit con mensaje descriptivo y **las rutas de la sesión** (nunca `git add -A`: con otra
  sesión viva en el repo se lleva sus ficheros bajo este mensaje). Si el `CONFIGURACION.yaml` del
  proyecto dice `git_commit: usuario`, no se commitea: se deja listo y se avisa (`READY_COMMIT`).
  ```bash
  git commit -m "feat([módulo]): [descripción]
  
  - [cambio 1]
  - [cambio 2]
  
  Session: [ID]" -- <ruta> <ruta>
  ```
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "QUESTION: commit hecho, ¿push?"
- [ ] **⏳ CONFIRMACIÓN RECIBIDA** para el push (`governance.md` §2) · Push: `git push origin develop`
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Push realizado"

---

## 🧹 Cleanup

### Borrar Worktrees
- [ ] **⏳ CONFIRMACIÓN RECIBIDA** del Supervisor o Usuario para borrar
- [ ] `git worktree remove worktrees/wave2-backend`
- [ ] `git worktree remove worktrees/wave2-frontend`
- [ ] Borrar branches locales si ya no se necesitan:
  ```bash
  git branch -d feature/wave2-backend
  git branch -d feature/wave2-frontend
  ```

### Consolidar Logs
- [ ] Merge PROGRESS.log de worktrees al principal
- [ ] Actualizar CHECKLIST.md del proyecto
- [ ] Marcar sesión como DONE en spec.md

---

## ✅ Verificación Final

- [ ] Todos los checkboxes arriba marcados
- [ ] PROGRESS.log consolidado
- [ ] Worktrees eliminados (con confirmación)
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Sesión [ID] COMPLETADA"

---

## 📞 Protocolo de Comunicación

### Tech Lead → Supervisor
```bash
python3 .claude/scripts/avisar.py "[PROYECTO] [ESTADO]: [mensaje]"   # Telegram; exit 1 si no llega
```

Estados:
- `READY_MERGE`: Listo para merge, tests OK
- `BLOCKED`: Problema que requiere decisión
- `DONE`: Tarea/wave completada
- `QUESTION`: Necesita clarificación

### Esperar Respuesta
Cuando se indica **⏳ ESPERAR APROBACIÓN**:
1. Enviar notificación al Supervisor
2. NO proceder hasta recibir confirmación
3. Si no hay respuesta en 10min, re-enviar

---

_Template v1.2 - 28 Feb 2026_
