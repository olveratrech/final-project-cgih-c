"""Portada del panteón: pilastras, arco de medio punto, ático con letrero, cruz y reja de dos hojas.

Jerarquía:  entrada_panteon (mampostería encalada, letrero y cruz)
              ├── reja_izquierda  (pivote en la bisagra para abrirla con el teclado)
              └── reja_derecha
"""
import math

from mathutils import Matrix

import mx

NOMBRE = "entrada_panteon"
VISTA = {"azimut": -30, "elevacion": 12, "sombra": False}  # la sombra se vería negra a través del arco
CLARO = 3.0          # ancho libre del vano
ARRANQUE = 2.3       # altura donde inicia el arco
ALTO_MURO = 4.2
PILASTRA = 0.7
FONDO = 0.7


def reja(lado, hierro):
    """Hoja de reja: barrotes con punta de lanza, travesaños y largueros."""
    bm, uv = mx.nuevo_bm()
    s = 1 if lado > 0 else -1          # la hoja crece hacia +x (izquierda) o -x (derecha)
    ancho = CLARO / 2 - 0.01
    alto = ARRANQUE - 0.12
    g = 0.012
    for k in range(10):
        x = s * (0.08 + k * (ancho - 0.12) / 9)
        mx.caja(bm, uv, (x - g, -g, 0.05), (x + g, g, alto - 0.12), mat=0, quitar=("-z", "+z"))
        punta = [bm.verts.new(p) for p in ((x - g * 1.8, -g * 1.8, alto - 0.12), (x + g * 1.8, -g * 1.8, alto - 0.12),
                                            (x + g * 1.8, g * 1.8, alto - 0.12), (x - g * 1.8, g * 1.8, alto - 0.12))]
        apice = bm.verts.new((x, 0, alto))
        for i in range(4):
            mx._cara(bm, [punta[i], punta[(i + 1) % 4], apice], [(0, 0), (1, 0), (0.5, 1)], uv, 0)
    for z in (0.12, 1.0, alto - 0.30):
        x0, x1 = sorted((0.0, s * ancho))
        mx.caja(bm, uv, (x0, -0.02, z), (x1, 0.02, z + 0.05), mat=0)
    for x in (0.0, s * (ancho - 0.04)):
        x0, x1 = sorted((x, x + 0.04))
        mx.caja(bm, uv, (x0, -0.022, 0.03), (x1, 0.022, alto - 0.25), mat=0)
    mx.plano(bm)
    return bm


def construir():
    cal = mx.material("cal", textura="cal.jpg", rugosidad=0.95)
    rojo = mx.material("aplanado_rojo", textura="aplanado_rojo.jpg", rugosidad=0.9)
    letrero = mx.material("letrero_panteon", textura="letrero_panteon.png", rugosidad=0.8)
    hierro = mx.material("hierro", color=mx.hex2lin("#232326"), rugosidad=0.45, metalico=0.75)

    bm, uv = mx.nuevo_bm()
    xi = CLARO / 2
    xe = xi + PILASTRA
    y0, y1 = -FONDO / 2, FONDO / 2
    for s in (-1, 1):
        a, b = sorted((s * xi, s * xe))
        # zócalo rojo, fuste encalado, capitel y remate
        mx.caja(bm, uv, (a - 0.05, y0 - 0.05, 0), (b + 0.05, y1 + 0.05, 0.6), mat=1, quitar=("-z",))
        mx.caja(bm, uv, (a, y0, 0.6), (b, y1, ALTO_MURO), mat=0, quitar=("-z", "+z"))
        mx.torno(bm, uv, [(0.0, 0.0), (0.22, 0.0), (0.22, 0.06), (0.12, 0.16), (0.10, 0.34), (0.16, 0.42),
                          (0.0, 0.50)], 4, M=Matrix.Translation(((a + b) / 2, 0, ALTO_MURO + 0.15)) @
                 Matrix.Rotation(math.pi / 4, 4, "Z"), mat=0, v_rango=(0, 0.5))
    # muro con arco de medio punto (contorno cóncavo extruido)
    contorno = [(-xi, ARRANQUE), (-xi, ALTO_MURO), (xi, ALTO_MURO), (xi, ARRANQUE)]
    for i in range(1, 16):
        t = math.pi * i / 16
        contorno.append((xi * math.cos(t), ARRANQUE + xi * math.sin(t)))
    mx.poligono_extruido(bm, uv, contorno, y0, y1, mat_frente=0, mat_lados=0, escala_uv=1.5)
    # cornisa corrida y ático
    mx.caja(bm, uv, (-xe - 0.12, y0 - 0.12, ALTO_MURO), (xe + 0.12, y1 + 0.12, ALTO_MURO + 0.15), mat=0)
    mx.caja(bm, uv, (-1.3, -0.2, ALTO_MURO + 0.15), (1.3, 0.2, ALTO_MURO + 0.85), mat=0, quitar=("-z",))
    mx.caja(bm, uv, (-1.38, -0.26, ALTO_MURO + 0.85), (1.38, 0.26, ALTO_MURO + 0.93), mat=0)
    # letrero en el frente del ático (proporción 4:1 igual que la textura)
    mx.tarjeta(bm, uv, [(-1.1, -0.205, ALTO_MURO + 0.22), (1.1, -0.205, ALTO_MURO + 0.22),
                        (1.1, -0.205, ALTO_MURO + 0.77), (-1.1, -0.205, ALTO_MURO + 0.77)], mat=2)
    # cruz de hierro sobre el ático
    zc = ALTO_MURO + 0.93
    mx.caja(bm, uv, (-0.04, -0.04, zc), (0.04, 0.04, zc + 0.75), mat=3, quitar=("-z",))
    mx.caja(bm, uv, (-0.26, -0.04, zc + 0.42), (0.26, 0.04, zc + 0.50), mat=3)
    mx.plano(bm)
    raiz = mx.objeto(NOMBRE, bm, [cal, rojo, letrero, hierro])

    mx.objeto("reja_izquierda", reja(1, hierro), [hierro], padre=raiz, loc=(-xi, 0, 0))
    mx.objeto("reja_derecha", reja(-1, hierro), [hierro], padre=raiz, loc=(xi, 0, 0))
    return raiz
