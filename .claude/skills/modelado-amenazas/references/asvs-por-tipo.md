# ASVS 5.0.0 — nivel por tipo de proyecto, el subconjunto y cómo se cita

> **Fuente primaria.** OWASP Application Security Verification Standard **5.0.0**, release publicada el
> **2025-05-30** (https://github.com/OWASP/ASVS/releases/tag/v5.0.0_release, fecha de la API de GitHub).
> Ids y niveles: el CSV oficial de esa release, en `asvs-5.0.0.json` (sha256 en el propio fichero; lo
> genera `_archive/2026-10-20/medicion-2.25/gen_asvs_json.py`). Niveles y formato de cita: capítulo
> *What is the ASVS?* (`5.0/en/0x03-What-is-the-ASVS.md` en esa misma etiqueta). Leído el 2026-10-20.
> Licencia de ASVS: CC BY-SA 4.0; aquí no se copia el texto de ningún requisito, se cita su id.
>
> **Decisión del template** (sub-ola 2.25, item SE-D14, aprobado por el Usuario en bloque el 18-10 con
> la opción A del informe r3: L1 webs · L2 apps y bots · L2 + L3 de V8/V14/V16 en salud). ASVS no
> prescribe un nivel: dice que cada organización lo elige por el riesgo de la aplicación. Esto es lo que
> elegimos nosotros, y por qué.

## Lo que dice ASVS de sus niveles

- **345 requisitos en 17 capítulos** (70 de nivel 1 · 183 de nivel 2 · 92 de nivel 3, contados en el CSV).
  El propio estándar habla de «around 350» y de un reparto de ~20 % / ~50 % / ~30 %.
- **Los niveles se acumulan:** cumplir L2 es cumplir todos los de L1 y L2 (el estándar lo cifra en torno
  al 70 % de los requisitos).
- **L1** es el mínimo, la primera capa contra los ataques comunes. **L2** es donde *«most applications
  should be striving to achieve this level of security»*. **L3** es para quien tiene que demostrar el
  máximo: defensa en profundidad y controles caros.
- **Cómo se cita:** `v<versión>-<capítulo>.<sección>.<requisito>`, con la `v` minúscula delante, porque
  los números cambian entre versiones. Ejemplo del estándar: `v5.0.0-1.2.5`.

## El nivel por tipo de proyecto

`python3 .claude/scripts/gate_amenazas.py --tipo <tipo>` da el nivel y la lista; la autoprueba del script
comprueba que esta tabla dice lo mismo que él.

| Tipo | Qué proyectos | Nivel | Requisitos de nivel superior que se suman | Por qué |
|---|---|---|---|---|
| `web-marketing` | Web de captación o landing **sin cuentas de usuario**: el formulario reenvía a un CRM y no guardamos nada nosotros | L1 | — | No hay sesión ni datos guardados por nosotros que proteger; el formulario y el CRM son la frontera, y el modelo la mira. En cuanto guarde leads o tenga login, pasa a `app` |
| `app` | Aplicación con cuentas, datos personales guardados por nosotros o varios clientes (multi-tenant) | **L2** | — | Es el nivel que ASVS pide para «la mayoría de aplicaciones», y el que la guía de ciberseguridad del Usuario ya fijaba (`r2-ciberseguridad.md:71`) |
| `bot` | Chatbot o agente LLM con tools que leen o cambian datos del cliente | **L2** | v5.0.0-8.3.3 | 8.3.3 (L3) pide que el acceso se decida por los permisos **del sujeto de origen**, no por los de un intermediario: la tool del bot actúa con la cuenta de servicio y el modelo no debe poder elegir para quién. Es la regla de `patterns/stack/agente-tools.md` y de la skill `multi-tenant-context` (el tenant sale del contexto) escrita en ASVS. **No estaba en la propuesta del informe**: lo añade la 2.25 |
| `salud` | Datos de salud u otras categorías especiales del art. 9 RGPD | **L2** | v5.0.0-8.1.3 · v5.0.0-8.1.4 · v5.0.0-8.2.4 · v5.0.0-8.3.2 · v5.0.0-8.3.3 · v5.0.0-8.4.2 · v5.0.0-14.2.5 · v5.0.0-14.2.6 · v5.0.0-14.2.7 · v5.0.0-14.2.8 · v5.0.0-16.5.4 | Son **todos** los L3 de V8 (autorización), V14 (protección de datos) y V16 (registro y errores), los tres capítulos que propuso el informe: autorización por contexto, cambios de permiso inmediatos, admin con varias capas, mínimo de datos devueltos, retención por clasificación, metadatos fuera de los ficheros subidos y un manejador de errores de último recurso. Es la vara de **seguridad**: la normativa va aparte (abajo, «Salud y las demás categorías del art. 9») |
| `pentest` | El producto de pentest y ciberseguridad del Usuario | **L2** | — | Fijado en la guía del Usuario (`r2-ciberseguridad.md:71`, ASVS 5.0.0 objetivo L2) |

### Salud y las demás categorías del art. 9 (revisión de Priya, 20-10)

- **Este modelo no sustituye a nadie.** Con datos de **salud**, `sara-salud-datos` y sus 7 preguntas
  bloqueantes (P-1 a P-7), y `nora-ai-act-auditor` si hay IA. Con **otras categorías del art. 9**
  (biometría, afiliación sindical, ideología, vida sexual…), Sara no las cubre: van a
  `priya-privacy-auditor` (eje 1, con la letra del art. 9.2 que se invoca) y, si el tratamiento es a gran
  escala, a la evaluación de impacto del art. 35.3.b. `gate_amenazas.py --tipo salud` lo recuerda al
  imprimir la lista.
- **v5.0.0-14.2.7 clasifica; no autoriza a borrar.** Pide que lo innecesario se borre automáticamente o
  según calendario, pero la historia clínica tiene plazo legal: *«como mínimo, cinco años contados desde
  la fecha del alta de cada proceso asistencial»* (Ley 41/2002, art. 17.1, BOE-A-2002-22188, leído el
  20-10), más lo que diga la norma autonómica. El plazo lo fija esa ley, no el equipo (Sara, P-18).
- **Cifrado y TLS:** en salud conviene sumar `--con cripto,tls` (V11 y V12). El RGPD cita el cifrado y la
  seudonimización entre las medidas del art. 32.1.a.
- **`web-marketing` no quiere decir «sin datos personales».** Recoger un formulario y reenviarlo al CRM
  ya es tratarlos: en su modelo, `datos_personales: sí`, aunque el nivel ASVS sea L1.

**La alternativa que no se tomó:** L2 para todo (opción B del informe). Cambiarla es tocar `TIPOS` en
`scripts/gate_amenazas.py` y esta tabla, y la autoprueba avisa si se cambia una sola.

## El subconjunto: qué capítulos se miran

El ASVS no se lee entero en cada feature. En un Django + React de casa se miran siempre estos doce
capítulos, y los demás solo si el proyecto tiene esa pieza:

| Siempre | V1 Encoding and Sanitization · V2 Validation and Business Logic · V3 Web Frontend Security · V4 API and Web Service · V5 File Handling · V6 Authentication · V7 Session Management · V8 Authorization · V13 Configuration · V14 Data Protection · V15 Secure Coding and Architecture · V16 Security Logging and Error Handling |
|---|---|
| `--con jwt` | V9 Self-contained Tokens (JWT de DRF, tokens firmados) |
| `--con oauth` | V10 OAuth and OIDC (SSO, «entrar con Google») |
| `--con cripto` | V11 Cryptography (cifrado propio, más allá de TLS y del hash de contraseñas del framework) |
| `--con tls` | V12 Secure Communication (TLS que no termina el proxy, servicio a servicio) |
| `--con webrtc` | V17 WebRTC |

V15 tampoco estaba en la lista del informe (V1-V8, V13, V14, V16): entra porque V15.2 son las
**dependencias** (A03 del Top 10:2025, el gate G2) y V15.3 la programación defensiva (*mass assignment*,
devolver solo los campos necesarios), que tocan todos los proyectos.

Recuentos con los doce capítulos fijos (salida de `--tipo <tipo> --resumen`, 2026-10-20):

| Nivel | Requisitos | |
|---|---|---|
| L1 | 55 | |
| L2 | 187 | `bot`: 188 · `salud`: 198 |
| L2 `--con jwt,oauth` | 223 | |
| L3 | 254 | |

## Dónde se cita el id

| Dónde | Cómo |
|---|---|
| El modelo de amenazas | Columna ASVS de la tabla STRIDE: cada defensa que se mitiga lleva su `v5.0.0-x.y.z`. El gate rechaza un id que no existe y uno escrito sin la versión |
| El proyecto | `asvs_nivel` en el frontmatter del modelo y en `07-superficie.md` de `/arrancar` (tanda 4b.3) |
| Una spec de SpecKit | `Constraints` de `.specify/templates/spec-template.md`: nivel e ids que toca la feature |
| Un hallazgo de Sofía | Campo `asvs` del finding (`agents/sofia-pentester.md`): el requisito que el fallo incumple |

## Límite honesto

Citar un id no demuestra cumplirlo. El gate comprueba que el id **existe** y que hay una prueba
nombrada; si la defensa cumple el requisito lo dice quien prueba (Sofía, el test) y quien revisa. Un
nivel ASVS declarado no es una certificación: el capítulo de certificación del propio estándar
(`0x04-Assessment_and_Certification.md`) trata eso aparte.
