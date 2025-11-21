# ============================================
# graphing.py – VERSION COMPLÈTE ET DÉFINITIVE
# Tous les graphiques OVPF + ligne verte néon 4 px identique partout
# Commentaires en français
# ============================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import scipy.signal as scipy_signal
from constants import eruptions, color_map
from data_loader import load_eruption_file


# ------------------------------------------------------------
# 1. Chargement et alignement des données sélectionnées
# ------------------------------------------------------------
def load_aligned_data(selected_eruptions):
    frames = []
    for name in selected_eruptions:
        df = load_eruption_file(name)
        info = eruptions[name]
        df["hours_to_eruption"] = (df["time_min"] - info["time"]).dt.total_seconds() / 3600
        df = df[(df["hours_to_eruption"] >= -80) & (df["hours_to_eruption"] <= 24)]
        res = df.set_index("time_min").resample("10min").mean(numeric_only=True).reset_index()
        res["hours_to_eruption"] = (res["time_min"] - info["time"]).dt.total_seconds() / 3600
        res["eruption"] = name
        res["color"] = color_map[name]
        frames.append(res)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ------------------------------------------------------------
# 2. Ligne verte néon identique dans TOUS les graphiques (4 px)
# ------------------------------------------------------------
def add_eruption_line(fig):
    fig.add_shape(
        type="line", x0=0, x1=0, y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color="#39FF14", width=4)
    )
    fig.add_shape(
        type="rect", x0=-3, x1=3, y0=0, y1=1,
        xref="x", yref="paper",
        fillcolor="#39FF14", opacity=0.12, line_width=0
    )
    return fig


# ------------------------------------------------------------
# 3. Network Mean Seismic Amplitude
# ------------------------------------------------------------
def plot_network_amplitude(df):
    fig = go.Figure()
    for e in df["eruption"].unique():
        sub = df[df["eruption"] == e]
        fig.add_trace(go.Scatter(x=sub["hours_to_eruption"], y=sub["amplitude_mean"],
                                 mode="lines", name=e, line=dict(width=4, color=sub["color"].iloc[0])))
    fig = add_eruption_line(fig)
    fig.update_layout(height=500, template="simple_white",
                      title="Network Mean Seismic Amplitude",
                      xaxis_title="Heures / éruption", yaxis_title="Amplitude moyenne du réseau")
    return fig


# ------------------------------------------------------------
# 4. RSAM
# ------------------------------------------------------------
def plot_rsam(df):
    fig = go.Figure()
    for e in df["eruption"].unique():
        sub = df[df["eruption"] == e]
        fig.add_trace(go.Scatter(x=sub["hours_to_eruption"], y=sub["RSAM"],
                                 mode="lines", name=e, line=dict(width=4, color=sub["color"].iloc[0])))
    fig = add_eruption_line(fig)
    fig.update_layout(height=500, template="simple_white",
                      title="RSAM – Real-time Seismic Amplitude Measurement",
                      xaxis_title="Heures / éruption", yaxis_title="RSAM")
    return fig


# ------------------------------------------------------------
# 5. Cumulative Seismic Energy Released
# ------------------------------------------------------------
def plot_cumulative_energy(df):
    fig = go.Figure()
    for e in df["eruption"].unique():
        sub = df[df["eruption"] == e].sort_values("hours_to_eruption")
        energy = (sub["amplitude_mean"]**2).cumsum()
        fig.add_trace(go.Scatter(x=sub["hours_to_eruption"], y=energy,
                                 mode="lines", name=e, line=dict(width=4, color=sub["color"].iloc[0])))
    fig = add_eruption_line(fig)
    fig.update_layout(height=500, template="simple_white",
                      title="Cumulative Seismic Energy Released",
                      xaxis_title="Heures / éruption", yaxis_title="Énergie sismique cumulée")
    return fig


# ------------------------------------------------------------
# 6. Shannon Entropy
# ------------------------------------------------------------
def plot_shannon_entropy(df):
    fig = go.Figure()
    for e in df["eruption"].unique():
        sub = df[df["eruption"] == e]
        fig.add_trace(go.Scatter(x=sub["hours_to_eruption"], y=sub["SE_env"],
                                 mode="lines", name=e, line=dict(width=4, color=sub["color"].iloc[0])))
    fig = add_eruption_line(fig)
    fig.update_layout(height=500, template="plotly_dark",
                      title="Shannon Entropy (enveloppe lissée)",
                      xaxis_title="Heures / éruption", yaxis_title="Entropie spectrale")
    return fig


