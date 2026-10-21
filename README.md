# 🛵 Sistema de Delivery Multi-Rol

Aplicación web desarrollada en **Python** utilizando **Streamlit** para la interfaz gráfica y **SQLite** para la gestión de bases de datos relacionales. El sistema implementa un modelo multi-rol completo para la gestión integral de un servicio de delivery.

## ✨ Características Principales
- **Roles de Usuario:**
  - **Cliente:** Registro de cuentas, visualización de catálogo de productos con imágenes, realización de pedidos, seguimiento en tiempo real y descarga de comprobantes en formato TXT.
  - **Vendedor (Restaurante):** Gestión de menús, subida de fotografías de platos mediante `st.file_uploader`, control de comandas y actualización de estados de pedidos.
  - **Repartidor:** Monitoreo de envíos activos y confirmación de entregas con efectos visuales.
  - **Administrador:** Panel de control global con altas/bajas de locales, cuentas de usuarios, asignación de envíos (RF-04), indicadores clave de rendimiento (KPIs), gráficos estadísticos y exportación de reportes operativos en formato CSV.
- **Notificaciones In-App (RF-10):** Alertas visuales flotantes (`st.toast`) para mantener al usuario informado sobre los cambios de estado en sus pedidos.
- **Buscadores en Tiempo Real:** Filtros inteligentes integrados en todos los módulos administrativos.

## 🛠️ Tecnologías Utilizadas
- **Python**
- **Streamlit** (Framework de interfaz web)
- **SQLite3** (Base de datos relacional)
- **Pandas** (Manipulación de datos y tablas)

## 🚀 Cómo ejecutar el proyecto localmente

1. Clonar o descargar este repositorio en tu computadora.
2. Abrir una terminal en la carpeta del proyecto e instalar las dependencias necesarias:
   ```bash
   pip install -r requirements.txt

               USUARIOS Y CONTRASEÑAS:
Administrador: admin        admin123
Vendedor:      vende        vende123
Repartidor:    repa         repa123
Cliente:       cliente      cliente123
