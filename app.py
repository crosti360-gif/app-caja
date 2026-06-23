import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="SIEMBRA CAJA - ERP", layout="wide", page_icon="🌱")

def recargar_app():
    if hasattr(st, 'rerun'):
        st.rerun()
    else:
        st.experimental_rerun()

# --- CONEXIÓN AUTOMÁTICA A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        # ttl="0d" obliga a traer los datos frescos de Google en tiempo real
        return conn.read(worksheet=pestana, ttl="0d")
    except Exception:
        return pd.DataFrame()

def guardar_datos(df, pestana):
    conn.update(worksheet=pestana, data=df)

# --- CARGA DE DATOS DESDE LA NUBE ---
df_clientes = cargar_datos("clientes")
df_productos = cargar_datos("productos")
df_ventas = cargar_datos("ventas")
df_cobranzas = cargar_datos("cobranzas")
df_compras = cargar_datos("compras")
df_retiros = cargar_datos("retiros")

# Asegurar estructuras mínimas por si las pestañas están vacías
if df_clientes.empty:
    df_clientes = pd.DataFrame(columns=["ID", "Cédula", "Nombre", "Teléfono", "Correo", "Dirección", "Fecha de Nacimiento", "Estado", "Saldo"])
if df_productos.empty:
    df_productos = pd.DataFrame(columns=["Código", "Variedad", "Familia", "Stock"])
if df_ventas.empty:
    df_ventas = pd.DataFrame(columns=["Fecha", "Recibo", "Cliente", "Variedad", "Gramos", "Precio/g", "Total", "Condición"])
if df_cobranzas.empty:
    df_cobranzas = pd.DataFrame(columns=["Fecha", "Cliente", "Monto Abonado"])
if df_compras.empty:
    df_compras = pd.DataFrame(columns=["Fecha", "Concepto", "Proveedor", "Monto"])
if df_retiros.empty:
    df_retiros = pd.DataFrame(columns=["Fecha", "Usuario", "Monto"])

# Formateo numérico para evitar errores de cálculo en Pandas
df_clientes["Saldo"] = pd.to_numeric(df_clientes["Saldo"], errors='coerce').fillna(0)
df_productos["Stock"] = pd.to_numeric(df_productos["Stock"], errors='coerce').fillna(0)

# --- MENÚ DE NAVEGACIÓN ---
st.sidebar.title("🌱 SIEMBRA CAJA")
st.sidebar.write("Sistema de Gestión Comercial")
menu = st.sidebar.radio("Ir a:", [
    "📊 Dashboard", 
    "👥 Clientes y Cobranzas", 
    "🌿 Inventario y Variedades", 
    "🛍️ Registrar Venta", 
    "💸 Compras y Retiros", 
    "💰 Caja y Finanzas"
])

# ==========================================
# --- MODULO 1: DASHBOARD ---
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 Panel de Control General")
    st.write("Resumen automatizado en tiempo real sincronizado con Google Sheets.")
    
    total_ventas = pd.to_numeric(df_ventas["Total"], errors='coerce').sum() if not df_ventas.empty else 0
    deuda_total = df_clientes["Saldo"].sum()
    total_clientes = len(df_clientes)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Ventas Totales Históricas ($)", f"${total_ventas:,.2f}")
    col2.metric("Deuda Pendiente a Cobrar ($)", f"${deuda_total:,.2f}", delta="- Activa", delta_color="inverse")
    col3.metric("Socios Registrados", total_clientes)