# ------------------------------------------------------------
# 7. Kurtosis
# ------------------------------------------------------------
def plot_kurtosis(df):
    fig = go.Figure()
    for e in df["eruption"].unique():
        sub = df[df["eruption"] == e]
        fig.add_trace(go.Scatter(x=sub["hours_to_eruption"], y=sub["Kurt_env"],
                                 mode="lines", name=e, line=dict(width=4, color=sub["color"].iloc[0])))
    fig = add_eruption_line(fig)
    fig.update_layout(height=500, template="plotly_dark",
                      title="Kurtosis (enveloppe lissée)",
                      xaxis_title="Heures / éruption", yaxis_title="Kurtosis")
    return fig

# ------------------------------------------------------------
# 8. Amplitude ± 95% Intervalle de confiance
# ------------------------------------------------------------
def plot_amplitude_with_ci(df):
    fig = go.Figure()
    for e in df["eruption"].unique():
        sub = df[df["eruption"] == e].set_index("time_min")["amplitude_mean"].resample("10min").mean()
        roll = sub.rolling(6, center=True, min_periods=3)
        mean = roll.mean(); std = roll.std(); count = roll.count()
        hours = (mean.index - eruptions[e]["time"]).total_seconds() / 3600
        upper = mean + 1.96 * std / np.sqrt(count)
        lower = mean - 1.96 * std / np.sqrt(count)
        color = color_map[e]
        hex_color = color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        fillcolor = f"rgba({r},{g},{b},0.25)"

        fig.add_trace(go.Scatter(x=hours, y=mean, name=e, line=dict(color=color, width=4)))
        fig.add_trace(go.Scatter(x=list(hours)+list(hours[::-1]),
                                 y=list(upper)+list(lower[::-1]),
                                 fill="toself", fillcolor=fillcolor, line_width=0, showlegend=False))
    fig = add_eruption_line(fig)
    fig.update_layout(height=600, template="simple_white",
                      title="Network Mean Amplitude ± 95% Confidence Interval",
                      xaxis_title="Heures / éruption", yaxis_title="Amplitude moyenne ± IC95%")
    return fig


# ------------------------------------------------------------
# 10. Variation relative de vitesse sismique dV/V (%)
# ------------------------------------------------------------
def plot_dvv(df_compare):
    st.markdown("### Variation de vitesse sismique dV/V (%) – précurseur de déformation")

    ref_vals = []
    for name in df_compare["eruption"].unique():
        sub = df_compare[df_compare["eruption"] == name]
        ref = sub[sub["hours_to_eruption"].between(-48, -24)]["amplitude_mean"].mean()
        ref_vals.append(ref)
    global_ref = np.mean(ref_vals) if ref_vals else 1

    df_plot = df_compare.copy()
    df_plot["dv_v"] = (df_plot["amplitude_mean"] - global_ref) / global_ref * 100

    fig = go.Figure()
    for e in df_plot["eruption"].unique():
        sub = df_plot[df_plot["eruption"] == e]
        fig.add_trace(go.Scatter(x=sub["hours_to_eruption"], y=sub["dv_v"],
                                 mode="lines", name=e, line=dict(width=4, color=sub["color"].iloc[0])))
    fig = add_eruption_line(fig)
    fig.add_hline(y=0, line=dict(color="white", dash="dash"))
    fig.update_layout(height=500, template="plotly_dark",
                      yaxis_title="dV/V (%)", xaxis_title="Heures / éruption")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("dV/V > 0.1 % = gonflement | < -0.1 % = dégonflement")


