from src.frontend.lexer import Lexer
from src.parser import Parser
from src.intermediate import GeneradorIntermedio
from src.optimizer import Optimizador

codigo = """
entero humedad = 50
entero limite = 80
entero aumento = 5

humedad = humedad + 0
entero resultado = 5 + 3

mientras (humedad < limite) {
    humedad = humedad + aumento
}

si (humedad >= limite) {
    registrar("Riego completado")
} si_no {
    regar(10)
}
"""

# Análisis léxico
lexer = Lexer(codigo)
tokens = lexer.analizar()

# Análisis sintáctico
parser = Parser(tokens)
arbol = parser.analizar()


if arbol is not None:

    # Generación de cuádruplos
    generador = GeneradorIntermedio()
    generador.generar(arbol)

    # Mostrar código intermedio original
    print("\n========== CODIGO INTERMEDIO ORIGINAL ==========")
    generador.imprimir()

    # Optimización
    optimizador = Optimizador()
    codigo_optimizado = optimizador.optimizar(
        generador.cuadruplos
    )

    # Mostrar código optimizado
    print("\n========== CODIGO INTERMEDIO OPTIMIZADO ==========")
    optimizador.imprimir()

    # Mostrar métricas
    optimizador.imprimir_metricas()
