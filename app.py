import streamlit as st
import pandas as pd
import mysql.connector

st.set_page_config(page_title="Informes Fútbol Base", layout="wide")

def get_connection():
    return mysql.connector.connect(
        host="185.14.58.24",
        user="tfgusu",
        password="t2V#zYufaA1^9crh",
        database="apptfg"
    )

@st.cache_data
def load_jugadores():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM jugadores", conn)
    conn.close()
    return df

@st.cache_data
def load_partidos():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM partidos WHERE en_juego=9", conn)
    conn.close()
    return df

@st.cache_data
def load_minutos():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM part_minutos", conn)
    conn.close()
    return df

@st.cache_data
def load_acciones():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM part_accion", conn)
    conn.close()
    return df

@st.cache_data
def load_asistencias():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM part_asistencias", conn)
    conn.close()
    return df

@st.cache_data
def load_convocatorias():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM convocatorias", conn)
    conn.close()
    return df

jugadores = load_jugadores()
partidos = load_partidos()
minutos = load_minutos()
acciones = load_acciones()
asistencias = load_asistencias()
convocatorias = load_convocatorias()

st.title("Informes y Estadísticas de Fútbol Base")

vista = st.sidebar.radio("¿Qué deseas ver?", [
    "Tablas comparativas del equipo",
    "Informe individual por jugador",
    "Gráficas"
])

if vista == "Tablas comparativas del equipo":
    st.header("Estadísticas globales (solo jugadores convocados)")

    jugadores_convocados = convocatorias["jugador_id"].unique()
    df_jug = jugadores[jugadores["id"].isin(jugadores_convocados)]

    # Minutos, acciones, etc. solo de convocados
    tabla_min = minutos[minutos["jugador_id"].isin(jugadores_convocados)].groupby("jugador_id")["minutos"].sum().reset_index()
    tabla_gol = acciones[(acciones["accion"]=="gol") & (acciones["jugador_id"].isin(jugadores_convocados))].groupby("jugador_id").size().reset_index(name="goles")
    tabla_asi = asistencias[asistencias["asistente_id"].isin(jugadores_convocados)].groupby("asistente_id").size().reset_index(name="asistencias")
    tabla_ama = acciones[(acciones["accion"]=="amarilla") & (acciones["jugador_id"].isin(jugadores_convocados))].groupby("jugador_id").size().reset_index(name="amarillas")
    tabla_les = acciones[(acciones["accion"]=="lesion") & (acciones["jugador_id"].isin(jugadores_convocados))].groupby("jugador_id").size().reset_index(name="lesiones")
    tabla_val = convocatorias.groupby("jugador_id")["valoracion"].mean().reset_index()

    resumen = df_jug[["id", "nombre", "dorsal", "demarcacion"]].copy()
    resumen = resumen.merge(tabla_min, left_on="id", right_on="jugador_id", how="left")
    resumen = resumen.merge(tabla_gol, left_on="id", right_on="jugador_id", how="left")
    resumen = resumen.merge(tabla_asi, left_on="id", right_on="asistente_id", how="left")
    resumen = resumen.merge(tabla_ama, left_on="id", right_on="jugador_id", how="left", suffixes=('', '_ama'))
    resumen = resumen.merge(tabla_les, left_on="id", right_on="jugador_id", how="left", suffixes=('', '_les'))
    resumen = resumen.merge(tabla_val, left_on="id", right_on="jugador_id", how="left")
    resumen = resumen.fillna(0)
    resumen.rename(columns={"valoracion": "media_valoracion"}, inplace=True)

    tabla_completa = resumen[["nombre", "dorsal", "demarcacion", "minutos", "goles", "asistencias", "amarillas", "lesiones", "media_valoracion"]]
    tabla_completa = tabla_completa.sort_values("minutos", ascending=False)
    st.subheader("Estadísticas globales de jugadores convocados")
    st.dataframe(tabla_completa, hide_index=True)

    # Porcentajes y estadísticas
    st.header("Estadísticas destacadas del equipo (convocados)")
    total_min = tabla_completa["minutos"].sum()
    total_gol = tabla_completa["goles"].sum()
    total_asi = tabla_completa["asistencias"].sum()
    total_ama = tabla_completa["amarillas"].sum()
    total_les = tabla_completa["lesiones"].sum()
    media_val = tabla_completa["media_valoracion"].mean()

    st.metric("Minutos totales jugados", int(total_min))
    st.metric("Goles totales", int(total_gol))
    st.metric("Asistencias totales", int(total_asi))
    st.metric("Amonestaciones totales", int(total_ama))
    st.metric("Lesiones totales", int(total_les))
    st.metric("Valoración media (convocados)", round(media_val,2))

    # Porcentaje de minutos, goles y asistencias por jugador
    st.subheader("Porcentaje de minutos jugados por jugador")
    tabla_completa["% minutos"] = tabla_completa["minutos"] / total_min * 100
    st.dataframe(tabla_completa[["nombre", "minutos", "% minutos"]].sort_values("% minutos", ascending=False), hide_index=True)

    st.subheader("Porcentaje de goles por jugador")
    if total_gol > 0:
        tabla_completa["% goles"] = tabla_completa["goles"] / total_gol * 100
        st.dataframe(tabla_completa[["nombre", "goles", "% goles"]].sort_values("% goles", ascending=False), hide_index=True)

