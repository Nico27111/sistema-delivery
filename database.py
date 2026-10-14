# database.py
import sqlite3

DB_NAME = "delivery_app.db"


def crear_tablas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabla Usuarios (Login y Roles: Administrador, Vendedor, Cliente, Repartidor)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            cliente_id INTEGER,
            restaurante_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (restaurante_id) REFERENCES restaurantes(id)
        )
    """
    )

    # Tabla Clientes
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT
        )
    """
    )

    # Tabla Restaurantes
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS restaurantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT,
            telefono TEXT,
            categoria TEXT
        )
    """
    )

    # Tabla Productos
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurante_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL,
            FOREIGN KEY (restaurante_id) REFERENCES restaurantes(id)
        )
    """
    )

    # Asegurar compatibilidad agregando la columna imagen_path si la tabla ya existía
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN imagen_path TEXT")
    except sqlite3.OperationalError:
        pass  # La columna ya existe

    # Tabla Pedidos (Actualizada con repartidor_id)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            restaurante_id INTEGER NOT NULL,
            repartidor_id INTEGER,
            fecha TEXT NOT NULL,
            total REAL NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (restaurante_id) REFERENCES restaurantes(id),
            FOREIGN KEY (repartidor_id) REFERENCES usuarios(id)
        )
    """
    )

    # Tabla Detalle Pedidos
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS detalle_pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """
    )

    # Crear usuario administrador por defecto
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO usuarios (username, password, rol)
            VALUES ('admin', 'admin123', 'Administrador')
        """
        )

    conn.commit()
    conn.close()


def validar_login(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, rol, cliente_id, restaurante_id FROM usuarios WHERE username = ? AND password = ?",
        (username, password),
    )
    usuario = cursor.fetchone()
    conn.close()
    return usuario


def registrar_usuario_cliente(
    username, password, nombre, telefono, direccion
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO clientes (nombre, telefono, direccion) VALUES (?, ?, ?)",
        (nombre, telefono, direccion),
    )
    cliente_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO usuarios (username, password, rol, cliente_id) VALUES (?, ?, 'Cliente', ?)",
        (username, password, cliente_id),
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    crear_tablas()