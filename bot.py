import time
import os
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from iqoptionapi.stable_api import IQ_Option

# ================= CONFIG =================

PAIRS = ["EURUSD", "GBPUSD", "EURJPY", "USDCHF", "EURGBP"]

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 175
COOLDOWN = 180

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not EMAIL or not PASSWORD:
    raise Exception("❌ Faltan credenciales IQ Option")

# ================= ESTADO =================

last_trade_time = 0
last_candle_time = None

# ================= TELEGRAM =================

def send(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ================= HORA BOGOTÁ =================

def get_bogota_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now - timedelta(hours=5)

def is_trading_time():
    hour = get_bogota_time().hour
    return 8 <= hour < 11  # 08:00 - 11:00

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)

def connect():
    while True:
        try:
            print("🔌 Conectando...")
            iq.connect()

            if iq.check_connect():
                iq.change_balance("PRACTICE")
                print("✅ Conectado")
                return
            else:
                print("❌ Fallo conexión, reintentando...")

        except Exception as e:
            print("❌ Error conexión:", e)

        time.sleep(5)

def reconnect():
    if not iq.check_connect():
        print("🔄 Reconectando...")
        connect()

# ================= DATA =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        if not candles:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        df = df.sort_values("from").reset_index(drop=True)

        return df
    except:
        return None

# ================= ESTRATEGIA =================

LOOKBACK = 20
MIN_BODY = 0.0002

def get_liquidity(df):
    recent = df.iloc[-LOOKBACK:]
    return recent["high"].max(), recent["low"].min()

def strong_bullish(c):
    body = c["close"] - c["open"]
    rng = c["high"] - c["low"]
    return body > MIN_BODY and c["close"] > (c["high"] - rng * 0.25)

def strong_bearish(c):
    body = c["open"] - c["close"]
    rng = c["high"] - c["low"]
    return body > MIN_BODY and c["close"] < (c["low"] + rng * 0.25)

def buy_signal(df):
    high, low = get_liquidity(df)
    prev = df.iloc[-3]
    c = df.iloc[-2]
    return prev["low"] < low and c["close"] > low and strong_bullish(c)

def sell_signal(df):
    high, low = get_liquidity(df)
    prev = df.iloc[-3]
    c = df.iloc[-2]
    return prev["high"] > high and c["close"] < high and strong_bearish(c)

# ================= CONTROL =================

def can_trade():
    return (time.time() - last_trade_time) > COOLDOWN

def wait_open():
    while True:
        try:
            t = iq.get_server_timestamp()
            if t % 60 == 0:
                time.sleep(0.2)
                return
        except:
            pass
        time.sleep(0.05)

# ================= TRADE =================

def trade(pair, direction):
    global last_trade_time

    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            last_trade_time = time.time()
            msg = f"🎯 {pair} {direction.upper()} (OVERLAP BOGOTÁ)"
            print(msg)
            send(msg)
        else:
            print(f"❌ Falló trade {pair}")

    except Exception as e:
        print("❌ Error trade:", e)

# ================= LÓGICA PRINCIPAL =================

def main():
    global last_candle_time

    reconnect()

    if not is_trading_time():
        time.sleep(60)
        return

    if not can_trade():
        time.sleep(0.5)
        return

    try:
        server_time = iq.get_server_timestamp()
    except:
        time.sleep(1)
        return

    current_candle = server_time // 60

    if current_candle == last_candle_time:
        time.sleep(0.1)
        return

    last_candle_time = current_candle

    for pair in PAIRS:
        df = get_candles(pair)
        if df is None or len(df) < 30:
            continue

        if buy_signal(df):
            send(f"💧 {pair} BUY")
            wait_open()
            trade(pair, "call")
            return

        elif sell_signal(df):
            send(f"💧 {pair} SELL")
            wait_open()
            trade(pair, "put")
            return

# ================= INICIO =================

print("🚀 BOT INICIANDO...")
connect()
send("🔥 BOT ACTIVO (OVERLAP BOGOTÁ)")

# ================= LOOP ESTABLE =================

last_log_time = 0

while True:
    try:
        main()

        now = time.time()
        if now - last_log_time > 30:
            print("🟢 Bot activo...")
            last_log_time = now

        time.sleep(0.2)

    except Exception as e:
        print("🔥 ERROR GLOBAL:", e)
        time.sleep(5)
