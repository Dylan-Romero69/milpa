
from src.frontend.ast_nodes import (
    Programa,
    DeclaracionVariable,
    Condicional,
    OperacionBinaria,
    Identificador,
    Literal,
    LlamadaFuncion,
    imprimir_ast
)

# Construimos un árbol de ejemplo
programa = Programa(
    instrucciones=[
        DeclaracionVariable(
            tipo="entero",
            nombre="humedad",
            valor=Literal(
                valor=50,
                tipo="entero"
            )
        ),

        Condicional(
            condicion=OperacionBinaria(
                izquierda=Identificador(
                    nombre="humedad"
                ),
                operador=">",
                derecha=Literal(
                    valor=30,
                    tipo="entero"
                )
            ),

            bloque_si=[
                LlamadaFuncion(
                    nombre="registrar",
                    argumentos=[
                        Literal(
                            valor="Necesita riego",
                            tipo="texto"
                        )
                    ]
                )
            ],

            bloque_si_no=[]
        )
    ]
)

# Imprimimos el árbol
print("\n========== ARBOL AST DE MILPA ==========\n")

imprimir_ast(programa)
