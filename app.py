import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de página
st.set_page_config(page_title="Informes y Estadísticas Fútbol Base", layout="wide")

# Función de conexión a la BD
def get_connection():
    return mysql.connector.connect(
        host="185.14.58.24",
        user="tfgusu",
        password="t2V#zYufaA1^9crh",
        database="apptfg"
    )

# Cargar datos de jugadores
@st.cache_data
def load_jugadores():
    conn = get_connection()
    df = pd.read_sql("SELECT id, nombre, dorsal, demarcacion, equipo_id FROM jugadores", conn)
    conn.close()
    return df

# Cargar datos de partidos
@st.cache_data
def load_partidos():
    conn = get_connection()
    df = pd.read_sql("SELECT id, fecha, rival, goles_favor, goles_contra, equipo_id, en_juego FROM partidos WHERE en_juego=9", conn)
    conn.close()
    return df

# Cargar minutos jugados
@st.cache_data
def load_minutos():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT pm.partido_id, pm.jugador_id, pm.periodo, pm.minutos, p.fecha
        FROM part_minutos pm
        JOIN partidos p ON pm.partido_id = p.id
        WHERE p.en_juego=9
    """, conn)
    conn.close()
    return df

# Cargar acciones de partidos
@st.cache_data
def load_acciones():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT pa.id, pa.partido_id, pa.jugador_id, pa.accion, pa.periodo, pa.minuto, p.fecha
        FROM part_accion pa
        JOIN partidos p ON pa.partido_id = p.id
        WHERE p.en_juego=9
    """, conn)
    conn.close()
    return df

