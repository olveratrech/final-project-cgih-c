"""
Convierte un HDRI equirectangular (Poly Haven, CC0) en las 6 caras de un
cube map para el skybox del programa.

Cada texel (s, t) de cada cara se llena con el color del entorno en la
dirección que OpenGL usa para esa cara (tabla de selección de caras de la
especificación), así el muestreo con samplerCube devuelve exactamente la
dirección del mundo sin espejos ni giros.

Uso (requiere Python 3 con numpy y Pillow):
    python Modelado/scripts/generar_skybox.py [id_hdri] [exposicion]
"""
import io
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
URL = "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/{0}_2k.hdr"
TAM_CARA = 512
# nombre de archivo -> cara de OpenGL (en el orden GL_TEXTURE_CUBE_MAP_POSITIVE_X + i)
CARAS = ["px", "nx", "py", "ny", "pz", "nz"]


def leer_hdr(datos):
    """Decodifica un archivo Radiance .hdr (RGBE con RLE) a un arreglo float32 HxWx3."""
    f = io.BytesIO(datos)
    while True:
        linea = f.readline().strip()
        if not linea:
            break
    tam = f.readline().split()
    alto, ancho = int(tam[1]), int(tam[3])
    img = np.zeros((alto, ancho, 4), np.uint8)
    buf = f.read()
    pos = 0
    for y in range(alto):
        if buf[pos] != 2 or buf[pos + 1] != 2:
            raise ValueError("Solo se admite el formato RLE moderno")
        pos += 4
        for c in range(4):
            x = 0
            fila = img[y, :, c]
            while x < ancho:
                n = buf[pos]
                pos += 1
                if n > 128:
                    n -= 128
                    fila[x:x + n] = buf[pos]
                    pos += 1
                else:
                    fila[x:x + n] = np.frombuffer(buf, np.uint8, n, pos)
                    pos += n
                x += n
    e = img[..., 3].astype(np.int32)
    escala = np.where(e > 0, np.ldexp(1.0, e - 136), 0.0).astype(np.float32)
    return img[..., :3].astype(np.float32) * escala[..., None]


def direcciones(cara, n):
    """Direcciones del mundo para cada texel de una cara (convención de OpenGL)."""
    c = (np.arange(n, dtype=np.float32) + 0.5) / n * 2 - 1
    sc, tc = np.meshgrid(c, c)          # sc varía en columnas (s), tc en filas (t)
    uno = np.ones_like(sc)
    r = {
        "px": (uno, -tc, -sc),
        "nx": (-uno, -tc, sc),
        "py": (sc, uno, tc),
        "ny": (sc, -uno, -tc),
        "pz": (sc, -tc, uno),
        "nz": (-sc, -tc, -uno),
    }[cara]
    d = np.stack(r, -1)
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


def muestrear(eq, d):
    """Muestreo bilineal del panorama equirectangular en las direcciones d."""
    alto, ancho, _ = eq.shape
    u = 0.5 + np.arctan2(d[..., 0], -d[..., 2]) / (2 * np.pi)
    v = np.arccos(np.clip(d[..., 1], -1, 1)) / np.pi
    x = u * ancho - 0.5
    y = v * alto - 0.5
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    x0m, x1m = x0 % ancho, (x0 + 1) % ancho
    y0c, y1c = np.clip(y0, 0, alto - 1), np.clip(y0 + 1, 0, alto - 1)
    a = eq[y0c, x0m] * (1 - fx) + eq[y0c, x1m] * fx
    b = eq[y1c, x0m] * (1 - fx) + eq[y1c, x1m] * fx
    return a * (1 - fy) + b * fy


def main(hdri="qwantani_dusk_2_puresky", exposicion=1.0, cache=None):
    if cache and os.path.exists(cache):
        datos = open(cache, "rb").read()
    else:
        with urllib.request.urlopen(URL.format(hdri)) as r:
            datos = r.read()
    eq = leer_hdr(datos)
    salida = os.path.join(RAIZ, "assets", "skybox", hdri.replace("_puresky", ""))
    os.makedirs(salida, exist_ok=True)
    for cara in CARAS:
        col = muestrear(eq, direcciones(cara, TAM_CARA)) * exposicion
        col = 1.0 - np.exp(-col)                         # mapeo de tonos exponencial
        col = np.power(np.clip(col, 0, 1), 1 / 2.2)       # corrección gamma (sRGB aprox.)
        img = Image.fromarray((col * 255 + 0.5).astype(np.uint8))
        ruta = os.path.join(salida, cara + ".jpg")
        img.save(ruta, quality=88, optimize=True)
        print(f"  {cara}.jpg {os.path.getsize(ruta) / 1024:6.1f} KB")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0] if args else "qwantani_dusk_2_puresky", float(args[1]) if len(args) > 1 else 1.0,
         args[2] if len(args) > 2 else None)