# ==========================================
# --- MODULO 2: CLIENTES Y COBRANZAS ---
# ==========================================
elif menu == "👥 Clientes y Cobranzas":
    st.title("👥 Base de Datos y Cobros")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Listado de Socios", "➕ Nuevo Socio", "✏️ Editar Socio", "💳 Cobrar Deuda", "🗑️ Eliminar Socio"])
    
    with tab1:
        st.dataframe(df_clientes, use_container_width=True)
        
    with tab2:
        with st.form("nuevo_cliente"):
            st.subheader("Registrar Nuevo Socio")
            col1, col2 = st.columns(2)
            with col1:
                cedula = st.text_input("Cédula de Identidad")
                nombre = st.text_input("Nombre Completo")
                tel = st.text_input("Teléfono")
            with col2:
                correo = st.text_input("Correo Electrónico")
                direccion = st.text_input("Dirección")
                fecha_nac = st.text_input("Fecha de Nacimiento (DD/MM/AAAA)")
            
            enviar = st.form_submit_button("Guardar Socio")
            if enviar and nombre:
                nuevo_id = len(df_clientes) + 1
                nueva_fila = {"ID": nuevo_id, "Cédula": cedula, "Nombre": nombre, "Teléfono": tel, "Correo": correo, "Dirección": direccion, "Fecha de Nacimiento": fecha_nac, "Estado": "Activo", "Saldo": 0}
                df_clientes = pd.concat([df_clientes, pd.DataFrame([nueva_fila])], ignore_index=True)
                guardar_datos(df_clientes, "clientes")
                st.success("Socio guardado en la nube con éxito.")
                recargar_app()

    with tab3:
        st.subheader("Modificar Datos de un Socio Existente")
        if not df_clientes.empty:
            cliente_a_editar = st.selectbox("Seleccione el Socio a editar", df_clientes["Nombre"].tolist(), key="select_editar")
            idx_editar = df_clientes.index[df_clientes["Nombre"] == cliente_a_editar].tolist()[0]
            datos_actuales = df_clientes.iloc[idx_editar]
            
            with st.form("editar_cliente"):
                colA, colB = st.columns(2)
                with colA:
                    edit_cedula = st.text_input("Cédula de Identidad", value=str(datos_actuales.get("Cédula", "")))
                    edit_nombre = st.text_input("Nombre Completo", value=str(datos_actuales.get("Nombre", "")))
                    edit_tel = st.text_input("Teléfono", value=str(datos_actuales.get("Teléfono", "")))
                    edit_estado = st.selectbox("Estado", ["Activo", "Inactivo"], index=0 if datos_actuales.get("Estado", "Activo") == "Activo" else 1)
                with colB:
                    edit_correo = st.text_input("Correo Electrónico", value=str(datos_actuales.get("Correo", "")))
                    edit_direccion = st.text_input("Dirección", value=str(datos_actuales.get("Dirección", "")))
                    edit_fecha_nac = st.text_input("Fecha de Nacimiento (DD/MM/AAAA)", value=str(datos_actuales.get("Fecha de Nacimiento", "")))
                
                btn_guardar_cambios = st.form_submit_button("Guardar Cambios")
                if btn_guardar_cambios and edit_nombre:
                    viejo_nombre = datos_actuales["Nombre"]
                    df_clientes.at[idx_editar, "Cédula"] = edit_cedula
                    df_clientes.at[idx_editar, "Nombre"] = edit_nombre
                    df_clientes.at[idx_editar, "Teléfono"] = edit_tel
                    df_clientes.at[idx_editar, "Correo"] = edit_correo
                    df_clientes.at[idx_editar, "Dirección"] = edit_direccion
                    df_clientes.at[idx_editar, "Fecha de Nacimiento"] = edit_fecha_nac
                    df_clientes.at[idx_editar, "Estado"] = edit_estado
                    
                    if viejo_nombre != edit_nombre:
                        if not df_ventas.empty:
                            df_ventas.loc[df_ventas["Cliente"] == viejo_nombre, "Cliente"] = edit_nombre
                            guardar_datos(df_ventas, "ventas")
                        if not df_cobranzas.empty:
                            df_cobranzas.loc[df_cobranzas["Cliente"] == viejo_nombre, "Cliente"] = edit_nombre
                            guardar_datos(df_cobranzas, "cobranzas")
                            
                    guardar_datos(df_clientes, "clientes")
                    st.success("Datos actualizados correctamente.")
                    recargar_app()
        else:
            st.info("No hay socios registrados para editar.")

    with tab4:
        st.subheader("Cobrar deuda a cliente")
        deudores = df_clientes[df_clientes["Saldo"] > 0]
        if deudores.empty:
            st.info("No hay clientes con deudas pendientes actualmente.")
        else:
            with st.form("cobrar_deuda"):
                cliente_cobro = st.selectbox("Seleccionar Socio Deudor", deudores["Nombre"].tolist())
                deuda_actual = deudores[deudores["Nombre"] == cliente_cobro]["Saldo"].values[0]
                st.write(f"**Deuda actual:** ${deuda_actual:,.2f}")
                max_deuda = int(deuda_actual) if deuda_actual >= 1 else 1
                monto_pago = st.number_input("Monto a entregar ($)", min_value=1, step=10, max_value=max_deuda)
                
                btn_cobrar = st.form_submit_button("Registrar Cobranza")
                if btn_cobrar:
                    nueva_cobranza = {"Fecha": str(datetime.date.today()), "Cliente": cliente_cobro, "Monto Abonado": monto_pago}
                    df_cobranzas = pd.concat([df_cobranzas, pd.DataFrame([nueva_cobranza])], ignore_index=True)
                    guardar_datos(df_cobranzas, "cobranzas")
                    
                    idx_cli = df_clientes.index[df_clientes["Nombre"] == cliente_cobro].tolist()[0]
                    df_clientes.at[idx_cli, "Saldo"] -= monto_pago
                    guardar_datos(df_clientes, "clientes")
                    st.success(f"Cobranza guardada.")
                    recargar_app()

    with tab5:
        st.subheader("🗑️ Eliminar Socio")
        if not df_clientes.empty:
            with st.form("eliminar_cliente"):
                cliente_a_borrar = st.selectbox("Seleccione el Socio a eliminar", df_clientes["Nombre"].tolist())
                btn_eliminar = st.form_submit_button("Eliminar Permanentemente", type="primary")
                if btn_eliminar:
                    df_clientes = df_clientes[df_clientes["Nombre"] != cliente_a_borrar].reset_index(drop=True)
                    guardar_datos(df_clientes, "clientes")
                    st.success(f"Socio eliminado.")
                    recargar_app()

