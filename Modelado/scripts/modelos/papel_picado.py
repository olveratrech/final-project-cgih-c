"""Tira de papel picado: cordel en catenaria con 8 banderitas.

Jerarquía:  papel_picado (cordel)
              ├── bandera_1 ... bandera_8   (pivote en el cordel para animar el viento)

Todas las banderitas comparten UNA textura en blanco con el calado
(alpha MASK); el color de cada una es el factor del material.
"""
import math

from mathutils import Vector

import mx

NOMBRE = "papel_picado"
VISTA = {"azimut": -12, "elevacion": 8}
CLARO = 3.0       # distancia entre los dos puntos de amarre (m)
FLECHA = 0.18     # caída del cordel al centro (m)
N = 8
COLORES = [("rosa", "#E4007C"), ("naranja", "#FF7F00"), ("morado", "#7B2CBF"),
           ("verde", "#2B9348"), ("amarillo", "#FFC300"), ("azul", "#1E6FD9")]


def altura(x):
    """Cordel parabólico (aproximación de catenaria) con extremos en z=0."""
    return -FLECHA * (1 - (2 * x / CLARO) ** 2)


def construir():
    cordel = mx.material("cordel", color=mx.hex2lin("#D8C9A3"), rugosidad=0.9)
    papeles = [mx.material("papel_" + n, textura="papel_picado.png", tinte=mx.hex2lin(c), rugosidad=0.9,
                           recorte=True, doble_cara=True) for n, c in COLORES]

    bm, uv = mx.nuevo_bm()
    xs = [-CLARO / 2 + CLARO * i / 16 for i in range(17)]
    mx.tubo(bm, uv, [(x, 0, altura(x)) for x in xs], 0.003, lados=4, mat=0, v_escala=0.05)
    raiz = mx.objeto(NOMBRE, bm, [cordel])

    ancho, alto = 0.28, 0.34
    for k in range(N):
        x = -CLARO / 2 + CLARO * (k + 0.5) / N
        celda = k % 4
        u0, v0 = (celda % 2) * 0.5, 0.5 - (celda // 2) * 0.5
        bm, uv = mx.nuevo_bm()
        mx.tarjeta(bm, uv, [(-ancho / 2, 0, -alto), (ancho / 2, 0, -alto), (ancho / 2, 0, 0), (-ancho / 2, 0, 0)],
                   uvs=((u0, v0), (u0 + 0.5, v0), (u0 + 0.5, v0 + 0.5), (u0, v0 + 0.5)), div=(1, 2),
                   deformar=lambda s, t, p: p + Vector((0, -0.012 * math.sin(t * math.pi), 0)))
        mx.plano(bm)
        pendiente = math.atan(-FLECHA * (-8 * x / CLARO ** 2))
        mx.objeto(f"bandera_{k + 1}", bm, [papeles[k % len(papeles)]], padre=raiz,
                  loc=(x, 0, altura(x) - 0.004), rot=(0, pendiente * 0.5, 0))
    return raiz
