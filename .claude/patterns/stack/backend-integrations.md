# Integraciones externas — un contrato, real y simulador detrás, y una factoría que decide

> **Cuándo aplicar:** en cuanto el backend hable con un sistema que no controlamos y que no es solo
> un canal de mensajes: la tienda del cliente (WooCommerce, Shopify), su agenda, su ERP, una pasarela
> de pago, un CRM. Al escribir la primera integración, no la tercera.
>
> **NO aplicar:** al canal por el que llegan y salen los mensajes (WhatsApp, Instagram, la web): eso
> es `backend-channel-adapter.md`, que se apoya en este · al simulador en sí (rutas, pantalla, `/_averia`):
> `mocks-externos.md` · a decidir si se puede tocar el dato real del cliente: `backend-candado-datos-reales.md`
> · a conectar un formulario con un CRM sin backend propio: skill `integrar-crm`.
>
> **Relacionado:** `integration_check.py` (IC1-IC3, el comprobador) · `mocks-externos.md` ·
> `backend-candado-datos-reales.md` · `backend-servicios.md` · `api-y-errores.md` ·
> `agente-tools.md` (cuando quien llama es un LLM) · skill `webhook-multi-tenant-validation`.
>
> Cosechado de `proxera_musa` (`backend/integrations/`: `base.py`, `factory.py`, `guard.py`), que a su
> vez lo tomó de `elvion` (`core/services/interfaces.py`). En musa era el saber del agente
> `integrations-engineer`; aquí tiene comprobador y no hace falta persona (AN-18).

## La regla (una frase)

**Todo lo de fuera va detrás de un `Protocol`, con una implementación real y un doble que lo imitan
igual, y SOLO la factoría decide cuál se usa: el resto del código pide `get_<integración>(client)` y
no sabe —ni puede saber— cuál le ha tocado.**

## 1. La forma

```
integrations/
├── base.py          # los Protocol: ShopGateway, AgendaGateway… y las denylists del límite
├── factory.py       # get_shop(client) · get_agenda(client): real | simulador, candado y guarda
├── guard.py         # guard_writes: bloquea los métodos de escritura si allow_write está apagado
├── shop/   real.py  mock.py
└── agenda/ real.py  mock.py     # mock_v2.py, simulator_bridge.py… también cuentan como doble
```

```python
# integrations/base.py
@runtime_checkable
class ShopGateway(Protocol):
    def search_products(self, query: str, *, per_page: int = 10) -> list[dict[str, Any]]: ...
    def create_order(self, order: dict[str, Any]) -> dict[str, Any]: ...  # devuelve payment_url
```

## 2. Lo que decide la factoría — y por qué ahí y no en cada sitio

| Decisión | Dónde | Por qué en la factoría |
|---|---|---|
| **Real o simulador** | Config por cliente (`IntegrationConfig.mode`, desde el panel) y, si no hay, el `*_MODE` del entorno | Un único sitio que leer al revisar «¿esto puede salir a la red?» |
| **Candado de entorno** | Fuera de producción, las integraciones **de cliente** se fuerzan a simulador y **sin credenciales**, diga lo que diga la BD | Un clon de la base de producción lleva dentro `mode='real'` y las credenciales: el entorno de pruebas escribiría en la agenda real del cliente. Va en código, marcado `# defensive:` |
| **Guarda de escritura** | Con `allow_write=False`, el gateway sale envuelto en un proxy que lanza `WriteNotAllowed` en los métodos de escritura (lista explícita por integración) | El «modo solo consulta» del dueño se cumple aunque el código de arriba se equivoque |
| **Credenciales** | Las del panel (cifradas) mandan sobre las del entorno | Una sola regla de precedencia, escrita una vez |

Quien se salta la factoría (`from integrations.shop.real import …` en una vista o una tarea) se salta
**las cuatro** a la vez. Por eso IC2 es la regla que más importa del comprobador.

## 3. Los límites duros viven en el contrato, no en el prompt ni en la vista

- **No cobra**: la tienda crea el pedido y devuelve `payment_url`; el cliente paga en la tienda. Ningún
  método del Protocol procesa un pago.
- **No toca lo que no debe**: si la integración expone campos que no son de nuestro negocio (datos
  clínicos en una agenda), el contrato declara una denylist y el adaptador real **descarta** esos
  campos antes de devolverlos; el doble no los tiene. Un test lo comprueba con un payload que los trae.
- **Escrituras, en lista**: `WRITE_METHODS` por integración; lo que no está en la lista es lectura.

## 4. El doble imita la API, no la sustituye

El `mock.py` cumple el mismo Protocol y responde con la forma real (mismos campos, mismos errores).
Si el doble es un servidor aparte (para poder abrir la app sin internet), el gateway real apuntado a
su URL es mejor doble que una clase: prueba también la capa HTTP. Detalle y registro de simuladores:
`mocks-externos.md`.

## 5. Las pruebas

```bash
python3 .claude/patterns/stack/integration_check.py --root backend     # IC1-IC3 (y CA1 con --engine)
python3 .claude/patterns/stack/integration_check.py --self-test        # cada regla vista fallar
```

Y en los tests de la app, cuatro que no faltan:

| Test | Comprueba |
|---|---|
| Factoría por modo | `mode=simulator` → doble · `mode=real` en producción → real |
| **Candado** | Con `APP_ENV != prod` y `mode='real'` en la BD → doble y sin credenciales |
| Guarda | `allow_write=False` → `create_order` lanza `WriteNotAllowed`; una lectura pasa |
| Denylist | Un payload real con campos prohibidos → no salen del adaptador |

## Anti-patterns

- ❌ `from integrations.<x>.real import …` fuera de la factoría «porque aquí sé que es real» (IC2).
- ❌ Una integración sin doble: nadie puede abrir la app sin la cuenta del cliente (IC1).
- ❌ El modo leído solo de la BD: un clon de producción sale a la red con las credenciales reales.
- ❌ Decidir real o simulador con un `if settings.DEBUG` repartido por las vistas.
- ❌ El límite («no cobres», «no leas la historia clínica») escrito en el prompt del bot y no en el contrato.
