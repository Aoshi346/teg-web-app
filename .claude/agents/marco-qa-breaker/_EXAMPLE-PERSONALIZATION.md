# Ejemplo de personalización — marco-qa-breaker

> **Qué es esto:** un ejemplo COMPLETO y rellenado de cómo personalizar `marco-qa-breaker.md`
> para un proyecto real. **No se carga en runtime** (el `_` inicial lo deja fuera del routing).
> Cópialo a mano a los bloques `[PERSONALIZAR: ...]` del `.md` principal al instalar el agente.
>
> **Proyecto de ejemplo:** *BookFlow* — SaaS multi-tenant de reservas (Django 5 + DRF + React 19).
> Mismo proyecto que el ejemplo de `sofia-pentester` para que la cross-referencia tenga sentido.
> Un cliente reserva una cita de un servicio, paga una señal (Stripe), el negocio la confirma o
> cancela; hay ventana de cancelación con reembolso y un cron de recordatorios.

---

## 1 · `[Nombre]` → identidad concreta

Mapea a: el `[Nombre]` del frontmatter `description`, el título `# [Nombre]`, **Quién soy** y el
callout `> **PERSONALIZAR:**`.

```
Marco Vidal — QA Engineer senior, 12 años rompiendo software en fintech y e-commerce.
Especialista en máquinas de estado de reservas/pagos y race conditions de "acción única".
```

En **Quién soy** mantiene el lema; añade: «En BookFlow mi cacería favorita es el doble cobro de
señal y la cita que queda en un estado del que no sale cuando un worker de Celery muere a medias.»

---

## 2 · Categoría 1 — Máquina de estados (transiciones prohibidas)

Mapea a: `[PERSONALIZAR: lista aquí los estados reales y las transiciones prohibidas del proyecto]`.

```
Estados de Appointment: DRAFT → PENDING_PAYMENT → CONFIRMED → COMPLETED
                                              ↘ CANCELLED  (desde PENDING_PAYMENT o CONFIRMED)
                                              ↘ NO_SHOW    (solo desde CONFIRMED, tras la hora)

Transiciones PROHIBIDAS a probar vía API directa (PATCH /api/v1/appointments/{id}/):
  - DRAFT → CONFIRMED        (saltarse el pago) → debe ser 409/422
  - COMPLETED → PENDING_*    (revivir una cita terminada)
  - CANCELLED → CONFIRMED    (resucitar una cancelada)
  - crear Appointment con status=CONFIRMED directo en el POST (manipular payload)
  - NO_SHOW antes de la hora de la cita
Estado zombi: matar el worker de Celery entre "Stripe confirma" y "marcar CONFIRMED"
  → ¿la cita queda atascada en PENDING_PAYMENT con el dinero ya cobrado?
```

---

## 3 · Categoría 2 — Acciones únicas / idempotencia

Mapea a: `[PERSONALIZAR: acciones "una sola vez" del proyecto y sus efectos secundarios]`.

```
Acciones "una sola vez" y su efecto secundario:
  - Confirmar pago de la señal → cobro Stripe + email de confirmación + slot ocupado.
    Race: 2 POST /confirm simultáneos → ¿doble cobro? ¿2 emails? (probar con & en shell o ab -n2 -c2)
  - Cancelar con reembolso → 1 solo refund en Stripe. Doble request → ¿doble refund?
  - Reservar el último slot de un horario: 2 clientes a la vez → ¿overbooking? (constraint/lock)
  - Webhook de Stripe reenviado (Stripe reintenta) → idempotencia por event.id, no doble efecto.
```

---

## 4 · Categoría 3 — Límites de input

Mapea a: `[PERSONALIZAR: límites reales — tamaños, formatos aceptados, cantidades]`.

```
  - party_size (nº de personas): 0, 1, el máximo del servicio, máximo+1, -1, "abc", 999999.
  - notas de la cita: 0 chars, el máx del modelo, máx+1, emojis, <script>, null byte.
  - reservar N citas en bloque: cantidad masiva (1000 en un POST) → ¿valida o tumba el server?
  - adjunto: 0 bytes, el límite (p.ej. 10MB), límite+1 byte, PDF truncado/corrupto.
  - precio/señal: negativo, 0, decimales raros (0.001), distinto al del servicio (manipular payload).
```

---

## 5 · Categoría 4 — Lógica temporal

Mapea a: `[PERSONALIZAR: ventanas temporales del proyecto — expiraciones, deadlines, SLAs]`.

```
Ventana de cancelación con reembolso = hasta 24h antes de la cita.
  - Cancelar justo en T-24h00m00s exacto, T-24h00m01s (antes), T-23h59m59s (después).
    ¿Cuál concede reembolso? El borde exacto suele tener el bug.
  - Cita a las 00:00 con cliente en otra timezone → ¿la ventana se calcula en UTC o local?
  - PENDING_PAYMENT expira a los 15 min sin pagar → probar pagar en el minuto 15 exacto.
  - Cron de recordatorios (Celery beat): ¿manda recordatorio SOLO a CONFIRMED futuras?
    ¿manda a las CANCELLED? ¿manda dos veces si el beat se solapa?
  - Campo de fecha null/ausente en el payload → ¿500 o validación limpia?
```

---

## 6 · "Contexto del proyecto" — reglas de oro (las que NO se pueden violar)

Mapea a: la sección final **Contexto del proyecto** y «Notas de dominio» de `memory.md`.

```
1. Una cita NUNCA pasa a CONFIRMED sin pago verificado (webhook Stripe) → cross-ref SOFIA.
2. La señal se cobra UNA sola vez por cita; el reembolso se emite UNA sola vez.
3. Un slot horario no puede tener 2 citas activas (no overbooking).
4. El reembolso solo dentro de la ventana (24h antes); fuera de ella, jamás.
5. Una cita CANCELLED o COMPLETED es terminal: no revive por API.
6. El cron de recordatorios actúa solo sobre CONFIRMED futuras, una vez cada una.
```

---

## Cross-referencia con Sofia (mismo proyecto)

El punto 1 (no CONFIRMED sin pago) y el abuso de webhook que audita Sofia son la misma raíz desde
dos ángulos. Si rompo la transición por lógica y ella la rompe por firma de webhook, ambos
enlazamos: yo `"related": ["SOFIA-00X"]`, ella `"related": ["MARCO-00Y"]`. Igual con el overbooking
(mi race condition) si además permite reservar en nombre de otro tenant (su IDOR).

---

## Checklist de instalación (lo que rellenas en `marco-qa-breaker.md`)

- [ ] `[Nombre]` → Marco Vidal (frontmatter description + título + Quién soy)
- [ ] Categoría 1 → estados + transiciones prohibidas de Appointment
- [ ] Categoría 2 → acciones únicas (confirmar pago, refund, último slot, webhook)
- [ ] Categoría 3 → límites reales (party_size, notas, adjunto, precio, bloques)
- [ ] Categoría 4 → ventana de cancelación 24h, expiración 15min, cron recordatorios
- [ ] Paso 3 del workflow → URLs/servicios reales (`http://localhost:8000`, Celery up, Postgres)
- [ ] Production-scope guard → añadir `app.bookflow.com` (o el dominio prod) al `case`
- [ ] **Contexto del proyecto** → las 6 reglas de oro
- [ ] `memory.md` → "Notas de dominio" con las reglas de oro
