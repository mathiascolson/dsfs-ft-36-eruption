import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_folium import st_folium
import plotly.express as px

# =============================================================
# IMPORTS LOCAUX
# =============================================================
from constants import eruptions, station_coords
from data_loader import load_eruption_file
from mapping import create_station_map
from graphing import show_graphics
from real_time_update import start_realtime_update, run_realtime_update

# =============================================================
# CONFIGURATION + FIXES HUGGING FACE (scroll + Plotly warnings)
# =============================================================
st.set_page_config(
    page_title="Piton de la Fournaise - Surveillance",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS para forçar scroll na sidebar e remover avisos do Plotly
st.markdown("""
<style>
    /* Força scroll na sidebar no Hugging Face */
    section[data-testid="stSidebar"] {
        overflow-y: auto !important;
        height: 100vh !important;
    }
    /* Remove barra de ferramentas do Plotly (elimina o aviso) */
    .js-plotly-plot .plotly .modebar {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================
# ÉTAT INITIAL DE LA SESSION
# =============================================================
if "last_ml_risk" not in st.session_state:
    st.session_state.last_ml_risk = None
if "selected_stations" not in st.session_state:
    st.session_state.selected_stations = ["SNE", "HIM", "DSO", "FOR", "FJS", "RVA", "CSS", "TKR"]
if "selected_eruption_map" not in st.session_state:
    st.session_state.selected_eruption_map = list(eruptions.keys())[0]

# Liste complète des stations
ALL_STATIONS = ["BON","DSM","DSO","ENO","NSR","NTR","BLE","CSS","HIM","PJR","PCR","PER","TKR","SNE","FJS","LCR","PRA","PHR","RVA","RVP","CRA","FOR","RER","DEL","CSR"]
RECOMMENDED = ["SNE", "HIM", "DSO", "FOR", "FJS", "RVA", "CSS", "TKR"]
BAD_STATIONS_REALTIME = ["ENO", "PHR", "PER", "BLE"]

# =============================================================
# TITRE PRINCIPAL
# =============================================================
st.markdown(
    """
    <h3 style='text-align:center; color:#3D9DF3; font-weight:bold;'>PITON DE LA FOURNAISE</h3>
    <h3 style='text-align:center; color:#f0f0f0;'>Système de surveillance sismologique et prédiction d'éruptions</h3>
    """,
    unsafe_allow_html=True
)

# =============================================================
# GRAPHIQUE RSAM 24H EN TEMPS RÉEL
# =============================================================
if "df_realtime" in st.session_state and not st.session_state.df_realtime.empty:
    df_plot = st.session_state.df_realtime.copy()
    stations_valides = [s for s in st.session_state.selected_stations if s not in BAD_STATIONS_REALTIME]
    df_plot = df_plot[df_plot["station"].isin(stations_valides)]

    if not df_plot.empty:
        fig_24h = px.line(
            df_plot,
            x="time_min",
            y="RSAM",
            color="station",
            title="RSAM en temps réel — Dernières 24 heures",
            labels={"time_min": "Date/Heure", "RSAM": "RSAM"},
            height=500
        )
        fig_24h.update_traces(line=dict(width=1.8))
        fig_24h.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f0f0f0"),
            title_x=0.5,
            legend=dict(title="Stations", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor="#333333"),
            yaxis=dict(showgrid=True, gridcolor="#333333")
        )
        st.plotly_chart(fig_24h, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Aucune donnée disponible (stations filtrées pour garantir la qualité du RSAM).")
else:
    st.info("Cliquez sur « Actualiser données 24h » pour afficher le graphique RSAM en temps réel.")

# =============================================================
# SIDEBAR — JAUGE + ALERTES
# =============================================================
st.sidebar.markdown("<div style='text-align: center;'><h3>Niveau de risque sismique actuel</h3></div>", unsafe_allow_html=True)

valeur_actuelle = st.session_state.last_ml_risk if st.session_state.last_ml_risk is not None else 0

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=valeur_actuelle,
    number={'suffix': "%", 'font': {'size': 40, 'color': 'white'}},
    delta={'reference': 50, 'position': "top"},
    title={'text': "<b>RISQUE D'ÉRUPTION</b>", 'font': {'size': 18, 'color': 'white'}},
    gauge={
        'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "white"},
        'bar': {'color': "#201e1e", 'thickness': 0.6},
        'bgcolor': "rgba(0,0,0,0)",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 30], 'color': "#00ff00"},
            {'range': [30, 60], 'color': "#ffff00"},
            {'range': [60, 80], 'color': "#ff8800"},
            {'range': [80, 100], 'color': "#ff0000"}
        ],
        'threshold': {'line': {'color': "red", 'width': 6}, 'thickness': 0.8, 'value': valeur_actuelle}
    }
))
fig_gauge.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
st.sidebar.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

# Alertes
if st.session_state.get("rt_running", False):
    st.sidebar.warning("Téléchargement et prédiction en cours… patience !")
elif st.session_state.last_ml_risk is not None:
    if valeur_actuelle < 30:
        st.sidebar.success("Risque très faible — Activité sismique normale")
    elif valeur_actuelle < 60:
        st.sidebar.warning("Risque modéré — Augmentation de l'activité sismique")
    elif valeur_actuelle < 80:
        st.sidebar.error("Risque élevé — Phase pré-éruptive détectée")
    else:
        st.sidebar.error("Risque très élevé — Éruption probable dans les prochaines heures")
else:
    st.sidebar.info("En attente de données… Veuillez mettre à jour les données dans le menu ci-dessous.")

# =============================================================
# MENU TEMPS RÉEL 24H
# =============================================================
st.sidebar.markdown("---")
st.sidebar.subheader("Mise à jour temps réel (24h)")

choix_rapide = st.sidebar.radio(
    "Choix rapide",
    ["Toutes", "Personnalisé"],
    horizontal=True,
    index=1
)

if choix_rapide == "Toutes":
    st.session_state.selected_stations = [s for s in ALL_STATIONS if s not in BAD_STATIONS_REALTIME]
else:
    sélection = st.sidebar.multiselect(
        "Stations à télécharger",
        options=ALL_STATIONS,
        default=RECOMMENDED
    )
    st.session_state.selected_stations = [s for s in sélection if s not in BAD_STATIONS_REALTIME]

st.sidebar.markdown(f"**{len(st.session_state.selected_stations)} stations sélectionnées.**")

if st.sidebar.button("Actualiser données 24h + Prédiction ML", type="primary", use_container_width=True):
    start_realtime_update()

run_realtime_update()

# =============================================================
# CARTE INTERACTIVE
# =============================================================
st.markdown("### Stations sismiques sélectionnées pour l'étude des éruptions passées")

éruption_carte = st.selectbox(
    "Sélectionnez la date d'une éruption passée",
    options=list(eruptions.keys()),
    index=list(eruptions.keys()).index(st.session_state.selected_eruption_map)
)
st.session_state.selected_eruption_map = éruption_carte

carte = create_station_map(éruption_carte)
st_folium(carte, width="100%", height=530)

# =============================================================
# GRAPHIQUES HISTORIQUES
# =============================================================
st.sidebar.markdown("---")
st.sidebar.subheader("Comparaison des éruptions passées")

éruptions_sélectionnées = st.sidebar.multiselect(
    "Éruptions",
    options=list(eruptions.keys()),
    default=list(eruptions.keys())[:6],
    key="selected_eruptions"
)

stations_historiques = st.sidebar.multiselect(
    "Stations (graphiques historiques)",
    options=list(station_coords.keys()),
    default=list(station_coords.keys()),
    key="stations_historiques"
)

show_graphics(éruptions_sélectionnées)

# =============================================================
# PIED DE PAGE
# =============================================================
st.markdown("---")
st.success("**Piton de la Fournaise – Real-time Volcano Monitoring System**")
st.caption("© David, Gabriel, Emmeline & Mathias | Jedha Fullstack 2025 | DSFS-FT-36")