# ==========================================
# --- MODULO 3: PRODUCTOS Y STOCK ---
# ==========================================
elif menu == "🌿 Inventario y Variedades":
    st.title("🌿 Gestión de Inventario y Catálogo")
    tab1, tab2 = st.tabs(["Inventario y Ajustes", "Agregar/Quitar Variedades"])
    
    with tab1:
        st.dataframe(df_productos, use_container_width=True)
        st.subheader("🔄 Ingreso / Egreso Manual")
        if not df_productos.empty:
            with st.form("modificar_stock"):
                var_seleccionada = st.selectbox("Seleccionar Variedad", df_productos["Variedad"].tolist())
                tipo_mov = st.radio("Tipo de Movimiento", ["Entrada (+)", "Salida (-)"])
                cantidad = st.number_input("Cantidad (Gramos)", min_value=1, step=1)
                btn_actualizar = st.form_submit_button("Actualizar Inventario")
                if btn_actualizar:
                    idx = df_productos.index[df_productos['Variedad'] == var_seleccionada].tolist()[0]
                    if "Entrada" in tipo_mov:
                        df_productos.at[idx, "Stock"] += cantidad
                    else:
                        df_productos.at[idx, "Stock"] -= cantidad
                    guardar_datos(df_productos, "productos")
                    st.success("Stock sincronizado en Google Sheets.")
                    recargar_app()

    with tab2:
        colA, colB = st.columns(2)
        with colA:
            with st.form("nueva_variedad"):
                st.subheader("➕ Agregar Variedad")
                nuevo_cod = st.text_input("Código")
                nueva_var = st.text_input("Nombre de la Variedad")
                nueva_fam = st.selectbox("Familia", ["Flores", "Extractos", "Comestibles", "Otros"])
                btn_crear = st.form_submit_button("Agregar")
                if btn_crear and nueva_var:
                    nueva_fila = {"Código": nuevo_cod, "Variedad": nueva_var, "Familia": nueva_fam, "Stock": 0}
                    df_productos = pd.concat([df_productos, pd.DataFrame([nueva_fila])], ignore_index=True)
                    guardar_datos(df_productos, "productos")
                    st.success("Variedad agregada de forma permanente.")
                    recargar_app()
        with colB:
            with st.form("eliminar_variedad"):
                st.subheader("🗑️ Eliminar Variedad")
                if not df_productos.empty:
                    var_a_borrar = st.selectbox("Seleccionar para eliminar", df_productos["Variedad"].tolist())
                    btn_borrar = st.form_submit_button("Eliminar Permanentemente")
                    if btn_borrar:
                        df_productos = df_productos[df_productos["Variedad"] != var_a_borrar].reset_index(drop=True)
                        guardar_datos(df_productos, "productos")
                        st.success("Variedad removida.")
                        recargar_app()

