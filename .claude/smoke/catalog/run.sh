#!/usr/bin/env bash
# Prueba de catalog_readiness.py: semilla de autoparte (huecos) · completo (verde) · sabotajes.
# Sin red salvo un servidor en 127.0.0.1 que hace de API de precio y stock. Sale 1 si algo no cuadra.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../../scripts/catalog_readiness.py"
TMP="$(mktemp -d)"
PORT="${CATALOG_SMOKE_PORT:-8871}"
FAILS=0
trap 'kill "$SRV" 2>/dev/null; rm -rf "$TMP"' EXIT

expect() {  # expect <descripción> <export> <python-assert sobre r> [args…]
  local what="$1" export="$2" cond="$3"; shift 3
  if python3 "$SCRIPT" "$export" --json "$@" > "$TMP/out.json" \
     && python3 -c "import json,sys; r=json.load(open('$TMP/out.json')); sys.exit(0 if ($cond) else 1)"; then
    echo "✓ $what"
  else
    echo "✗ $what"; python3 -c "import json; r=json.load(open('$TMP/out.json')); print('  ', r['verdict'], r['gaps'], r['unmeasured'])" 2>/dev/null
    FAILS=$((FAILS + 1))
  fi
}

# La API de precio y stock, de mentira pero de verdad: un GET real a 127.0.0.1.
mkdir -p "$TMP/api/offer"
echo '{"price": 189.0, "stock": 7, "currency": "EUR"}' > "$TMP/api/offer/amplitud-blanca"
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$TMP/api" > /dev/null 2>&1 &
SRV=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.3; done
API="http://127.0.0.1:$PORT/offer/{id}"

expect "semilla de autoparte → huecos de atributos, complementos y políticas; API sin medir" \
  "$HERE/autoparte_seed.json" \
  "r['verdict']=='con huecos' and set(r['gaps'])=={'decisive_attributes','complements','policies'} and r['unmeasured']==['price_api']"
expect "completo con la API real → listo" "$HERE/complete.json" "r['verdict']=='listo'" --price-api "$API"
expect "completo sin llamar a la API → sin medir del todo (no es verde)" "$HERE/complete.json" \
  "r['verdict']=='sin medir del todo' and r['unmeasured']==['price_api']"
expect "completo con la API caída → hueco de API" "$HERE/complete.json" \
  "r['gaps']==['price_api']" --price-api "http://127.0.0.1:9/offer/{id}"

# Sabotajes plantados: cada uno tiene que encender su comprobación (control negativo).
python3 - "$HERE/complete.json" "$TMP" <<'PY'
import copy, json, sys
base = json.load(open(sys.argv[1])); out = sys.argv[2]
def save(name, data): json.dump(data, open(f"{out}/{name}.json", "w"), ensure_ascii=False)
d = copy.deepcopy(base); d["products"][0]["offer"] = {"price": 136.0, "currency": "EUR", "stock": 1}; save("parent_offer", d)
d = copy.deepcopy(base); d["products"][-1]["components"] = []; save("empty_bundle", d)
d = copy.deepcopy(base); d["families"].append({"id": "correderas2", "name": "VENTANAS CORREDERAS", "parent": "ventanas"}); save("dup_family", d)
d = copy.deepcopy(base); d["products"][1]["attributes"].pop("color"); d["products"][2]["attributes"].pop("color"); save("no_color", d)
d = copy.deepcopy(base); [p.update(cross_sell_ids=[], upsell_ids=[], grouped_products=[]) for p in d["products"]]; d["relations"] = []; save("no_complements", d)
d = copy.deepcopy(base); d["policies"][2].pop("version"); save("policy_no_version", d)
d = copy.deepcopy(base); d["products"][4]["family"] = "accesorios"; save("branch_family", d)
d = copy.deepcopy(base); [p.update(references=[]) for p in d["products"]]; save("no_refs", d)
d = copy.deepcopy(base); d["products"][4]["kind"] = "WEIRD"; save("bad_kind", d)
d = copy.deepcopy(base); d["families"].append({"id": "x", "name": "Ventanás  Correderas", "parent": "ventanas"}); save("dup_spaces", d)
PY
expect "sabotaje: oferta sobre el padre de variantes" "$TMP/parent_offer.json" "r['gaps']==['antipatterns']" --price-api "$API"
expect "sabotaje: kit sin componentes" "$TMP/empty_bundle.json" "r['gaps']==['antipatterns']" --price-api "$API"
expect "sabotaje: familia duplicada por mayúsculas" "$TMP/dup_family.json" "r['gaps']==['antipatterns']" --price-api "$API"
expect "sabotaje: falta un atributo decisivo" "$TMP/no_color.json" "r['gaps']==['decisive_attributes']" --price-api "$API"
expect "sabotaje: sin complementos" "$TMP/no_complements.json" "r['gaps']==['complements']" --price-api "$API"
expect "sabotaje: política sin versión" "$TMP/policy_no_version.json" "r['gaps']==['policies']" --price-api "$API"
expect "sabotaje: producto en una rama, no en una hoja" "$TMP/branch_family.json" "r['gaps']==['leaf_family']" --price-api "$API"
expect "sabotaje: sin referencias en un vertical que las exige" "$TMP/no_refs.json" "r['gaps']==['references']" --price-api "$API"
expect "sabotaje: kind desconocido" "$TMP/bad_kind.json" "'antipatterns' in r['gaps']" --price-api "$API"
expect "sabotaje: familia duplicada por tilde y doble espacio" "$TMP/dup_spaces.json" "r['gaps']==['antipatterns']" --price-api "$API"

# Códigos de salida: sombra sale 0 con huecos; --strict sale 1; un export roto sale 2.
python3 "$SCRIPT" "$HERE/autoparte_seed.json" > /dev/null; c0=$?
python3 "$SCRIPT" "$HERE/autoparte_seed.json" --strict > /dev/null; c1=$?
echo "no es json" > "$TMP/broken.json"; python3 "$SCRIPT" "$TMP/broken.json" > /dev/null 2>&1; c2=$?
if [ "$c0" = 0 ] && [ "$c1" = 1 ] && [ "$c2" = 2 ]; then echo "✓ salida 0 en sombra · 1 con --strict · 2 si no se lee"
else echo "✗ códigos de salida: $c0 $c1 $c2 (esperado 0 1 2)"; FAILS=$((FAILS + 1)); fi

[ "$FAILS" = 0 ] && echo "OK: todo cuadra" || echo "FALLAN $FAILS"
exit $(( FAILS > 0 ))
