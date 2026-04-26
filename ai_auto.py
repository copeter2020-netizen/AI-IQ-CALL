import os
import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = "model.pkl"
DATASET_PATH = "dataset.csv"

MIN_TRAIN = 30
RETRAIN_EVERY = 20

trade_count = 0

# ================= FEATURES =================
def extract_features(df):
    c = df.iloc[-2]
    p = df.iloc[-3]

    return [
        c["close"] - c["ema"],
        c["tii"],
        abs(c["close"] - c["open"]),
        1 if c["close"] > c["open"] else 0,
        p["tii"]
    ]

# ================= DATASET =================
def save_trade(df, result):
    try:
        row = extract_features(df) + [result]
        cols = ["f1", "f2", "f3", "f4", "f5", "label"]

        if not os.path.exists(DATASET_PATH):
            pd.DataFrame([row], columns=cols).to_csv(DATASET_PATH, index=False)
        else:
            pd.DataFrame([row]).to_csv(DATASET_PATH, mode="a", header=False, index=False)

    except Exception as e:
        print("Error guardando dataset:", e)

# ================= MODELO =================
def train():
    try:
        if not os.path.exists(DATASET_PATH):
            print("❌ No hay dataset")
            return None

        df = pd.read_csv(DATASET_PATH)

        if len(df) < MIN_TRAIN:
            print(f"⚠️ Muy pocos datos: {len(df)}")
            return None

        X = df[["f1", "f2", "f3", "f4", "f5"]]
        y = df["label"]

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )

        model.fit(X, y)

        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)

        print("🤖 Modelo entrenado")
        return model

    except Exception as e:
        print("Error entrenando modelo:", e)
        return None

# ================= CARGAR =================
def load():
    try:
        if not os.path.exists(MODEL_PATH):
            print("⚠️ Modelo no encontrado")
            return None

        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)

    except Exception as e:
        print("Error cargando modelo:", e)
        return None

# ================= PREDICCIÓN =================
def predict(model, df):
    try:
        if model is None:
            return 1.0  # deja pasar todo si no hay modelo

        X = np.array(extract_features(df)).reshape(1, -1)
        prob = model.predict_proba(X)[0][1]

        return prob

    except Exception as e:
        print("Error predicción:", e)
        return 1.0

# ================= AUTO-RETRAIN =================
def auto_retrain(model):
    global trade_count

    trade_count += 1

    if trade_count % RETRAIN_EVERY == 0:
        print("🔄 Reentrenando modelo...")
        return train()

    return model
