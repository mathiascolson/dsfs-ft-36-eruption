import folium
import streamlit as st
from constants import station_coords, eruptions


def create_station_map(current_eruption: str):
    """
    Crée une carte Folium propre avec toutes les stations de l'OVPF.
    Les stations actives dans l'éruption sélectionnée sont en couleur,
    les autres en gris discret. Taille des marqueurs fixe (en pixels).
    """
    # Carte centrée sur le Piton de la Fournaise
    m = folium.Map(
        location=[-21.254, 55.700],
        zoom_start=13,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        max_zoom=18
    )

    # Récupère les stations actives dans l'éruption courante
    try:
        from data_loader import load_eruption_file
        df = load_eruption_file(current_eruption)
        active_stations = set(df["station"].unique()) if not df.empty else set()
    except:
        active_stations = set()

    # Palette de couleurs vives pour les stations actives
    colors_active = [
        "#FF1744", "#03A9F4", "#FF9800", "#9C27B0", "#FFEB3B", "#4CAF50",
        "#8BC34A", "#00BCD4", "#FF5722", "#2196F3",
        "#3F51B5", "#E91E63", "#FFC107"
    ]
    color_map = {}
    color_idx = 0

    for station, (lat, lon) in station_coords.items():
        est_active = station in active_stations

        if est_active:
            # Couleur vive et unique pour chaque station active
            if station not in color_map:
                color_map[station] = colors_active[color_idx % len(colors_active)]
                color_idx += 1
            couleur = color_map[station]
            fill_opacity = 0.9
            weight = 3
            radius_pixels = 10  # Très petit
        else:
            # Station sans données dans cette éruption → gris discret
            couleur = "#666666"
            fill_opacity = 0.4
            weight = 2
            radius_pixels = 7

        # Marqueur avec taille FIXE en pixels (ne grossit pas au zoom out)
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius_pixels,
            color=couleur,
            weight=weight,
            fill=True,
            fill_color=couleur,
            fill_opacity=fill_opacity,
            opacity=1,
            tooltip=f"{station} → {'Active' if est_active else 'Aucune donnée'}",
            # Important : taille fixe en pixels
            popup=None
        ).add_to(m)

        # Étiquette du nom de la station (toujours visible, petite police)
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-size: 13px;
                    font-weight: bold;
                    color: {'white' if est_active else '#bbbbbb'};
                    text-shadow: 1px 1px 3px black;
                    white-space: nowrap;
                ">{station}</div>
                """
            )
        ).add_to(m)

    # Légende discrète en bas à gauche
    legend_html = '''
    <div style="
        position: fixed; 
        bottom: 15px; left: 15px; 
        background: rgba(0,0,0,0.7); 
        padding: 8px 12px; 
        border-radius: 6px; 
        color: white; 
        font-size: 13px;
        z-index: 1000;
    ">
        <b>Légende</b><br>
        <span style="color:#00ff00">●</span> Station active<br>
        <span style="color:#888888">●</span> Pas de données pour cette éruption
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    return m