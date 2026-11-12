# `patterns/diseno/` — el canon de gusto: DECLARADO, y nunca bloquea

> **Cuándo aplicar:** cuando hay que **decidir cómo se ve algo** y no basta con que sea correcto:
> la dirección de arte de una marca (`skills/marca`), el boceto de una pantalla
> (`disenar-pantalla`), la revisión de una web de cliente, o la conversación de por qué un diseño
> «funciona pero parece de plantilla». Da la **doctrina**: qué técnica existe, cuándo se usa, qué
> cuesta y qué NO arregla.
>
> **NO aplicar:** para **cómo se declara** el sistema de diseño de un proyecto —dónde viven los
> tokens, qué preguntas responde el documento fundacional, qué comprueba el linter— que es
> `patterns/stack/frontend-design-system.md` y manda él · para **el molde de ficheros** de una
> pantalla nueva (`patterns/stack/frontend-nueva-pantalla.md`) · para **auditar** lo ya construido
> (`vera-art-director`, `aitor-a11y-auditor`, `rules/qa-loop.md`) · para el **orden de las fases**
> de diseño (`rules/motores-de-diseno.md` Parte F) · para el **texto** (`skills/escribir-copy`).
>
> **Relacionado:** `resources/referencias-diseno/` (la evidencia que esto cita) ·
> `patterns/README.md` §1 (la regla de dominancia que esta carpeta **no** cumple, y el precedente
> que la autoriza igual) · `patterns/stack/frontend-design-system.md` · `rules/motores-de-diseno.md` Parte F ·
> `agents/shared/red-flags.sh` · el skill oficial `frontend-design`.

---

## 1. Qué es esto, en una frase

> **El tercer cuerpo del canon: hermano de `patterns/stack/`, pero DECLARADO en vez de medido, y
> sin ningún mecanismo que bloquee.**

El canon de este repo tenía dos mitades y las dos son de **corrección**: `catalog.yaml` mide cómo
se escribe el código aquí, y `ownership.yaml` declara quién manda en cada carpeta. Ninguna de las
dos sabe responder *«¿esto se ve bien?»*, y por eso no lo respondía nadie.

Esta carpeta responde a esa pregunta. Y lo hace sabiendo que **el gusto no se mide como se mide una
convención de código**.

## 2. Por qué está permitido que no esté medido — el precedente

`patterns/README.md` §Reglas duras, **regla 1**, es explícito: **≥85 % de dominancia medida** o no
hay patrón. Diez
diseños de un solo equipo no son eso, y fingir lo contrario sería exactamente el fallo que este
repo documenta una y otra vez.

El precedente que autoriza un cuerpo declarado sin romper la regla está escrito dos líneas más
abajo, en la misma regla 1 (**GAP-1**): las diez reglas `ag-*` están medidas en **dos
repos y los dos son nuestros**, así que *«eso no es dominancia; puede ser nuestra manera de
escribir»*, y por eso **siguen todas en `sombra`**.

Aquí es el mismo trato, un escalón más abajo:

| | `catalog.yaml` | `ownership.yaml` | **`diseno/`** (esto) |
|---|---|---|---|
| De dónde sale | Se **mide** (dominancia) | Se **declara**, con `source:` a una rule | Se **declara**, citando el corpus |
| Qué responde | ¿así se escribe aquí? | ¿quién manda en esta carpeta? | **¿por qué esto se ve así?** |
| Quién lo consume | Rita + el hook | `ownership_check.py` | Personas, `skills/marca`, `disenar-pantalla`, `vera-art-director` |
| Si lo ignoras | El hook bloquea (patrones `activo`) | `ownership_check.py` sale con 1 | **Nada. No pasa nada** |

## 3. La frontera mecánica — quién NO lee esto (medido, no supuesto)

Es la parte que hay que tener clara antes de escribir aquí una línea más, porque determina qué
clase de documento es:

```bash
grep -c "patterns/diseno\|diseno/" .claude/agents/rita-pattern-keeper.md   # → 0
grep -c "diseno"                    .claude/hooks/pattern-check.sh          # → 0
```

- **Rita no lo lee.** Su canon es `catalog.yaml` + los docs de patrón + el baseline
  (`agents/rita-pattern-keeper.md:13`), y su contrato exige **≥2 precedentes `file:line` del propio
  repo o silencio**. Un documento de gusto no le da eso.
- **`hooks/pattern-check.sh` no lo grepea.** Su bucle carga `patterns/stack/pattern_check_<capa>.py`
  (`hooks/pattern-check.sh:68`) y nada más. Esta carpeta no tiene comprobador y no va a tenerlo.
- **Lo que sí puede bloquear algún día** son las 12 semillas de
  `resources/referencias-diseno/anti-patrones.yaml` (`GD-01`…`GD-14`), que son **otra cosa**: cada
  una señala un fichero y una línea donde el defecto ocurrió, y **todas nacen en `sombra`**.
  Doctrina y gate viven separados a propósito.

