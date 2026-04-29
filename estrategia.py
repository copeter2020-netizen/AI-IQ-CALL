# ===============================
# PRICE ACTION PRO SNIPER
# ===============================

def body(c):
    return abs(c["close"] - c["open"])


def rango(c):
    return c["high"] - c["low"]


def fuerza(c):
    r = rango(c)
    if r == 0:
        return 0
    return body(c) / r


def is_doji(c):
    return fuerza(c) < 0.3


# ===============================
# TENDENCIA
# ===============================

def tendencia(df):
    closes = df["close"].values[-6:]

    up = all(closes[i] > closes[i-1] for i in range(1, len(closes)))
    down = all(closes[i] < closes[i-1] for i in range(1, len(closes)))

    if up:
        return "call"
    if down:
        return "put"

    return None


# ===============================
# RUPTURA
# ===============================

def ruptura(df):
    last = df.iloc[-1]
    prev_high = df["high"].iloc[-5:-1].max()
    prev_low = df["low"].iloc[-5:-1].min()

    if last["close"] > prev_high:
        return "call"

    if last["close"] < prev_low:
        return "put"

    return None


# ===============================
# SCORE
# ===============================

def score_pair(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0

    f = fuerza(last)

    if f > 0.75:
        score += 2
    elif f > 0.65:
        score += 1

    # continuidad
    if last["close"] > prev["close"]:
        score += 1
    elif last["close"] < prev["close"]:
        score += 1

    # tendencia
    if tendencia(df):
        score += 1

    # ruptura
    if ruptura(df):
        score += 1

    return score


# ===============================
# SEÑAL FINAL
# ===============================

def check_signal(df):

    if len(df) < 10:
        return None, 0

    last = df.iloc[-1]

    if is_doji(last):
        return None, 0

    f = fuerza(last)

    if f < 0.6:
        return None, 0

    t = tendencia(df)

    if not t:
        return None, 0

    score = score_pair(df)

    # 🔥 SOLO ALTA PROBABILIDAD
    if score < 3:
        return None, score

    if t == "call" and last["close"] > last["open"]:
        return "call", score

    if t == "put" and last["close"] < last["open"]:
        return "put", score

    return None, score
