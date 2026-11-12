# Candado de datos reales — el proceso no arranca tocando datos de terceros sin permiso

> **Cuándo aplicar:** en todo proyecto que vaya a tratar datos **de terceros** —los de un cliente (los
> fiscales de una gestoría), los de sus pacientes, los de sus trabajadores— y que hoy se construye
> con datos sintéticos o anonimizados mientras el permiso (contrato de encargo, DPA, EIPD) no está
> firmado. Al conectar la primera integración con credenciales reales, y antes de poner la variable
> que la abre.
>
> **NO aplicar:** para decidir si el tratamiento es lícito o qué dice el contrato (eso es de un DPD o
> un abogado: `sara-salud-datos`, `priya-privacy-auditor`, skill `cumplimiento-salud`) · para el
> gate documental de salud, que comprueba que las ocho piezas existen y están firmadas
> (`scripts/gate_datos_salud.py`; el candado puede tener a ese gate como una de sus condiciones) ·
> para datos de prueba que el propio producto genera.
>
> **Relacionado:** `templates/candado-datos-reales/` (las piezas que se copian) ·
> `scripts/gate_datos_reales.py` (el gate y su `--autoprueba`) · `rules/backend-seguridad.md` ·
> `rules/security.md` §Un deny no se aplica siempre · `rules/layer-decision.md`.

## La regla (una frase)

**Que «sin permiso firmado no se tocan datos reales» no lo diga un párrafo: Django no arranca con una
integración en modo real si una persona no ha abierto el candado con su firma.**

## Por qué un mecanismo y no una norma

Es la norma más fácil de incumplir sin querer —«solo miro un Excel real para entender el formato»,
«pongo la variable a 1 un momento para probar»—, porque incumplirla no duele hasta que es tarde y
entonces no se deshace. `rules/layer-decision.md`, pregunta 1: si el peor caso es caro e
irreversible, la norma baja a un gate con exit ≠ 0. Cosechado de `accounting_AMC` (invariante 2,
SCRUM-72: *«Miller no accede a datos reales de AMC hasta que el DPA esté firmado»*), donde funciona
desde agosto de 2026.

## Las dos mitades, que es lo que se confunde

| Mitad | Qué gobierna | Dónde vive | En producción |
|---|---|---|---|
| **El estado** — `.claude/estado-datos-reales.json` + `scripts/gate_datos_reales.py` | Si una **persona** tiene derecho a poner `<PROYECTO>_DATOS_REALES=1` | El harness. Lo rellena una persona con su evidencia; ningún agente lo edita | **No existe** |
| **El candado** — `candado.py`, llamado desde un `ready()` | Si **este proceso** puede arrancar con una integración en `real` | El código de la app | Es lo único que hay |

En desarrollo están las dos y se cruzan: con la variable a 1 y el estado en rojo, el candado tampoco
arranca. Es justo donde se comete el error.

## Las piezas (`templates/candado-datos-reales/`)

1. **`candado.py`** → `backend/core/seguridad/candado.py`. Se rellenan `VARIABLE`, `MODOS` (las
   variables que ponen cada integración en `real`), `REQUISITOS_CON_DATOS_REALES` y la profundidad
   hasta la raíz. `comprobar_candado()` lanza `ImproperlyConfigured` si:
   - una integración está en `real` con la variable a 0;
   - la variable está a 1 y el estado tiene condiciones pendientes (una condición con `ok: true` sin
     quién, cuándo y evidencia cuenta como pendiente: es un fichero editado a mano);
   - la variable está a 1 y falta un requisito (en AMC, una clave de cifrado propia que no salga de
     `SECRET_KEY`).
   Sin estado (producción) manda el entorno, que es la única fuente que hay allí.
2. **El `ready()`** de una app transversal que esté en `INSTALLED_APPS`:
   ```python
   class NucleoConfig(AppConfig):
       name = "core"

       def ready(self) -> None:
           from core.seguridad.candado import comprobar_candado
           comprobar_candado()
   ```
   `ready()` corre en **todo** arranque —runserver, gunicorn, celery, manage.py, pytest—. Un system
   check no basta: gunicorn no los ejecuta.
3. **`test_candado.py`**, junto al candado. Si pasa a verde solo, alguien lo desarmó. Sus 8 casos
   cazan los 5 mutantes de la medición de la 2.29 (cada mecanismo apagado pone uno en rojo).
