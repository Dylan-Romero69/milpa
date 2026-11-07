
from src.notation import a_postfija, a_prefija


def probar_expresiones():
    expresiones = [
        "5 + 3 * 2",
        "(5 + 3) * 2",
        "a - b / c",
        "humedad >= limite",
        "a y b o c",
        "-5 + 3"
    ]

    print("\n========== CONVERSION DE EXPRESIONES ==========\n")

    for expresion in expresiones:
        postfija = a_postfija(expresion)
        prefija = a_prefija(expresion)

        print(f"Infija:    {expresion}")
        print(f"Postfija:  {postfija}")
        print(f"Prefija:   {prefija}")
        print("-" * 50)


if __name__ == "__main__":
    probar_expresiones()
