import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Cambia 'hospital123' por la clave que tú quieras
PASSWORD_SISTEMA = "hospital2026"

def check_password():
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
    
    if not st.session_state["auth"]:
        st.title("🔒 Acceso Restringido")
        pwd = st.text_input("Introduce la contraseña del centro médico:", type="password")
        if st.button("Ingresar"):
            if pwd == PASSWORD_SISTEMA:
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        return False
    return True

# Solo si la contraseña es correcta, se ejecuta el resto
if check_password():
    st.set_page_config(page_title="Control Medico", layout="wide")

    def init_db():
        conn = sqlite3.connect('meds.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Meds (id INTEGER PRIMARY KEY, nombre TEXT, cat TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS Lotes (id INTEGER PRIMARY KEY, id_m INTEGER, lote TEXT, vence DATE, cant INTEGER)')
        areas = ["Urgencias","UCI","Quirofano","Maternidad","Pediatria","Farmacia","Radiologia","Laboratorio"]
        for i in range(1, 41):
            area_nombre = areas[i-1] if i <= len(areas) else f"Area_{i}"
            c.execute(f'CREATE TABLE IF NOT EXISTS Stock_{area_nombre} (id INTEGER PRIMARY KEY, id_m INTEGER, cant INTEGER)')
        conn.commit()
        return conn, [areas[i-1] if i <= len(areas) else f"Area_{i}" for i in range(1, 41)]

    conn, lista_areas = init_db()
    st.title("🏥 Control de Insumos")
    
    # Botón para cerrar sesión
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["auth"] = False
        st.rerun()

    op = st.sidebar.selectbox("Menú Principal", ["Estado de Inventario", "Registro de Entradas", "Salidas a Áreas"])

    if op == "Estado de Inventario":
        st.subheader("Vencimientos y Stock General")
        df = pd.read_sql_query("SELECT Lotes.lote, Lotes.vence, Lotes.cant, Meds.nombre FROM Lotes JOIN Meds ON Lotes.id_m = Meds.id", conn)
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        a_ver = st.selectbox("Consultar Stock por Área Específica", lista_areas)
        df_area = pd.read_sql_query(f"SELECT m.nombre, s.cant FROM Stock_{a_ver} s JOIN Meds m ON s.id_m = m.id", conn)
        st.table(df_area)

    elif op == "Registro de Entradas":
        st.subheader("Ingreso de nuevos medicamentos")
        with st.form("f1", clear_on_submit=True):
            n = st.text_input("Nombre del Medicamento")
            l = st.text_input("Número de Lote")
            c_val = st.number_input("Cantidad Recibida", min_value=1)
            v = st.date_input("Fecha de Vencimiento")
            if st.form_submit_button("Guardar en Almacén"):
                curr = conn.cursor()
                curr.execute("INSERT OR IGNORE INTO Meds (nombre, cat) VALUES (?,?)", (n, "Gral"))
                id_m = curr.execute("SELECT id FROM Meds WHERE nombre=?", (n,)).fetchone()[0]
                curr.execute("INSERT INTO Lotes (id_m, lote, vence, cant) VALUES (?,?,?,?)", (id_m, l, v, c_val))
                conn.commit()
                st.success(f"Registrado: {n} (Lote {l})")

    elif op == "Salidas a Áreas":
        st.subheader("Transferencia a Departamentos")
        dest = st.selectbox("Área de Destino", lista_areas)
        ms = pd.read_sql_query("SELECT id, nombre FROM Meds", conn)
        with st.form("f2", clear_on_submit=True):
            sel = st.selectbox("Seleccione Insumo", ms['nombre'])
            can = st.number_input("Cantidad a enviar", min_value=1)
            if st.form_submit_button("Confirmar Envío"):
                id_m = ms[ms['nombre'] == sel]['id'].values[0]
                curr = conn.cursor()
                curr.execute(f"INSERT INTO Stock_{dest} (id_m, cant) VALUES (?,?)", (int(id_m), can))
                conn.commit()
                st.info(f"Se han enviado {can} unidades a {dest}")
        
