"""Portarretrato de hojalata repujada con la fotografía del difunto.

Jerarquía:  portarretrato (vacío en la base)
              ├── marco   (marco + respaldo, inclinado 12°)
              │     └── foto
              └── pata    (soporte trasero)
"""
import math

import mx

NOMBRE = "portarretrato"
VISTA = {"azimut": -30, "elevacion": 12}
ANCHO, ALTO, BORDE, GROSOR = 0.20, 0.26, 0.026, 0.018
INCLINACION = math.radians(12)


def construir():
    marco = mx.material("hojalata_dorada", textura="hojalata.png", tinte=mx.hex2lin("#E0B04A"), rugosidad=0.35,
                        metalico=0.8)
    carton = mx.material("carton", color=mx.hex2lin("#6B4F35"), rugosidad=0.95)
    foto = mx.material("foto", textura="foto_retrato.png", rugosidad=0.4)

    raiz = mx.vacio(NOMBRE)
    bm, uv = mx.nuevo_bm()
    w, h, b, g = ANCHO / 2, ALTO, BORDE, GROSOR
    s = 0.12  # escala UV de la hojalata
    mx.caja(bm, uv, (-w, 0, 0), (w, g, b), mat=0, escala_uv=s)                 # travesaño inferior
    mx.caja(bm, uv, (-w, 0, h - b), (w, g, h), mat=0, escala_uv=s)             # travesaño superior
    mx.caja(bm, uv, (-w, 0, b), (-w + b, g, h - b), mat=0, escala_uv=s, quitar=("-z", "+z"))
    mx.caja(bm, uv, (w - b, 0, b), (w, g, h - b), mat=0, escala_uv=s, quitar=("-z", "+z"))
    mx.caja(bm, uv, (-w + b, g * 0.6, b), (w - b, g * 0.6 + 0.002, h - b), mat=1, quitar=("-z", "+z", "-x", "+x"))
    mx.plano(bm)
    ob_marco = mx.objeto("marco", bm, [marco, carton], padre=raiz, rot=(-INCLINACION, 0, 0))

    # foto: proporción vertical recortada al centro de la textura cuadrada
    bm, uv = mx.nuevo_bm()
    fw = w - b
    prop = (2 * fw) / (h - 2 * b)
    mx.tarjeta(bm, uv, [(-fw, g * 0.55, b), (fw, g * 0.55, b), (fw, g * 0.55, h - b), (-fw, g * 0.55, h - b)],
               uvs=((0.5 - prop / 2, 0), (0.5 + prop / 2, 0), (0.5 + prop / 2, 1), (0.5 - prop / 2, 1)))
    mx.plano(bm)
    mx.objeto("foto", bm, [foto], padre=ob_marco)

    # pata trasera
    bm, uv = mx.nuevo_bm()
    largo = 0.20
    mx.caja(bm, uv, (-0.02, 0, 0), (0.02, 0.006, largo), mat=0)
    mx.plano(bm)
    mx.objeto("pata", bm, [carton], padre=raiz, loc=(0, 0.13, 0.0), rot=(math.radians(28), 0, 0))
    return raiz
