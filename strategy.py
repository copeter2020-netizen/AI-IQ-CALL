instrument {
    name = "AGOTAMIENTO PRO",
    short_name = "EXHAUSTION_PRO",
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
-- 🔥 ZONAS (LIQUIDEZ)
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
-- 🔥 AGOTAMIENTO REAL
-- ==========================
agotamiento_venta =
    h >= zona_alta and
    mecha_sup > cuerpo * 1.5 and
    c < o

agotamiento_compra =
    l <= zona_baja and
    mecha_inf > cuerpo * 1.5 and
    c > o

-- ==========================
-- 🔥 DIBUJAR ZONAS
-- ==========================
bgcolor(
    h >= zona_alta and rgba(255,0,0,0.08) or
    l <= zona_baja and rgba(0,0,255,0.08)
)

-- ==========================
-- 🔥 LÍMITES ZONA
-- ==========================
plot(zona_alta, "ZONA VENTA", "red", 1)
plot(zona_baja, "ZONA COMPRA", "blue", 1)

-- ==========================
-- 🔥 SEÑALES
-- ==========================
plot_shape(
    agotamiento_venta,
    "SELL",
    shape_style.triangledown,
    shape_size.large,
    colorSell,
    shape_location.abovebar,
    0,
    "SELL",
    "white"
)

plot_shape(
    agotamiento_compra,
    "BUY",
    shape_style.triangleup,
    shape_size.large,
    colorBuy,
    shape_location.belowbar,
    0,
    "BUY",
    "white"
)

-- ==========================
-- 🔥 MARCA PRECISA
-- ==========================
plot(
    agotamiento_compra and low or na,
    "BUY DOT",
    colorBuy,
    2
)

plot(
    agotamiento_venta and high or na,
    "SELL DOT",
    colorSell,
    2
)
