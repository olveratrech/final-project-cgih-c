"""
Figuras de diseño para la documentación:
  * docs/img/diseno/plano_escena.jpg      - vista aérea del programa con anotaciones
  * docs/img/diseno/boceto_interfaz.png   - boceto (wireframe) de la interfaz en ambos modos

Requiere Pillow y numpy; usa docs/img/escena/vista_7.jpg (tools/capturar_figuras.sh).
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SALIDA = os.path.join(RAIZ, "docs", "img", "diseno")


def fuente(tam, negrita=True):
    nombres = ["LiberationSans-Bold.ttf" if negrita else "LiberationSans-Regular.ttf"]
    for base in ("/usr/share/fonts/truetype/liberation/", os.path.join(RAIZ, "assets", "fuentes") + "/"):
        for n in nombres + ["LiberationSans-Regular.ttf"]:
            if os.path.exists(base + n):
                return ImageFont.truetype(base + n, tam)
    for c in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(c):
            return ImageFont.truetype(c, tam)
    return ImageFont.load_default()


def proyectar(p, ojo, objetivo, fov, aspecto, w, h):
    """Misma cámara que el programa: glm::lookAt + glm::perspective."""
    f = np.array(objetivo, float) - ojo
    f /= np.linalg.norm(f)
    s = np.cross(f, [0, 1, 0])
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
    v = np.array(p, float) - ojo
    x, y, z = v @ s, v @ u, -(v @ f)
    t = np.tan(np.radians(fov) / 2)
    nx, ny = x / (-z * t * aspecto), y / (-z * t)
    return (nx * 0.5 + 0.5) * w, (1 - (ny * 0.5 + 0.5)) * h


def plano():
    img = Image.open(os.path.join(RAIZ, "docs", "img", "escena", "vista_7.jpg")).convert("RGB")
    w, h = img.size
    d = ImageDraw.Draw(img, "RGBA")
    ojo, obj = np.array([0.0, 60.0, 21.0]), [0.0, 0.0, 6.0]
    etiquetas = [
        ((0, 0, -17.5), "Casa de adobe con portal", (0, -70)),
        ((0, 0.2, -15.0), "Ofrenda: altar, arco y ofrendas", (250, -10)),
        ((0.6, 0, -8.5), "Camino de cempasúchil (spline Catmull-Rom)", (150, 0)),
        ((-1.4, 2.5, 4.0), "Faroles + papel picado", (-260, -10)),
        ((-1.5, 0, 10.0), "Calaca y ánima en el camino", (-260, 30)),
        ((0, 0, 16.0), "Portada del panteón", (260, 0)),
        ((-7.5, 0, 23.6), "Tumbas con flores y veladoras", (-270, 10)),
        ((9.0, 0, 31.0), "Criptas y cruz atrial", (200, -20)),
        ((-14.5, 0, -6.0), "Casas vecinas (instancias)", (-120, -60)),
    ]
    f = fuente(20)
    for p, texto, (dx, dy) in etiquetas:
        x, y = proyectar(p, ojo, obj, 60.0, 16 / 9, w, h)
        tx, ty = x + dx, y + dy
        tw = d.textlength(texto, font=f)
        bx0 = tx - tw / 2 - 8 if dx == 0 else (tx if dx > 0 else tx - tw - 16)
        bx0 = min(max(bx0, 6), w - tw - 22)       # la etiqueta no sale de la imagen
        ty = min(max(ty, 20), h - 20)
        caja = [bx0, ty - 15, bx0 + tw + 16, ty + 15]
        d.line([(x, y), ((caja[0] + caja[2]) / 2 if dx == 0 else (caja[0] if dx > 0 else caja[2]), ty)],
               fill=(255, 245, 230, 230), width=2)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(228, 0, 124, 255))
        d.rounded_rectangle(caja, radius=8, fill=(40, 20, 45, 215))
        d.text((caja[0] + 8, ty - 12), texto, font=f, fill=(255, 190, 90))
    # rosa de los vientos
    cx, cy = w - 70, 80
    d.polygon([(cx, cy - 40), (cx - 12, cy), (cx + 12, cy)], fill=(228, 0, 124, 255))
    d.polygon([(cx, cy + 40), (cx - 12, cy), (cx + 12, cy)], fill=(240, 240, 240, 255))
    d.text((cx - 7, cy - 68), "N", font=fuente(22), fill=(255, 255, 255))
    os.makedirs(SALIDA, exist_ok=True)
    img.save(os.path.join(SALIDA, "plano_escena.jpg"), quality=90, optimize=True)


def boceto():
    W, H = 1600, 560
    img = Image.new("RGB", (W, H), (245, 242, 236))
    d = ImageDraw.Draw(img)
    f, fs, ft = fuente(17), fuente(14, False), fuente(22)

    def pantalla(x0, titulo, paneles, centro, textos):
        x1, y0, y1 = x0 + 760, 50, 520
        d.text((x0, 12), titulo, font=ft, fill=(90, 20, 80))
        d.rectangle([x0, y0, x1, y1], outline=(60, 60, 60), width=3, fill=(214, 226, 236))
        for i, t in enumerate(textos):
            tw = d.textlength(t, font=f)
            d.text((x0 + centro - tw / 2, y0 + 360 + i * 24), t, font=f, fill=(90, 100, 110))
        for (a, b, c, e), nombre, lineas in paneles:
            caja = [x0 + a, y0 + b, x0 + c, y0 + e]
            d.rectangle(caja, fill=(70, 28, 78), outline=(30, 10, 35), width=2)
            d.rectangle([caja[0], caja[1], caja[2], caja[1] + 24], fill=(150, 30, 110))
            d.text((caja[0] + 8, caja[1] + 3), nombre, font=f, fill=(255, 255, 255))
            for i, l in enumerate(lineas):
                d.text((caja[0] + 10, caja[1] + 32 + i * 20), l, font=fs, fill=(255, 200, 120))

    pantalla(20, "Modo escena", [
        ((10, 10, 260, 330), "Panel principal",
         ["FPS, llamadas, triángulos", "Modo: escena / galería", "Vistas de cámara 1-7", "Velocidad de la cámara",
          "Visualización (alambre,", "  skybox, niebla, frustum)", "Ayuda · Captura · Ocultar"]),
        ((470, 10, 750, 220), "Transformaciones",
         ["Nodo seleccionado", "Traslación / Rotación / Escala", "Matriz local 4x4", "Matriz de mundo 4x4",
          "Restablecer · Padre · Enfocar"]),
        ((470, 230, 750, 460), "Jerarquía de la escena",
         ["Escena", "  Casa > Ofrenda > altar", "    nivel_1 > nivel_2 > nivel_3", "  Camino de cempasúchil",
          "  Panteón > Tumbas ...", "Colores: propio / librería /", "  procedural / grupo"]),
    ], 365, ["Vista 3D", "(OpenGL 3.3)", "clic: seleccionar"])
    pantalla(820, "Modo galería de modelos", [
        ((10, 10, 260, 150), "Panel principal", ["FPS y estadísticas", "Modo: escena / galería", "Visualización"]),
        ((420, 10, 750, 460), "Galería de modelos",
         ["Título, origen y descripción", "Triángulos, vértices, nodos", "Materiales y texturas",
          "Usos en la escena", "Jerarquía del modelo (árbol)", "Lista: 18 propios,", "  25 de librería, 3 procedurales",
          "Flechas: cambiar · Espacio: girar"]),
    ], 340, ["Vista 3D:", "modelo sobre", "pedestal giratorio"])
    img.save(os.path.join(SALIDA, "boceto_interfaz.png"), optimize=True)


if __name__ == "__main__":
    plano()
    boceto()
    print("Diagramas en", SALIDA)
