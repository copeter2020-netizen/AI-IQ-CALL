import os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = "model.pkl"
DATASET_PATH = "dataset.csv"

MIN_TRAIN = 30
RETRAIN_EVERY = 20
trade_count = 0

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

def save_trade(df, result):
    row = extract_features(df) + [result]
    cols = ["f1","f2","f3","f4","f5","label"]

    if not os.path.exists(DATASET_PATH):
        pd.DataFrame([row], columns=cols).to_csv(DATASET_PATH, index=False)
    else:
        pd.DataFrame([row]).to_csv(DATASET_PATH, mode="a", header=False, index=False)

def train():
    if not os.path.exists(DATASET_PATH):
        return None

    df = pd.read_csv(DATASET_PATH)
    if len(df) < MIN_TRAIN:
        return None

    X = df[["f1","f2","f3","f4","f5"]]
    y = df["label"]

    model = RandomForestClassifier(n_estimators=100, max_depth=5)
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)
    return model

def load():
    if not os.path.exists(MODEL_PATH):
        return None
    return joblib.load(MODEL_PATH)

def predict(model, df):
    if model is None:
        return 1.0

    X = np.array(extract_features(df)).reshape(1, -1)
    return model.predict_proba(X)[0][1]

def auto_retrain(model):
    global trade_count
    trade_count += 1

    if trade_count % RETRAIN_EVERY == 0:
        return train()
    return model
