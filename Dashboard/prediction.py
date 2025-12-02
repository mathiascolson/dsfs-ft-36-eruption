# prediction.py — MODELO DUMMY PROFISSIONAL (23h de análise!)
import numpy as np
import pandas as pd

def run_model(df_full):
    """
    Usa até 23h de dados (1380 minutos) para predição realista.
    Combina:
    - Valor atual de RSAM
    - Tendência (aumento nas últimas horas)
    - Pico nas últimas 23h
    """
    try:
        # Garante que temos dados ordenados
        df = df_full.copy()
        df = df.sort_values("time_min")
        
        # Últimas 23h (1380 minutos)
        last_23h = df.tail(1380)
        if len(last_23h) < 10:
            return np.random.uniform(10, 40)  # Poucos dados

        # 1. RSAM atual (último valor)
        rsam_current = last_23h["RSAM"].iloc[-1]
        
        # 2. Tendência (média das últimas 3h vs média das 20h anteriores)
        recent_3h = last_23h.tail(180)
        older_20h = last_23h.head(len(last_23h) - 180)
        
        rsam_recent = recent_3h["RSAM"].mean() if len(recent_3h) > 0 else rsam_current
        rsam_older = older_20h["RSAM"].mean() if len(older_20h) > 0 else rsam_current
        
        trend_factor = max(0, (rsam_recent - rsam_older) / (rsam_older + 100)) * 100  # 0 a ~100
        
        # 3. Pico nas últimas 23h
        rsam_max = last_23h["RSAM"].max()
        
        # Base de risco por nível atual
        if rsam_current < 300:
            base = np.random.uniform(5, 25)
        elif rsam_current < 800:
            base = np.random.uniform(25, 55)
        elif rsam_current < 1500:
            base = np.random.uniform(55, 80)
        else:
            base = np.random.uniform(80, 98)

        # Amplifica com tendência e pico
        risk = base + 0.4 * trend_factor + 0.2 * min(50, rsam_max / 30)
        
        # Limite e ruído realista
        risk = np.clip(risk + np.random.normal(0, 4), 0, 100)
        return round(float(risk), 1)

    except Exception as e:
        return np.random.uniform(20, 50)