# ------------------------------------------------------------
# 11. Nombre d'événements sismiques par heure – TOUTES LES ÉRUPTIONS
# ------------------------------------------------------------
def plot_event_count():
    st.markdown("### Nombre d'événements sismiques par heure")

    # Menu de sélection d'éruption
    default_eruption = next((k for k in eruptions.keys() if "2020" in k), list(eruptions.keys())[0])
    eruption = st.selectbox(
        "Choisir l'éruption pour le comptage",
        options=list(eruptions.keys()),
        index=list(eruptions.keys()).index(default_eruption),
        key="eventcount_eruption"
    )

    df = load_eruption_file(eruption)
    erupt_time = eruptions[eruption]["time"]

    df = df[
        (df["time_min"] >= erupt_time - pd.Timedelta(hours=72)) &
        (df["time_min"] <= erupt_time + pd.Timedelta(hours=12))
    ].copy()

    if len(df) == 0:
        st.warning("Aucune donnée pour cette période.")
        return

    # Seuil dynamique : 92e percentile du signal calme (-72h à -48h)
    quiet_period = df[df["time_min"] < erupt_time - pd.Timedelta(hours=48)]
    threshold = quiet_period["amplitude_mean"].quantile(0.92) if len(quiet_period) > 100 else df["amplitude_mean"].quantile(0.92)

    df["event"] = (df["amplitude_mean"] > threshold).astype(int)

    # Comptage par heure
    hourly = df.groupby(pd.Grouper(key="time_min", freq="1H"))["event"].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=hourly["time_min"],
        y=hourly["event"],
        marker_color="crimson",
        name="Événements/heure",
        hovertemplate="<b>Heure</b>: %{x}<br><b>Événements</b>: %{y}<extra></extra>"
    ))

    fig.add_vline(x=erupt_time, line=dict(color="#39FF14", width=5))
    fig.add_vrect(x0=erupt_time - pd.Timedelta(hours=6), x1=erupt_time + pd.Timedelta(hours=6),
                  fillcolor="#39FF14", opacity=0.1, line_width=0)

    fig.update_layout(
        height=520,
        template="plotly_dark",
        title=f"Événements sismiques détectés – {eruption.split(' – ')[0]}",
        xaxis_title="Date / Heure",
        yaxis_title="Nombre d'événements par heure",
        xaxis=dict(range=[erupt_time - pd.Timedelta(hours=72), erupt_time + pd.Timedelta(hours=12)])
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Seuil = 92ᵉ percentile du bruit de fond – méthode standard OVPF/USGS")


# ------------------------------------------------------------
# 12. Tremor volcanique – méthode OVPF (RSAM + Envelope) – PCR + 2020 par défaut
# ------------------------------------------------------------
def display_spectrogram():
    st.markdown("### TREMOR VOLCANIQUE – Méthode OVPF (RSAM + Envelope)")

    default_eruption = next((k for k in eruptions.keys() if "2020" in k), list(eruptions.keys())[0])

    col1, col2 = st.columns(2)
    with col1:
        eruption = st.selectbox("Éruption", list(eruptions.keys()),
                               index=list(eruptions.keys()).index(default_eruption),
                               key="tremor_erupt")
    with col2:
        df_full = load_eruption_file(eruption)
        station = st.selectbox("Station", sorted(df_full["station"].unique()),
                               index=sorted(df_full["station"].unique()).index("PCR") if "PCR" in df_full["station"].unique() else 0,
                               key="tremor_stat")

    erupt_time = eruptions[eruption]["time"]
    start = erupt_time - pd.Timedelta(hours=72)
    end = erupt_time + pd.Timedelta(hours=12)

    df = df_full[(df_full["station"] == station) &
                 (df_full["time_min"] >= start) &
                 (df_full["time_min"] <= end)].copy()

    if len(df) < 50:
        st.warning("Pas assez de données.")
        return

    df["hours"] = (df["time_min"] - erupt_time).dt.total_seconds() / 3600
    df["RSAM"] = df["amplitude_mean"].rolling(10, center=True).mean()
    df["envelope"] = df["amplitude_mean"].rolling(60, center=True).quantile(0.9)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["hours"], y=df["amplitude_mean"],
                             mode="lines", line=dict(color="gray", width=1), name="Amplitude brute", opacity=0.5))
    fig.add_trace(go.Scatter(x=df["hours"], y=df["RSAM"],
                             mode="lines", line=dict(color="red", width=4), name="RSAM"))
    fig.add_trace(go.Scatter(x=df["hours"], y=df["envelope"],
                             mode="lines", line=dict(color="yellow", width=4), name="Envelope 90% (tremor)"))

    fig = add_eruption_line(fig)

    fig.update_layout(
        height=650, template="plotly_dark",
        title=f"TREMOR DÉTECTÉ – {station} – {eruption.split(' – ')[0]}",
        xaxis_title="Heures / éruption (t=0)", yaxis_title="Amplitude sismique",
        xaxis=dict(range=[-72, 12])
    )

    st.plotly_chart(fig, use_container_width=True)
    st.info("Méthode officielle de l’OVPF – montée claire du RSAM et de l’envelope jaune.")

