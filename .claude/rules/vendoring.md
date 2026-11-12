---
paths:
  - ".claude/skills/*/SKILL.md"
  - ".claude/skills/*/LICENSE*"
  - ".claude/envios-externos.json"
  - ".claude/templates/envios-externos.json"
  - ".claude/skills/skill-authoring/check_frontmatter.py"
---
# Vendorizar una skill de terceros — fijada, a mano y con su procedencia

> **Cuándo aplicar:** al traer a un proyecto (o al template) una skill escrita por otros: de un
> repositorio, de un marketplace abierto o de la carpeta de otro proyecto. **NO aplicar:** a un
> plugin del marketplace oficial instalado con `/plugin` (eso es `agent-security.md` §5b, con la
> versión fijada y `check_plugins.py`), ni a una skill nuestra (`skill-authoring`).

Por qué (AN-5): cada proyecto traía skills ajenas a su manera, a veces con el instalador del autor
(`npx … @latest`, `install.sh`), que puede escribir hooks o tocar `settings.json`, y con `@latest` el
código cambia sin que nadie lo revise. Y una skill ajena que se activa sola es una voz más que el
modelo pondera en cada sesión y alarga el listado (`check_instrucciones.py` lo mide). Procedimiento
escrito por fitapp (`improvements_tl.md`, T-070, 17-10), generalizado aquí.

## La norma — siete pasos, todos

1. **Leer antes de copiar.** Descargar sin ejecutar nada y pasar el escaneo de `agent-security.md` §5;
   los ficheros ejecutables se leen enteros, el grep solo prioriza.
2. **Copiar desde un commit fijo, nunca con el instalador del autor.** Ni `npx …@latest`, ni
   `curl … | sh`, ni su `install.sh`: se copia la carpeta de la skill del commit elegido. Se quitan sus
   tests, ejemplos y lo que no se va a usar, y no se instalan las sub-skills que dupliquen algo de casa.
3. **La licencia, antes de nada**: `rules/licenses.md`. AGPL o PolyForm no entran en lo que se entrega.
4. **Solo a mano**: `disable-model-invocation: true` en su frontmatter. Se llama con `/<nombre>`,
   nunca porque el modelo la crea útil.
5. **Procedencia en el frontmatter, y una línea arriba del cuerpo** que la diga en claro:

   ```yaml
   metadata:
     vendored:
       repo: https://github.com/<autor>/<repo>
       commit: 434b7f9            # sha; nunca una rama, un tag móvil ni «latest»
       license: MIT               # SPDX, leída en el LICENSE de ese commit
       date: 2026-10-31
       sends_out: none            # o la lista de comandos/tools que mandan algo fuera
   ```
   `> Vendorizada de <repo>@<commit> el <fecha>; parches marcados «<proyecto> (T-…)».`
6. **Cada parche propio, marcado** en el código (`# fitapp (T-070): …`), para poder volver a traer el
   original y reaplicarlos.
7. **Lo que envía fuera, declarado** en `.claude/envios-externos.json` (plantilla:
   `templates/envios-externos.json`, con el campo `skill`): así `aviso-envio-externo.sh` pregunta antes
   de cada envío en un proyecto delicado y avisa en los demás. Con `"always_ask": true` en la entrada,
   pregunta en cualquier proyecto (lo usan los generadores de UI/UX Pro Max, 3.66).

**Comprobación** (antes del commit, la misma que pide `skill-authoring`):

```bash
python3 .claude/skills/skill-authoring/check_frontmatter.py .claude/skills/<nombre>/SKILL.md
```

Con `metadata.vendored`, sale con 1 si falta un campo, si el commit no es un sha, si falta
`disable-model-invocation: true`, si el cuerpo manda usar el instalador del autor o si `sends_out`
no está declarado en `envios-externos.json`. Una skill con `LICENSE` y sin `metadata.vendored` da
aviso: parece de terceros sin declarar. `--self-test` lo ve fallar con cada violación plantada.

**Actualizar** es repetir los pasos con el commit nuevo y reaplicar los parches marcados; nunca
`@latest` «para estar al día». Lo propio de diseño (qué sub-skills no traer, «delicado»):
`motores-de-diseno.md` §7.

_Rule version: 1.0 · 2026-10-31 — sub-ola 3.18 (AN-5): la parte general de `motores-de-diseno.md` §7
(2.29, SE-40) sale a una norma para toda skill de terceros, con su comprobación en `check_frontmatter.py`._
