---
name: ram-before-pytest
description: Usar SIEMPRE antes de lanzar cualquier test en este repositorio — pytest, tests del backend, correr la suite, comprobar que pasa, verificar el módulo, ejecutar las pruebas. Dice cómo se lanzan los tests aquí sin tumbar el servidor, por qué la suite entera está prohibida y qué hacer si el comprobador de memoria bloquea.
---

# Los tests, aquí, se lanzan por módulo

Este repositorio corre en un servidor compartido con otras sesiones. La suite entera agota la
memoria y **tumba el servidor**. No es una precaución: ha pasado.

## Siempre, en este orden

```bash
bash .claude/hooks/check-ram.sh                       # 1. el gate. Si bloquea, ESPERA
{{pytest}} <ruta-del-modulo>/ -v --maxfail=3          # 2. por módulo, nunca entero
```

Otras formas válidas: `{{pytest}} -k "nombre_del_test" -v` · `{{pytest}} tests/fichero.py -v -x`.
Con muchos tests, en tandas de unos veinte, con el gate entre una y otra.

## Prohibido

`pytest` a secas · `pytest tests/` · sin ruta · `-n auto` · `--cov`

`--cov` multiplica la memoria: si hace falta cobertura, se pide para un módulo suelto y se dice. El
número de workers máximo lo da `bash .claude/hooks/check-ram.sh --explain` para **esta** máquina.

## Si el comprobador bloquea

**Espera y reintenta. No lo saltes.** Bloquea por dos razones y las dos son ciertas: no hay memoria
libre suficiente, o hay demasiadas sesiones a la vez. Ninguna se arregla insistiendo. **No memorices
los números**: se derivan del hardware y cambian.

## Si se acaba la memoria (OOM)

Es un fallo grave, no mala suerte: dilo, reduce el alcance, espera a que se libere memoria y
reintenta con una tanda más pequeña.

## Un test que nunca has visto fallar no es una red

Antes de fiarte de que un módulo está cubierto, rompe una línea a propósito y comprueba que la suite
se pone **roja**. Si sigue verde, no hay red: hay ficheros de test.
