# vendedores.py
import sqlite3

DB_NAME = "delivery_app.db"


def registrar_usuario_vendedor(username, password, restaurante_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO usuarios (username, password, rol, restaurante_id) 
        VALUES (?, ?, 'Vendedor', ?)
    """,
        (username, password, restaurante_id),
    )
    conn.commit()
    conn.close()


def obtener_vendedores():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT u.id, u.username, r.nombre 
        FROM usuarios u
        JOIN restaurantes r ON u.restaurante_id = r.id
        WHERE u.rol = 'Vendedor'
    """
    )
    vendedores = cursor.fetchall()
    conn.close()
    return vendedores


def eliminar_vendedor(vendedor_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM usuarios WHERE id = ? AND rol = 'Vendedor'",
        (vendedor_id,),
    )
    conn.commit()
    conn.close()