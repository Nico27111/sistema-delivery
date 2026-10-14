# pedidos.py
import datetime
import sqlite3

DB_NAME = "delivery_app.db"


def crear_pedido(cliente_id, restaurante_id, items):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = sum(cantidad * precio for _, cantidad, precio in items)
    estado = "Pendiente"

    cursor.execute(
        "INSERT INTO pedidos (cliente_id, restaurante_id, fecha, total, estado) VALUES (?, ?, ?, ?, ?)",
        (cliente_id, restaurante_id, fecha, total, estado),
    )
    pedido_id = cursor.lastrowid

    for producto_id, cantidad, precio_unitario in items:
        cursor.execute(
            "INSERT INTO detalle_pedidos (pedido_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, producto_id, cantidad, precio_unitario),
        )

    conn.commit()
    conn.close()
    return pedido_id, total


def obtener_pedidos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.id, c.nombre, r.nombre, p.fecha, p.total, p.estado
        FROM pedidos p
        JOIN clientes c ON p.cliente_id = c.id
        JOIN restaurantes r ON p.restaurante_id = r.id
    """
    )
    pedidos = cursor.fetchall()
    conn.close()
    return pedidos


def obtener_pedidos_por_cliente(cliente_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.id, r.nombre, p.fecha, p.total, p.estado
        FROM pedidos p
        JOIN restaurantes r ON p.restaurante_id = r.id
        WHERE p.cliente_id = ?
    """,
        (cliente_id,),
    )
    pedidos = cursor.fetchall()
    conn.close()
    return pedidos


def cambiar_estado_pedido(pedido_id, nuevo_estado):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pedidos SET estado = ? WHERE id = ?", (nuevo_estado, pedido_id)
    )
    conn.commit()
    conn.close()


def asignar_repartidor_pedido(pedido_id, repartidor_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE pedidos 
        SET repartidor_id = ?, estado = 'Asignado a Repartidor' 
        WHERE id = ?
    """,
        (repartidor_id, pedido_id),
    )
    conn.commit()
    conn.close()


def ver_detalle_pedido(pedido_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT pr.nombre, dp.cantidad, dp.precio_unitario, (dp.cantidad * dp.precio_unitario)
        FROM detalle_pedidos dp
        JOIN productos pr ON dp.producto_id = pr.id
        WHERE dp.pedido_id = ?
    """,
        (pedido_id,),
    )
    detalle = cursor.fetchall()

    cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
    pedido = cursor.fetchone()

    conn.close()
    return pedido, detalle


def obtener_productos_por_restaurante(restaurante_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, precio, imagen_path FROM productos WHERE restaurante_id = ?",
        (restaurante_id,),
    )
    productos = cursor.fetchall()
    conn.close()
    return productos