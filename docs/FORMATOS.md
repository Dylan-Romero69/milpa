# Formatos compartidos (acordarlos antes de programar)

## Token (lexer -> parser)
Token(tipo, lexema, linea, col)
Tipos: PALABRA_RESERVADA, ID, ENTERO, DECIMAL, TEXTO, OPERADOR, DELIMITADOR, EOF
El lexema de un TEXTO es el contenido SIN las comillas. Línea y columna empiezan en 1.
Las funciones predefinidas (leer, lloviendo, regar, registrar, a_entero) son tokens ID.
Palabras reservadas: zona constante entero decimal texto booleano si si_no mientras repetir
para_cada en y o no verdadero falso

## AST (parser -> semántico)
Definido en src/ast_nodes.py. Cada nodo tiene: linea, col y, tras el semántico, .tipo
(entero, decimal, texto, booleano, zona, vacio) y .val (valor constante o None).
Un bloque es una lista de sentencias. Para ver un árbol: python milpa.py programa.milpa --ast
Nodos:
  Programa(sentencias)
  DeclZona(nombre, campos: [CampoZona(nombre, valor)])
  DeclConst(tipo_decl, nombre, valor)     DeclVar(tipo_decl, nombre, valor)
  Asig(nombre, valor)
  Si(cond, entonces, sino|None)           Mientras(cond, cuerpo)
  Repetir(cuerpo, cond)  (opcional)       ParaCada(var, zonas: [nombres], cuerpo)
  Llamada(nombre, args)  (sentencia o expresión)
  BinOp(op, izq, der)    op: + - * / % == != < <= > >= y o
  UnOp(op, operando)     op: neg, no
  Literal(tipo_lit, valor)  valor es int, float, str o bool de Python
  Var(nombre)            AccesoCampo(objeto, campo)
Palabras reservadas que NO se pueden usar como nombre de variable: y, o, no, en, si, si_no,
mientras, repetir, para_cada, zona, constante, entero, decimal, texto, booleano, verdadero, falso.

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
