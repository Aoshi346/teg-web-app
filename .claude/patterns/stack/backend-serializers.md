# Serializers — patrón de casa

> **Cuándo aplicar:** al crear o modificar cualquier serializer de DRF.

## La regla (una frase)

**El serializer es el contrato de la API: declara campo por campo qué entra y qué sale, valida la
FORMA de los datos, y no provoca ningún efecto.**

Por qué la frontera está justo ahí: un serializer se ejecuta **también cuando la petición va a
fallar**. `is_valid()` corre antes de saber si el resto de validaciones pasan, y `create()` puede
quedar a medias. Todo lo que tenga consecuencias fuera del proceso —un correo, una task, un
cargo— colocado aquí se dispara en peticiones que acaban en 400.

## Implementación de referencia

`_fixtures/conforme/apps/facturacion/serializers.py`:

```python
class FacturaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)

    class Meta:
        model = Factura
        fields = [
            "id", "numero", "cliente", "cliente_nombre", "concepto",
            "importe", "estado", "emitida_en", "creada_en",
        ]
        # `cliente` y `estado` los decide el servidor: si fueran escribibles, el cliente podría
        # facturar a nombre de otro o marcarse una factura como pagada desde el payload.
        read_only_fields = ["id", "numero", "cliente", "estado", "emitida_en", "creada_en"]

    def validate_importe(self, value):
        if value <= 0:
            raise serializers.ValidationError("El importe debe ser mayor que cero.")
        return value
```

Tres decisiones:

- **`fields` enumerado.** Es la lista de lo que la API promete. Un campo nuevo en el modelo no
  entra en el contrato hasta que alguien lo añade aquí conscientemente.
- **`read_only_fields` para todo lo que decide el servidor.** El dueño (`cliente`), el estado del
  flujo (`estado`) y los sellos de tiempo no se aceptan del cliente. Se asignan en el
  `perform_create` (desde la sesión) o en el servicio.
- **`validate_<campo>` valida forma, no estado del sistema.** "El importe debe ser positivo" es
  forma. "Esta factura ya no se puede emitir" depende del estado y vive en el servicio.

## El antipatrón que sustituye

`_fixtures/infractor/apps/facturacion/serializers.py`:

```python
class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = "__all__"

    def create(self, validated_data):
        factura = Factura.objects.create(**validated_data)
        enviar_factura_por_email.delay(str(factura.pk))
        return factura


class FacturaEntradaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = ["id", "cliente", "numero", "importe"]     # `cliente` escribible
```

Los tres daños:

1. **`fields = "__all__"` es una fuga con fecha futura.** Hoy publica lo que hay; el día que
   alguien añada `margen_interno`, `coste_proveedor` o `notas_internas` al modelo, ese campo sale
   por la API en el mismo deploy, sin que aparezca en ningún diff de serializer. Nadie revisa un
   PR de modelo pensando "¿esto se publica?".
2. **`cliente` escribible es asignación masiva.** El cliente manda `{"cliente": "<otro-uuid>",
   "importe": 10}` y crea una factura a nombre de otra persona. No hace falta ningún fallo de
   permisos: el endpoint hace justo lo que le piden.
3. **`.delay()` en `create()`**: si una validación posterior falla, la petición devuelve 400 y el
   correo ya salió.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-ser-fields-all,\
be-ser-campo-servidor-escribible,be-ser-sin-efectos
```

| Regla | Estado | Qué detecta (AST) |
|---|---|---|
| `be-ser-fields-all` | activo | `Meta.fields = "__all__"` en una clase `*Serializer` |
| `be-ser-campo-servidor-escribible` | activo | `Meta.fields` incluye un campo de dueño (`user`, `owner`, `cliente`, `usuario`, `tenant`, `created_by`, `creado_por`, `empresa`…) que no está en `read_only_fields` ni declarado con `read_only=True` |
| `be-ser-sin-efectos` | activo | `.delay()`, `.apply_async()`, `send_mail()`, `requests.*`, `httpx.*` dentro de una clase `*Serializer` |

## Excepciones legítimas

- **Serializer interno que nunca se expone** (un informe, un export a un sistema propio) donde
  `__all__` es justo la intención. Requiere dejarlo escrito, porque el lector siguiente no puede
  distinguirlo de un descuido:

```python
class ExportContableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        # pattern-exempt: be-ser-fields-all — export contable interno: queremos TODOS los campos,
        # incluidos los que se añadan en el futuro. No se sirve por la API pública.
        fields = "__all__"
```

- **Campo de dueño escribible en un endpoint de administración**, donde un `staff` sí asigna
  propietario. La exención va con la razón y, sobre todo, con el permiso que la respalda.

## Related

- `backend-vistas.md` (`perform_create` asigna el dueño desde la sesión) ·
  `backend-servicios.md` (las reglas que dependen del estado) ·
  skill `code-review-gate` (§Seguridad Django/DRF) (asignación masiva y exposición de datos)