# ==========================================
# --- MODULO 4: REGISTRAR VENTA ---
# ==========================================
elif menu == "🛍️ Registrar Venta":
    st.title("🛍️ Nueva Transacción")
    if df_productos.empty or df_clientes.empty:
        st.warning("Debes registrar al menos un cliente y una variedad antes de operar.")
    else:
        with st.form("formulario_venta"):
            cliente_sel = st.selectbox("Seleccionar Socio", df_clientes["Nombre"].tolist())
            producto_sel = st.selectbox("Seleccionar Variedad", df_productos["Variedad"].tolist())
            gramos = st.number_input("Cantidad (Gramos)", min_value=1, step=1)
            precio = st.number_input("Precio por Gramo ($)", min_value=1, step=10)
            condicion = st.radio("Condición de Pago", ["Paga en el momento", "Debe"])
            
            procesar = st.form_submit_button("Procesar Venta 🚀")
            if procesar:
                total = gramos * precio
                nro_recibo = f"V-{len(df_ventas) + 1:03d}"
                nueva_venta = {"Fecha": str(datetime.date.today()), "Recibo": nro_recibo, "Cliente": cliente_sel, "Variedad": producto_sel, "Gramos": gramos, "Precio/g": precio, "Total": total, "Condición": condicion}
                
                df_ventas = pd.concat([df_ventas, pd.DataFrame([nueva_venta])], ignore_index=True)
                guardar_datos(df_ventas, "ventas")
                
                idx_prod = df_productos.index[df_productos["Variedad"] == producto_sel].tolist()[0]
                df_productos.at[idx_prod, "Stock"] -= gramos
                guardar_datos(df_productos, "productos")
                
                if condicion == "Debe":
                    idx_cli = df_clientes.index[df_clientes["Nombre"] == cliente_sel].tolist()[0]
                    df_clientes.at[idx_cli, "Saldo"] += total
                    guardar_datos(df_clientes, "clientes")
                    
                st.success(f"Venta grabada en la nube. Total: ${total:,.2f}")
                recargar_app()

