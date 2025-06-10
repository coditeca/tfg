import streamlit as st
import pandas as pd
import mysql.connector

st.set_page_config(page_title="Informes Fútbol Base", layout="wide")

# ------ CONEXIÓN BD ------
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
    df = pd.read_sql("SELECT id, nombre, dorsal, demarcacion, equipo_id FROM jugadores", conn)
    conn.close()
    return df

@st.cache_data
def load_partidos():
    conn = get_connection()
    df = pd.read_sql("SELECT id, fecha, rival, goles_favor, goles_contra, equipo_id, en_juego FROM partidos WHERE en_juego=9", conn)
    conn.close()
    return df

@st.cache_data
def load_minutos():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT pm.partido_id, pm.jugador_id, pm.periodo, pm.minutos, p.fecha, j.nombre AS jugador
        FROM part_minutos pm
        JOIN partidos p ON pm.partido_id = p.id
        JOIN jugadores j ON pm.jugador_id = j.id
        WHERE p.en_juego=9
    """, conn)
    conn.close()
    return df

@st.cache_data
def load_acciones():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT pa.id, pa.partido_id, pa.jugador_id, pa.accion, pa.periodo, pa.minuto, p.fecha, j.nombre AS jugador
        FROM part_accion pa
        JOIN partidos p ON pa.partido_id = p.id
        JOIN jugadores j ON pa.jugador_id = j.id
        WHERE p.en_juego=9
    """, conn)
    conn.close()
    return df

