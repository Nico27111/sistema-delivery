# app.py
import datetime
import pandas as pd
import streamlit as st

from database import (
    crear_tablas,
    registrar_usuario_cliente,
    validar_login,
)

crear_tablas()

from clientes import obtener_clientes
from pedidos import (
    asignar_repartidor_pedido,
    cambiar_estado_pedido,
    crear_pedido,
    obtener_pedidos,
    obtener_pedidos_por_cliente,
    obtener_productos_por_restaurante,
    ver_detalle_pedido,
)
from productos import obtener_productos, crear_producto
from repartidores import (
    eliminar_repartidor,
    obtener_repartidores,
    registrar_usuario_repartidor,
)
from restaurantes import (
    crear_restaurante,
    eliminar_restaurante,
    obtener_restaurantes,
)
from vendedores import (
    eliminar_vendedor,
    obtener_vendedores,
    registrar_usuario_vendedor,
)

st.set_page_config(
    page_title="Sistema de Delivery Multi-Rol", page_icon="🛵", layout="wide"
)

# Inicialización de la sesión
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = None
    st.session_state["rol"] = None
    st.session_state["cliente_id"] = None
    st.session_state["restaurante_id"] = None

# ==========================================
# 1. PANTALLA DE LOGIN Y REGISTRO PUBLICO
# ==========================================
if not st.session_state["autenticado"]:
    st.title("🛵 Bienvenido al Sistema de Delivery")

    tab_login, tab_registro = st.tabs(
        ["🔑 Iniciar Sesión", "📝 Registro de Clientes"]
    )

    with tab_login:
        st.subheader("Ingreso de Usuarios")
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")

        if st.button("Ingresar"):
            datos_usuario = validar_login(user, pwd)
            if datos_usuario:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = datos_usuario[1]
                st.session_state["rol"] = datos_usuario[2]
                st.session_state["cliente_id"] = datos_usuario[3]
                st.session_state["restaurante_id"] = datos_usuario[4]
                st.success(f"¡Bienvenido {datos_usuario[1]}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

    with tab_registro:
        st.subheader("Crear Cuenta de Cliente")
        reg_user = st.text_input("Nuevo Usuario")
        reg_pwd = st.text_input("Nueva Contraseña", type="password")
        reg_nombre = st.text_input("Nombre Completo")
        reg_tel = st.text_input("Teléfono")
        reg_dir = st.text_input("Dirección de Entrega")

        if st.button("Registrarme"):
            if reg_user and reg_pwd and reg_nombre:
                try:
                    registrar_usuario_cliente(
                        reg_user, reg_pwd, reg_nombre, reg_tel, reg_dir
                    )
                    st.success(
                        "✅ Registro exitoso. Ya podés iniciar sesión."
                    )
                except Exception:
                    st.error("El nombre de usuario ya está registrado.")
            else:
                st.warning("Completa todos los campos obligatorios.")

# ==========================================
# 2. VISTAS PROTEGIDAS SEGÚN EL ROL
# ==========================================
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['usuario']}")
    st.sidebar.caption(f"Rol: **{st.session_state['rol']}**")

    if st.sidebar.button("🔴 Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()

    st.sidebar.divider()

    # ----------------------------------------------------
    # VISTA 1: CLIENTE
    # ----------------------------------------------------
    if st.session_state["rol"] == "Cliente":
        st.title("🛒 Tienda de Pedidos")

        restaurantes = obtener_restaurantes()
        if not restaurantes:
            st.info("No hay restaurantes registrados por el momento.")
        else:
            tab1, tab2 = st.tabs(["🍕 Realizar Pedido", "📦 Mis Pedidos"])

            with tab1:
                resto_dict = {f"{r[1]}": r[0] for r in restaurantes}
                r_select = st.selectbox(
                    "Seleccione Restaurante:", list(resto_dict.keys())
                )
                r_id = resto_dict[r_select]

                prods = obtener_productos_por_restaurante(r_id)
                if not prods:
                    st.info(
                        "Este restaurante aún no cargó productos a su menú."
                    )
                else:
                    st.subheader("Catálogo de Productos")
                    items_pedido = []

                    for p in prods:
                        col_img, col_info = st.columns([1, 3])

                        with col_img:
                            if len(p) > 3 and p[3]:
                                st.image(p[3], width=100)
                            else:
                                st.image(
                                    "https://via.placeholder.com/100",
                                    width=100,
                                )

                        with col_info:
                            cant = st.number_input(
                                f"**{p[1]}** — ${p[2]:.2f}",
                                min_value=0,
                                step=1,
                                key=f"cli_p_{p[0]}",
                            )
                            if cant > 0:
                                items_pedido.append((p[0], cant, p[2]))
                        st.divider()

                    if st.button("🚀 Confirmar Pedido"):
                        if items_pedido:
                            p_id, total = crear_pedido(
                                st.session_state["cliente_id"],
                                r_id,
                                items_pedido,
                            )
                            st.balloons()
                            st.success(
                                f"🎉 ¡Pedido #{p_id} realizado! Total: ${total:.2f}"
                            )

                            # Comprobante / Ticket descargable
                            ticket_texto = f"""========================================
       TICKET DE COMPRA - DELIVERY APP
========================================
Nro. de Pedido : #{p_id}
Fecha/Hora     : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Restaurante    : {r_select}
----------------------------------------
DETALLE DE PRODUCTOS:
"""
                            for _, cant, prec in items_pedido:
                                ticket_texto += f"- Cantidad: {cant} | Subtotal: ${cant * prec:.2f}\n"

                            ticket_texto += f"""----------------------------------------
TOTAL ABONADO: ${total:.2f}
========================================
¡Gracias por tu compra!
"""
                            st.download_button(
                                label="📄 Descargar Comprobante / Ticket (TXT)",
                                data=ticket_texto,
                                file_name=f"ticket_pedido_{p_id}.txt",
                                mime="text/plain",
                            )
                        else:
                            st.warning("Agregue al menos un producto.")

            with tab2:
                st.subheader("Estado de tus Pedidos")

                # Inicializar el registro de estados anteriores en la sesión (RF-10)
                if "last_order_states" not in st.session_state:
                    st.session_state["last_order_states"] = {}

                mis_pedidos = obtener_pedidos_por_cliente(
                    st.session_state["cliente_id"]
                )

                if mis_pedidos:
                    # --- SISTEMA DE NOTIFICACIONES IN-APP (RF-10) ---
                    for p in mis_pedidos:
                        p_id, resto_nom, fecha, total, estado_actual = (
                            p[0],
                            p[1],
                            p[2],
                            p[3],
                            p[4],
                        )

                        if p_id in st.session_state["last_order_states"]:
                            estado_anterior = st.session_state[
                                "last_order_states"
                            ][p_id]
                            if estado_anterior != estado_actual:
                                st.toast(
                                    f"🔔 ¡Actualización en Pedido #{p_id} ({resto_nom})! Nuevo estado: **{estado_actual}**",
                                    icon="🚀",
                                )

                        st.session_state["last_order_states"][
                            p_id
                        ] = estado_actual
                    # -----------------------------------------------

                    df = pd.DataFrame(
                        mis_pedidos,
                        columns=[
                            "ID",
                            "Restaurante",
                            "Fecha",
                            "Total ($)",
                            "Estado",
                        ],
                    )
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No tenés pedidos activos o registrados.")

    # ----------------------------------------------------
    # VISTA 2: VENDEDOR (RESTAURANTE)
    # ----------------------------------------------------
    elif st.session_state["rol"] == "Vendedor":
        st.title("🍳 Panel del Restaurante / Cocina")

        r_id = st.session_state["restaurante_id"]

        tab1, tab2 = st.tabs(
            ["📋 Comandas / Pedidos Recibidos", "🍔 Mi Menú de Productos"]
        )

        with tab1:
            st.subheader("Gestionar Comandas")
            todos_pedidos = obtener_pedidos()

            resto_info = [
                r
                for r in obtener_restaurantes()
                if r[0] == st.session_state["restaurante_id"]
            ]
            r_nombre = resto_info[0][1] if resto_info else ""

            mis_pedidos = [p for p in todos_pedidos if p[2] == r_nombre]

            if mis_pedidos:
                df_p = pd.DataFrame(
                    mis_pedidos,
                    columns=[
                        "ID Pedido",
                        "Cliente",
                        "Restaurante",
                        "Fecha",
                        "Total ($)",
                        "Estado",
                    ],
                )
                st.dataframe(
                    df_p[
                        ["ID Pedido", "Cliente", "Fecha", "Total ($)", "Estado"]
                    ],
                    use_container_width=True,
                )

                st.divider()
                col1, col2 = st.columns(2)

                with col1:
                    p_id_est = st.number_input(
                        "ID de Pedido", min_value=1, step=1
                    )
                    nuevo_est = st.selectbox(
                        "Nuevo Estado",
                        [
                            "En preparación",
                            "Listo para despacho",
                            "En camino",
                            "Entregado",
                            "Cancelado",
                        ],
                    )
                    if st.button("Actualizar Estado"):
                        cambiar_estado_pedido(p_id_est, nuevo_est)
                        st.success(
                            f"Pedido #{p_id_est} cambiado a '{nuevo_est}'."
                        )
                        st.rerun()

                with col2:
                    p_id_ver = st.number_input(
                        "Ver detalle de Pedido ID", min_value=1, step=1
                    )
                    if st.button("🔍 Ver Ítems"):
                        ped, det = ver_detalle_pedido(p_id_ver)
                        if ped:
                            st.table(
                                pd.DataFrame(
                                    det,
                                    columns=[
                                        "Producto",
                                        "Cantidad",
                                        "Precio U.",
                                        "Subtotal",
                                    ],
                                )
                            )
            else:
                st.info("No hay pedidos registrados para tu restaurante.")

        with tab2:
            st.subheader("Agregar Producto a tu Menú")
            with st.form("form_vendor_prod", clear_on_submit=True):
                nom = st.text_input("Nombre del plato/producto")
                desc = st.text_area("Descripción")
                precio = st.number_input(
                    "Precio ($)", min_value=0.0, format="%.2f"
                )
                imagen_subida = st.file_uploader(
                    "Fotografía del plato", type=["jpg", "jpeg", "png"]
                )

                if st.form_submit_button("Guardar Producto"):
                    if nom and precio > 0:
                        crear_producto(
                            r_id, nom, desc, precio, imagen_subida
                        )
                        st.success("✅ Producto agregado a tu carta.")
                        st.rerun()

            st.subheader("Menú Actual")
            prods = obtener_productos_por_restaurante(r_id)
            if prods:
                df_menu = pd.DataFrame(
                    prods, columns=["ID", "Producto", "Precio ($)", "Imagen"]
                )
                st.dataframe(
                    df_menu[["ID", "Producto", "Precio ($)"]],
                    use_container_width=True,
                )

    # ----------------------------------------------------
    # VISTA 3: REPARTIDOR (LOGÍSTICA)
    # ----------------------------------------------------
    elif st.session_state["rol"] == "Repartidor":
        st.title("🛵 Panel del Repartidor / Logística")

        st.subheader("📦 Pedidos Listos para Entrega")
        pedidos = obtener_pedidos()

        if pedidos:
            df_rep_pedidos = pd.DataFrame(
                pedidos,
                columns=[
                    "ID",
                    "Cliente",
                    "Restaurante",
                    "Fecha",
                    "Total ($)",
                    "Estado",
                ],
            )
            st.dataframe(df_rep_pedidos, use_container_width=True)

            st.divider()
            st.markdown("### 🎯 Confirmar Entrega de Pedido (RF-08)")

            ids_validos = [p[0] for p in pedidos]

            with st.form("form_entrega"):
                p_id_entrega = st.number_input(
                    "ID de Pedido entregado", min_value=1, step=1
                )
                submit_entrega = st.form_submit_button("✅ Confirmar Entrega Final")

                if submit_entrega:
                    if p_id_entrega in ids_validos:
                        cambiar_estado_pedido(p_id_entrega, "Entregado")
                        st.balloons()
                        st.success(
                            f"🎉 ¡El pedido #{p_id_entrega} ha sido entregado con éxito!"
                        )
                        st.toast(
                            f"Pedido #{p_id_entrega} actualizado a Entregado",
                            icon="✅",
                        )
                        st.rerun()
                    else:
                        st.error(
                            f"⚠️ El ID de pedido #{p_id_entrega} no existe en el sistema."
                        )
        else:
            st.info("No hay pedidos activos en este momento.")

    # ----------------------------------------------------
    # VISTA 4: ADMINISTRADOR (MÓDULOS, REPORTES Y ASIGNACIÓN)
    # ----------------------------------------------------
    elif st.session_state["rol"] == "Administrador":
        st.title("⚙️ Panel de Administración General")

        menu_admin = st.sidebar.radio(
            "Sección Administrativa",
            [
                "🍽️ Gestión de Restaurantes",
                "👨‍🍳 Gestión de Vendedores",
                "🛵 Gestión de Repartidores",
                "👥 Clientes",
                "🍕 Productos Global",
                "📦 Pedidos Global",
            ],
        )

        # 1. MÓDULO RESTAURANTES
        if menu_admin == "🍽️ Gestión de Restaurantes":
            st.subheader("🍽️ Módulo de Restaurantes")
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("**Registrar Nuevo Local**")
                with st.form("form_crear_resto", clear_on_submit=True):
                    r_nom = st.text_input("Nombre del Restaurante")
                    r_dir = st.text_input("Dirección")
                    r_tel = st.text_input("Teléfono")
                    r_cat = st.text_input("Categoría (ej. Pizza, Sushi)")
                    if st.form_submit_button("Guardar Restaurante"):
                        if r_nom:
                            crear_restaurante(r_nom, r_dir, r_tel, r_cat)
                            st.success("✅ Restaurante creado correctamente.")
                            st.rerun()
                        else:
                            st.warning("El nombre es obligatorio.")

            with col2:
                st.markdown("**Listado de Restaurantes Activos**")
                restos = obtener_restaurantes()
                if restos:
                    df_restos = pd.DataFrame(
                        restos,
                        columns=[
                            "ID",
                            "Nombre",
                            "Dirección",
                            "Teléfono",
                            "Categoría",
                        ],
                    )

                    busq_resto = st.text_input(
                        "🔍 Buscar restaurante...", key="b_resto"
                    )
                    if busq_resto:
                        df_restos = df_restos[
                            df_restos.astype(str)
                            .apply(
                                lambda x: x.str.contains(
                                    busq_resto, case=False, na=False
                                )
                            )
                            .any(axis=1)
                        ]

                    st.dataframe(df_restos, use_container_width=True)

                    st.divider()
                    r_id_del = st.number_input(
                        "ID de Restaurante a eliminar", min_value=1, step=1
                    )
                    if st.button("❌ Eliminar Restaurante"):
                        eliminar_restaurante(r_id_del)
                        st.success(f"Restaurante #{r_id_del} eliminado.")
                        st.rerun()
                else:
                    st.info("No hay restaurantes registrados.")

        # 2. MÓDULO VENDEDORES
        elif menu_admin == "👨‍🍳 Gestión de Vendedores":
            st.subheader("👨‍🍳 Módulo de Cuentas de Vendedores")
            restos = obtener_restaurantes()

            if not restos:
                st.warning(
                    "⚠️ Primero debés registrar al menos un restaurante."
                )
            else:
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.markdown("**Crear Usuario y Clave de Acceso**")
                    resto_map = {f"{r[1]} (ID: {r[0]})": r[0] for r in restos}
                    r_sel = st.selectbox(
                        "Vincular al Restaurante:", list(resto_map.keys())
                    )

                    with st.form("form_crear_vendedor", clear_on_submit=True):
                        v_user = st.text_input("Nombre de Usuario")
                        v_pass = st.text_input("Contraseña", type="password")
                        if st.form_submit_button("Crear Cuenta Vendedor"):
                            if v_user and v_pass:
                                try:
                                    registrar_usuario_vendedor(
                                        v_user, v_pass, resto_map[r_sel]
                                    )
                                    st.success(
                                        f"✅ Vendedor '{v_user}' creado con éxito."
                                    )
                                    st.rerun()
                                except Exception:
                                    st.error(
                                        "El nombre de usuario ya está en uso."
                                    )
                            else:
                                st.warning("Completá usuario y contraseña.")

                with col2:
                    st.markdown("**Vendedores Registrados en el Sistema**")
                    vendedores = obtener_vendedores()
                    if vendedores:
                        df_v = pd.DataFrame(
                            vendedores,
                            columns=["ID Usuario", "Usuario", "Restaurante Asignado"],
                        )

                        busq_vend = st.text_input(
                            "🔍 Buscar vendedor...", key="b_vend"
                        )
                        if busq_vend:
                            df_v = df_v[
                                df_v.astype(str)
                                .apply(
                                    lambda x: x.str.contains(
                                        busq_vend, case=False, na=False
                                    )
                                )
                                .any(axis=1)
                            ]

                        st.dataframe(df_v, use_container_width=True)

                        st.divider()
                        v_id_del = st.number_input(
                            "ID de cuenta a eliminar", min_value=1, step=1
                        )
                        if st.button("❌ Revocar Acceso Vendedor"):
                            eliminar_vendedor(v_id_del)
                            st.success(f"Cuenta #{v_id_del} eliminada.")
                            st.rerun()
                    else:
                        st.info("No hay cuentas de vendedores creadas.")

        # 3. MÓDULO REPARTIDORES
        elif menu_admin == "🛵 Gestión de Repartidores":
            st.subheader("🛵 Módulo de Cuentas de Repartidores")
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("**Crear Cuenta de Repartidor**")
                with st.form("form_crear_rep", clear_on_submit=True):
                    rep_user = st.text_input("Nombre de Usuario")
                    rep_pass = st.text_input("Contraseña", type="password")
                    if st.form_submit_button("Crear Repartidor"):
                        if rep_user and rep_pass:
                            try:
                                registrar_usuario_repartidor(rep_user, rep_pass)
                                st.success(
                                    f"✅ Repartidor '{rep_user}' creado con éxito."
                                )
                                st.rerun()
                            except Exception:
                                st.error("El usuario ya está registrado.")
                        else:
                            st.warning("Completa todos los campos.")

            with col2:
                st.markdown("**Repartidores Registrados en el Sistema**")
                reps = obtener_repartidores()
                if reps:
                    df_reps = pd.DataFrame(reps, columns=["ID Usuario", "Usuario"])
                    st.dataframe(df_reps, use_container_width=True)

                    st.divider()
                    rep_id_del = st.number_input(
                        "ID de Repartidor a revocar", min_value=1, step=1
                    )
                    if st.button("❌ Eliminar Repartidor"):
                        eliminar_repartidor(rep_id_del)
                        st.success("Repartidor eliminado.")
                        st.rerun()
                else:
                    st.info("No hay repartidores registrados.")

        # 4. MÓDULO CLIENTES
        elif menu_admin == "👥 Clientes":
            st.subheader("👥 Clientes Registrados")
            clientes = obtener_clientes()
            if clientes:
                df_cli = pd.DataFrame(
                    clientes, columns=["ID", "Nombre", "Teléfono", "Dirección"]
                )

                busq_cli = st.text_input("🔍 Buscar cliente...", key="b_cli")
                if busq_cli:
                    df_cli = df_cli[
                        df_cli.astype(str)
                        .apply(
                            lambda x: x.str.contains(
                                busq_cli, case=False, na=False
                            )
                        )
                        .any(axis=1)
                    ]

                st.dataframe(df_cli, use_container_width=True)
            else:
                st.info("No hay clientes registrados.")

        # 5. MÓDULO PRODUCTOS GLOBAL
        elif menu_admin == "🍕 Productos Global":
            st.subheader("🍕 Catálogo Completo de Productos")
            prods = obtener_productos()
            if prods:
                df_prod = pd.DataFrame(
                    prods,
                    columns=[
                        "ID",
                        "Producto",
                        "Descripción",
                        "Precio ($)",
                        "Restaurante",
                        "Imagen",
                    ],
                )

                busq_prod = st.text_input(
                    "🔍 Buscar producto o plato...", key="b_prod"
                )
                if busq_prod:
                    df_prod = df_prod[
                        df_prod.astype(str)
                        .apply(
                            lambda x: x.str.contains(
                                busq_prod, case=False, na=False
                            )
                        )
                        .any(axis=1)
                    ]

                st.dataframe(
                    df_prod[["ID", "Producto", "Descripción", "Precio ($)", "Restaurante"]],
                    use_container_width=True,
                )
            else:
                st.info("No hay productos cargados.")

        # 6. MÓDULO PEDIDOS GLOBAL, ASIGNACIÓN Y REPORTES (RF-04 / RF-09)
        elif menu_admin == "📦 Pedidos Global":
            st.subheader("📦 Monitoreo General y Reportes Operativos")
            pedidos = obtener_pedidos()

            if pedidos:
                df_pedidos = pd.DataFrame(
                    pedidos,
                    columns=[
                        "ID",
                        "Cliente",
                        "Restaurante",
                        "Fecha",
                        "Total ($)",
                        "Estado",
                    ],
                )

                # KPIs
                st.markdown("### 📊 Indicadores Clave de Rendimiento (KPIs)")
                total_ventas = df_pedidos["Total ($)"].sum()
                total_ordenes = len(df_pedidos)
                ticket_promedio = (
                    total_ventas / total_ordenes if total_ordenes > 0 else 0
                )

                col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
                col_kpi1.metric("💰 Ventas Totales", f"${total_ventas:,.2f}")
                col_kpi2.metric("📦 Total de Pedidos", total_ordenes)
                col_kpi3.metric("📈 Ticket Promedio", f"${ticket_promedio:,.2f}")

                st.divider()

                # Asignación de Repartidores (RF-04)
                st.markdown("### 🛵 Asignar Pedido a Repartidor (RF-04)")
                reps = obtener_repartidores()
                if reps:
                    col_asg1, col_asg2, col_asg3 = st.columns(3)
                    with col_asg1:
                        p_id_asg = st.number_input(
                            "ID de Pedido", min_value=1, step=1, key="asg_p"
                        )
                    with col_asg2:
                        rep_dict = {f"{r[1]} (ID: {r[0]})": r[0] for r in reps}
                        rep_select = st.selectbox(
                            "Seleccionar Repartidor", list(rep_dict.keys())
                        )
                    with col_asg3:
                        st.write("")
                        st.write("")
                        if st.button("Asignar Envío"):
                            r_id_sel = rep_dict[rep_select]
                            asignar_repartidor_pedido(p_id_asg, r_id_sel)
                            st.success(
                                f"✅ Pedido #{p_id_asg} asignado correctamente."
                            )
                            st.rerun()
                else:
                    st.info(
                        "⚠️ Registre al menos un repartidor para poder asignar envíos."
                    )

                st.divider()

                # Gráfico Estadístico
                st.markdown("### 🍔 Ventas Generadas por Restaurante")
                if not df_pedidos.empty:
                    df_ventas_resto = (
                        df_pedidos.groupby("Restaurante")["Total ($)"]
                        .sum()
                        .reset_index()
                    )
                    st.bar_chart(
                        df_ventas_resto.set_index("Restaurante")[
                            "Total ($)"
                        ]
                    )

                st.divider()

                # Buscador, Tabla de Transacciones y Botón de Exportación CSV
                st.markdown("### 📋 Listado Completo de Transacciones")
                busq_ped = st.text_input(
                    "🔍 Buscar por cliente, restaurante o estado...", key="b_ped"
                )
                if busq_ped:
                    df_pedidos = df_pedidos[
                        df_pedidos.astype(str)
                        .apply(
                            lambda x: x.str.contains(
                                busq_ped, case=False, na=False
                            )
                        )
                        .any(axis=1)
                    ]

                st.dataframe(df_pedidos, use_container_width=True)

                st.divider()
                st.markdown("### 📥 Exportar Datos")
                csv_data = df_pedidos.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Descargar Reporte de Pedidos (CSV)",
                    data=csv_data,
                    file_name="reporte_ventas_delivery.csv",
                    mime="text/csv",
                )

            else:
                st.info("No hay pedidos registrados en el sistema.")