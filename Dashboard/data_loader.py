# ============================================
# data_loader.py — VERSION FINALE AVEC NETTOYAGE AUTOMATIQUE DES OUTLIERS
# Données parfaites + propres + prêtes pour le dashboard
# ============================================

import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
from constants import DATA_DIR, eruptions


def clean_outliers(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()
    
    positive_cols = ["amplitude_mean", "RSAM", "infrasound_mean", "infrasound", "SE_env", "Kurt_env"]
    positive_cols = [col for col in positive_cols if col in df_clean.columns]

    for col in positive_cols:
        data = df_clean[col].dropna()
        if len(data) == 0: 
            continue
            
        # Clip apenas colunas que devem ser ≥ 0
        df_clean[col] = df_clean[col].clip(lower=0)
        
        # IQR robusto + substituição suave
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        upper = Q3 + 3 * IQR
        
        p995 = data.quantile(0.995)
        mask = df_clean[col] > upper
        df_clean.loc[mask, col] = p995
        
        # Suavização final
        df_clean[col] = df_clean[col].rolling(window=5, center=True, min_periods=1).median()
    
    df_clean = df_clean.dropna(subset=["time_min", "amplitude_mean"], how="any")
    
    # ← NENHUMA MENSAGEM st.success / st.info AQUI!
    return df_clean


def load_eruption_file(eruption_name: str) -> pd.DataFrame:
    """
    Charge le CSV et applique automatiquement le nettoyage des outliers
    """
    info = eruptions[eruption_name]
    path = DATA_DIR / info["file"]

    if not path.exists():
        st.error(f"Fichier non trouvé : {path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
        df["time_min"] = pd.to_datetime(df["time_min"], utc=True)
        
        print(f"{eruption_name} → {len(df):,} lignes brutes | {df['station'].nunique()} stations")
        
        # NETTOYAGE AUTOMATIQUE DES OUTLIERS
        df = clean_outliers(df)
        
        print(f"→ Après nettoyage : {len(df):,} lignes | données propres et lisses")
        return df
        
    except Exception as e:
        st.error(f"Erreur lors du chargement de {eruption_name}: {e}")
        return pd.DataFrame()


def load_raw_file(eruption_name: str) -> pd.DataFrame:
    """
    Identique à load_eruption_file (les nouveaux CSV sont déjà "bruts")
    """
    return load_eruption_file(eruption_name)


def load_window(eruption_name: str, hours_before=48, hours_after=12):
    """
    Extrait une fenêtre temporelle autour de l'éruption (avec données déjà nettoyées)
    """
    df = load_eruption_file(eruption_name)
    if df.empty:
        return df
        
    erupt_time = eruptions[eruption_name]["time"]
    start = erupt_time - pd.Timedelta(hours=hours_before)
    end = erupt_time + pd.Timedelta(hours=hours_after)

    return df[(df["time_min"] >= start) & (df["time_min"] <= end)].copy()