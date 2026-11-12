# Plan de Paralelización - [Feature Name]

**Fecha:** [YYYY-MM-DD]  
**Total instancias:** [N]  
**Worktrees necesarios:** [Sí/No]

---

## 📊 Resumen

| Fase | Instancias | Dependencias | Estimado |
|------|------------|--------------|----------|
| 1 | 2 | Ninguna | 2h |
| 2 | 1 | Fase 1 | 1h |
| 3 | 2 | Fase 2 | 2h |

---

## Fase 1: [Nombre] (PARALELO)

> Sin dependencias - puede ejecutarse inmediatamente

### Instancia A: Backend Base
**Tareas:**
- [ ] Crear modelos para [X]
- [ ] Migrations
- [ ] Serializers básicos

**Archivos:**
```
apps/module/models.py
apps/module/serializers.py
apps/module/migrations/
```

**Comando para lanzar:**
```bash
tmux new-session -d -s inst-a "cd /home/proyecto && claude --dangerously-skip-permissions --model claude-sonnet-4-6 -p '[prompt]'"
```

### Instancia B: Frontend Base
**Tareas:**
- [ ] Componentes UI para [X]
- [ ] Hooks básicos

**Archivos:**
```
frontend/src/components/Module/
frontend/src/hooks/useModule.ts
```

**Comando para lanzar:**
```bash
tmux new-session -d -s inst-b "cd /home/proyecto && claude --dangerously-skip-permissions --model claude-sonnet-4-6 -p '[prompt]'"
```

---

## Fase 2: [Nombre] (SECUENCIAL)

> Depende de Fase 1 completada

### Instancia C: Integración
**Tareas:**
- [ ] Conectar frontend con backend
- [ ] Tests de integración

**Archivos:**
```
apps/module/views.py
frontend/src/services/moduleApi.ts
tests/integration/
```

---

## Fase 3: [Nombre] (PARALELO)

> Depende de Fase 2 completada

### Instancia D: Polish UI
**Tareas:**
- [ ] Estilos finales
- [ ] Responsive

### Instancia E: Tests & Docs
**Tareas:**
- [ ] Tests unitarios
- [ ] Documentación

---

## 🌳 Worktrees (si necesarios)

```bash
# Crear worktrees para trabajo paralelo sin conflictos
cd /home/proyecto
git worktree add ../proyecto-inst-a feature/module-backend
git worktree add ../proyecto-inst-b feature/module-frontend

# Al terminar, merge y limpiar
git worktree remove ../proyecto-inst-a
git worktree remove ../proyecto-inst-b
```

**Nota:** Usar worktrees cuando las instancias modifican archivos que podrían conflictuar.

---

## ✅ Criterios de completado por fase

### Fase 1
- [ ] Instancia A: modelos creados, migrations aplicadas
- [ ] Instancia B: componentes renderizan sin errores

### Fase 2
- [ ] API endpoints funcionando
- [ ] Frontend consume API correctamente

### Fase 3
- [ ] >80% coverage
- [ ] Docs actualizados
- [ ] Sin errores de lint

---

_Plan creado: [fecha]_