elif vista == "Informe individual por jugador":
    jugadores_convocados = convocatorias["jugador_id"].unique()
    jugador_sel = st.sidebar.selectbox("Selecciona un jugador", jugadores[jugadores["id"].isin(jugadores_convocados)]["nombre"])
    jugador_id = jugadores[jugadores["nombre"] == jugador_sel]["id"].values[0]
    st.header(f"Informe individual de {jugador_sel}")

    min_jug = minutos[minutos["jugador_id"] == jugador_id]
    min_por_part = min_jug.groupby("periodo")["minutos"].sum().reset_index()
    st.subheader("Minutos jugados por periodo")
    st.dataframe(min_por_part, hide_index=True)

    goles_jug = acciones[(acciones["jugador_id"] == jugador_id) & (acciones["accion"] == "gol")].groupby("periodo").size().reset_index(name="goles")
    asist_jug = asistencias[asistencias["asistente_id"] == jugador_id].groupby("partido_id").size().reset_index(name="asistencias")
    amos_jug = acciones[(acciones["jugador_id"] == jugador_id) & (acciones["accion"] == "amarilla")].groupby("periodo").size().reset_index(name="amarillas")
    les_jug = acciones[(acciones["jugador_id"] == jugador_id) & (acciones["accion"] == "lesion")].groupby("periodo").size().reset_index(name="lesiones")
    val_jug = convocatorias[convocatorias["jugador_id"] == jugador_id]["valoracion"].mean()

    st.markdown("### Resumen global")
    total_min = min_jug["minutos"].sum()
    total_gol = goles_jug["goles"].sum() if not goles_jug.empty else 0
    total_asi = asist_jug["asistencias"].sum() if not asist_jug.empty else 0
    total_ama = amos_jug["amarillas"].sum() if not amos_jug.empty else 0
    total_les = les_jug["lesiones"].sum() if not les_jug.empty else 0

    st.table(pd.DataFrame({
        "Estadística": ["Minutos jugados", "Goles", "Asistencias", "Amonestaciones", "Lesiones", "Valoración media"],
        "Total": [total_min, total_gol, total_asi, total_ama, total_les, round(val_jug,2)]
    }))

    # Porcentajes
    if total_min > 0:
        porc_gol = round(100*total_gol/total_min,2)
        st.metric("Goles por minuto jugado (%)", porc_gol)
    if total_asi > 0:
        porc_asi = round(100*total_asi/total_min,2)
        st.metric("Asistencias por minuto jugado (%)", porc_asi)

# Gráficas igual que antes, pero solo con convocados

st.sidebar.markdown("---")
st.sidebar.info("App desarrollada por Coditeca para TFG - Fútbol Base")
