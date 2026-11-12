# UI/UX Pro Max — base de datos de consulta (terceros, sin red)

> Vendorizada de nextlevelbuilder/ui-ux-pro-max-skill@a38d04c3d5c298c851dbe5e6ee1965ee3de42cb5
> (tag v2.15.0, carpeta `.claude/skills/ui-ux-pro-max`) el 31-10-2026. Licencia **MIT**, leída en el
> `LICENSE` de ese commit (copia aquí). Sin parches en el código. Se quitaron `scripts/tests/`,
> `scripts/validate_data.py` (validador del autor) y los tres ficheros de más de 400 KB
> (`data/google-fonts.csv`, `google-font-licenses.json`, `phosphor-icons-upstream.json`): el dominio
> `google-fonts` del buscador no está; los demás, sí. Se recuperan del commit si hacen falta. El
> `SKILL.md` del autor queda como `UPSTREAM-SKILL.md` (sus rutas `~/.claude/skills/…` no valen aquí).
> Sub-ola 3.66, UX-D2.

**Qué es:** CSV con 79 estilos, 192 paletas por tipo de producto, 74 parejas tipográficas, 119 guías
de UX, iconos, gráficas y reglas por stack, más un buscador BM25 (`scripts/search.py`). **No sale a
internet** (leído entero el 31-10: solo `argparse`, `json`, `csv` y los módulos de al lado).

**Para qué, aquí:** consulta en las fases 0-1 (`rules/motores-de-diseno.md` Parte F). Pesa en el
**escalón 8** (§1): es una sugerencia ajena. Manda `design-system.md` del proyecto; lo que se tome de
aquí se escribe allí, con su porqué.

```bash
R=.claude/resources/referencias-diseno/terceros/ui-ux-pro-max/scripts
python3 $R/search.py "fintech dashboard trust" --domain color -n 5
python3 $R/search.py "saas onboarding" --domain ux
python3 $R/search.py "editorial serif" --domain typography --json
```

**Nunca `--persist`** ni `--design-system --persist`: crea `design-system/<proyecto>/MASTER.md`, un
segundo sistema de diseño que compite con `design-system.md` (§1, escalón 4). Y en las consultas no se
mete nada privado del proyecto: aunque no salga de la máquina, queda en el historial.

Los generadores que sí mandan la marca fuera (logo, CIP, iconos) son otra pieza:
`.claude/skills/ui-ux-pro-max-design/`, a mano y con confirmación en cada envío.