> **La consecuencia, dicha entera:** lo que impide que salga un diseño malo **no es este
> documento**. Es el gate determinista cuando se promueva alguna de sus semillas, el auditor que
> mira la pantalla, y la persona que decide. Esto solo hace que la decisión se tome **sabiendo**.

## 4. Los once ficheros

| Fichero | Responde a |
|---|---|
| `README.md` | ⬅️ estás aquí: qué es, qué no bloquea, cómo se cita |
| **`tipografia.md`** | el titular display, los emparejamientos por sector, la escala fluida, el eyebrow |
| **`composicion.md`** | rejillas, orbes, marcas de agua, formas orgánicas, ritmo vertical, asimetría |
| **`textura-y-profundidad.md`** | la capa semántica de tokens, sombras teñidas, easing, grano, borde vs sombra |
| `movimiento.md` | qué se mueve, cuándo, y el motor de revelado que no deja contenido invisible |
| `imagen.md` | fotografía, overlays teñidos, tratamiento y qué hacer cuando no hay fotos |
| `estructura-de-pagina.md` | el orden de las secciones y qué hace cada una |
| `demo-de-producto.md` | enseñar el producto funcionando en vez de ilustrarlo |
| `catalogo-direcciones.md` | las direcciones de arte con nombre, y por qué se generan varias |
| `catalogo-diseno.yaml` | el índice legible por máquina: técnica → ficheros → anclas |
| `perfiles.yaml` | `web-cliente` vs `producto-panel`: qué cambia entre ellos |

⚠️ Medido el 2026-09-18: existen **10 de los 11**; falta `catalogo-direcciones.md`. Se lista igual porque el índice describe el cuerpo completo, no el estado de hoy — pero si sigue faltando en la próxima revisión, o se escribe o se quita de esta tabla.

> **Por qué `patterns/README.md` se cita por SECCIÓN y el corpus por LÍNEA.** No es incoherencia:
> el corpus está **congelado** —su propia regla de uso dice que no se edita— así que una línea suya
> es una dirección estable. `patterns/README.md` es un documento **vivo**: mientras se escribía esta
> carpeta, GAP-1 se movió de la línea 50 a la 57 porque alguien le añadió la columna de este tercer
> cuerpo. Una cita por línea a un fichero vivo nace caducando.


## 5. Cómo se cita el corpus

La evidencia vive en **`resources/referencias-diseno/`** y **se cita con `fichero:línea`**, en ruta
relativa desde `.claude/`:

```
resources/referencias-diseno/bien/kalinayoga-v6.html:55-59
```

Tres reglas, y las tres vienen del propio corpus (`resources/referencias-diseno/README.md`):

1. **Nunca «como hace Stripe hoy».** Una afirmación sobre una web viva no es verificable y caduca
   sin avisar. Si no se puede citar un fichero congelado, se escribe como **criterio**, no como
   evidencia.
2. **Se cita por lo que la referencia hace bien, no por lo que es.** El corpus tiene defectos
   reales listados uno a uno en `INDEX.json → defectos_conocidos`: se citan por su tipografía, su
   composición y su movimiento, **nunca por su accesibilidad** — 6 de sus 9 «buenos» quitan el
   `outline` sin reponer el foco (`anti-patrones.yaml` GD-12).
3. **El corpus no se edita.** Es evidencia: se añade con procedencia, y no se corrige un fichero
   para que quede mejor.

**Y las citas se comprueban solas**, que es lo que separa esto de una bibliografía decorativa:

```bash
python3 .claude/scripts/verificar_precedentes.py    # falla si una cita deja de resolver
```

⚠️ Los otros dos comprobadores que `patterns/README.md` declara para este cuerpo —
`scripts/gate_diseno.py` (las 12 semillas `GD-*`) y `scripts/corpus_lint.py` (caducidad y
concentración)— **todavía no existen en disco** (medido el 2026-09-18). Mientras no existan, lo
único que vigila esta carpeta es `verificar_precedentes.py` y quien lea.

## 6. Cuándo se retira una técnica de aquí

Un cuerpo declarado que solo crece acaba como acaban los `CLAUDE.md`: engordando hasta que nadie lo
lee. Una ficha sale de esta carpeta cuando ocurre cualquiera de estas cuatro cosas, **y se anota
por qué**:

| Sale cuando… | Porque |
|---|---|
| Su única ancla desaparece del corpus (se retiró la entrada) | Sin evidencia es una opinión con formato de canon |
| El skill oficial `frontend-design` la lista como señal de página generada **y** no tenemos un motivo escrito para contradecirlo | Está calibrado contra una muestra mayor que la nuestra (§`tipografia.md`) |
| Se mide y resulta que era gusto de un cliente, no técnica | Una dirección de arte no es doctrina |
| Lleva dos revisiones sin que ninguna skill ni ningún auditor la cite | No se está usando, y ocupa atención |

La revisión se engancha donde ya se revisa lo demás: `rules/self-improvement-loop.md` §5 (la fase
de poda). Y el corpus tiene su propia caducidad declarada: `caducidad_revision: 2027-09-18` en cada
entrada de `INDEX.json`.

## 7. Límites honestos