4. **`estado-datos-reales.json`** → `.claude/`. Cuatro condiciones de partida (encargo firmado,
   subencargados con región, acceso mínimo con evidencia, retención pactada); cada proyecto añade
   las suyas. Cada una se cierra con `ok`, `quien`, `fecha` y `evidencia` (una ruta del repo o un
   enlace).
5. **El `deny`**: `"Edit(.claude/estado-datos-reales.json)"` en `.claude/settings.json`. Un
   `Write(...)` **no se consulta nunca** (`claude-code-referencia` §8.4): solo `Edit` y `Read`. Y el
   `deny` es la segunda capa, no la primera (`security.md` §Un deny no se aplica siempre): donde de
   verdad importe, un hook PreToolUse que bloquee la ruta.
6. **`estado-datos-reales.sh`** → `.claude/hooks/`, en el SessionStart: enseña el estado al abrir la
   sesión (registrarlo toca `settings.json`: pide aprobación, `governance.md` §2).
7. **El paso de CI que demuestra que bloquea**, en cada PR. Si deja de fallar, alguien lo desarmó:
   ```yaml
   - name: Demostrar que el candado de datos reales bloquea
     run: |
       if CRM_MODE=real MIPROYECTO_DATOS_REALES=0 python manage.py check 2>/dev/null; then
         echo "✗ El candado NO bloqueó: manage.py check arrancó en modo real con el candado cerrado."
         exit 1
       fi
   ```
   El gate del estado va en el CI **informativo** (`|| true`): en rojo es lo normal hasta que se
   firme, y bloquear por eso pararía el proyecto durante meses. Lo que bloquea es arrancar en real.

Las puertas por las que entran datos **a mano** (una subida de ficheros, un import) no se bloquean
—el sistema tiene que poder demostrarse con datos de prueba—: miran `hay_datos_reales()`, avisan en
pantalla y dejan traza. En AMC fue la puerta que el candado no miraba: protegía los cuatro conectores
y dejaba fuera `/subir`, la pantalla más usada (PRIYA-003).

## Comprobación

```bash
python3 .claude/scripts/gate_datos_reales.py                 # el estado: 0 se puede · 1 no · 2 ilegible
python3 .claude/scripts/gate_datos_reales.py . --completo    # + el estado protegido y el candado cableado
python3 .claude/scripts/gate_datos_reales.py . --demostrar --python .venv/bin/python   # + arranca y se niega
python3 .claude/scripts/gate_datos_reales.py --autoprueba --python <venv con Django>   # el gate se ve fallar
```

`--demostrar` es lo único que caza un candado cuya app **no está en `INSTALLED_APPS`**: el `ready()`
existe, lo estático lo ve llamado, y no corre nunca. Medido en la autoprueba (34/34, sub-ola 2.29).

## Lo que se encontró al cosecharlo

`accounting_AMC` (medido el 2026-10-21 en solo lectura): `gate_datos_reales.py` dice que el estado
*«está en el deny del settings»*, y **no lo está** —ni hoy ni en el commit que lo creó (`74a85d5`)—:
el `deny` tiene `Edit(.claude/settings.json)` y `Write(.claude/settings.json)`, nada sobre
`estado-dpa.json`. Cualquier agente puede ponerlo en verde. `gate_datos_reales.py --completo` lo da
como `CANDADO-ESTADO-SIN-PROTEGER`. Va a su `to_apply` cuando se pruebe el `deny` con su sesión.

## Anti-patterns

- ❌ La norma solo en `CLAUDE.md` o en una rule: se incumple sin querer y no se deshace.
- ❌ El candado como system check en vez de en `ready()`: gunicorn arranca sin pasar por él.
- ❌ Poner la variable a 1 «para probar» con el gate en rojo: es el error que el cruce existe para cazar.
- ❌ Un `ok: true` sin quién, cuándo y evidencia, o firmado por un agente.
- ❌ Proteger el estado con `Write(...)`: no se consulta nunca.
- ❌ Bloquear el CI entero por el estado en rojo: lo que se bloquea es arrancar en real.
- ❌ Llamar «datos de prueba» a una copia de producción: si es real, el candado tiene que estar abierto.
