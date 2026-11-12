# Ficha de pantalla — `<nombre>`

> Una por pantalla del inventario. Es la parte que más mejora el resultado: sin ella, el agente
> improvisa el contenido y las conversiones salen débiles. Lo que no se sepa va como
> `[PENDIENTE: …]`, **nunca inventado**.

| Campo | |
|---|---|
| **Objetivo** | qué tiene que conseguir esta pantalla, en una frase |
| **Usuario** | quién la ve, con qué contexto |
| **De dónde viene** | canal o pantalla anterior |
| **Qué sabe al llegar** | y qué NO sabe todavía |
| **Acción principal** | una sola |
| **Acción secundaria** | opcional; nunca compite en peso |
| **Mensaje principal** | la frase que debe entender aunque no lea nada más |
| **Quién la diseña** | 🤖 agente · 🤝 a medias · ✍️ el Usuario |

### Intención visual

Sin esto, la pantalla sale correcta y muerta: el agente sabe qué tiene que hacer y no qué tiene que
**sentir** quien la ve. Se hereda del proyecto salvo que aquí se diga otra cosa.

| Campo | |
|---|---|
| **Qué debe sentir en 3 segundos** | una frase; si no sabes escribirla, la pantalla no está decidida |
| **Dirección de arte** | el nombre, o `hereda del proyecto` (§0b de `design-system.md`) |
| **Referencia** | URL o fichero del corpus + **qué se toma exactamente** de ella |
| **Nivel de movimiento** | 0/1/2 + los efectos con nombre que aplican AQUÍ |
| **Tratamiento de imagen** | cuál de §4e, y **de dónde sale la foto** |
| **Densidad** | según el perfil; `producto-panel` va denso y `web-cliente`, aireado |
| **Bloque de la estructura** | solo `web-cliente`: qué hueco ocupa en el recorrido (`patterns/diseno/estructura-de-pagina.md`) |

## Contenido obligatorio
- …

## Objeciones que debe resolver
- «…»

## Datos de entrada
| Campo | Tipo | Obligatorio | Validación |
|---|---|---|---|

## Estado de éxito
qué pasa exactamente cuando sale bien (y a dónde va)

## Estados
```
[ ] con datos   [ ] vacío      [ ] cargando      [ ] error
[ ] éxito       [ ] desactivado [ ] seleccionado [ ] completado
[ ] sin permisos [ ] sin conexión [ ] caducado   [ ] móvil
```
Los que no apliquen: **N/A con su razón**. El silencio es un olvido, no una decisión.

## Métricas
| De → a | Qué mide |
|---|---|
