instrument {
    name = "AGOTAMIENTO INVERTIDO PRO",
    short_name = "EXHAUSTION_INV",
    overlay = true
}

-- ==========================
-- 🎨 COLORES
-- ==========================
input_group {
    "COLORES",
    colorBuy = input { default = "green", type = input.color },
    colorSell = input { default = "red", type = input.color }
}

-- ==========================
-- 📊 DATOS
-- ==========================
h = high
l = low
c = close
o = open

-- ==========================
-- 🔥 ZONAS
-- ==========================
lookback = 30

maximo = highest(high, lookback)
minimo = lowest(low, lookback)

rango_total = maximo - minimo
zona = rango_total * 0.02

zona_alta = maximo - zona
zona_baja = minimo + zona

-- ==========================
-- 🔥 VELA
-- ==========================
rango = h - l
rango = rango == 0 and 0.000001 or rango

cuerpo = math.abs(c - o)

mecha_sup = h - math.max(o, c)
mecha_inf = math.min(o, c) - l

-- ==========================
-- 🔥 AGOTAMIENTO DETECTADO
-- ==========================
agotamiento_arriba =
    h >= zona_alta and
    mecha_sup > cuerpo * 1.5

agotamiento_abajo =
    l <= zona_baja and
    mecha_inf > cuerpo * 1.5

-- ==========================
-- 🔥 CONFIRMACIÓN (CLAVE)
-- ==========================
confirmacion_alcista = c > o
confirmacion_bajista = c < o

-- ==========================
-- 🎯 SEÑALES INVERTIDAS
-- ==========================
call_signal =
    agotamiento_arriba and
    confirmacion_alcista

put_signal =
    agotamiento_abajo and
    confirmacion_bajista

-- ==========================
-- 🔥 ZONAS VISUALES
-- ==========================
bgcolor(
    agotamiento_arriba and rgba(255,0,0,0.08) or
    agotamiento_abajo and rgba(0,0,255,0.08)
)

-- ==========================
-- 🔥 LÍNEAS
-- ==========================
plot(zona_alta, "ZONA ALTA", "red", 1)
plot(zona_baja, "ZONA BAJA", "blue", 1)

-- ==========================
-- 🔥 SEÑALES
-- ==========================
plot_shape(
    call_signal,
    "CALL",
    shape_style.triangleup,
    shape_size.large,
    colorBuy,
    shape_location.belowbar,
    0,
    "CALL",
    "white"
)

plot_shape(
    put_signal,
    "PUT",
    shape_style.triangledown,
    shape_size.large,
    colorSell,
    shape_location.abovebar,
    0,
    "PUT",
    "white"
)

-- ==========================
-- 🔥 MARCA PRECISA
-- ==========================
plot(
    call_signal and low or na,
    "BUY DOT",
    colorBuy,
    2
)

plot(
    put_signal and high or na,
    "SELL DOT",
    colorSell,
    2
)
