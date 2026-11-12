# Adaptador de canal — el motor habla un idioma; cada canal traduce en la puerta

> **Cuándo aplicar:** cuando el mismo producto (un bot, un asistente, un sistema de avisos) recibe o
> envía mensajes por más de un canal —la web, WhatsApp, Instagram, correo, Telegram— o lo hará. Al
> añadir el segundo canal como muy tarde; mejor con el primero.
>
> **NO aplicar:** a integraciones que no son un canal de conversación (la tienda, la agenda, el pago):
> `backend-integrations.md` · a la firma y el enrutado del webhook entrante: skill
> `webhook-multi-tenant-validation` · a la ventana de 24 h y los topes de coste del canal:
> `templates/canal-bot/` · a qué dice el bot: skill `disenar-conversacion`.
>
> **Relacionado:** `integration_check.py` (CA1, con `--engine`) · `backend-integrations.md` (el envío
> real pasa por su factoría y su candado) · `backend-celery.md` (la respuesta asíncrona) ·
> `frontend-embeddable-widget.md` (el canal web del lado del cliente) · `agente-traza-comunicaciones.md`.
>
> Cosechado de `proxera_musa` (`core/channels/`: `base.py`, `dto.py`, `web.py`, `manychat.py`, y la
> prueba de paridad de `apps/channels/tests/test_channel_adapters.py`). Era el saber del agente
> `integrations-engineer`; aquí tiene comprobador (AN-18).

## La regla (una frase)

**El motor solo conoce dos tipos —`InboundMessage` y `AgentResult`—; cada canal es un adaptador con
dos métodos (`normalize_inbound` y `send_outbound`), y la prueba de que está bien es que el mismo
texto por dos canales da la misma respuesta del motor.**

## 1. El contrato

```python
# core/channels/dto.py
@dataclass(slots=True)
class InboundMessage:
    client_id: int                 # tenant, resuelto en la puerta (token del canal), nunca del texto
    channel: str                   # web | whatsapp | instagram
    external_user_id: str
    text: str
    thread_id: str | None = None
    channel_meta: dict[str, Any] = field(default_factory=dict)   # crudo del canal; el motor no lo lee

@dataclass(slots=True)
class AgentResult:
    text: str
    handoff_requested: bool = False
    blocks: list[dict[str, Any]] = field(default_factory=list)   # tarjetas, respuestas rápidas
    parts: list[str] = field(default_factory=list)               # la respuesta en varios mensajes

# core/channels/base.py
class ChannelAdapter(ABC):
    channel: str = ""
    @abstractmethod
    def normalize_inbound(self, raw_payload: dict[str, Any]) -> InboundMessage: ...
    @abstractmethod
    def send_outbound(self, result: AgentResult) -> dict[str, Any]: ...
```

## 2. Qué va en el adaptador y qué no

| En el adaptador | En el motor | Nunca |
|---|---|---|
| Deducir el canal del payload (`subscriber.channel`) | La conversación, las tools, el estado | Un `if channel == "whatsapp"` dentro del grafo |
| El formato que el canal admite: WhatsApp e Instagram no pintan Markdown → se quita al salir; la web convierte negrita en `<strong>` | Qué decir | Pedirle al prompt «sin markdown» y fiarse |
| Partir `parts` en varios mensajes si el canal lo pide | Decidir cuándo partir | Partir en el motor según el canal |
| Resolver `client_id` desde el token del canal | Usar `client_id` | Sacar el tenant del texto del usuario |

## 3. El webhook responde ya; la respuesta va por cola

El webhook valida la firma (`webhook-multi-tenant-validation`), normaliza, **encola** la tarea
(`process_message.delay(...)`) y devuelve 200 al momento. El turno del motor y el envío corren en
Celery: el proveedor reintenta si tardas, y un turno de LLM tarda. El envío real sale por la
**factoría** de `backend-integrations.md`, así que fuera de producción va al simulador aunque la BD
diga «real».

## 4. Las pruebas

| Test | Comprueba |
|---|---|
| **Paridad** | El mismo texto por la web y por WhatsApp, con el LLM falso y determinista → el mismo `AgentResult.text` |
| Normalización | Un payload real de cada canal (guardado como fixture) → el `InboundMessage` esperado; uno sin texto → error claro, no un turno vacío |
| Salida | `**negrita**` y `[texto](url)` → sin marcas en WhatsApp e Instagram |
| Webhook | Sin firma → 401/403 · con firma → 200 al momento y la tarea encolada |

```bash
python3 .claude/patterns/stack/integration_check.py --root backend --engine core/workflow core/tools
```

CA1 marca el motor que importa un canal concreto (`core.channels.whatsapp`) o una integración
concreta en vez del contrato. Sin `--engine` no se mide, y el comprobador lo dice.

## Anti-patterns

- ❌ Lógica de canal en el motor: el tercer canal obliga a tocar el grafo.
- ❌ Contestar síncrono al webhook con el turno del LLM dentro.
- ❌ Un adaptador que llama al proveedor real directamente, sin la factoría: se salta el candado.
- ❌ Sin prueba de paridad: los canales divergen en silencio y el bug sale solo en WhatsApp.
