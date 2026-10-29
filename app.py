import streamlit as st
import sqlite3
import pandas as pd
import os
import hashlib
from datetime import datetime, timedelta
from database import obtener_conexion, inicializar_base_datos

# Inicializar base de datos externa
inicializar_base_datos()
os.makedirs("uploads", exist_ok=True)

st.set_page_config(
    page_title="Sistema de Delivery Multi-Rol",
    page_icon="🛵",
    layout="wide"
)

# ==========================================
# GESTIÓN DE SESIÓN Y PERSISTENCIA (F5 / Recarga)
# ==========================================
if "usuario_autenticado" not in st.session_state:
    if "auth" in st.query_params and st.query_params["auth"] == "true":
        st.session_state["usuario_autenticado"] = True
        st.session_state["nombre_usuario"] = st.query_params.get("user", "")
        st.session_state["tipo_usuario"] = st.query_params.get("role", "")
        st.session_state["id_usuario"] = int(st.query_params.get("id", 0))
    else:
        st.session_state["usuario_autenticado"] = False
        st.session_state["nombre_usuario"] = ""
        st.session_state["tipo_usuario"] = ""
        st.session_state["id_usuario"] = None

if "carrito" not in st.session_state:
    st.session_state["carrito"] = []

def cerrar_sesion():
    st.session_state["usuario_autenticado"] = False
    st.session_state["nombre_usuario"] = ""
    st.session_state["tipo_usuario"] = ""
    st.session_state["id_usuario"] = None
    st.session_state["carrito"] = []
    st.query_params.clear()

def validar_login_directo(nombre_o_correo, password):
    """Función de inicio de sesión robusta que valida contraseñas hasheadas y en texto plano"""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        pass_hashed = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            SELECT * FROM usuarios 
            WHERE (nombre_usuario = ? OR correo_electronico = ?)
        """, (nombre_o_correo, nombre_o_correo))
        usuario = cursor.fetchone()
        conexion.close()
        
        if usuario:
            u_dict = dict(usuario)
            pass_registrada = u_dict.get('contrasena') or u_dict.get('contrasena_hash') or u_dict.get('password')
            
            # Comparamos tanto el hash como texto plano por compatibilidad total con registros anteriores
            if pass_registrada == pass_hashed or pass_registrada == password:
                return u_dict
        return None
    except Exception as e:
        print(f"Error en login: {e}")
        return None

def registrar_usuario_directo(nombre, correo, password, tipo_rol, direccion="", telefono=""):
    """Función de registro dinámica e infalible que se adapta a la estructura real de la tabla usuarios"""
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT id_usuario FROM usuarios WHERE nombre_usuario = ? OR correo_electronico = ?", (nombre, correo))
        if cursor.fetchone():
            conexion.close()
            return False, "El nombre de usuario o correo electrónico ya están registrados."
        
        pass_hashed = hashlib.sha256(password.encode()).hexdigest()
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("PRAGMA table_info(usuarios)")
        columnas_info = cursor.fetchall()
        nombres_columnas = [col[1] for col in columnas_info]
        
        valores_posibles = {
            "nombre_usuario": nombre,
            "correo_electronico": correo,
            "contrasena_hash": pass_hashed,
            "contrasena": pass_hashed,
            "tipo_usuario": tipo_rol,
            "direccion": direccion,
            "telefono": telefono,
            "fecha_registro": fecha_actual
        }
        
        columnas_a_insertar = []
        valores_a_insertar = []
        
        for col in nombres_columnas:
            if col in valores_posibles and col != "id_usuario":
                columnas_a_insertar.append(col)
                valores_a_insertar.append(valores_posibles[col])
                
        cols_sql = ", ".join(columnas_a_insertar)
        placeholders = ", ".join(["?"] * len(columnas_a_insertar))
        sql = f"INSERT INTO usuarios ({cols_sql}) VALUES ({placeholders})"
        
        cursor.execute(sql, tuple(valores_a_insertar))
        conexion.commit()
        conexion.close()
        return True, "Registro exitoso."
    except Exception as e:
        return False, f"Error en la base de datos: {e}"

def mostrar_recibo_pedido(id_pedido):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute("""
        SELECT p.*, r.nombre_restaurante, r.direccion as dir_rest
        FROM pedidos p
        LEFT JOIN restaurantes r ON p.id_restaurante = r.id_restaurante
        WHERE p.id_pedido = ?
    """, (id_pedido,))
    pedido = cursor.fetchone()
    
    cursor.execute("""
        SELECT pr.nombre_producto, dp.cantidad, dp.subtotal
        FROM detalle_pedido dp
        JOIN productos pr ON dp.id_producto = pr.id_producto
        WHERE dp.id_pedido = ?
    """, (id_pedido,))
    detalles = cursor.fetchall()
    conexion.close()
    
    if pedido:
        nombre_local = pedido['nombre_restaurante'] if pedido['nombre_restaurante'] else 'Local Eliminado'
        dir_local = pedido['dir_rest'] if pedido['dir_rest'] else 'Sin dirección'
        
        texto_recibo = f"""========================================
       COMPROBANTE DE PAGO / RECIBO
