"""
Prepara las figuras de los modelos para la documentación.

  * Compone cada render de Blender (Modelado/render/*.png, fondo
    transparente) junto a su versión de malla de alambre, en JPEG con fondo
    neutro (docs/img/modelos/<modelo>_par.jpg).
  * Arma el catálogo de modelos propios.

Uso (después de construir_modelos.py; requiere Pillow):
    python Modelado/scripts/preparar_figuras.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RENDER = os.path.join(RAIZ, "Modelado", "render")
SALIDA = os.path.join(RAIZ, "docs", "img", "modelos")

TITULOS = {
    "altar_muertos": "Altar de muertos",
    "arco_cempasuchil": "Arco de cempasúchil",
    "flor_cempasuchil": "Flor de cempasúchil",
    "petalo_cempasuchil": "Pétalo de cempasúchil",
    "veladora": "Veladora",
    "cirio": "Cirio con candelero",
    "pan_de_muerto": "Pan de muerto",
    "calaverita_azucar": "Calaverita de azúcar",
    "papel_picado": "Papel picado",
    "sahumerio": "Sahumerio",
    "portarretrato": "Portarretrato",
    "jarron_talavera": "Jarrón de Talavera",
    "vaso_agua": "Vaso con agua",
    "maceta_cempasuchil": "Maceta con cempasúchil",
    "mariposa_monarca": "Mariposa monarca",
    "farol": "Farol de hojalata",
    "entrada_panteon": "Portada del panteón",
    "casa_adobe": "Casa de adobe",
}
FONDO = (58, 52, 64)


def fuente(tam):
    for c in ("C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(c):
            return ImageFont.truetype(c, tam)
    return ImageFont.load_default()


def componer(ruta, tam=512):
    img = Image.open(ruta).convert("RGBA")
    fondo = Image.new("RGBA", img.size, FONDO + (255,))
    # degradado vertical suave
    d = ImageDraw.Draw(fondo)
    for y in range(img.size[1]):
        k = y / img.size[1]
        c = tuple(int(FONDO[i] * (1.15 - 0.35 * k)) for i in range(3))
        d.line([(0, y), (img.size[0], y)], fill=c + (255,))
    fondo.alpha_composite(img)
    return fondo.convert("RGB").resize((tam, tam), Image.LANCZOS)


def main():
    os.makedirs(SALIDA, exist_ok=True)
    # catálogo: 6 columnas x 3 filas, cada celda con render y título
    claves = list(TITULOS)
    celda, alto_txt, cols = 256, 30, 6
    filas = (len(claves) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * celda, filas * (celda + alto_txt)), FONDO)
    d = ImageDraw.Draw(hoja)
    f = fuente(17)
    for i, clave in enumerate(claves):
        ruta = os.path.join(RENDER, clave + ".png")
        if not os.path.exists(ruta):
            continue
        x, y = (i % cols) * celda, (i // cols) * (celda + alto_txt)
        hoja.paste(componer(ruta, celda), (x, y))
        t = f"{i + 1}. {TITULOS[clave]}"
        w = d.textlength(t, font=f)
        d.text((x + (celda - w) / 2, y + celda + 5), t, fill=(250, 235, 215), font=f)
    hoja.save(os.path.join(SALIDA, "catalogo_modelos_propios.jpg"), quality=90, optimize=True)

    # comparativa textura / malla de alambre para cada modelo
    for clave in claves:
        a, b = (os.path.join(RENDER, clave + s + ".png") for s in ("", "_malla"))
        if os.path.exists(a) and os.path.exists(b):
            par = Image.new("RGB", (1024, 512))
            par.paste(componer(a), (0, 0))
            par.paste(componer(b), (512, 0))
            par.save(os.path.join(SALIDA, clave + "_par.jpg"), quality=88, optimize=True)
    print("Figuras en", SALIDA)


if __name__ == "__main__":
    main()
