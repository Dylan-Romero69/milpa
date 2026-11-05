# Formatos compartidos (acordarlos antes de programar)

## Token (lexer -> parser)
Token(tipo, lexema, linea, col)
Tipos: PALABRA_RESERVADA, ID, ENTERO, DECIMAL, TEXTO, OPERADOR, DELIMITADOR, EOF
Palabras reservadas: zona constante entero decimal texto booleano si si_no mientras repetir
para_cada en y o no verdadero falso

## AST (parser -> semántico)
Cada nodo tiene: tipo_nodo, linea, col, hijos y, tras el semántico, .tipo (entero, decimal,
texto, booleano, zona, vacio) y .val (valor constante o None).
Nodos: Programa, DeclZona, DeclConst, DeclVar, Asig, Si, Mientras, ParaCada, Llamada,
BinOp, UnOp, Literal, Var, Campo, LlamadaExp.

## Cuádruplo (semántico/intermedio -> optimizador -> codegen)
Cuadruplo(op, arg1, arg2, res)
Operadores: + - * / % neg i2d d2i < <= > >= == != y o no = etiqueta goto if_falso param call
Argumentos: nombre de variable, temporal (t1, t2...), literal o etiqueta (L1, L2...)
Ejemplos:
  (*, minutos, 1.5, t1)      (=, t1, -, litros_total)
  (if_falso, t3, -, L2)      (etiqueta, -, -, L2)
  (param, z, -, -)           (call, regar, 2, -)

## Error (todas las fases -> errors.py)
Error(fase, codigo, linea, col, mensaje)
Códigos: E-LEX-01..03, E-SIN-01, E-SEM-01..07, E-DOM-01..03 (ver documento de definición)

## Tabla de símbolos y direcciones
Simbolo(nombre, tipo, categoria, nivel, direccion, tamano, valor, inicializada)
categoria: variable, constante, zona
direccion: etiqueta en .data, por ejemplo v_minutos_1
