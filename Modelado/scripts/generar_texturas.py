"""
Generador de texturas propias del proyecto "Camino de Cempasúchil".

Todas las texturas se crean desde cero de forma procedural (ruido + dibujo
vectorial) para que sean reproducibles y ligeras. Se guardan en
assets/textures/ con resoluciones potencia de dos (128-512 px) para
aprovechar mipmapping y reducir memoria de video.

Uso (requiere Python 3 con Pillow y numpy):
    python Modelado/scripts/generar_texturas.py
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SALIDA = os.path.join(RAIZ, "assets", "textures")
SS = 4  # factor de supermuestreo para bordes suaves


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ruido(w, h, celdas, semilla, octavas=4):
    """Ruido fractal (fBm) en [0,1] construido con ruido de valor bicúbico."""
    rng = np.random.default_rng(semilla)
    total = np.zeros((h, w), np.float32)
    amp, norm = 1.0, 0.0
    c = celdas
    for _ in range(octavas):
        base = rng.random((c, c), dtype=np.float32)
        # se repite la primera fila/columna para que el ruido sea repetible (tileable)
        base = np.pad(base, ((0, 1), (0, 1)), mode="wrap")
        img = Image.fromarray((base * 255).astype(np.uint8))
        big = img.resize((w + w // c, h + h // c), Image.BICUBIC)
        arr = np.asarray(big, np.float32)[:h, :w] / 255.0
        total += arr * amp
        norm += amp
        amp *= 0.5
        c *= 2
    return total / norm


def mezclar(c1, c2, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.asarray(c1, np.float32) * (1 - t) + np.asarray(c2, np.float32) * t


def guardar(arr_o_img, nombre, calidad=90):
    if isinstance(arr_o_img, np.ndarray):
        img = Image.fromarray(np.clip(arr_o_img, 0, 255).astype(np.uint8))
    else:
        img = arr_o_img
    ruta = os.path.join(SALIDA, nombre)
    if nombre.endswith(".jpg"):
        img.convert("RGB").save(ruta, quality=calidad, optimize=True)
    else:
        img.save(ruta, optimize=True)
    print(f"  {nombre:28s} {img.size[0]}x{img.size[1]}  {os.path.getsize(ruta) / 1024:6.1f} KB")


def lienzo(w, h, color=(0, 0, 0, 0)):
    img = Image.new("RGBA", (w * SS, h * SS), color)
    return img, ImageDraw.Draw(img)


def reducir(img, w, h):
    return img.resize((w, h), Image.LANCZOS)


def fuente(tam, negrita=True):
    candidatas = [
        "C:/Windows/Fonts/georgiab.ttf",
        "C:/Windows/Fonts/timesbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/Library/Fonts/Georgia Bold.ttf",
    ]
    for c in candidatas:
        if os.path.exists(c):
            return ImageFont.truetype(c, tam)
    return ImageFont.load_default()


def circulo(d, cx, cy, r, **kw):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], **kw)


def flor_petalos(d, cx, cy, r, n, color, centro=None, rel=0.45):
    """Flor esquemática: n pétalos elípticos alrededor de un centro."""
    for i in range(n):
        a = 2 * math.pi * i / n
        px, py = cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55
        pts = []
        for k in range(16):
            t = 2 * math.pi * k / 16
            ex, ey = math.cos(t) * r * 0.5, math.sin(t) * r * 0.5 * rel * 1.6
            pts.append((px + ex * math.cos(a) - ey * math.sin(a),
                        py + ex * math.sin(a) + ey * math.cos(a)))
        d.polygon(pts, fill=color)
    if centro:
        circulo(d, cx, cy, r * 0.28, fill=centro)


# ---------------------------------------------------------------------------
# Texturas
# ---------------------------------------------------------------------------
def tex_petalo():
    """Pétalo de cempasúchil: v=0 base (rojo anaranjado) -> v=1 punta (amarillo)."""
    w = h = 256
    y = np.linspace(1, 0, h, dtype=np.float32)[:, None] * np.ones((1, w), np.float32)
    x = np.linspace(0, 1, w, dtype=np.float32)[None, :] * np.ones((h, 1), np.float32)
    base, medio, punta = hex2rgb("#C2410C"), hex2rgb("#F76707"), hex2rgb("#FFB020")
    col = np.where((y < 0.5)[..., None], mezclar(base, medio, y / 0.5), mezclar(medio, punta, (y - 0.5) / 0.5))
    # nervaduras: líneas que nacen en la base y se abren hacia la punta
    ang = (x - 0.5) / (0.15 + y * 0.85)
    vena = np.abs(np.sin(ang * math.pi * 7)) ** 18
    col *= (1 - 0.18 * vena * (0.3 + y))[..., None]
    # borde ondulado (rizos) más oscuro en la punta
    rizo = 0.5 + 0.5 * np.sin(x * math.pi * 22)
    borde = np.clip((y - 0.86) / 0.14, 0, 1) * (0.6 + 0.4 * rizo)
    col = mezclar(col, hex2rgb("#E8590C"), borde * 0.55)
    n = ruido(w, h, 8, 11)
    col *= (0.88 + 0.24 * n)[..., None]
    guardar(col, "petalo_cempasuchil.png")


def tex_papel_picado():
    """Atlas 2x2 de banderitas de papel picado en blanco; el color se aplica por vértice."""
    w = h = 512
    celda = 256
    img, d = lienzo(w, h)
    S = SS

    def cortes_fondo(x0, y0, x1, y1, paso, forma="rombo"):
        yy = y0
        fila = 0
        while yy + paso <= y1:
            xx = x0 + (paso / 2 if fila % 2 else 0)
            while xx + paso <= x1:
                cx, cy, r = xx + paso / 2, yy + paso / 2, paso * 0.32
                if forma == "rombo":
                    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=(0, 0, 0, 0))
                else:
                    circulo(d, cx, cy, r * 0.8, fill=(0, 0, 0, 0))
                xx += paso
            yy += paso
            fila += 1

    for idx in range(4):
        cx0 = (idx % 2) * celda * S
        cy0 = (idx // 2) * celda * S
        C = celda * S
        # papel completo
        d.rectangle([cx0, cy0, cx0 + C - 1, cy0 + C - 1], fill=(255, 255, 255, 255))
        m = int(C * 0.07)       # margen lateral
        top = int(C * 0.13)     # franja superior (doblez sobre el cordel)
        bot = int(C * 0.84)     # inicio de los picos inferiores
        # picos inferiores (zigzag)
        npicos = 8
        anchop = C / npicos
        for k in range(npicos):
            x0 = cx0 + k * anchop
            d.polygon([(x0, cy0 + C), (x0 + anchop / 2, cy0 + bot + C * 0.03), (x0 + anchop, cy0 + C)],
                      fill=(0, 0, 0, 0))
        # area interior con calado
        ix0, iy0, ix1, iy1 = cx0 + m, cy0 + top, cx0 + C - m, cy0 + bot - C * 0.04
        cxm, cym = (ix0 + ix1) / 2, (iy0 + iy1) / 2
        rmot = (ix1 - ix0) * 0.30
        cortes_fondo(ix0, iy0, ix1, iy1, C * 0.075, "rombo" if idx % 2 == 0 else "circulo")
        # el motivo central se dibuja en papel sólido sobre el calado
        if idx == 0:  # calavera
            circulo(d, cxm, cym - rmot * 0.15, rmot * 1.02, fill=(255, 255, 255, 255))
            d.rounded_rectangle([cxm - rmot * 0.55, cym + rmot * 0.4, cxm + rmot * 0.55, cym + rmot * 1.1],
                                radius=rmot * 0.2, fill=(255, 255, 255, 255))
            for sx in (-1, 1):
                circulo(d, cxm + sx * rmot * 0.38, cym - rmot * 0.1, rmot * 0.27, fill=(0, 0, 0, 0))
            d.polygon([(cxm, cym + rmot * 0.18), (cxm - rmot * 0.12, cym + rmot * 0.42),
                       (cxm + rmot * 0.12, cym + rmot * 0.42)], fill=(0, 0, 0, 0))
            for k in range(-2, 3):
                d.rectangle([cxm + k * rmot * 0.2 - rmot * 0.06, cym + rmot * 0.62,
                             cxm + k * rmot * 0.2 + rmot * 0.06, cym + rmot * 0.92], fill=(0, 0, 0, 0))
            flor_petalos(d, cxm, cym - rmot * 0.72, rmot * 0.32, 6, (0, 0, 0, 0), (255, 255, 255, 255))
        elif idx == 1:  # flor de cempasúchil
            circulo(d, cxm, cym, rmot * 1.15, fill=(255, 255, 255, 255))
            flor_petalos(d, cxm, cym, rmot * 1.05, 10, (0, 0, 0, 0), (255, 255, 255, 255), rel=0.35)
            circulo(d, cxm, cym, rmot * 0.32, fill=(255, 255, 255, 255))
            circulo(d, cxm, cym, rmot * 0.14, fill=(0, 0, 0, 0))
        elif idx == 2:  # cruz con velas
            d.rectangle([cxm - rmot * 1.1, cym - rmot * 1.15, cxm + rmot * 1.1, cym + rmot * 1.15],
                        fill=(255, 255, 255, 255))
            g = rmot * 0.16
            d.rectangle([cxm - g, cym - rmot * 1.0, cxm + g, cym + rmot * 1.0], fill=(0, 0, 0, 0))
            d.rectangle([cxm - rmot * 0.6, cym - rmot * 0.55, cxm + rmot * 0.6, cym - rmot * 0.55 + 2 * g],
                        fill=(0, 0, 0, 0))
            for sx in (-1, 1):
                vx = cxm + sx * rmot * 0.82
                d.rectangle([vx - g * 0.7, cym + rmot * 0.1, vx + g * 0.7, cym + rmot * 0.95], fill=(0, 0, 0, 0))
                d.polygon([(vx, cym - rmot * 0.25), (vx - g * 0.8, cym), (vx + g * 0.8, cym)], fill=(0, 0, 0, 0))
        else:  # sol / estrella geométrica
            circulo(d, cxm, cym, rmot * 1.15, fill=(255, 255, 255, 255))
            for k in range(12):
                a = 2 * math.pi * k / 12
                p1 = (cxm + math.cos(a - 0.12) * rmot * 0.45, cym + math.sin(a - 0.12) * rmot * 0.45)
                p2 = (cxm + math.cos(a) * rmot * 1.05, cym + math.sin(a) * rmot * 1.05)
                p3 = (cxm + math.cos(a + 0.12) * rmot * 0.45, cym + math.sin(a + 0.12) * rmot * 0.45)
                d.polygon([p1, p2, p3], fill=(0, 0, 0, 0))
            circulo(d, cxm, cym, rmot * 0.3, fill=(0, 0, 0, 0))
        # perforaciones de la franja superior (donde pasa el cordel)
        for k in range(10):
            circulo(d, cx0 + C * (k + 0.5) / 10, cy0 + top * 0.55, C * 0.012, fill=(0, 0, 0, 0))
    out = reducir(img, w, h)
    guardar(out, "papel_picado.png")


def tex_calaverita():
    """Mitad izquierda: cara frontal (proyección plana). Mitad derecha: laterales/nuca."""
    W = H = 512
    img, d = lienzo(W, H, (250, 247, 240, 255))
    S = SS
    # Mapeo idéntico al de Modelado/scripts/modelos/calaverita_azucar.py:
    # u = 0.25 + x/ANCHO*0.5 en [0,0.5]  (x en [-ANCHO/2, ANCHO/2])
    # v = (z - z0) / ALTO           (v=0 abajo => fila H en la imagen)
    ANCHO, ALTO = 0.10, 0.11

    def p(x, z):
        u = 0.25 + x / ANCHO * 0.5
        v = z / ALTO
        return u * W * S, (1 - v) * H * S

    def R(m):  # radio en metros -> pixeles
        return m / ANCHO * 0.5 * W * S

    rosa, verde, azul, amarillo, morado, naranja = (hex2rgb(c) for c in
                                                     ("#E64980", "#2F9E44", "#1C7ED6", "#FAB005", "#9C36B5", "#F76707"))
    negro = (40, 30, 35)
    # ojos: cuencas con pétalos de colores
    for sx, col in ((-1, azul), (1, verde)):
        ex, ey = p(sx * 0.021, 0.062)
        for k in range(10):
            a = 2 * math.pi * k / 10
            circulo(d, ex + math.cos(a) * R(0.0155), ey + math.sin(a) * R(0.0155), R(0.0065), fill=rosa)
        circulo(d, ex, ey, R(0.0145), fill=col)
        circulo(d, ex, ey, R(0.0095), fill=negro)
        circulo(d, ex - R(0.003), ey - R(0.003), R(0.0025), fill=(255, 255, 255))
    # nariz: corazón invertido
    nx, ny = p(0.0, 0.043)
    r = R(0.0055)
    circulo(d, nx - r * 0.8, ny + r * 0.4, r, fill=negro)
    circulo(d, nx + r * 0.8, ny + r * 0.4, r, fill=negro)
    d.polygon([(nx - r * 1.75, ny + r * 0.6), (nx + r * 1.75, ny + r * 0.6), (nx, ny - r * 1.6)], fill=negro)
    # dientes con costuras
    x0, y0 = p(-0.024, 0.030)
    x1, y1 = p(0.024, 0.018)
    d.rounded_rectangle([x0, y0, x1, y1], radius=R(0.004), fill=(255, 255, 255), outline=negro, width=int(S * 3))
    for k in range(1, 8):
        xx = x0 + (x1 - x0) * k / 8
        d.line([(xx, y0), (xx, y1)], fill=negro, width=int(S * 2))
    d.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=negro, width=int(S * 2))
    # frente: flor de cempasúchil y hojas
    fx, fy = p(0.0, 0.092)
    for sx in (-1, 1):
        d.ellipse([fx + sx * R(0.018) - R(0.009), fy - R(0.004), fx + sx * R(0.018) + R(0.009), fy + R(0.006)],
                  fill=verde)
    flor_petalos(d, fx, fy, R(0.016), 8, naranja, amarillo)
    flor_petalos(d, fx, fy, R(0.009), 6, amarillo, naranja)
    # mejillas: espirales de puntos
    for sx, col in ((-1, morado), (1, rosa)):
        cx, cy = p(sx * 0.034, 0.040)
        for k in range(14):
            a = k * 0.55
            rr = R(0.002) + k * R(0.0007)
            circulo(d, cx + math.cos(a) * rr * 1.2, cy + math.sin(a) * rr * 1.2, R(0.0018), fill=col)
    # barbilla: puntos de colores
    for k, col in enumerate((rosa, amarillo, azul, amarillo, rosa)):
        bx, by = p(-0.012 + k * 0.006, 0.010)
        circulo(d, bx, by, R(0.0022), fill=col)
    # contorno de ojos superior (cejas decorativas)
    for sx in (-1, 1):
        ex, ey = p(sx * 0.021, 0.080)
        d.arc([ex - R(0.016), ey - R(0.006), ex + R(0.016), ey + R(0.010)], 200, 340, fill=morado, width=int(S * 5))
    # mitad derecha: laterales y nuca con puntos y flores pequeñas
    rng = np.random.default_rng(7)
    colores = [rosa, verde, azul, amarillo, morado, naranja]
    for k in range(70):
        x = rng.uniform(0.52, 0.98) * W * S
        y = rng.uniform(0.05, 0.95) * H * S
        if k % 7 == 0:
            flor_petalos(d, x, y, R(0.007), 6, colores[k % 6], (255, 255, 255))
        else:
            circulo(d, x, y, R(0.0018), fill=colores[k % 6])
    out = reducir(img, W, H).convert("RGB")
    arr = np.asarray(out, np.float32)
    n = ruido(W, H, 32, 5, 3)
    arr *= (0.94 + 0.08 * n)[..., None]
    # destellos de azúcar
    rng = np.random.default_rng(9)
    m = rng.random((H, W)) > 0.996
    arr[m] = 255
    guardar(arr, "calaverita.png")


def tex_pan_de_muerto():
    w = h = 256
    n = ruido(w, h, 6, 21)
    y = np.linspace(1, 0, h, dtype=np.float32)[:, None] * np.ones((1, w), np.float32)
    col = mezclar(hex2rgb("#7A4716"), hex2rgb("#C98E4E"), np.clip(y * 1.3, 0, 1))
    col *= (0.85 + 0.3 * n)[..., None]
    rng = np.random.default_rng(3)
    azucar = rng.random((h, w)) > 0.80
    brillo = rng.random((h, w))
    col[azucar] = col[azucar] * 0.25 + np.array(hex2rgb("#FFF4E0"), np.float32) * 0.75 * (0.85 + 0.15 * brillo[azucar, None])
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.4))
    guardar(img, "pan_de_muerto.png")


def chaikin(pts, iteraciones=3):
    """Suaviza un polígono cerrado recortando esquinas (algoritmo de Chaikin)."""
    for _ in range(iteraciones):
        nuevo = []
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            nuevo += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1),
                      (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        pts = nuevo
    return pts


def tex_mariposa():
    """Alas derechas de mariposa monarca: ala anterior arriba, posterior abajo (RGBA)."""
    w = h = 256
    img, d = lienzo(w, h)
    S = SS
    naranja, negro, blanco = hex2rgb("#F08C00"), (25, 20, 18), (250, 250, 245)
    mascara = Image.new("L", img.size, 0)
    dm = ImageDraw.Draw(mascara)

    def ala(pts, venas):
        pts = chaikin([(x * S, y * S) for x, y in pts], 3)
        dm.polygon(pts, fill=255)
        d.polygon(pts, fill=negro)
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        interior = [(cx + (x - cx) * 0.82, cy + (y - cy) * 0.82) for x, y in pts]
        d.polygon(interior, fill=naranja)
        for (x0, y0), (x1, y1) in venas:
            d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=negro, width=int(S * 2.2))
        # puntos blancos sobre el borde negro
        for i in range(0, len(pts), 3):
            px, py = pts[i]
            px, py = px + (cx - px) * 0.085, py + (cy - py) * 0.085
            circulo(d, px, py, S * 2.0, fill=blanco)

    # ala anterior en [0,128] vertical; la base del ala (unión al cuerpo) está en x=0
    ala([(4, 118), (60, 20), (120, 8), (250, 30), (240, 70), (150, 118)],
        [((6, 116), (240, 34)), ((6, 116), (200, 70)), ((6, 116), (150, 112)), ((70, 70), (120, 12))])
    # ala posterior en [128,256]
    ala([(4, 134), (150, 134), (230, 170), (210, 230), (120, 252), (40, 230)],
        [((6, 136), (220, 175)), ((6, 136), (200, 228)), ((6, 136), (120, 248)), ((6, 136), (45, 228))])
    # ápice del ala anterior con manchas
    for (x, y) in ((205, 40), (222, 52), (190, 30)):
        circulo(d, x * S, y * S, S * 4, fill=hex2rgb("#FFD8A8"))
    # recorta las venas que salen del contorno del ala
    alfa = Image.fromarray(np.minimum(np.asarray(img.getchannel("A")), np.asarray(mascara)))
    img.putalpha(alfa)
    out = reducir(img, w, h)
    guardar(out, "mariposa_monarca.png")


def tex_veladora():
    w = h = 256
    img, d = lienzo(w, h, hex2rgb("#B3123A") + (255,))
    S = SS
    oro = hex2rgb("#F2C14E")
    # franjas superior e inferior
    d.rectangle([0, 0, w * S, 18 * S], fill=hex2rgb("#7A0C27"))
    d.rectangle([0, (h - 18) * S, w * S, h * S], fill=hex2rgb("#7A0C27"))
    for k in range(16):
        x = (k + 0.5) * w * S / 16
        circulo(d, x, 9 * S, 3 * S, fill=oro)
        circulo(d, x, (h - 9) * S, 3 * S, fill=oro)
    # motivo frontal (u=0.5 queda al frente del vaso)
    cx, cy = w * S / 2, h * S / 2
    d.ellipse([cx - 48 * S, cy - 70 * S, cx + 48 * S, cy + 70 * S], outline=oro, width=4 * S)
    flor_petalos(d, cx, cy + 18 * S, 30 * S, 10, hex2rgb("#F76707"), oro)
    d.rectangle([cx - 4 * S, cy - 58 * S, cx + 4 * S, cy - 14 * S], fill=oro)
    d.rectangle([cx - 16 * S, cy - 46 * S, cx + 16 * S, cy - 38 * S], fill=oro)
    out = reducir(img, w, h).convert("RGB")
    arr = np.asarray(out, np.float32) * (0.92 + 0.12 * ruido(w, h, 16, 4, 2))[..., None]
    guardar(arr, "veladora.png")


def tex_mantel():
    """Mantel blanco con cenefa bordada (v en [0,0.25] = borde inferior)."""
    w = h = 512
    img, d = lienzo(w, h, (246, 244, 238, 255))
    S = SS
    morado, naranja, rosa, verde = (hex2rgb(c) for c in ("#6741D9", "#F76707", "#D6336C", "#2B8A3E"))
    y0 = int(h * 0.75) * S
    d.rectangle([0, y0, w * S, h * S], fill=hex2rgb("#5F3DC4"))
    d.rectangle([0, y0, w * S, y0 + 6 * S], fill=naranja)
    d.rectangle([0, h * S - 8 * S, w * S, h * S], fill=naranja)
    n = 8
    for k in range(n):
        cx = (k + 0.5) * w * S / n
        cy = (y0 + h * S) / 2 + 2 * S
        flor_petalos(d, cx, cy, 26 * S, 8, naranja if k % 2 == 0 else rosa, hex2rgb("#FFD43B"))
        for sx in (-1, 1):
            d.ellipse([cx + sx * 34 * S - 10 * S, cy - 5 * S, cx + sx * 34 * S + 10 * S, cy + 5 * S], fill=verde)
    # puntadas en zigzag sobre la cenefa
    pts = []
    for k in range(65):
        pts.append((k * w * S / 64, y0 - (10 if k % 2 else 2) * S))
    d.line(pts, fill=morado, width=3 * S)
    out = reducir(img, w, h).convert("RGB")
    arr = np.asarray(out, np.float32)
    # tejido: patrón de trama fina
    yy, xx = np.mgrid[0:h, 0:w]
    trama = 0.5 + 0.25 * np.sin(xx * math.pi / 1.5) + 0.25 * np.sin(yy * math.pi / 1.5)
    arr *= (0.95 + 0.06 * trama * ruido(w, h, 16, 8, 2))[..., None]
    guardar(arr, "mantel.png")


def tex_barro():
    """Barro rojo con banda pintada (tileable en horizontal)."""
    w = h = 512
    n = ruido(w, h, 8, 31)
    n2 = ruido(w, h, 64, 32, 2)
    col = mezclar(hex2rgb("#8C3B1C"), hex2rgb("#B5562A"), n)
    col *= (0.9 + 0.15 * n2)[..., None]
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).convert("RGBA")
    big = img.resize((w * SS, h * SS), Image.BICUBIC)
    d = ImageDraw.Draw(big)
    S = SS
    crema = hex2rgb("#F1E3C6") + (255,)
    yb0, yb1 = int(h * 0.42) * S, int(h * 0.58) * S
    d.line([(0, yb0), (w * S, yb0)], fill=crema, width=3 * S)
    d.line([(0, yb1), (w * S, yb1)], fill=crema, width=3 * S)
    n_mot = 8
    for k in range(n_mot):
        cx = (k + 0.5) * w * S / n_mot
        cy = (yb0 + yb1) / 2
        flor_petalos(d, cx, cy, 22 * S, 6, crema, hex2rgb("#2B2B2B") + (255,))
        for sx in (-1, 1):
            circulo(d, cx + sx * 32 * S, cy, 3 * S, fill=crema)
    out = reducir(big, w, h).convert("RGB")
    guardar(out, "barro.png")


def tex_talavera():
    """Cerámica de Talavera poblana: fondo blanco esmaltado y motivos en azul cobalto."""
    w = h = 512
    img, d = lienzo(w, h, (244, 241, 230, 255))
    S = SS
    azul, amarillo, verde = hex2rgb("#1C3F94"), hex2rgb("#F2A900"), hex2rgb("#2F7D32")
    # bandas superior e inferior
    for yb in (0.08, 0.92):
        y = yb * h * S
        d.rectangle([0, y - 14 * S, w * S, y + 14 * S], fill=azul)
        for k in range(16):
            circulo(d, (k + 0.5) * w * S / 16, y, 6 * S, fill=(244, 241, 230))
    # motivos florales centrales repetidos en 4 columnas (repetible en u)
    for k in range(4):
        cx = (k + 0.5) * w * S / 4
        cy = h * S * 0.5
        flor_petalos(d, cx, cy, 70 * S, 8, azul, amarillo, rel=0.5)
        circulo(d, cx, cy, 14 * S, fill=azul)
        for sy in (-1, 1):
            d.ellipse([cx - 10 * S, cy + sy * 95 * S - 22 * S, cx + 10 * S, cy + sy * 95 * S + 22 * S], fill=verde)
        for sx in (-1, 1):
            circulo(d, cx + sx * w * S / 8, cy + 120 * S, 9 * S, fill=azul)
            circulo(d, cx + sx * w * S / 8, cy - 120 * S, 9 * S, fill=azul)
    out = reducir(img, w, h).convert("RGB")
    arr = np.asarray(out, np.float32) * (0.97 + 0.04 * ruido(w, h, 16, 12, 2))[..., None]
    guardar(arr, "talavera.png")


def tex_foto():
    """Retrato en sepia ilustrado (marcador de posición para fotos familiares)."""
    w = h = 256
    img, d = lienzo(w, h, hex2rgb("#C9A77C") + (255,))
    S = SS
    oscuro = hex2rgb("#4A3420")
    medio = hex2rgb("#7B5B3A")
    cx = w * S / 2
    # silueta: hombros, cabeza y sombrero
    d.ellipse([cx - 95 * S, 170 * S, cx + 95 * S, 330 * S], fill=oscuro)
    d.rectangle([cx - 20 * S, 140 * S, cx + 20 * S, 185 * S], fill=medio)
    d.ellipse([cx - 40 * S, 75 * S, cx + 40 * S, 165 * S], fill=medio)
    d.ellipse([cx - 92 * S, 70 * S, cx + 92 * S, 96 * S], fill=oscuro)          # ala del sombrero
    d.rounded_rectangle([cx - 38 * S, 30 * S, cx + 38 * S, 84 * S], radius=18 * S, fill=oscuro)
    d.arc([cx - 22 * S, 128 * S, cx + 22 * S, 148 * S], 200, 340, fill=oscuro, width=5 * S)  # bigote
    out = reducir(img, w, h).convert("RGB")
    arr = np.asarray(out, np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w * 0.5)) ** 2 + ((yy - h / 2) / (h * 0.55)) ** 2)
    vineta = np.clip(1.15 - r ** 2 * 0.55, 0.35, 1)
    arr *= vineta[..., None] * (0.92 + 0.12 * ruido(w, h, 32, 2, 3))[..., None]
    guardar(arr, "foto_retrato.png")


def tex_hojalata():
    w = h = 256
    n = ruido(w, h, 4, 41, 2)
    yy, xx = np.mgrid[0:h, 0:w]
    cepillado = ruido(w, 1, 128, 42, 1)[0][None, :] * np.ones((h, 1))
    base = mezclar(hex2rgb("#8E9196"), hex2rgb("#D5D8DC"), 0.5 * n + 0.5 * cepillado)
    # relieve repujado: puntos y líneas de troquel
    relieve = np.zeros((h, w), np.float32)
    for cy in range(16, h, 32):
        for cx in range(16, w, 32):
            relieve += np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / 18.0)
    relieve += np.exp(-((yy % 64) - 2) ** 2 / 2.0) * 0.8
    base *= (0.9 + 0.25 * relieve)[..., None]
    guardar(base, "hojalata.png")


def tex_vidrio():
    w = h = 256
    img, d = lienzo(w, h, (60, 60, 60, 255))
    S = SS
    colores = [hex2rgb(c) for c in ("#E03131", "#2F9E44", "#FAB005", "#1971C2")]
    for i, col in enumerate(colores):
        x0, y0 = (i % 2) * 128 * S, (i // 2) * 128 * S
        d.rectangle([x0 + 6 * S, y0 + 6 * S, x0 + 122 * S, y0 + 122 * S], fill=col)
        circulo(d, x0 + 64 * S, y0 + 64 * S, 22 * S, fill=tuple(min(255, c + 70) for c in col))
    out = reducir(img, w, h).convert("RGB")
    arr = np.asarray(out, np.float32) * (0.9 + 0.15 * ruido(w, h, 8, 50, 2))[..., None]
    guardar(arr, "vidrio_colores.png")


def tex_petate():
    """Tejido de palma (petate): tiras diagonales entrelazadas, repetible."""
    w = h = 256
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = (xx + yy) / 16.0
    b = (xx - yy) / 16.0
    ia, ib = np.floor(a), np.floor(b)
    arriba = ((ia + ib) % 2) == 0
    fa, fb = a - ia, b - ib
    tira = np.where(arriba, np.sin(fa * math.pi), np.sin(fb * math.pi)) ** 0.6
    base = mezclar(hex2rgb("#9C7A3C"), hex2rgb("#E3C77F"), tira)
    fibras = np.where(arriba, np.sin(b * 22) * 0.5 + 0.5, np.sin(a * 22) * 0.5 + 0.5)
    base *= (0.9 + 0.1 * fibras)[..., None]
    guardar(base, "petate.png")


def tex_letrero():
    w, h = 512, 128
    img, d = lienzo(w, h, hex2rgb("#F3EEE2") + (255,))
    S = SS
    d.rectangle([4 * S, 4 * S, (w - 4) * S, (h - 4) * S], outline=hex2rgb("#7A1F1F"), width=5 * S)
    f = fuente(56 * S)
    texto = "PANTEÓN"
    bb = d.textbbox((0, 0), texto, font=f)
    d.text(((w * S - (bb[2] - bb[0])) / 2, (h * S - (bb[3] - bb[1])) / 2 - bb[1]), texto,
           fill=hex2rgb("#3B1F1F"), font=f)
    for sx in (40, w - 40):
        flor_petalos(d, sx * S, h * S / 2, 22 * S, 8, hex2rgb("#F76707"), hex2rgb("#FAB005"))
    out = reducir(img, w, h).convert("RGB")
    arr = np.asarray(out, np.float32) * (0.93 + 0.1 * ruido(w, h, 16, 60, 3))[..., None]
    guardar(arr, "letrero_panteon.png")


def tex_cera():
    """Cera de vela con escurrimientos (v=1 arriba)."""
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rng = np.random.default_rng(70)
    largo = np.zeros(w, np.float32)
    for _ in range(9):
        c = rng.uniform(0, w)
        l = rng.uniform(0.15, 0.55) * h
        ancho = rng.uniform(3, 8)
        dx = np.minimum(np.abs(np.arange(w) - c), w - np.abs(np.arange(w) - c))
        largo = np.maximum(largo, l * np.exp(-(dx / ancho) ** 2))
    gota = (yy < (largo[None, :] + 4)).astype(np.float32)
    base = mezclar(hex2rgb("#EFE6CF"), hex2rgb("#FFF8E7"), gota * 0.8 + 0.2 * ruido(w, h, 8, 71, 2))
    guardar(base, "cera.png")


def tex_alfombra():
    """Alfombra de pétalos (RGBA): u = ancho del camino (más denso al centro), v = largo (repetible).

    Se aplica sobre una franja de 2 triángulos por tramo; los pétalos 3D
    instanciados aportan el relieve cercano.
    """
    w = h = 512
    img, d = lienzo(w, h)
    S = SS
    rng = np.random.default_rng(15)
    colores = [hex2rgb(c) for c in ("#F76707", "#FF922B", "#FD7E14", "#FFA94D", "#E8590C", "#FAB005", "#FFC078")]
    for _ in range(2600):
        u = 0.5 + rng.normal(0.0, 0.17)
        if not 0.04 < u < 0.96:
            continue
        v = rng.uniform(0.0, 1.0)
        L = rng.uniform(9, 16) * S
        a = rng.uniform(0, math.pi)
        col = colores[rng.integers(len(colores))] if rng.random() > 0.05 else hex2rgb("#C2185B")
        sombra = tuple(int(c * 0.72) for c in col)
        for dv in (-1, 0, 1):  # se repite arriba/abajo para que sea continuo en v
            cx, cy = u * w * S, (v + dv) * h * S
            pts = []
            for k in range(10):
                t = 2 * math.pi * k / 10
                ex, ey = math.cos(t) * L * 0.5, math.sin(t) * L * 0.32 * (1.1 if math.cos(t) > 0 else 0.8)
                pts.append((cx + ex * math.cos(a) - ey * math.sin(a), cy + ex * math.sin(a) + ey * math.cos(a)))
            d.polygon([(x + S * 1.5, y + S * 1.5) for x, y in pts], fill=sombra + (255,))
            d.polygon(pts, fill=col + (255,))
    out = reducir(img, w, h)
    guardar(out, "alfombra_petalos.png")


def main():
    os.makedirs(SALIDA, exist_ok=True)
    print("Generando texturas propias en", SALIDA)
    tex_petalo()
    tex_papel_picado()
    tex_calaverita()
    tex_pan_de_muerto()
    tex_mariposa()
    tex_veladora()
    tex_mantel()
    tex_barro()
    tex_talavera()
    tex_foto()
    tex_hojalata()
    tex_vidrio()
    tex_petate()
    tex_letrero()
    tex_cera()
    tex_alfombra()


if __name__ == "__main__":
    main()
