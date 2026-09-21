# /qa-loop — QA convergente de UI (Lidia + Vera + Ignacio) hasta avg ≥ 9.0

Ejecuta el protocolo completo de `.claude/rules/qa-loop.md` sobre la wave/feature de UI actual.
Orquesta los tres auditores de persona que trae el template y itera hasta que la nota media ≥ 9.0
o se agota el tope de iteraciones.

**Úsalo** al cerrar cualquier wave con UI. **No lo uses** en waves backend-only (usa
`/verification-loops` o la skill `ux-reviewer`), ni sobre código que no compila.

## Pasos

1. **Pre-flight**
   ```bash
   bash .claude/hooks/check-ram.sh                         # en verde, o no se lanza la ronda
   # build del proyecto (ajusta al stack): npm run build / python manage.py check
   curl -fsS http://localhost:<PORT>/ -o /dev/null && echo "URL viva"
   ```
   Anota `WAVE_ID` (p. ej. `W4`) e `iteration_n` (empieza en 1).

2. **Lanza los 3 auditores EN PARALELO** (un solo mensaje, 3 Agent tool calls):
   - `lidia-naive-tester` → naive test como la persona objetivo del proyecto, 30s, móvil+desktop.
   - `vera-art-director` → audit visual tier-1, gate 9.0, 5 tokens obligatorios.
   - `ignacio-roig` → crítica adversarial, ≥10 findings, delta ≥1.0 vs Vera.

   Cada uno escribe en `.docs/feedback/qa-loop/<WAVE_ID>/iter-<n>/<agente>/`.

3. **Calcula** `score_wave = (lidia_avg + vera_avg) / 2` (Ignacio es informativo) y evalúa el
   **gate PASS** (todos los criterios de la rule).

4. **Si score < 9.0** → **arréglalo tú, en esta sesión** (no un subagente) con los findings (P0/P1
   de Lidia, severity≥medium de Vera, UGLY/AMATEUR/PLACEHOLDER/INCONSISTENT de Ignacio); cierra cada
   pantalla tocada con `ux-reviewer`, `iteration_n += 1` y vuelve al paso 2.

5. **Tope**: 5 iteraciones o mejora < 0.3 entre dos → escalar al Supervisor con `openclaw gateway wake`.

6. **Al PASS**: marca la wave `[x]` en `tasks.md`, actualiza `MEMORY.md`, notifica DONE.

Detalle completo, rúbrica y estructura de output: **`.claude/rules/qa-loop.md`**.