Se dicen antes de que nadie se confíe, porque son severos:

1. **Diez diseños de un solo equipo no son dominancia; puede ser simplemente nuestro gusto.** Es el
   mismo límite que GAP-1 declara para las reglas `ag-*`, y no se arregla escribiendo mejor: se
   arregla midiendo en repos ajenos, y no lo hemos hecho.
2. **Todo lo de aquí es criterio salvo lo que lleve un número medido al lado.** Cuando hay medición
   se escribe con su comando; cuando no, se dice «criterio».
3. **Esto no hace que un diseño salga bien.** Hace que las decisiones se tomen con vocabulario y
   con precedente. Un diseño puede cumplir las once fichas y seguir siendo mediocre — el gate
   detecta lo roto, no lo mediocre (`rules/refactor-progresivo.md` §A0 dice lo mismo del código).
4. **La accesibilidad NO está cubierta por este cuerpo** y hay que decirlo alto: el corpus falla en
   ella. Eso lo miran `aitor-a11y-auditor` y GD-12, no estas fichas.
5. **Hay un cabo suelto declarado:** `resources/referencias-diseno/README.md` dice que el corpus
   *«está declarado en `patterns/ownership.yaml`»*, y hoy `grep -n "diseno" patterns/ownership.yaml`
   no devuelve nada. O se declara o se corrige esa frase; mientras tanto, esta carpeta **no tiene
   contrato de propiedad**.

## 8. Chequeo a 3 anchos — destilado de TasteSkill (sub-ola 3.65, UX-D8)

TasteSkill (`Leonxlnx/taste-skill`, MIT) **no se instala**: reparte la dirección por sorteo y aquí la
rankea el Usuario (`rules/motores-de-diseno.md` §1, escalón 1, y §8). De ella se toma lo que no choca
con eso: **antes de enseñar una pantalla o una página, se mira a tres anchos y se corrige lo peor.**

```bash
for w in 1440 768 390; do
  python3 .claude/scripts/screenshot.py "http://127.0.0.1:<PUERTO>/<ruta>" /tmp/<pagina>-$w.png $w 900 3000
done
```

1. **Lo que solo tiene este cliente**, escrito antes de mirar: dos o tres cosas del brief que no
   valdrían para otra web. Si la captura no enseña ninguna, ya hay hallazgo (es la frase que pide
   `rules/motores-de-diseno.md` §2 para cada rasgo del «look de IA»).
2. **Mirar las tres capturas**, no solo la de escritorio: scroll horizontal, texto cortado o
   montado, la llamada a la acción fuera de la primera pantalla a 390, imágenes deformadas.
3. **Los 3 peores, y se arreglan.** Hasta **3 rondas**; si a la tercera sigue habiendo un fallo de
   los del punto 2, se para y se dice. No se pule lo que no está en la lista.

Es **criterio** (escalón 7): no bloquea. Lo que se mide a esos mismos anchos lo dice su medidor —axe
en Aitor y `contraste.py`, que llegan en la sub-ola 3.64; el desbordamiento lo ve `gate_diseno.py`
cuando 3.67 le dé `--dom`—, y sobre lo que mide gana el medidor. **Sin medir:** el «estudio de 247
webs» de TasteSkill (`references/research.md` de su repo; no se leyó) y si su bucle de corrección
mejora algo frente al nuestro (era la cuarta variante de X-13, laboratorio saltado el 31-10).

---

## Anti-patterns

- ❌ Tratar una ficha de aquí como un patrón `activo` y bloquear un PR con ella → no hay
  comprobador, no hay dominancia, y no es su trabajo (§3).
- ❌ Escribir una técnica **sin ancla `fichero:línea`** y sin marcarla como criterio → un canon con
  citas inventadas es peor que no tener canon.
- ❌ Citar una web viva («como la home de X») en vez del corpus congelado → no es verificable y
  caduca sin avisar (§5).
- ❌ Copiar una referencia **entera**, defectos incluidos, porque está en `bien/` → para eso existe
  la columna `defectos_conocidos`.
- ❌ Mover aquí una regla que **sí** se puede comprobar con un parser → su sitio es
  `anti-patrones.yaml`, donde puede llegar a bloquear.
- ❌ Pedirle a Rita que revise una pantalla contra esta carpeta → no la lee, y su contrato le
  obliga a callar sin precedentes de código (§3).
- ❌ Dejar que esta carpeta crezca sin retirar nada (§6).
- ❌ Enseñar una página mirada solo a 1440 → el chequeo es a tres anchos (§8).
- ❌ Presentar el corpus como dominancia medida → es canon declarado, precedente GAP-1 (§2).

---

_Versión 1.1 · 2026-10-31 · §8 chequeo a 3 anchos, destilado de TasteSkill (3.65, UX-D8). 1.0 · 2026-09-18 · Ola 2. Nace de la medición de que los diseños de esta casa salían
genéricos y de que la causa era estructural: `patterns/README.md` §1 solo sabe fijar lo que ya se
hacía, y lo que ya se hacía nunca fue tipografía atrevida._