# Cargar asistencias
@st.cache_data
def load_asistencias():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT pa.partido_id, pa.gol_accion_id, pa.asistente_id, p.fecha
        FROM part_asistencias pa
        JOIN partidos p ON pa.partido_id = p.id
        WHERE p.en_juego=9
    """, conn)
    conn.close()
    return df

# DATOS
jugadores = load_jugadores()
partidos = load_partidos()
minutos = load_minutos()
acciones = load_acciones()
asistencias = load_asistencias()

st.title("Informes y Estadísticas de Fútbol Base")

# SELECCIÓN DE JUGADOR O REPORTE GENERAL
opcion = st.sidebar.radio("¿Qué deseas visualizar?", ["Informe general del equipo", "Informe individual por jugador"])

if opcion == "Informe general del equipo":
    st.header("Resumen de minutos jugados por jugador (Temporada)")
    minutos_total = minutos.groupby("jugador_id")["minutos"].sum().reset_index()
    minutos_total = minutos_total.merge(jugadores, left_on="jugador_id", right_on="id")
    minutos_total = minutos_total.sort_values("minutos", ascending=False)

    st.dataframe(minutos_total[["nombre", "dorsal", "demarcacion", "minutos"]])

    # Gráfica de minutos jugados por jugador
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    sns.barplot(x="minutos", y="nombre", data=minutos_total, palette="Blues_r", ax=ax1)
    ax1.set_xlabel("Minutos totales jugados")
    ax1.set_ylabel("Jugador")
    st.pyplot(fig1)

    st.header("Minutos jugados por partido (distribución)")
    partido_min = minutos.groupby(["partido_id", "jugador_id"])["minutos"].sum().reset_index()
    partido_min = partido_min.merge(jugadores, left_on="jugador_id", right_on="id")
    partido_min = partido_min.merge(partidos, left_on="partido_id", right_on="id", suffixes=('', '_part'))
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    sns.boxplot(x="nombre", y="minutos", data=partido_min, ax=ax2)
    plt.xticks(rotation=45)
    st.pyplot(fig2)

    st.header("Estadísticas de goles, asistencias, amonestaciones y lesiones (Temporada)")
    # Goles por jugador
    goles = acciones[acciones["accion"] == "gol"].groupby("jugador_id").size().reset_index(name="goles")
    asist = asistencias.groupby("asistente_id").size().reset_index(name="asistencias")
    amarillas = acciones[acciones["accion"] == "amarilla"].groupby("jugador_id").size().reset_index(name="amarillas")
    lesiones = acciones[acciones["accion"] == "lesion"].groupby("jugador_id").size().reset_index(name="lesiones")

    resumen = jugadores[["id", "nombre", "dorsal", "demarcacion"]].copy()
    resumen = resumen.merge(goles, left_on="id", right_on="jugador_id", how="left").drop("jugador_id", axis=1)
    resumen = resumen.merge(asist, left_on="id", right_on="asistente_id", how="left").drop("asistente_id", axis=1)
    resumen = resumen.merge(amarillas, left_on="id", right_on="jugador_id", how="left").drop("jugador_id", axis=1)
    resumen = resumen.merge(lesiones, left_on="id", right_on="jugador_id", how="left").drop("jugador_id", axis=1)
    resumen = resumen.fillna(0)
    st.dataframe(resumen[["nombre", "dorsal", "demarcacion", "goles", "asistencias", "amarillas", "lesiones"]].sort_values("goles", ascending=False))

    # Gráfica de goles y asistencias
    st.subheader("Goles y asistencias por jugador")
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    resumen_ord = resumen.sort_values("goles", ascending=False)
    ax3.bar(resumen_ord["nombre"], resumen_ord["goles"], label="Goles", color="steelblue")
    ax3.bar(resumen_ord["nombre"], resumen_ord["asistencias"], label="Asistencias", color="orange", alpha=0.7, bottom=resumen_ord["goles"])
    plt.xticks(rotation=45)
    ax3.set_ylabel("Total")
    ax3.legend()
    st.pyplot(fig3)

elif opcion == "Informe individual por jugador":
    jugador_sel = st.sidebar.selectbox("Selecciona un jugador", jugadores["nombre"])
    jugador_id = jugadores[jugadores["nombre"] == jugador_sel]["id"].values[0]

    st.header(f"Informe de {jugador_sel}")

    # Minutos jugados por partido
    min_jug = minutos[minutos["jugador_id"] == jugador_id]
    min_por_part = min_jug.groupby("fecha")["minutos"].sum().reset_index()
    st.subheader("Minutos jugados por partido")
    st.dataframe(min_por_part)
    fig4, ax4 = plt.subplots()
    ax4.plot(min_por_part["fecha"], min_por_part["minutos"], marker="o")
    ax4.set_xlabel("Partido")
    ax4.set_ylabel("Minutos jugados")
    plt.xticks(rotation=45)
    st.pyplot(fig4)

    # Goles y asistencias por partido
    goles_jug = acciones[(acciones["jugador_id"] == jugador_id) & (acciones["accion"] == "gol")].groupby("fecha").size().reset_index(name="goles")
    asist_jug = asistencias[asistencias["asistente_id"] == jugador_id].groupby("fecha").size().reset_index(name="asistencias")
    df_graf = pd.merge(min_por_part, goles_jug, on="fecha", how="left").merge(asist_jug, on="fecha", how="left").fillna(0)

    st.subheader("Goles y asistencias por partido")
    st.dataframe(df_graf[["fecha", "goles", "asistencias"]])
    fig5, ax5 = plt.subplots()
    ax5.bar(df_graf["fecha"], df_graf["goles"], label="Goles", color="steelblue")
    ax5.bar(df_graf["fecha"], df_graf["asistencias"], label="Asistencias", color="orange", alpha=0.7, bottom=df_graf["goles"])
    ax5.set_ylabel("Total")
    plt.xticks(rotation=45)
    ax5.legend()
    st.pyplot(fig5)

    # Amostestaciones y lesiones por partido
    amos_jug = acciones[(acciones["jugador_id"] == jugador_id) & (acciones["accion"] == "amarilla")].groupby("fecha").size().reset_index(name="amarillas")
    les_jug = acciones[(acciones["jugador_id"] == jugador_id) & (acciones["accion"] == "lesion")].groupby("fecha").size().reset_index(name="lesiones")
    df_graf2 = pd.merge(min_por_part, amos_jug, on="fecha", how="left").merge(les_jug, on="fecha", how="left").fillna(0)

    st.subheader("Amonestaciones y lesiones por partido")
    st.dataframe(df_graf2[["fecha", "amarillas", "lesiones"]])

    # Control del reparto de minutos
    st.header("Control de reparto de minutos (Temporada)")
    total_min_temporada = minutos[minutos["jugador_id"] == jugador_id]["minutos"].sum()
    total_min_equipo = minutos.groupby("jugador_id")["minutos"].sum()
    media_equipo = total_min_equipo.mean()
    st.metric("Minutos jugados por temporada", int(total_min_temporada))
    st.metric("Media de minutos del equipo", int(media_equipo))
    ratio = float(total_min_temporada) / (media_equipo * 2) if media_equipo > 0 else 0
    st.progress(min(ratio, 1.0))

    # Ranking de minutos jugados
    st.subheader("Ranking de minutos jugados en la temporada")
    ranking = total_min_equipo.reset_index().merge(jugadores, left_on="jugador_id", right_on="id")
    ranking = ranking.sort_values("minutos", ascending=False)
    st.dataframe(ranking[["nombre", "minutos"]])

st.sidebar.markdown("---")
st.sidebar.info("App desarrollada por Coditeca para TFG - Fútbol Base")
