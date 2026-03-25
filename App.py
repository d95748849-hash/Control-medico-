import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Configuración de la Página
st.set_page_config(page_title="Control Médico Pro", layout="wide")

# 1. INICIALIZACIÓN DE LA BASE DE DATOS
def init_db():
    conn = sqlite3.connect('gestion_medica.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tablas Base
    c.execute('''CREATE TABLE IF NOT EXISTS Medicamentos 
                 (id_med INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, categoria TEXT, stock_minimo INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Lotes 
                 (id_lote INTEGER PRIMARY KEY AUTOINCREMENT, id_med INTEGER, codigo_lote TEXT, fecha_vencimiento DATE, cantidad INTEGER)''')
    
    # GENERACIÓN DE LAS 40 TABLAS DE ÁREAS
    areas = [
        "Urgencias", "UCI_Adultos", "UCI_Pediatrica", "Quirofano_1", "Quirofano_2", "Maternidad",
        "Cardiologia", "Radiologia", "Laboratorio", "Odontologia", "Ginecologia", "Traumatologia",
        "Farmacia_Interna", "Oncologia", "Neurologia", "Pediatria_A", "Pediatria_B", "Consulta_Externa",
        "Nefrologia", "Urologia", "Dermatologia", "Oftalmologia", "Otorrinolaringologia", "Psiquiatria",
        "Rehabilitacion", "Terapia_Intensiva", "Banco_Sangre", "Nutricion", "Endoscopia", "Patologia",
        "Admision", "Emergencia_Shock", "Cuidados_Intermedios", "Infectologia", "Reumatologia",
        "Geriatria", "Hematologia", "Gastroenterologia", "Neumologia", "Almacen_General"
    ]
    
    for area in areas:
        c.execute(f'''CREATE TABLE IF NOT EXISTS Stock_{area} 
                     (id_stock INTEGER PRIMARY KEY AUTOINCREMENT, id_med INTEGER, cantidad INTEGER)''')
    
    conn.commit()
    return conn, areas

conn, lista_areas = init_db()

# --- INTERFAZ DE USUARIO ---
st.title("🏥 Sistema de Control de Insumos Médicos")

opcion = st.sidebar.selectbox("Seleccione Acción", ["Dashboard", "Ingreso (Entradas)", "Salida a Áreas", "Auditoría"])

if opcion == "Dashboard":
    st.subheader("Estado General")
    df_lotes = pd.read_sql_query("SELECT Lotes.*, Medicamentos.nombre FROM Lotes JOIN Medicamentos ON Lotes.id_med = Medicamentos.id_med", conn)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Alertas de Vencimiento (30 días)**")
        hoy = datetime.now().date()
        proximo = (hoy + timedelta(days=30)).isoformat()
        vencidos = df_lotes[df_lotes['fecha_vencimiento'] <= proximo]
        st.dataframe(vencidos)
    
    with col2:
        area_ver = st.selectbox("Ver Stock por Área", lista_areas)
        df_area = pd.read_sql_query(f"""
            SELECT m.nombre, s.cantidad 
            FROM Stock_{area_ver} s 
            JOIN Medicamentos m ON s.id_med = m.id_med""", conn)
        st.table(df_area)

elif opcion == "Ingreso (Entradas)":
    st.subheader("Registro de Insumos")
    with st.form("entrada"):
        nombre = st.text_input("Nombre del Medicamento")
        lote = st.text_input("Código de Lote")
        cantidad = st.number_input("Cantidad", min_value=1)
        vence = st.date_input("Fecha de Vencimiento")
        if st.form_submit_button("Guardar"):
            c = conn.cursor()
            c.execute("INSERT OR IG