# ==========================================
# --- MODULO 5: COMPRAS Y RETIROS ---
# ==========================================
elif menu == "💸 Compras y Retiros":
    st.title("💸 Registro de Salidas de Dinero")
    tab1, tab2 = st.tabs(["🛒 Compras y Gastos", "🏧 Retiros de Dinero"])
    
    with tab1:
        with st.form("registro_compra"):
            st.subheader("Registrar Compra/Gasto Operativo")
            concepto = st.text_input("Concepto")
            proveedor = st.text_input("Proveedor")
            monto_compra = st.number_input("Monto del Gasto ($)", min_value=1, step=100)
            btn_compra = st.form_submit_button("Registrar Gasto")
            if btn_compra and concepto:
                nueva_compra = {"Fecha": str(datetime.date.today()), "Concepto": concepto, "Proveedor": proveedor, "Monto": monto_compra}
                df_compras = pd.concat([df_compras, pd.DataFrame([nueva_compra])], ignore_index=True)
                guardar_datos(df_compras, "compras")
                st.success("Gasto guardado.")
                recargar_app()
        st.dataframe(df_compras, use_container_width=True)
        
    with tab2:
        st.subheader("📊 Resumen de Retiros por Usuario")
        if not df_retiros.empty:
            df_retiros["Monto"] = pd.to_numeric(df_retiros["Monto"], errors='coerce').fillna(0)
            resumen_usuarios = df_retiros.groupby("Usuario")["Monto"].sum().reset_index()
            cols_resumen = st.columns(len(resumen_usuarios) if len(resumen_usuarios) > 0 else 1)
            for i, row in resumen_usuarios.iterrows():
                with cols_resumen[i]:
                    st.metric(f"Total {row['Usuario']}", f"${row['Monto']:,.2f}")
        
        with st.form("registro_retiro"):
            st.subheader("Registrar Nuevo Retiro")
            usuario = st.selectbox("Usuario que realiza el retiro", ["Usuario 1", "Usuario 2"])
            monto_retiro = st.number_input("Monto a retirar ($)", min_value=1, step=100)
            btn_retiro = st.form_submit_button("Registrar Retiro")
            if btn_retiro:
                nuevo_retiro = {"Fecha": str(datetime.date.today()), "Usuario": usuario, "Monto": monto_retiro}
                df_retiros = pd.concat([df_retiros, pd.DataFrame([nuevo_retiro])], ignore_index=True)
                guardar_datos(df_retiros, "retiros")
                st.success("Retiro registrado con éxito.")
                recargar_app()
        st.dataframe(df_retiros, use_container_width=True)

# ==========================================
# --- MODULO 6: CAJA Y FINANZAS ---
# ==========================================
elif menu == "💰 Caja y Finanzas":
    st.title("💰 Flujo de Fondos y Resultados")
    
    ventas_efectivo = df_ventas[df_ventas["Condición"] == "Paga en el momento"]["Total"].astype(float).sum() if not df_ventas.empty else 0
    cobranzas = df_cobranzas["Monto Abonado"].astype(float).sum() if not df_cobranzas.empty else 0
    total_ingresos = ventas_efectivo + cobranzas
    
    compras = df_compras["Monto"].astype(float).sum() if not df_compras.empty else 0
    retiros = df_retiros["Monto"].astype(float).sum() if not df_retiros.empty else 0
    total_egresos = compras + retiros
    
    caja_neta = total_ingresos - total_egresos
    
    st.markdown("### Estado de Flujo de Caja")
    st.markdown("""
    | Concepto | Monto |
    | :--- | :--- |
    | **(+) Ventas al Contado** |  ${:,.2f} |
    | **(+) Cobro de Deudas (Atrasadas)** |  ${:,.2f} |
    | --- | --- |
    | **TOTAL INGRESOS CAJA** | **${:,.2f}** |
    | | |
    | **(-) Compras y Gastos Operativos** | -${:,.2f} |
    | **(-) Retiros de Socios** | -${:,.2f} |
    | --- | --- |
    | **TOTAL EGRESOS CAJA** | **-${:,.2f}** |
    | | |
    | **(=) SALDO NETO EN CAJA HOY** | **${:,.2f}** |
    """.format(ventas_efectivo, cobranzas, total_ingresos, compras, retiros, total_egresos, caja_neta))
    
    if caja_neta < 0:
        st.error("⚠️ Atención: La caja está en negativo. Hay más salidas registradas que ingresos de efectivo.")