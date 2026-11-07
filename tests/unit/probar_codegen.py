
from src.intermediate import Cuadruplo
from src.codegen_mips import GeneradorMIPS


# Código intermedio de prueba
codigo = [
    Cuadruplo("+", "5", "3", "t1"),
    Cuadruplo("*", "t1", "2", "t2"),
    Cuadruplo("-", "t2", "1", "t3"),
    Cuadruplo("=", "t3", "", "resultado"),
    Cuadruplo("RET")
]

# Generar código MIPS
generador = GeneradorMIPS(codigo)

contenido = generador.generar()

# Mostrar instrucciones en consola
print("\n========== CODIGO MIPS GENERADO ==========\n")
print(contenido)

# Guardar archivo ASM
generador.guardar("salida.asm")

print("\nArchivo generado: salida.asm")
