# dashboard.py rewritten using modules
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium

from constants import eruptions, color_map, rgba_map, station_coords
from data_loader import load_eruption_file, load_raw_file, load_window
from mapping import create_station_map
from graphing import show_graphics

st.set_page_config(page_title="Piton de la Fournaise - Prédiction", layout="wide")

# Title
st.markdown("<h1 style='text-align:center; color:darkred; font-weight:bold;'>Prédiction d'éruption volcanique🌋</h1>", unsafe_allow_html=True)

main_col, risk_col = st.columns([4.5, 1.5])

# Sidebar alert system
# ------------------------------------------------------------
# GAUGE DE RISQUE ACTUEL – À METTRE DANS LA SIDEBAR (app.py)
# ------------------------------------------------------------
st.sidebar.markdown("Niveau de risque sismique actuel")

# On prend la dernière éruption disponible
latest_eruption = list(eruptions.keys())[-1]
try:
    df_latest = load_eruption_file(latest_eruption).tail(200)  # 200 derniers points = ~3h
    current_rsam = df_latest["amplitude_mean"].mean()
    current_rsam = round(current_rsam)
except:
    current_rsam = 500  # valeur par défaut si erreur

# Calcul du niveau et couleur
if current_rsam > 5000:
    level = "ÉRUPTION EN COURS"
    color = "#9f00e0"
    emoji = "🟪"
elif current_rsam > 3000:
    level = "IMMINENT (< 1h)"
    color = "#e60000"
    emoji = "🔴"
elif current_rsam > 1500:
    level = "ÉLEVÉ (< 12h)"
    color = "#ff6600"
    emoji = "🟠"
elif current_rsam > 800:
    level = "MODÉRÉ (< 48h)"
    color = "#ffd700"
    emoji = "🟡"
else:
    level = "NORMAL"
    color = "#00b300"
    emoji = "🟢"

# Le Gauge Plotly (super beau et professionnel)
fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=current_rsam,
    number={'suffix': " RSAM", 'font': {'size': 28, 'color': "white"}},
    delta={'reference': 800, 'position': "top"},
    title={'text': f"<b>{level}</b>", 'font': {'size': 22, 'color': color}},
    gauge={
        'axis': {'range': [0, 6000], 'tickwidth': 2, 'tickcolor': "white"},
        'bar': {'color': color, 'thickness': 0.8},
        'bgcolor': "rgba(0,0,0,0)",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 800],   'color': "#00b300"},
            {'range': [800, 1500], 'color': "#ffd700"},
            {'range': [1500, 3000], 'color': "#ff6600"},
            {'range': [3000, 6000], 'color': "#e60000"}
        ],
        'threshold': {
            'line': {'color': "white", 'width': 6},
            'thickness': 0.8,
            'value': current_rsam
        }
    }
))

fig.update_layout(
    height=320,
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    margin=dict(l=20, r=20, t=50, b=20)
)

# Affichage du gauge + emoji + texte
st.sidebar.markdown(f"<div style='text-align:center; font-size:60px'>{emoji}</div>", unsafe_allow_html=True)
st.sidebar.plotly_chart(fig, use_container_width=True)

# Sidebar selection for comparison
st.sidebar.markdown("---")
st.sidebar.subheader("Éruptions comparées")
selected_for_compare = st.sidebar.multiselect(
    "Sélectionnez les éruptions à comparer",
    options=list(eruptions.keys()),
    default=list(eruptions.keys())
)
st.sidebar.markdown("### Stations pour les comparatifs")
selected_compare_stations = st.sidebar.multiselect(
    "Stations à inclure dans les comparatifs",
    options=station_coords.keys(),
    default=list(station_coords.keys())
)

# MAP SECTION
st.markdown("### Stations sismiques actives")
col_map, col_controls = st.columns([7, 3])

with col_map:
    selected_main = st.session_state.get("main_eruption_map", list(eruptions.keys())[0])

    df_map = load_eruption_file(selected_main)
    erupt_time = eruptions[selected_main]["time"]
    df_map = df_map[df_map["time_min"] >= erupt_time - pd.Timedelta(days=4)]

    tile_option = st.radio(
        "Style de carte",
        options=["Street (OpenStreetMap)", "Satellite (Google)", "Topographic (OpenTopoMap)"],
        index=1,
        horizontal=True,
        key="map_tile_selector"
    )

    if tile_option == "Street (OpenStreetMap)":
        tiles = "OpenStreetMap"; attr = "© OpenStreetMap contributors"
    elif tile_option == "Satellite (Google)":
        tiles = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}&s=Galileo"; attr = "© Google"
    else:
        tiles = "https://tile.opentopomap.org/{z}/{x}/{y}.png"; attr = "© OpenTopoMap"

    selected_stations_map = st.session_state.get("selected_stations_map", [])
    m = create_station_map(selected_stations_map, tiles, attr)
    st_folium(m, width=700, height=555, key="map_final")

with col_controls:
    st.markdown("**Paramètres de la carte**")
    selected_main = st.selectbox("Éruption pour l'affichage de la carte", options=list(eruptions.keys()), key="main_eruption_map")

    df_temp = load_raw_file(selected_main)
    available_stations = sorted(df_temp["station"].unique())

    selected_stations_map = st.multiselect(
        "Stations à afficher",
        options=available_stations,
        default=available_stations[:10],
        key="selected_stations_map"
    )

# COMPARISON DATA
@st.cache_data
def load_aligned_selected(selected_list, selected_stations):
    frames = []
    for name in selected_list:
        df = load_eruption_file(name)

        # filtrage par stations
        df = df[df["station"].isin(selected_stations)]

        info = eruptions[name]
        start = info["time"] - pd.Timedelta(hours=82)
        end = info["time"] + pd.Timedelta(hours=24)

        df = df[(df["time_min"] >= start) & (df["time_min"] <= end)]
        if df.empty:
            continue

        # Ré-agrégation APRÈS filtrage
        df["hours_to_eruption"] = (df["time_min"] - info["time"]).dt.total_seconds() / 3600
        df = df[(df["hours_to_eruption"] >= -80) & (df["hours_to_eruption"] <= 24)]

        res = (
            df.set_index("time_min")
            .resample("10min")
            .mean(numeric_only=True)
            .reset_index()
        )

        res["hours_to_eruption"] = (res["time_min"] - info["time"]).dt.total_seconds() / 3600
        res["eruption"] = name
        res["color"] = color_map[name]

        frames.append(res)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

df_compare = load_aligned_selected(selected_for_compare, selected_compare_stations)

if not df_compare.empty:
    st.markdown("---")
    st.markdown(f"# Précurseurs pré-éruptifs – {len(selected_for_compare)} éruptions alignées")

# APPEL GRAPHICS graphing.py MODULE
show_graphics(selected_for_compare)

()
# FOOTER
st.success("**Piton de la Fournaise – Volcano Monitoring System**")
st.caption("© David, Gabriel, Emmeline & Mathias | Jedha Fullstack 2025")

