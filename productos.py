# productos.py
import os
import sqlite3

DB_NAME = "delivery_app.db"
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def crear_producto(restaurante_id, nombre, descripcion, precio, imagen_file):
    imagen_path = None
    if imagen_file is not None:
        imagen_path = os.path.join(UPLOAD_FOLDER, imagen_file.name)
        with open(imagen_path, "wb") as f:
            f.write(imagen_file.getbuffer())

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO productos (restaurante_id, nombre, descripcion, precio, imagen_path) 
        VALUES (?, ?, ?, ?, ?)
    """,
        (restaurante_id, nombre, descripcion, precio, imagen_path),
    )
    conn.commit()
    conn.close()


def obtener_productos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.id, p.nombre, p.descripcion, p.precio, r.nombre, p.imagen_path 
        FROM productos p
        JOIN restaurantes r ON p.restaurante_id = r.id
    """
    )
    productos = cursor.fetchall()
    conn.close()
    return productos


def eliminar_producto(producto_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT imagen_path FROM productos WHERE id = ?", (producto_id,))
    res = cursor.fetchone()
    if res and res[0] and os.path.exists(res[0]):
        os.remove(res[0])

    cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    conn.commit()
    conn.close()