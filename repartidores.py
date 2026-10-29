# repartidores.py
import sqlite3

DB_NAME = "delivery_app.db"


def registrar_usuario_repartidor(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO usuarios (username, password, rol) 
        VALUES (?, ?, 'Repartidor')
    """,
        (username, password),
    )
    conn.commit()
    conn.close()


def obtener_repartidores():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, username 
        FROM usuarios 
        WHERE rol = 'Repartidor'
    """
    )
    repartidores = cursor.fetchall()
    conn.close()
    return repartidores


def eliminar_repartidor(repartidor_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM usuarios WHERE id = ? AND rol = 'Repartidor'",
        (repartidor_id,),
    )
    conn.commit()
    conn.close()