# Plan — ORD-7: filtro de pendientes y estado de pedido en el bot

## Alcance (Usuario, 01-12, verbatim)

> En la pantalla de pedidos, un check «Solo pendientes» que viene marcado. La API de lista
> `/api/orders/` devuelve por defecto solo los pendientes y con `?status=all` todos los activos.
> Se añade a pedido el campo `priority` (por defecto 0) y la lista se ordena por prioridad. El bot
> puede responder el estado de un pedido por su número. No se tocan el export, el informe mensual,
> la pantalla de facturas ni el contrato de la API fuera del campo nuevo, que sale en todas las
> respuestas con pedidos, también las que ya recibe el bot.

## Ficheros previstos

- orders/models.py
- orders/migrations/0002_order_priority.py
- orders/views.py
- frontend/src/hooks/useOrders.ts
- frontend/src/pages/OrdersPage.tsx
- agent/tools.py
- agent/graph.py