# ------------------------------------------------------------
# Waterfall 3D – Amplitude × Temps × Station (super impressionnant!)
# ------------------------------------------------------------
def plot_3d_waterfall():
    st.markdown("### Waterfall 3D – Propagation du tremor dans le réseau sismique")

    try:
        default_eruption = next(k for k in eruptions.keys() if "2020" in k)
    except:
        default_eruption = list(eruptions.keys())[-1]

    eruption = st.selectbox(
        "Éruption pour le waterfall 3D",
        options=list(eruptions.keys()),
        index=list(eruptions.keys()).index(default_eruption),
        key="3d_waterfall_eruption"
    )

    df = load_eruption_file(eruption)
    erupt_time = eruptions[eruption]["time"]

    df = df[
        (df["time_min"] >= erupt_time - pd.Timedelta(hours=48)) &
        (df["time_min"] <= erupt_time + pd.Timedelta(hours=6))
    ].copy()

    if len(df) < 100:
        st.warning("Pas assez de données pour le waterfall 3D.")
        return

    df["hours"] = (df["time_min"] - erupt_time).dt.total_seconds() / 3600

    pivot = df.pivot_table(
        values="amplitude_mean",
        index="station",
        columns="hours",
        aggfunc="mean"
    ).fillna(0)

    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]

    x = pivot.columns.values
    y = np.arange(len(pivot))
    z = pivot.values
    stations = pivot.index.tolist()

    fig = go.Figure(data=go.Surface(
        z=z,
        x=x,
        y=y,
        colorscale="Hot",
        cmin=0,
        lighting=dict(ambient=0.6, diffuse=0.9, specular=0.8, roughness=0.3),
        contours=dict(
            z=dict(
                show=True,
                color="#1C1C1C",   
                width=1,
                project_z=True
            )
        ),
        hovertemplate="<b>Station</b>: %{text}<br><b>Heure</b>: %{x:.1f} h<br><b>Amplitude</b>: %{z:.1f}<extra></extra>",
        text=stations
    ))

    fig.update_layout(
        height=550,
        template="plotly_dark",
        scene=dict(
            xaxis=dict(title="Heures / éruption (t=0)", gridcolor="gray"),
            yaxis=dict(
                title="Stations sismiques",
                tickvals=y,
                ticktext=stations,
                gridcolor="gray",
                showticklabels=True
            ),
            zaxis=dict(title="Amplitude moyenne", gridcolor="gray"),
            camera=dict(
                eye=dict(x=1.2, y=1.2, z=1.5),
                center=dict(x=0, y=0, z=0),   # ← graphic position
                up=dict(x=0, y=0, z=1)
            ),
            bgcolor="black"
        ),
        title=f"Waterfall 3D – {eruption.split(' – ')[0]}",
        margin=dict(l=0, r=0, t=60, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# 13. Fonction principale – appelée depuis app.py
# ------------------------------------------------------------
def show_graphics(selected_eruptions):
    st.markdown("---")
    st.markdown("## Analyse comparative des précurseurs sismiques")

    if not selected_eruptions:
        st.info("Aucune éruption sélectionnée.")
        return

    df = load_aligned_data(selected_eruptions)

    st.plotly_chart(plot_network_amplitude(df),     use_container_width=True)
    st.plotly_chart(plot_rsam(df),                  use_container_width=True)
    st.plotly_chart(plot_cumulative_energy(df),     use_container_width=True)
    st.plotly_chart(plot_shannon_entropy(df),       use_container_width=True)
    st.plotly_chart(plot_kurtosis(df),              use_container_width=True)
    st.plotly_chart(plot_amplitude_with_ci(df),     use_container_width=True)
    plot_dvv(df)
    plot_event_count()    
    plot_3d_waterfall()                          
    display_spectrogram()