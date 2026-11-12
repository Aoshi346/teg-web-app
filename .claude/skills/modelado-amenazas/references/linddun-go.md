# LINDDUN GO — las 33 cartas, para el bloque de privacidad del modelo

> **Fuente:** baraja *LINDDUN GO*, versión **v241203** (PDF creado el 2024-12-03), DistriNet, KU Leuven,
> descargada el 2026-10-20 de https://downloads.linddun.org/linddun-go/default/latest/go.pdf
> (sha256 `0f8b8d6161ebe6e310402890fa50f75877dc1ad4d17bdaf204c82615d017d4f8`). Licencia
> **CC BY 4.0** (https://creativecommons.org/licenses/by/4.0/): los títulos son los de la baraja; la
> columna «Qué mira», un resumen nuestro en castellano de la descripción de cada carta.
> Las categorías: https://linddun.org/threat-types/ · cómo se juega: https://linddun.org/go-getting-started/
> (leídas el 2026-10-20).
>
> **Esta tabla es la fuente del gate.** `scripts/gate_amenazas.py` lee de aquí los códigos válidos: una
> carta que no está en esta tabla (un `L7`, un `DD9`) es una carta inventada y el modelo no pasa.

## Cómo se usa aquí (versión de una persona, no de taller)

LINDDUN GO está pensado para una sesión de equipo: se saca una carta, se mira si la amenaza es posible en
algún *hotspot* del sistema y se apunta; se acaba cuando todas las cartas se han discutido para todos los
hotspots que aplican (linddun.org, *GO – getting started*). En el modelo de una página se hace lo mismo
**recorriendo la tabla de abajo contra las fronteras del modelo**: el hotspot de cada carta dice en qué
frontera mirarla (entrada de datos, salida, almacenamiento, proceso). Se apuntan las que **sí** aplican, con
la amenaza concreta y la defensa decidida; una carta que no aplica no se escribe.

## Las siete categorías

| Sigla | Categoría | Qué es (linddun.org/threat-types) |
|---|---|---|
| L | Linking | Asociar datos o acciones para saber más de una persona o de un grupo |
| I | Identifying | Conocer la identidad de alguien por fugas, deducción o inferencia |
| Nr | Non-repudiation | Poder atribuir una afirmación a una persona |
| D | Detecting | Deducir que alguien participa a partir de la observación |
| DD | Data Disclosure | Recoger, guardar, procesar o compartir más datos personales de los necesarios |
| U | Unawareness & Unintervenability | Informar, implicar o dar control insuficiente a las personas sobre sus datos |
| Nc | Non-compliance | Apartarse de las buenas prácticas, estándares y leyes de seguridad y gestión de datos |

## Las cartas

| Código | Carta | Hotspot | Qué mira |
|---|---|---|---|
| L1 | LINKED USER REQUESTS | Entrada de usuario con datos personales | Peticiones enlazables porque llevan un identificador único |
| L2 | LINKABLE USER REQUESTS | Entrada de datos personales | Atributos que juntos forman un cuasi-identificador |
| L3 | LINKING THROUGH DISTINGUISHABLE PATTERNS | Entrada de usuario | Patrones en los (meta)datos que enlazan peticiones entre sí |
| L4 | LINKABLE DATASET | Almacenamiento / consulta | Datos guardados que se pueden enlazar a personas |
| L5 | PROFILING USERS | Proceso | Perfilar a los usuarios buscando patrones en sus datos |
| I1 | IDENTIFIED USER REQUESTS | Entrada de usuario con datos personales | La petición revela directamente quién es |
| I2 | IDENTIFIABLE USER REQUESTS | Entrada de usuario | Se puede inferir quién es por los datos de la petición |
| I3 | IDENTIFIABLE DATA FLOWS | Entrada de datos personales | Lo que se envía basta para identificar al usuario |
| I4 | IDENTIFIERS IN DATA REQUESTS | Entrada de usuario con datos personales | La comunicación lleva (cuasi-)identificadores |
| I5 | IDENTIFIABLE DATASET | Almacenamiento | Datos guardados que permiten identificar a personas |
| Nr1 | NON-REPUDIATION OF SERVICE USAGE | Entrada / salida de usuario | No poder negar haber usado el servicio (autenticación, accesos registrados) |
| Nr2 | NON-REPUDIATION OF SENDING | Entrada de usuario | No poder negar haber enviado un mensaje |
| Nr3 | NON-REPUDIATION OF RECEIPT | Salida hacia el usuario | No poder negar haber recibido un mensaje |
| Nr4 | NON-REPUDIATION OF STORAGE | Almacenamiento | Afirmaciones imposibles de negar sobre datos en almacenamiento no repudiable |
| Nr5 | NON-REPUDIATION OF HIDDEN DATA OR METADATA | Proceso | Metadatos ocultos de un documento que atan a alguien a él |
| D1 | DETECTABLE USERS | Flujos de salida | Saber que un usuario existe por la respuesta del sistema |
| D2 | DETECTABLE SERVICE USAGE | Entrada / salida de usuario | Detectar que alguien se comunica con el servicio |
| D3 | DETECTABLE EVENTS | Flujos de entrada / salida | Efectos o comunicaciones visibles que dispara un evento de la aplicación |
| D4 | DETECTABLE RECORDS | Consulta | Saber que un registro existe por los mensajes de estado («sin permiso» frente a «no existe») |
| DD1 | EXCESSIVELY SENSITIVE DATA COLLECTED | Entrada de datos personales | Recoger datos más sensibles o finos de lo necesario |
| DD2 | EXCESSIVE AMOUNT OF DATA COLLECTED | Entrada de datos personales | Recoger más datos de los necesarios |
| DD3 | UNNECESSARY DATA ANALYSIS | Proceso de datos personales | Analizar o enriquecer los datos más allá de lo que pide la función |
| DD4 | UNNECESSARY DATA RETENTION | Almacenamiento | Guardar los datos más tiempo del necesario |
| DD5 | OVEREXPOSURE OF PERSONAL DATA | Salida de datos personales | Compartir con más servicios o terceros de los necesarios |
| U1 | INSUFFICIENT TRANSPARENCY | Entrada de usuario con datos personales | La persona no sabe bien qué se recoge ni para qué |
| U2 | INSUFFICIENT INFORMATION WHEN SHARING DATA OF OTHERS | Entrada de datos personales | Quien comparte datos de otros no sabe qué se hará con ellos |
| U3 | INSUFFICIENT PRIVACY CONTROLS | Entrada de usuario | Pocos controles para gestionar sus preferencias |
| U4 | INSUFFICIENT ACCESS | Almacenamiento | La persona no puede acceder a sus datos |
| U5 | INSUFFICIENT RECTIFICATION OR ERASURE | Consulta | La persona no puede corregir ni borrar sus datos |
| Nc1 | NON-COMPLIANCE OF PROCESSING WITH APPLICABLE REGULATIONS | Proceso de datos personales | El tratamiento no cumple la normativa aplicable |
| Nc2 | NON-ADHERENCE TO PRIVACY STANDARDS | Proceso de datos personales | No sigue los estándares y buenas prácticas de privacidad |
| Nc3 | IMPROPER DATA LIFECYCLE MANAGEMENT | Proceso | Los datos no se gestionan bien durante todo su ciclo de vida |
| Nc4 | INSUFFICIENT SECURITY OF PROCESSING | Proceso | Las medidas de seguridad no siguen las buenas prácticas de gestión de riesgo |

**33 cartas** (5 L · 5 I · 5 Nr · 4 D · 5 DD · 5 U · 4 Nc), como dice linddun.org («33 threat type
cards, which come in 7 suits»).

## Dónde se cruza con lo que ya hay en casa

| Carta | Ya lo cubre | Lo que el modelo añade |
|---|---|---|
| D4 | `patterns/stack/agente-mcp-comercio.md` §4: ajeno, inexistente o basura dan la **misma** respuesta | Escrito como amenaza de privacidad, no solo de seguridad: un «no tienes permiso» confirma que existe |
| DD4 · Nc3 | `/arrancar` fase 4.2 (cuánto se conserva y quién lo borra) | La retención por tabla, en la frontera de almacenamiento |
| U5 | `priya-privacy-auditor` eje 4 (borrado downstream: logs, embeddings) | Se decide en diseño, no se descubre en la auditoría |
| L5 · U3 | `priya-privacy-auditor` eje 8 (RGPD 21.2-21.3: la baja corta también el perfilado) | La oposición al perfilado como control de la frontera de proceso |
| U1 | Priya ejes 1 y 7 (información y consentimiento) · `nora-ai-act-auditor` (aviso de IA, art. 50) | Quién informa y dónde, decidido en la frontera de entrada |
| U4 | Priya eje 2 (derechos self-service) | El acceso a sus datos, por la frontera de almacenamiento |
| DD5 | Priya eje 5 (el proveedor de LLM no transfiere la responsabilidad) | Cada salida hacia un tercero, con su contrato de encargado (RGPD art. 28) |
| Nc1 | Priya eje 1 (base legal por dato) | Responsable y encargado escritos: contrato del art. 28 y registro del art. 30 |

**Un dato seudonimizado sigue siendo personal** (RGPD art. 4.5 y considerando 26): un id de
conversación que enlaza las llamadas de alguien (L1) necesita base, plazo y borrado igual que el nombre.