========================================
Comercio: {nombre_local} ({dir_local})
Pedido N°: {pedido['id_pedido']}
Fecha: {pedido['fecha_pedido']}
Estado del Pedido: {pedido['estado_pedido']}
Dirección de Entrega: {pedido['direccion_entrega']}
----------------------------------------
DETALLE DE PRODUCTOS:
"""
        if detalles:
            for item in detalles:
                texto_recibo += f"- {item['nombre_producto']} | Cant: {item['cantidad']} | Subtotal: ${item['subtotal']:.2f}\n"
        else:
            texto_recibo += "Sin detalles registrados.\n"
            
        texto_recibo += f"""----------------------------------------
TOTAL ABONADO: ${pedido['total_pedido']:.2f}
========================================="""

        st.write(f"🧾 **Recibo Pedido #{pedido['id_pedido']}** — Total: **${pedido['total_pedido']:.2f}**")
        
        st.download_button(
            label=f"📥 Descargar Recibo #{pedido['id_pedido']} (TXT)",
            data=texto_recibo,
            file_name=f"recibo_pedido_{pedido['id_pedido']}.txt",
            mime="text/plain",
            key=f"btn_dl_recibo_{id_pedido}"
        )

# ==========================================
# 1. PANTALLA DE AUTENTICACIÓN (LOGIN / REGISTRO)
# ==========================================
if not st.session_state["usuario_autenticado"]:
    st.title("🛵 Sistema de Delivery Multi-Rol")
    st.markdown("Plataforma de gestión de pedidos, comercios y repartidores.")
    
    tab1, tab2, tab3 = st.tabs(["Iniciar Sesión", "Registrarse como Cliente", "Registrarse como Restaurante"])

    with tab1:
        st.subheader("Acceso al Sistema")
        user_login = st.text_input("Nombre de Usuario", key="login_user")
        pass_login = st.text_input("Contraseña", type="password", key="login_pass")
        
        if st.button("Ingresar al Sistema"):
            if user_login and pass_login:
                usuario = validar_login_directo(user_login, pass_login)

                if usuario:
                    st.session_state["usuario_autenticado"] = True
                    st.session_state["id_usuario"] = usuario["id_usuario"]
                    st.session_state["nombre_usuario"] = usuario["nombre_usuario"]
                    st.session_state["tipo_usuario"] = usuario["tipo_usuario"]
                    
                    st.query_params["auth"] = "true"
                    st.query_params["user"] = usuario["nombre_usuario"]
                    st.query_params["role"] = usuario["tipo_usuario"]
                    st.query_params["id"] = str(usuario["id_usuario"])
                    
                    st.success(f"¡Bienvenido, {usuario['nombre_usuario']}!")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifique sus datos.")
            else:
                st.warning("Por favor, complete todos los campos.")

    with tab2:
        st.subheader("Registro de Nuevos Clientes")
        nuevo_user = st.text_input("Nombre de Usuario", key="reg_user")
        nuevo_correo = st.text_input("Correo Electrónico", key="reg_email")
        nuevo_pass = st.text_input("Contraseña", type="password", key="reg_pass")
        nueva_dir = st.text_input("Dirección Predeterminada", key="reg_dir")
        nuevo_tel = st.text_input("Teléfono", key="reg_tel")

        if st.button("Registrarse como Cliente"):
            if nuevo_user and nuevo_correo and nuevo_pass:
                exito, mensaje = registrar_usuario_directo(
                    nuevo_user, nuevo_correo, nuevo_pass, "Cliente", nueva_dir, nuevo_tel
                )
                if exito:
                    st.success("¡Cuenta de cliente creada con éxito! Ya puedes iniciar sesión.")
                else:
                    st.error(mensaje)
            else:
                st.warning("Por favor, complete los campos obligatorios para registrarse.")

    with tab3:
        st.subheader("Registro de Nuevo Restaurante / Comercio")
        st.info("Registra tu local para comenzar a recibir pedidos y administrar tu menú.")
        
        rest_user = st.text_input("Nombre del Restaurante / Usuario", key="reg_rest_user")
        rest_correo = st.text_input("Correo Electrónico", key="reg_rest_correo")
        rest_pass = st.text_input("Contraseña", type="password", key="reg_rest_pass")
        rest_dir = st.text_input("Dirección del Local", key="reg_rest_dir")
        rest_tel = st.text_input("Teléfono de Contacto", key="reg_rest_tel")
        rest_tipo = st.text_input("Tipo de Cocina (Ej. Pizzería, Hamburguesas, Sushi)", key="reg_rest_tipo")
        rest_hap = st.text_input("Hora de Apertura (Ej. 08:00)", value="08:00", key="reg_rest_hap")
        rest_hci = st.text_input("Hora de Cierre (Ej. 23:59)", value="23:59", key="reg_rest_hci")

        if st.button("Registrar mi Restaurante"):
            if rest_user and rest_correo and rest_pass:
                exito, mensaje = registrar_usuario_directo(
                    rest_user, rest_correo, rest_pass, "Restaurante", rest_dir, rest_tel
                )
                if exito:
                    try:
                        con_r = obtener_conexion()
                        cur_r = con_r.cursor()
                        cur_r.execute("""
                            INSERT INTO restaurantes (nombre_restaurante, direccion, tipo_cocina, hora_apertura, hora_cierre)
                            VALUES (?, ?, ?, ?, ?)
                        """, (rest_user, rest_dir, rest_tipo if rest_tipo else 'General', rest_hap, rest_hci))
                        con_r.commit()
                        con_r.close()
                        
                        st.success("¡Restaurante registrado con éxito! Ya puedes iniciar sesión en la pestaña 'Iniciar Sesión'.")
                    except Exception as e:
                        st.error(f"Usuario creado, pero hubo un error al registrar el local: {e}")
                else:
                    st.error(mensaje)
            else:
                st.warning("Por favor, complete los campos obligatorios.")

# ==========================================
# 2. PANALES SEGÚN EL ROL DEL USUARIO
# ==========================================
else:
    rol = st.session_state["tipo_usuario"]

    st.sidebar.title("Panel de Control")
    st.sidebar.write(f"Usuario: **{st.session_state['nombre_usuario']}**")
    st.sidebar.write(f"Rol: **{rol}**")
    
    if st.sidebar.button("Cerrar Sesión"):
        cerrar_sesion()
        st.rerun()

    st.sidebar.divider()

    # ==========================================
    # PANEL DE CLIENTE
    # ==========================================
    if rol == "Cliente":
        st.title("🛒 Panel de Cliente - Catálogo y Pedidos")
        
        tab_cli1, tab_cli2 = st.tabs(["🍽️ Explorar y Comprar", "📦 Mis Pedidos y Recibos"])
        
        with tab_cli1:
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM restaurantes")
            restaurantes = cursor.fetchall()
            
            if restaurantes:
                mapa_restaurantes = {r["nombre_restaurante"]: r["id_restaurante"] for r in restaurantes}
                rest_elegido_nombre = st.selectbox("Selecciona un Restaurante", list(mapa_restaurantes.keys()))
                id_rest_elegido = mapa_restaurantes[rest_elegido_nombre]
                
                st.subheader(f"Menú de {rest_elegido_nombre}")
                cursor.execute("SELECT * FROM productos WHERE id_restaurante = ?", (id_rest_elegido,))
                productos = cursor.fetchall()
                
                if productos:
                    for prod in productos:
                        col_img, col_desc, col_precio, col_btn = st.columns([1, 2, 1, 1])
                        with col_img:
                            if prod["imagen"] and os.path.exists(prod["imagen"]):
                                st.image(prod["imagen"], width=80)
                            else:
                                st.write("🖼️ *Sin imagen*")
                        with col_desc:
                            st.write(f"**{prod['nombre_producto']}**")
                            st.caption(prod["descripcion"])
                        with col_precio:
                            st.write(f"${prod['precio']:.2f}")
                        with col_btn:
                            if st.button("🛒 Agregar", key=f"add_{prod['id_producto']}"):
                                st.session_state["carrito"].append({
                                    "id_producto": prod["id_producto"],
                                    "nombre": prod["nombre_producto"],
                                    "precio": prod["precio"],
                                    "id_restaurante": id_rest_elegido
                                })
                                st.success("¡Agregado!")
                else:
                    st.info("Este restaurante aún no tiene productos disponibles en su menú.")
                
                st.divider()
                st.subheader("🛍️ Tu Carrito de Compras")
                if st.session_state["carrito"]:
                    df_carrito = pd.DataFrame(st.session_state["carrito"])
                    st.dataframe(df_carrito[["nombre", "precio"]], use_container_width=True)
                    total_carrito = df_carrito["precio"].sum()
                    st.write(f"**Total a Pagar:** ${total_carrito:.2f}")
                    
                    dir_entrega = st.text_input("Dirección de Entrega", value="Mi domicilio predeterminado")
                    
                    if st.button("Confirmar y Realizar Pedido"):
                        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute("""
                            INSERT INTO pedidos (id_cliente, id_restaurante, estado_pedido, total_pedido, direccion_entrega, fecha_pedido)
                            VALUES (?, ?, 'Pendiente de Aceptación', ?, ?, ?)
                        """, (st.session_state["id_usuario"], id_rest_elegido, total_carrito, dir_entrega, fecha_actual))
                        id_nuevo_pedido = cursor.lastrowid
                        
                        for item in st.session_state["carrito"]:
                            cursor.execute("""
                                INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, subtotal)
                                VALUES (?, ?, 1, ?)
                            """, (id_nuevo_pedido, item["id_producto"], item["precio"]))
                        
                        conexion.commit()
                        st.session_state["carrito"] = []
                        
                        st.balloons()
                        st.success("🎉 ¡Pedido realizado con éxito! Enviado al comercio para su confirmación. Tienes 5 minutos para cancelarlo si lo deseas.")
                        st.rerun()
                else:
                    st.info("El carrito está vacío. Agrega productos del menú.")
            else:
                st.warning("No hay restaurantes disponibles en este momento.")
            conexion.close()

        with tab_cli2:
            st.subheader("Historial y Descarga de Recibos")
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT p.id_pedido, r.nombre_restaurante, p.estado_pedido, p.total_pedido, p.fecha_pedido, p.direccion_entrega
                FROM pedidos p
                LEFT JOIN restaurantes r ON p.id_restaurante = r.id_restaurante
                WHERE p.id_cliente = ?
                ORDER BY p.id_pedido DESC
            """, (st.session_state["id_usuario"],))
            mis_pedidos = cursor.fetchall()
            conexion.close()
            
            if mis_pedidos:
                for mp in mis_pedidos:
                    nombre_local = mp['nombre_restaurante'] if mp['nombre_restaurante'] else 'Local Eliminado'
                    
                    try:
                        dt_pedido = datetime.strptime(mp['fecha_pedido'], '%Y-%m-%d %H:%M:%S')
                    except Exception:
                        dt_pedido = datetime.now()
                    
                    tiempo_transcurrido = datetime.now() - dt_pedido
                    se_puede_cancelar = (mp['estado_pedido'] == 'Pendiente de Aceptación') and (tiempo_transcurrido < timedelta(minutes=5))
                    
                    with st.expander(f"Pedido #{mp['id_pedido']} | Local: {nombre_local} | Estado: **{mp['estado_pedido']}**"):
                        mostrar_recibo_pedido(mp['id_pedido'])
                        
                        if se_puede_cancelar:
                            minutos_restantes = 5 - int(tiempo_transcurrido.total_seconds() // 60)
                            st.warning(f"⏰ Estás dentro del plazo de cancelación. Tienes aproximadamente {minutos_restantes} minuto(s) restante(s).")
                            
                            if st.button(f"❌ Cancelar Pedido #{mp['id_pedido']}", key=f"cancel_{mp['id_pedido']}"):
                                con_c = obtener_conexion()
                                cur_c = con_c.cursor()
                                cur_c.execute("UPDATE pedidos SET estado_pedido = 'Cancelado' WHERE id_pedido = ?", (mp['id_pedido'],))
                                con_c.commit()
                                con_c.close()
                                st.success("¡Pedido cancelado con éxito!")
                                st.rerun()
                        elif mp['estado_pedido'] == 'Cancelado':
                            st.error("❌ Este pedido fue cancelado.")
                        
                        st.divider()
                        if st.button(f"🗑️ Eliminar Pedido #{mp['id_pedido']} de mi historial", key=f"del_cli_{mp['id_pedido']}"):
                            con_del = obtener_conexion()
                            cur_del = con_del.cursor()
                            cur_del.execute("DELETE FROM detalle_pedido WHERE id_pedido = ?", (mp['id_pedido'],))
                            cur_del.execute("DELETE FROM pedidos WHERE id_pedido = ? AND id_cliente = ?", (mp['id_pedido'], st.session_state["id_usuario"]))
                            con_del.commit()
                            con_del.close()
                            st.success(f"Pedido #{mp['id_pedido']} eliminado de tu historial.")
                            st.rerun()
            else:
                st.info("Aún no has realizado ningún pedido.")

    # ==========================================
    # PANEL DE RESTAURANTE / VENDEDOR
    # ==========================================
    elif rol == "Restaurante":
        st.title("🍔 Panel de Vendedor / Restaurante")
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT * FROM restaurantes WHERE nombre_restaurante = ?", (st.session_state["nombre_usuario"],))
        mi_restaurante = cursor.fetchone()
        
        if not mi_restaurante:
            cursor.execute("SELECT * FROM restaurantes")
            todos_rests = cursor.fetchall()
            if todos_rests:
                mapa_temp = {r["nombre_restaurante"]: r for r in todos_rests}
                local_seleccionado = st.selectbox("Selecciona tu local asignado", list(mapa_temp.keys()))
                mi_restaurante = mapa_temp[local_seleccionado]

        nuevos_pedidos_count = 0
        if mi_restaurante:
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM pedidos 
                WHERE id_restaurante = ? AND estado_pedido = 'Pendiente de Aceptación'
            """, (mi_restaurante["id_restaurante"],))
            res_nuevos = cursor.fetchone()
            nuevos_pedidos_count = res_nuevos["total"] if res_nuevos else 0
            
        conexion.close()

        if mi_restaurante:
            st.write(f"Gestionando local: **{mi_restaurante['nombre_restaurante']}** (ID Local: {mi_restaurante['id_restaurante']})")
            
            if nuevos_pedidos_count > 0:
                st.markdown(f"""
                    <div style="background-color: #ff4b4b; padding: 15px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 20px;">
                        🚨 ¡ATENCIÓN! Tienes {nuevos_pedidos_count} nuevo(s) pedido(s) esperando confirmación en la pestaña 'Comandas / Pedidos Recibidos'.
                    </div>
                """, unsafe_allow_html=True)

            tab_v1, tab_v2 = st.tabs([
                "🍕 Administrar Mi Menú", 
                f"📋 Comandas / Pedidos Recibidos ({nuevos_pedidos_count})"
            ])
            
            with tab_v1:
                st.subheader("Agregar Producto con Imagen a tu Menú")
                with st.form("form_nuevo_prod", clear_on_submit=True):
                    n_prod = st.text_input("Nombre del Producto")
                    d_prod = st.text_area("Descripción")
                    p_prod = st.number_input("Precio ($)", min_value=0.0, step=10.0)
                    img_prod = st.file_uploader("Imagen del Producto", type=["png", "jpg", "jpeg"])
                    
                    btn_p = st.form_submit_button("Guardar Producto en el Menú")
                    
                    if btn_p:
                        if n_prod and p_prod > 0:
                            ruta_imagen = None
                            if img_prod is not None:
                                ruta_imagen = os.path.join("uploads", img_prod.name)
                                with open(ruta_imagen, "wb") as f:
                                    f.write(img_prod.getbuffer())

                            con_p = obtener_conexion()
                            cur_p = con_p.cursor()
                            cur_p.execute("""
                                INSERT INTO productos (id_restaurante, nombre_producto, descripcion, precio, disponibilidad, imagen)
                                VALUES (?, ?, ?, ?, 1, ?)
                            """, (mi_restaurante["id_restaurante"], n_prod, d_prod, p_prod, ruta_imagen))
                            con_p.commit()
                            con_p.close()
                            
                            st.success("✅ ¡Producto agregado al menú con éxito!")
                            st.rerun()
                        else:
                            st.warning("Complete el nombre y asegúrese de que el precio sea mayor a 0.")
                
                st.divider()
                st.subheader("Tu Menú Actual (Eliminar Productos)")
                con_m = obtener_conexion()
                cur_m = con_m.cursor()
                cur_m.execute("SELECT id_producto, nombre_producto, descripcion, precio, disponibilidad, imagen FROM productos WHERE id_restaurante = ?", (mi_restaurante["id_restaurante"],))
                menu_actual = cur_m.fetchall()
                con_m.close()
                
                if menu_actual:
                    for m in menu_actual:
                        col_i, col_d, col_btn = st.columns([1, 3, 1])
                        with col_i:
                            if m["imagen"] and os.path.exists(m["imagen"]):
                                st.image(m["imagen"], width=70)
                            else:
                                st.write("Sin imagen")
                        with col_d:
                            st.write(f"**{m['nombre_producto']}** - ${m['precio']:.2f}")
                            st.caption(m["descripcion"])
                        with col_btn:
                            if st.button("🗑️ Eliminar", key=f"del_prod_{m['id_producto']}"):
                                con_dp = obtener_conexion()
                                cur_dp = con_dp.cursor()
                                cur_dp.execute("DELETE FROM productos WHERE id_producto = ?", (m['id_producto'],))
                                con_dp.commit()
                                con_dp.close()
                                st.success(f"Producto '{m['nombre_producto']}' eliminado correctamente.")
                                st.rerun()
                        st.divider()
                else:
                    st.info("No tienes productos cargados en tu menú actualmente para este local.")

            with tab_v2:
                st.subheader("Control de Comandas y Recibos")
                con_ped = obtener_conexion()
                cur_ped = con_ped.cursor()
                cur_ped.execute("""
                    SELECT id_pedido, id_cliente, estado_pedido, total_pedido, direccion_entrega, fecha_pedido
                    FROM pedidos WHERE id_restaurante = ? AND estado_pedido != 'Cancelado'
                    ORDER BY id_pedido DESC
                """, (mi_restaurante["id_restaurante"],))
                comandas = cur_ped.fetchall()
                con_ped.close()
                
                if comandas:
                    for com in comandas:
                        badge = "🚨 [NUEVO]" if com['estado_pedido'] == 'Pendiente de Aceptación' else ""
                        with st.expander(f"{badge} Pedido #{com['id_pedido']} - Estado: **{com['estado_pedido']}**"):
                            mostrar_recibo_pedido(com['id_pedido'])
                            
                            nuevo_estado = st.selectbox(
                                "Actualizar Estado del Pedido",
                                ["Pendiente de Aceptación", "Listo para entrega"],
                                key=f"est_{com['id_pedido']}"
                            )
                            if st.button("Guardar Estado", key=f"btn_est_{com['id_pedido']}"):
                                con_up = obtener_conexion()
                                cur_up = con_up.cursor()
                                cur_up.execute("UPDATE pedidos SET estado_pedido = ? WHERE id_pedido = ?", (nuevo_estado, com['id_pedido']))
                                con_up.commit()
                                con_up.close()
                                
                                st.balloons()
                                if nuevo_estado == "Listo para entrega":
                                    st.success(f"✅ ¡Pedido #{com['id_pedido']} marcado como **Listo para entrega**. ¡Ya está disponible para los repartidores!")
                                else:
                                    st.success(f"✅ ¡Estado del pedido #{com['id_pedido']} actualizado a '{nuevo_estado}'!")
                                st.rerun()
                else:
                    st.info("No hay pedidos activos recibidos para este restaurante.")
        else:
            st.warning("No hay un restaurante registrado con el nombre de tu usuario. Asegúrate de registrarte correctamente.")

    # ==========================================
    # PANEL DE REPARTIDOR
    # ==========================================
    elif rol == "Repartidor":
        st.title("🛵 Panel de Repartidor - Gestión de Entregas")
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total_libres 
            FROM pedidos 
            WHERE repartidor_id IS NULL AND estado_pedido = 'Listo para entrega'
        """)
        resultado_libres = cursor.fetchone()
        total_libres = resultado_libres["total_libres"] if resultado_libres else 0
        conexion.close()

        if total_libres > 0:
            st.markdown(f"""
                <div style="background-color: #ff4b4b; padding: 15px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 20px;">
                    🚨 ¡ATENCIÓN! Hay {total_libres} pedido(s) listos en los comercios esperando repartidor. ¡Revisa la pestaña de 'Pedidos Disponibles'!
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ No hay pedidos listos para entrega en este momento.")

        tab_r1, tab_r2 = st.tabs([
            "📦 Mis Pedidos Asignados", 
            f"🚀 Pedidos Disponibles ({total_libres})"
        ])
        
        with tab_r1:
            st.subheader("Pedidos Asignados a tu Flota")
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT p.id_pedido, r.nombre_restaurante, p.estado_pedido, p.total_pedido, p.direccion_entrega
                FROM pedidos p
                LEFT JOIN restaurantes r ON p.id_restaurante = r.id_restaurante
                WHERE p.repartidor_id = ? AND p.estado_pedido != 'Entregado' AND p.estado_pedido != 'Cancelado'
            """, (st.session_state["id_usuario"],))
            mis_entregas = cursor.fetchall()
            conexion.close()
            
            if mis_entregas:
                for ent in mis_entregas:
                    nombre_local = ent['nombre_restaurante'] if ent['nombre_restaurante'] else 'Local Eliminado'
                    with st.expander(f"Pedido #{ent['id_pedido']} | Local: {nombre_local} | Estado: {ent['estado_pedido']}"):
                        mostrar_recibo_pedido(ent['id_pedido'])
                        nuevo_estado_env = st.selectbox(
                            "Actualizar Estado de Envío",
                            ["En camino", "Entregado"],
                            key=f"env_{ent['id_pedido']}"
                        )
                        if st.button("Actualizar Envío", key=f"btn_env_{ent['id_pedido']}"):
                            con_e = obtener_conexion()
                            cur_e = con_e.cursor()
                            cur_e.execute("UPDATE pedidos SET estado_pedido = ? WHERE id_pedido = ?", (nuevo_estado_env, ent['id_pedido']))
                            con_e.commit()
                            con_e.close()
                            
                            if nuevo_estado_env == "Entregado":
                                st.balloons()
                                st.success(f"🏆 ¡Felicitaciones! Pedido #{ent['id_pedido']} marcado como **Entregado** con éxito.")
                            else:
                                st.success(f"✅ ¡Estado de envío actualizado a '{nuevo_estado_env}'!")
                            st.rerun()
            else:
                st.info("No tienes pedidos asignados actualmente en curso.")

        with tab_r2:
            st.subheader("Bolsa de Pedidos Libres (Listos para Retirar)")
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT p.id_pedido, r.nombre_restaurante, p.estado_pedido, p.total_pedido, p.direccion_entrega
                FROM pedidos p
                LEFT JOIN restaurantes r ON p.id_restaurante = r.id_restaurante
                WHERE p.repartidor_id IS NULL AND p.estado_pedido = 'Listo para entrega'
            """)
            libres = cursor.fetchall()
            conexion.close()
            
            if libres:
                for lib in libres:
                    nombre_local = lib['nombre_restaurante'] if lib['nombre_restaurante'] else 'Local Eliminado'
                    with st.expander(f"🔥 Pedido Libre #{lib['id_pedido']} | Local: {nombre_local} | Total: ${lib['total_pedido']}"):
                        mostrar_recibo_pedido(lib['id_pedido'])
                        if st.button(f"Tomar Pedido #{lib['id_pedido']}", key=f"tomar_{lib['id_pedido']}"):
                            con_t = obtener_conexion()
                            cur_t = con_t.cursor()
                            cur_t.execute("UPDATE pedidos SET repartidor_id = ?, estado_pedido = 'En camino' WHERE id_pedido = ?", (st.session_state["id_usuario"], lib['id_pedido']))
                            con_t.commit()
                            con_t.close()
                            
                            st.balloons()
                            st.success(f"🚀 ¡Te has asignado el pedido #{lib['id_pedido']} con éxito! Ya aparece en tus pedidos asignados.")
                            st.rerun()
            else:
                st.info("No hay pedidos listos para retirar por los repartidores en este momento.")

    # ==========================================
    # PANEL DE ADMINISTRADOR (SOLO VISTA DE RESTAURANTES)
    # ==========================================
    elif rol == "Administrador":
        st.title("🛠️ Panel de Administración Global")
        st.info("Control centralizado de usuarios, visualización de comercios, flota y reportes.")
        
        tab_admin1, tab_admin2, tab_admin3, tab_admin4, tab_admin5 = st.tabs([
            "👥 Usuarios", 
            "➕ Cargar Personal", 
            "🏪 Ver Restaurantes", 
            "📦 Pedidos & Recibos", 
            "📊 Reportes CSV"
        ])
        
        with tab_admin1:
            st.subheader("Gestión Global de Usuarios")
            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor()
                cursor.execute("SELECT id_usuario, nombre_usuario, correo_electronico, tipo_usuario, fecha_registro FROM usuarios")
                usuarios = cursor.fetchall()
                conexion.close()
                
                if usuarios:
                    st.dataframe([dict(u) for u in usuarios], use_container_width=True)
                else:
                    st.warning("No hay usuarios registrados.")
            except Exception as e:
                st.error(f"Error al cargar los usuarios: {e}")

        with tab_admin2:
            st.subheader("Alta Exclusiva de Repartidores o Administradores")
            
            with st.form("form_alta_privilegiada"):
                nombre_personal = st.text_input("Nombre de Usuario")
                correo_personal = st.text_input("Correo Electrónico")
                pass_personal = st.text_input("Contraseña Temporal", type="password")
                rol_seleccionado = st.selectbox("Rol a Asignar", ["Repartidor", "Administrador"])
                dir_personal = st.text_input("Dirección (Opcional)")
                tel_personal = st.text_input("Teléfono (Opcional)")
                
                btn_crear_privilegiado = st.form_submit_button("Crear Cuenta")
                
                if btn_crear_privilegiado:
                    if nombre_personal and correo_personal and pass_personal:
                        exito, mensaje = registrar_usuario_directo(
                            nombre_personal, correo_personal, pass_personal, rol_seleccionado, dir_personal, tel_personal
                        )
                        if exito:
                            st.success(f"✅ ¡Cuenta de tipo '{rol_seleccionado}' creada con éxito para {nombre_personal}!")
                        else:
                            st.error(mensaje)
                    else:
                        st.warning("Por favor, complete los campos obligatorios.")

        with tab_admin3:
            st.subheader("Restaurantes Registrados (Solo Visualización)")
            st.info("Los restaurantes se registran de forma autónoma desde la pantalla de inicio.")
            
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM restaurantes")
            restaurantes = cursor.fetchall()
            conexion.close()
            
            if restaurantes:
                st.dataframe([dict(r) for r in restaurantes], use_container_width=True)
            else:
                st.info("No hay restaurantes registrados en el sistema.")

        with tab_admin4:
            st.subheader("Control de Pedidos y Descarga de Recibos")
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT id_pedido, id_cliente, id_restaurante, estado_pedido, total_pedido, repartidor_id 
                FROM pedidos
            """)
            pedidos = cursor.fetchall()
            cursor.execute("SELECT id_usuario, nombre_usuario FROM usuarios WHERE tipo_usuario = 'Repartidor'")
            repartidores = cursor.fetchall()
            conexion.close()
            
            if pedidos:
                for p in pedidos:
                    with st.expander(f"Pedido #{p['id_pedido']} | Estado: {p['estado_pedido']} | Total: ${p['total_pedido']}"):
                        mostrar_recibo_pedido(p['id_pedido'])
                        st.write(f"Repartidor Actual ID: {p['repartidor_id'] if p['repartidor_id'] else 'Sin asignar'}")
                        if repartidores:
                            opciones_repartidores = {r["nombre_usuario"]: r["id_usuario"] for r in repartidores}
                            nombre_rep_sel = st.selectbox(
                                f"Seleccionar Repartidor para Pedido #{p['id_pedido']}",
                                list(opciones_repartidores.keys()),
                                key=f"rep_sel_{p['id_pedido']}"
                            )
                            if st.button(f"Asignar Repartidor al Pedido #{p['id_pedido']}", key=f"btn_asg_{p['id_pedido']}"):
                                id_rep_elegido = opciones_repartidores[nombre_rep_sel]
                                con_up = obtener_conexion()
                                cur_up = con_up.cursor()
                                cur_up.execute("UPDATE pedidos SET repartidor_id = ? WHERE id_pedido = ?", (id_rep_elegido, p["id_pedido"]))
                                con_up.commit()
                                con_up.close()
                                st.success(f"✅ ¡Repartidor {nombre_rep_sel} asignado!")
                                st.rerun()
                        else:
                            st.warning("No hay repartidores registrados.")
            else:
                st.info("No hay pedidos registrados.")

        with tab_admin5:
            st.subheader("Generación de Reportes y Datos Operativos")
            if st.button("Generar Reporte de Pedidos en CSV"):
                conexion = obtener_conexion()
                cursor = conexion.cursor()
                cursor.execute("SELECT * FROM pedidos")
                filas = cursor.fetchall()
                conexion.close()
                if filas:
                    df_pedidos = pd.DataFrame([dict(f) for f in filas])
                    csv_data = df_pedidos.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Descargar CSV de Pedidos",
                        data=csv_data,
                        file_name="reporte_pedidos.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No hay datos suficientes.")