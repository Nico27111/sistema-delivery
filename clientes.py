# clientes.py
import sqlite3

DB_NAME = "delivery_app.db"


def crear_cliente(nombre, telefono, direccion):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clientes (nombre, telefono, direccion) VALUES (?, ?, ?)",
        (nombre, telefono, direccion),
    )
    conn.commit()
    conn.close()


def obtener_clientes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    conn.close()
    return clientes


def eliminar_cliente(cliente_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()