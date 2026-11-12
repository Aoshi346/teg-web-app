# `templates/diseno/` — piezas pegables, no doctrina

La doctrina está en `patterns/diseno/`. Aquí está **el código que tardarías media hora en escribir
bien**, ya escrito y ya probado, para que nadie lo improvise a las 11 de la noche.

| Fichero | Qué resuelve | Precedente |
|---|---|---|
| `motor-reveal.html` | El motor de entrada por defecto, **con la regla dura dentro**: el `opacity:0` cuelga de `body.js-ready`, así que sin JS el contenido se ve | `bien/elevaiti-v53.html:92-94` |
| `grano.html` | Textura de grano con `feTurbulence` en data-uri: cero peticiones | 3 diseños del corpus |
| `demos/chat-typing.html` | T22 · enseñar el producto conversando | `bien/elevaiti-v5.html:756` — **patrón** |
| `demos/terminal-escribiendo.html` | T22 · para producto de línea de comandos | ⚠️ **ninguno: es una propuesta** |
| `demos/calculadora-roi.html` | T22 · convierte tu promesa en SU número | `bien/elevaiti-v5.html:2366` — **patrón** |
| `demos/tabla-comparativa.html` | T22 · responde «¿en qué se diferencia de lo que hago hoy?» | `bien/consultorpro.html:1773` — **anécdota** (la única del corpus) |

> **Los cuatro arquetipos NO valen lo mismo, y la columna de la derecha es la que lo dice.** Dos
> tienen precedente real en el corpus; la tabla comparativa tiene uno solo (anécdota); y la terminal
> **no tiene ninguno** — cero coincidencias de `typewriter` en los diez diseños. Se incluye porque
> el arquetipo es conocido, pero no se puede presentar como «así lo hacemos aquí».
>
> Aquí se citaba además `elevaiti-v7:1801` como calculadora: **es una tarjeta con una cifra**, y v7
> tiene cero `type="range"`. El `RANKING.csv` se la atribuye a v7 y el fichero dice otra cosa.
> Corregido el 2026-09-18 midiendo, no recordando.

## Lo que comparten las seis, y no es negociable

- **Cero red.** Ni CDN, ni fuentes remotas, ni `fetch`. Abren desde disco.
- **Se ven sin JS.** El contenido está en el HTML; el JS solo lo anima. Comprobado con el navegador
  a `java_script_enabled=False`: **4 de 4 elementos visibles y el texto completo**, contra 3 de 4
  a mitad de la animación cuando el JS sí corre.
- **`prefers-reduced-motion` respetado en CSS y en JS** donde hay animación. En `calculadora-roi` y
  `tabla-comparativa` no hay ninguna, y por eso no lo llevan: ponerlo sería ruido.
- **Accesibles de serie**: `aria-live` donde el contenido cambia solo, `<table>` de verdad donde hay
  una tabla, controles que son `<input>` y no `<div>`.

## Cómo se usan

Se **copian y se adaptan**, no se enlazan: son plantillas, no una librería. Al pegarlas, lo primero
que se cambia son los tokens del `:root` por los del proyecto (`design-system.md` §2, §3, §4c).

Y la parte que no viene en el fichero: **el contenido tiene que ser real**. Una demo de chat con
una conversación inventada es una ilustración con más pasos. La del ejemplo es de una peluquería
porque el precedente era un negocio real; la tuya tiene que ser del negocio del cliente
(`patterns/diseno/imagen.md` §activos reales).

## Anti-patterns

- ❌ Declarar `opacity:0` en el elemento en vez de bajo `body.js-ready` → si el JS falla, la página
  no se ve. Pasó de verdad y está guardado: `mal/attomo-digital.html:1006` + `:1441`.
- ❌ Un loader que retrasa el contenido «para que se vea la animación» → el corpus tiene dos, de
  3,2 s y de 1,6 s, y los dos son deuda.
- ❌ Una tabla comparativa donde el rival pierde en todo → no se la cree nadie y se lleva por
  delante la credibilidad del resto de la página.
- ❌ Usar la demo de terminal para un producto con interfaz gráfica → es disfraz.