@st.cache_data
def load_asistencias():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT pa.partido_id, pa.gol_accion_id, pa.asistente_id, p.fecha, j.nombre AS asistente
        FROM part_asistencias pa
        JOIN partidos p ON pa.partido_id = p.id
        JOIN jugadores j ON pa.asistente_id = j.id
        WHERE p.en_juego=9
    """, conn)
    conn.close()
    return df

# ------ CARGA DE DATOS ------
jugadores = load_jugadores()
partidos = load_partidos()
minutos = load_minutos()
acciones = load_acciones()
asistencias = load_asistencias()

st.title("Informes y Estadísticas de Fútbol Base")

# ------ MENÚ PRINCIPAL ------
vista = st.sidebar.radio("¿Qué deseas ver?", [
    "Tablas comparativas del equipo",
    "Informe individual por jugador",
    "Gráficas"
])

# ------ TABLAS COMPARATIVAS ------
if vista == "Tablas comparativas del equipo":
    st.header("Tablas comparativas - Estadísticas globales del equipo")

    # Agrega todos los jugadores aunque no tengan registros en minutos/acciones/asistencias
    tabla_minutos = minutos.groupby(["jugador_id"]).agg({"minutos":"sum"}).reset_index()
    tabla_goles = acciones[acciones["accion"] == "gol"].groupby("jugador_id").size().reset_index(name="goles")
    tabla_asis = asistencias.groupby("asistente_id").size().reset_index(name="asistencias")
    tabla_ama = acciones[acciones["accion"] == "amarilla"].groupby("jugador_id").size().reset_index(name="amarillas")
    tabla_les = acciones[acciones["accion"] == "lesion"].groupby("jugador_id").size().reset_index(name="lesiones")

    # Siempre merge desde jugadores
    resumen = jugadores[["id", "nombre", "dorsal", "demarcacion"]].copy()
    resumen = resumen.merge(tabla_minutos, left_on="id", right_on="jugador_id", how="left")
    resumen = resumen.merge(tabla_goles, left_on="id", right_on="jugador_id", how="left")
    resumen = resumen.merge(tabla_asis, left_on="id", right_on="asistente_id", how="left")
    resumen = resumen.merge(tabla_ama, left_on="id", right_on="jugador_id", how="left", suffixes=('', '_ama'))
    resumen = resumen.merge(tabla_les, left_on="id", right_on="jugador_id", how="left", suffixes=('', '_les'))
    resumen = resumen.fillna(0)

    tabla_completa = resumen[["nombre", "dorsal", "demarcacion", "minutos", "goles", "asistencias", "amarillas", "lesiones"]]
    tabla_completa = tabla_completa.astype({"minutos": int, "goles": int, "asistencias": int, "amarillas": int, "lesiones": int})
    tabla_completa = tabla_completa.sort_values("minutos", ascending=False)
    st.subheader("Tabla comparativa de estadísticas globales")
    st.dataframe(tabla_completa, hide_index=True)

    # Tabla por partido
    st.header("Estadísticas por partido (todos los jugadores)")

    partidos_lista = partidos.sort_values("fecha")["fecha"].astype(str).tolist()
    partido_sel = st.selectbox("Selecciona un partido para ver tabla comparativa", partidos_lista)

    id_partido = partidos[partidos["fecha"].astype(str) == partido_sel]["id"].values[0]
    min_part = minutos[minutos["partido_id"] == id_partido].groupby("jugador_id")["minutos"].sum().reset_index()
    goles_part = acciones[(acciones["partido_id"] == id_partido) & (acciones["accion"] == "gol")].groupby("jugador_id").size().reset_index(name="goles")
    asis_part = asistencias[asistencias["partido_id"] == id_partido].groupby("asistente_id").size().reset_index(name="asistencias")
    ama_part = acciones[(acciones["partido_id"] == id_partido) & (acciones["accion"] == "amarilla")].groupby("jugador_id").size().reset_index(name="amarillas")
    les_part = acciones[(acciones["partido_id"] == id_partido) & (acciones["accion"] == "lesion")].groupby("jugador_id").size().reset_index(name="lesiones")

    tabla_partido = jugadores[["id", "nombre", "dorsal", "demarcacion"]].copy()
    tabla_partido = tabla_partido.merge(min_part, left_on="id", right_on="jugador_id", how="left")
    tabla_partido = tabla_partido.merge(goles_part, left_on="id", right_on="jugador_id", how="left")
    tabla_partido = tabla_partido.merge(asis_part, left_on="id", right_on="asistente_id", how="left")
    tabla_partido = tabla_partido.merge(ama_part, left_on="id", right_on="jugador_id", how="left", suffixes=('', '_ama'))
    tabla_partido = tabla_partido.merge(les_part, left_on="id", right_on="jugador_id", how="left", suffixes=('', '_les'))
    tabla_partido = tabla_partido.fillna(0)
    tabla_partido = tabla_partido[["nombre", "dorsal", "demarcacion", "minutos", "goles", "asistencias", "amarillas", "lesiones"]]
    tabla_partido = tabla_partido.astype({"minutos": int, "goles": int, "asistencias": int, "amarillas": int, "lesiones": int})
    st.dataframe(tabla_partido, hide_index=True)

# ------ INFORME INDIVIDUAL ------
elif vista == "Informe individual por jugador":
    jugador_sel = st.sidebar.selectbox("Selecciona un jugador", jugadores["nombre"])
    jugador_id = jugadores[jugadores["nombre"] == jugador_sel]["id"].values[0]
    st.header(f"Informe individual de {jugador_sel}")

    min_jug = minutos[minutos["jugador_id"] == jugador_id]
    min_por_part = min_jug.groupby("fecha")["minutos"].sum().reset_index()
    st.subheader("Minutos jugados por partido")
    st.dataframe(min_por_part, hide_index=True)

    goles_jug = acciones[(acciones["jugador_id"] == jugador_id) & (acciones["accion"] == "gol")].groupby("fecha").size().reset_index(name="goles")
    asist_jug = asistencias[asistencias["asistente_id"] == jugador_id].groupby("fecha").size().reset_index(name="asistencias")
    amos_jug = acciones[(acciones["jugador_id"] == jugador_id) & (acciones["accion"] == "amarilla")].groupby("fecha").size().reset_index(name="amarillas")
    les_jug = acciones[(acciones["jugador_id"] == jugador_id) & (acciones["accion"] == "lesion")].groupby("fecha").size().reset_index(name="lesiones")

    tabla_ind = min_por_part.merge(goles_jug, on="fecha", how="left") \
                            .merge(asist_jug, on="fecha", how="left") \
                            .merge(amos_jug, on="fecha", how="left") \
                            .merge(les_jug, on="fecha", how="left").fillna(0)
    tabla_ind = tabla_ind.astype({"minutos": int, "goles": int, "asistencias": int, "amarillas": int, "lesiones": int})
    st.subheader("Tabla comparativa individual por partido")
    st.dataframe(tabla_ind, hide_index=True)

    total_min = min_jug["minutos"].sum()
    total_gol = goles_jug["goles"].sum() if not goles_jug.empty else 0
    total_asi = asist_jug["asistencias"].sum() if not asist_jug.empty else 0
    total_ama = amos_jug["amarillas"].sum() if not amos_jug.empty else 0
    total_les = les_jug["lesiones"].sum() if not les_jug.empty else 0

    st.markdown("### Resumen global de la temporada")
    st.table(pd.DataFrame({
        "Estadística": ["Minutos jugados", "Goles", "Asistencias", "Amarillas", "Lesiones"],
        "Total": [total_min, total_gol, total_asi, total_ama, total_les]
    }))

    total_min_equipo = minutos.groupby("jugador_id")["minutos"].sum()
    ranking = total_min_equipo.reset_index().merge(jugadores, left_on="jugador_id", right_on="id")
    ranking = ranking.sort_values("minutos", ascending=False)
    st.subheader("Ranking de minutos jugados en la temporada")
    st.dataframe(ranking[["nombre", "minutos"]], hide_index=True)

# ------ OPCIÓN GRÁFICAS ------
elif vista == "Gráficas":
    import matplotlib.pyplot as plt
    import seaborn as sns

    st.header("Gráficas de estadísticas de equipo y jugadores")
    graf = st.selectbox("Selecciona gráfica", [
        "Minutos jugados por jugador (temporada)",
        "Goles y asistencias por jugador (temporada)",
        "Minutos jugados por partido (jugadores)",
        "Goles y asistencias por partido (jugador individual)"
    ])

    if graf == "Minutos jugados por jugador (temporada)":
        tabla = minutos.groupby(["jugador_id", "jugador"]).agg({"minutos":"sum"}).reset_index().sort_values("minutos", ascending=False)
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x="minutos", y="jugador", data=tabla, palette="Blues_r", ax=ax)
        ax.set_xlabel("Minutos totales jugados")
        ax.set_ylabel("Jugador")
        st.pyplot(fig)

    elif graf == "Goles y asistencias por jugador (temporada)":
        goles = acciones[acciones["accion"] == "gol"].groupby("jugador")["accion"].count()
        asis = asistencias.groupby("asistente")["asistente"].count()
        df = pd.DataFrame({
            "goles": goles,
            "asistencias": asis
        }).fillna(0).astype(int).sort_values("goles", ascending=False)
        fig, ax = plt.subplots(figsize=(10, 5))
        df.plot(kind="bar", ax=ax)
        plt.xticks(rotation=45)
        ax.set_ylabel("Total")
        st.pyplot(fig)

    elif graf == "Minutos jugados por partido (jugadores)":
        tabla = minutos.groupby(["fecha", "jugador"])["minutos"].sum().unstack().fillna(0).astype(int)
        st.dataframe(tabla, hide_index=True)
        fig, ax = plt.subplots(figsize=(12, 6))
        tabla.plot(ax=ax)
        plt.xticks(rotation=45)
        ax.set_ylabel("Minutos")
        ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1))
        st.pyplot(fig)

    elif graf == "Goles y asistencias por partido (jugador individual)":
        jugador_sel = st.selectbox("Selecciona jugador", jugadores["nombre"])
        jugador_id = jugadores[jugadores["nombre"] == jugador_sel]["id"].values[0]
        goles_jug = acciones[(acciones["jugador_id"] == jugador_id) & (acciones["accion"] == "gol")].groupby("fecha").size().reset_index(name="goles")
        asist_jug = asistencias[asistencias["asistente_id"] == jugador_id].groupby("fecha").size().reset_index(name="asistencias")
        fechas = partidos["fecha"].astype(str).tolist()
        df = pd.DataFrame({"fecha": fechas}).merge(goles_jug, on="fecha", how="left").merge(asist_jug, on="fecha", how="left").fillna(0)
        fig, ax = plt.subplots()
        ax.plot(df["fecha"], df["goles"], marker="o", label="Goles")
        ax.plot(df["fecha"], df["asistencias"], marker="s", label="Asistencias")
        plt.xticks(rotation=45)
        ax.set_ylabel("Total")
        ax.legend()
        st.pyplot(fig)

st.sidebar.markdown("---")
st.sidebar.info("App desarrollada por Coditeca para TFG - Fútbol Base")
