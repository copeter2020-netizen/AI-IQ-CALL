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
AMOUNT = 10
COOLDOWN = 180

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ================= VALIDACIÓN =================

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

def get_bogota_hour():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    bogota_time = utc_now - timedelta(hours=5)
    return bogota_time.hour, bogota_time.minute

def is_trading_time():
    hour, minute = get_bogota_hour()

    # 🔥 Overlap Bogotá: 08:00 - 11:00
    if hour == 8:
        return True
    elif hour == 9:
        return True
    elif hour == 10:
        return True
    elif hour == 11 and minute == 0:
        return True

    return False

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)

def connect():
    print("🔌 Conectando...")
    iq.connect()

    if not iq.check_connect():
        raise Exception("❌ No conecta a IQ Option")

    iq.change_balance("PRACTICE")
    print("✅ Conectado")

def reconnect():
    if not iq.check_connect():
        print("🔄 Reconectando...")
        try:
            iq.connect()
            iq.change_balance("PRACTICE")
        except:
            time.sleep(3)

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
            msg = f"🎯 {pair} {direction.upper()} (BOGOTÁ)"
            print(msg)
            send(msg)
        else:
            print(f"❌ Falló trade {pair}")

    except Exception as e:
        print("❌ Error trade:", e)

# ================= INICIO =================

connect()
send("🔥 BOT ACTIVO (HORA BOGOTÁ 08:00–11:00)")

# ================= LOOP =================

while True:
    try:
        reconnect()

        if not is_trading_time():
            print("⏸ Fuera de horario Bogotá")
            time.sleep(60)
            continue

        if not can_trade():
            time.sleep(0.5)
            continue

        try:
            server_time = iq.get_server_timestamp()
        except:
            time.sleep(1)
            continue

        current_candle = server_time // 60

        if current_candle == last_candle_time:
            time.sleep(0.1)
            continue

        last_candle_time = current_candle

        for pair in PAIRS:
            df = get_candles(pair)
            if df is None or len(df) < 30:
                continue

            if buy_signal(df):
                send(f"💧 {pair} BUY (BOGOTÁ)")
                wait_open()
                trade(pair, "call")
                break

            elif sell_signal(df):
                send(f"💧 {pair} SELL (BOGOTÁ)")
                wait_open()
                trade(pair, "put")
                break

        time.sleep(0.1)

    except Exception as e:
        print("❌ ERROR LOOP:", e)
        time.sleep(3)
