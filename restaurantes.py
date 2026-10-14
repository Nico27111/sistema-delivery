# restaurantes.py
import sqlite3

DB_NAME = "delivery_app.db"


def crear_restaurante(nombre, direccion, telefono, categoria):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO restaurantes (nombre, direccion, telefono, categoria) VALUES (?, ?, ?, ?)",
        (nombre, direccion, telefono, categoria),
    )
    conn.commit()
    conn.close()


def obtener_restaurantes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM restaurantes")
    restaurantes = cursor.fetchall()
    conn.close()
    return restaurantes


def eliminar_restaurante(restaurante_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM restaurantes WHERE id = ?", (restaurante_id,))
    conn.commit()
    conn.close()