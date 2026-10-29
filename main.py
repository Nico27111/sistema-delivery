# main.py
from clientes import menu_clientes
from restaurantes import menu_restaurantes
from productos import menu_productos
from pedidos import menu_pedidos


def menu_principal():
    while True:
        print("\n=== SISTEMA DE GESTIÓN DE DELIVERY ===")
        print("1. Gestión de Clientes")
        print("2. Gestión de Restaurantes")
        print("3. Gestión de Productos")
        print("4. Gestión de Pedidos")
        print("5. Salir")

        opcion = input("\nSeleccione una opción: ")

        if opcion == "1":
            menu_clientes()

        elif opcion == "2":
            menu_restaurantes()

        elif opcion == "3":
            menu_productos()

        elif opcion == "4":
            menu_pedidos()

        elif opcion == "5":
            print("¡Hasta luego!")
            break

        else:
            print("Opción inválida. Intente de nuevo.")


if __name__ == "__main__":
    menu_principal()