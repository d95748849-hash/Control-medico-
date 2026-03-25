import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Control Medico", layout="wide")

def init_db():
    conn = sqlite3.connect('meds.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS Meds (id INTEGER PRIMARY KEY, nombre TEXT, cat TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS Lotes (id INTEGER PRIMARY KEY, id_m INTEGER, lote TEXT, vence DATE, cant INTEGER)')
    areas = ["Urgencias","UCI","Quirofano","Maternidad","Pediatria","Farmacia","Radiologia","Laboratorio"]
    for i in range(1, 41): # Esto crea las 40 tablas numeradas por si faltan nombres
        area_nombre = areas[i-1] if i <= len(areas) else f"Area_{i}"
        c.execute(f'CREATE TABLE IF NOT EXISTS Stock_{area_nombre} (id INTEGER PRIMARY KEY, id_m INTEGER, cant INTEGER)')
    conn.commit()
    return conn, [areas[i-1] if i <= len(areas) else f"Area_{i}" for i in range(1, 41)]

conn, lista_areas = init_db()
st.title("🏥 Control de Insumos")
op = st.sidebar.selectbox("Menu", ["Estado", "Entradas", "Salidas"])

if op == "Estado":
    st.subheader("Vencimientos y Stock")
    df = pd.read_sql_query("SELECT Lotes.*, Meds.nombre FROM Lotes JOIN Meds ON Lotes.id_m = Meds.id", conn)
    st.dataframe(df)
    a_ver = st.selectbox("Ver Área", lista_areas)
    st.table(pd.read_sql_query(f"SELECT m.nombre, s.cant FROM Stock_{a_ver} s JOIN Meds m ON s.id_m = m.id", conn))

elif op == "Entradas":
    with st.form("f1"):
        n = st.text_input("Medicamento")
        l = st.text_input("Lote")
        c_val = st.number_input("Cantidad", min_value=1)
        v = st.date_input("Vence")
        if st.form_submit_button("Guardar"):
            curr = conn.cursor()
            curr.execute("INSERT OR IGNORE INTO Meds (nombre, cat) VALUES (?,?)", (n, "Gral"))
            id_m = curr.execute("SELECT id FROM Meds WHERE nombre=?", (n,)).fetchone()[0]
            curr.execute("INSERT INTO Lotes (id_m, lote, vence, cant) VALUES (?,?,?,?)", (id_m, l, v, c_val))
            conn.commit()
            st.success("Registrado")

elif op == "Salidas":
    dest = st.selectbox("Destino", lista_areas)
    ms = pd.read_sql_query("SELECT id, nombre FROM Meds", conn)
    with st.form("f2"):
        sel = st.selectbox("Insumo", ms['nombre'])
        can = st.number_input("Cantidad", min_value=1)
        if st.form_submit_button("Enviar"):
            id_m = ms[ms['nombre'] == sel]['id'].values[0]
            curr = conn.cursor()
            curr.execute(f"INSERT INTO Stock_{dest} (id_m, cant) VALUES (?,?)", (int(id_m), can))
            conn.commit()
            st.info("Enviado")
            
