#!/bin/bash
# Hook: Valida que PROGRESS.json existe y tiene formato válido

if [ ! -f "PROGRESS.json" ]; then
  echo "WARNING: PROGRESS.json no encontrado en la raíz del proyecto."
  echo "Crea PROGRESS.json con el formato estándar antes de empezar."
  exit 0
fi

# Validate JSON format
if ! python3 -c "import json; json.load(open('PROGRESS.json'))" 2>/dev/null; then
  echo "ERROR: PROGRESS.json tiene formato JSON inválido."
  exit 1
fi

# Check required fields
python3 -c "
import json, sys
d = json.load(open('PROGRESS.json'))
required = ['task', 'status', 'checklist']
missing = [f for f in required if f not in d]
if missing:
    print(f'WARNING: PROGRESS.json le faltan campos: {missing}')
" 2>/dev/null || true

exit 0
