import sqlite3

DB_NAME = "delivery.db"

def obtener_conexion():
    """Establece y devuelve una conexión a la base de datos SQLite con WAL y timeout."""
    conexion = sqlite3.connect(DB_NAME, timeout=15.0)
    conexion.row_factory = sqlite3.Row
    # Activar el modo WAL para evitar errores de "database is locked"
    conexion.execute("PRAGMA journal_mode=WAL;")
    return conexion

def inicializar_base_datos():
    """Crea las tablas del sistema si no existen y aplica migraciones necesarias."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # 1. Tabla de Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_usuario TEXT UNIQUE NOT NULL,
        correo_electronico TEXT NOT NULL,
        contrasena_hash TEXT NOT NULL,
        tipo_usuario TEXT NOT NULL,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Tabla de Clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
        direccion_predeterminada TEXT,
        telefono TEXT
    );
    """)

    # 3. Tabla de Restaurantes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurantes (
        id_restaurante INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_restaurante TEXT NOT NULL,
        direccion TEXT,
        tipo_cocina TEXT,
        hora_apertura TEXT,
        hora_cierre TEXT
    );
    """)

    # 4. Tabla de Productos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
        id_restaurante INTEGER,
        nombre_producto TEXT NOT NULL,
        descripcion TEXT,
        precio REAL NOT NULL,
        disponibilidad BOOLEAN DEFAULT 1,
        imagen TEXT,
        FOREIGN KEY (id_restaurante) REFERENCES restaurantes(id_restaurante)
    );
    """)

    # 5. Tabla de Pedidos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER,
        id_restaurante INTEGER,
        repartidor_id INTEGER,
        fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        estado_pedido TEXT DEFAULT 'Pendiente',
        total_pedido REAL,
        direccion_entrega TEXT,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
        FOREIGN KEY (id_restaurante) REFERENCES restaurantes(id_restaurante),
        FOREIGN KEY (repartidor_id) REFERENCES usuarios(id_usuario)
    );
    """)

    # 6. Tabla de Detalle del Pedido
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalle_pedido (
        id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
        id_pedido INTEGER,
        id_producto INTEGER,
        cantidad INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido),
        FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
    );
    """)

    conexion.commit()

    # Migraciones seguras
    try:
        cursor.execute("ALTER TABLE pedidos ADD COLUMN repartidor_id INTEGER;")
        conexion.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN imagen TEXT;")
        conexion.commit()
    except sqlite3.OperationalError:
        pass

    conexion.close()

def crear_tablas():
    return inicializar_base_datos()

def registrar_usuario_cliente(nombre_usuario, correo_electronico, contrasena_hash, tipo_usuario, direccion="", telefono=""):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (nombre_usuario, correo_electronico, contrasena_hash, tipo_usuario)
            VALUES (?, ?, ?, ?)
        """, (nombre_usuario, correo_electronico, contrasena_hash, tipo_usuario))
        
        usuario_id = cursor.lastrowid
        
        if tipo_usuario == "Cliente":
            cursor.execute("""
                INSERT INTO clientes (id_cliente, direccion_predeterminada, telefono)
                VALUES (?, ?, ?)
            """, (usuario_id, direccion, telefono))
            
        conexion.commit()
        return True, "Usuario registrado exitosamente."
    except sqlite3.IntegrityError:
        return False, "El nombre de usuario ya se encuentra registrado."
    finally:
        conexion.close()

def validar_login(nombre_usuario, contrasena_hash):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT * FROM usuarios 
        WHERE nombre_usuario = ? AND contrasena_hash = ?
    """, (nombre_usuario, contrasena_hash))
    usuario = cursor.fetchone()
    conexion.close()
    return usuario