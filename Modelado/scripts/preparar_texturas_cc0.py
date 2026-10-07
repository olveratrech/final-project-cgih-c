"""
Descarga y optimiza las texturas de dominio público (CC0) de Poly Haven
que se usan en superficies grandes (suelo, empedrado, muros, tejas, madera).

Cada textura se reduce a 512x512 y se guarda como JPEG (calidad 85) para
reducir el tamaño en disco y el consumo de memoria de video; al ser
texturas repetibles (tileables) se aplican con GL_REPEAT y mipmaps.

Uso (requiere Python 3 con Pillow):
    python Modelado/scripts/preparar_texturas_cc0.py
"""
import io
import os
import urllib.request

from PIL import Image

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SALIDA = os.path.join(RAIZ, "assets", "textures")
URL = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/{0}/{0}_diff_1k.jpg"
TAM = 512

# id en Poly Haven -> nombre de archivo en el proyecto
TEXTURAS = {
    "wood_table_worn": "madera_oscura.jpg",
    "brown_planks_09": "madera_clara.jpg",
    "cobblestone_large_01": "empedrado.jpg",
    "red_dirt_mud_01": "tierra.jpg",
    "clay_plaster": "adobe.jpg",
    "white_stucco": "cal.jpg",
    "clay_roof_tiles_02": "tejas.jpg",
    "red_plaster_weathered": "aplanado_rojo.jpg",
}


def main(cache=None):
    os.makedirs(SALIDA, exist_ok=True)
    for pid, nombre in TEXTURAS.items():
        local = os.path.join(cache, pid + ".jpg") if cache else None
        if local and os.path.exists(local):
            datos = open(local, "rb").read()
        else:
            with urllib.request.urlopen(URL.format(pid)) as r:
                datos = r.read()
        img = Image.open(io.BytesIO(datos)).convert("RGB").resize((TAM, TAM), Image.LANCZOS)
        ruta = os.path.join(SALIDA, nombre)
        img.save(ruta, quality=85, optimize=True)
        print(f"  {pid:24s} -> {nombre:20s} {os.path.getsize(ruta) / 1024:6.1f} KB")


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
