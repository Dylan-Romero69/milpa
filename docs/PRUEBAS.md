# Pruebas de Milpa

Programas con errores o entradas inusuales que un usuario podría escribir. El compilador debe rechazar
los incorrectos con un mensaje claro, en la fase correcta, y **nunca caerse con un error de Python**.

- Casos: `tests/casos_prueba.py` (228 programas, cada uno con su resultado esperado).
- Ejecutar: `python -m unittest tests.test_pruebas -v`
- Para agregar un caso, añade una línea `ok(...)`, `mal(...)` o `limpio(...)` en ese archivo.
  El prefijo del nombre (`lex/`, `sin/`, `sem/`, `zon/`) indica en qué fase debe fallar.

## Qué se encontró en el commit 3772525 y cómo se resolvió

| Problema | Ejemplo | Arreglo |
|---|---|---|
| El compilador se caía | `entero b = a.x` con `a` entero; 300 paréntesis; suma de 2000 términos | Se valida que el nombre sea una zona; límite de recursión y mensaje claro en `milpa.py` |
| No aceptaba comentarios | `// hola` | El léxico ignora `//` |
| Aceptaba tipos mezclados | `"a" + "b"`, `no 5`, `1 y 2`, `"a" < "b"`, `verdadero == 1` | Reglas de tipos por operador en el semántico |
| Aceptaba `riego_max` y `humedad_min` inválidos | `riego_max: "hola"`, `riego_max: -5`, `humedad_min: 140` | Se valida el tipo y el rango de cada campo de la zona |
| Los bloques no tenían ámbito | `entero t = 1` dentro de un `si` se veía afuera; dos bloques hermanos con la misma variable daban error | Ámbito de bloque con entrada y salida |
| Aceptaba usar el valor al declarar | `entero a = a + 1` | Se evalúa el valor antes de declarar |
| Aceptaba división entre cero | `1 / 0`, `5 % 0` | Plegado de constantes con E-SEM-09 |
| Aceptaba enteros enormes | `entero a = 99999999999` | E-LEX-03 si pasa de 2147483647 |
| Aceptaba letras no ASCII | `entero ñ = 1` | Solo letras ASCII en identificadores |
| Números mal escritos daban errores confusos | `5.`, `1.2.3`, `12abc`, `0x10` | E-LEX-03 "número mal formado" |
| Coma sobrante y zona vacía | `zona z { cultivo: "a", }`, `zona z { }` | Error sintáctico |
| Aceptaba nombres reservados | `entero y = 1`, `entero leer = 1` | E-SEM-02 |
| Aceptaba una zona dentro de un bloque | | E-SEM-08 |
| Funciones sin validar | `a_entero("x")`, `registrar(z)` | Tabla de funciones con parámetros y tipos |
| Validaciones de dominio ausentes | `leer(z, "viento")`, `regar(z, 30)` con `riego_max: 15` | V1, V2 y V3 |

## Pendiente (no es del frontend)

El generador de código todavía no implementa el dialecto del documento:
decimales (`li $k0, 2.5` no ensambla en MARS), `registrar` con varios argumentos (descarta los
extra sin avisar), `leer(z, "sensor")`, `regar(z, n)` y las zonas / `para_cada`.
