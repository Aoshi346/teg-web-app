# Probar como cliente sin ensuciar la cola real

> **Para los auditores del `/qa-loop`** (y cualquiera que pruebe una web pública, un widget o un bot
> en un entorno con datos reales). Una línea al principio del guion y se acabó el problema.
> Cosechado de elvion (AN-25, sub-ola 3.20), donde dos auditoras lo sufrieron en la misma ronda.

## El problema

La única forma de probar el recorrido público **como un cliente de verdad** crea registros de verdad:
peticiones en la cola de un asesor, pedidos pendientes de cobro, conversaciones con el nombre de
prueba puesto. En el caso de origen, una mañana de QA dejó **siete** filas reales sin marcar; ninguna
llegó a una persona por pura suerte (el canal de aviso estaba desconectado).

## La salida: la clave de pruebas, puesta ANTES de que la página cargue

Si el producto distingue tráfico de pruebas (una clave pública de pruebas, un tenant de pruebas, una
cabecera) y lo marca (`is_synthetic=True`) y no avisa a nadie, el auditor usa **ese** camino. Lo que no
funciona y parece que sí: cambiar el atributo **después** de cargar. Un widget que lee su clave al
montarse ya la ha leído; el cambio tardío cubre una vía (la cola) y no la otra (la conversación).

Lo que cubre las dos, medido en el caso de origen: reescribir la respuesta antes de que el navegador
la parsee (Playwright):

```python
async def reescribe(route):
    r = await route.fetch()
    await route.fulfill(response=r, body=(await r.text()).replace(
        'data-api-key="<clave-real>"', 'data-api-key="<clave-de-pruebas>"'))
await page.route("**/<ruta-de-la-página>", reescribe)
```

Un `MutationObserver` en `add_init_script` **no** sirve (probado). Y se comprueba, no se supone: tras
el recorrido, el registro creado sale marcado como de pruebas y sin aviso entregado.

## Lo que esto NO resuelve

- **No es idéntico a ser un cliente.** Si lo que se mide es la vía real de aviso (el mensaje que le
  llega al asesor, la integración externa), hace falta la clave real, y entonces se ensucia: se
  declara en el informe con las referencias creadas, para que se limpien.
- **La clave de pruebas es un secreto de bajo grado**: ni en el informe, ni en una captura, ni en un
  commit.

## Regla de la casa

1. **Por defecto, clave de pruebas**, en la primera línea del guion.
2. **Si necesitas la vía real**, úsala y **dilo en el informe** con lo que creaste.
3. **No borres datos tú**: eso es del orquestador (con copia previa). Nómbralos y ya está.
