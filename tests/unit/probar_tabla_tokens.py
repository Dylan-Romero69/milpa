
from src.frontend.lexer import Lexer

codigo = """
entero humedad = 50
decimal temperatura = 25.5

si (humedad > 30) {
    registrar("Necesita riego")
}
"""

lexer = Lexer(codigo)

# Ejecuta el análisis léxico
lexer.analizar()

# Muestra los tokens en una tabla
lexer.imprimir_tabla()

# Muestra los errores encontrados
if lexer.errores.hay_errores():
    lexer.errores.imprimir()
