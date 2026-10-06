"""Pétalo suelto de cempasúchil.

Es la pieza base del camino de flores: el programa lo dibuja miles de veces
con instanciado por GPU (una sola llamada de dibujo), por eso tiene solo
8 triángulos. Se apoya acostado sobre el plano XY con el origen al centro.
"""
from mathutils import Vector

import mx

NOMBRE = "petalo_cempasuchil"
VISTA = {"azimut": -30, "elevacion": 45}


def construir():
    petalo = mx.material("cempasuchil_petalo", textura="petalo_cempasuchil.png", rugosidad=0.65, doble_cara=True)
    bm, uv = mx.nuevo_bm()
    largo, ancho = 0.032, 0.024

    def rizo(s, t, p):
        # bordes levantados (copa) y punta curvada hacia arriba
        return p + Vector((0, 0, (abs(s - 0.5) * 2) ** 2 * 0.004 + t * t * 0.004))

    mx.tarjeta(bm, uv, [(-ancho * 0.25, -largo / 2, 0), (ancho * 0.25, -largo / 2, 0),
                        (ancho / 2, largo / 2, 0), (-ancho / 2, largo / 2, 0)],
               mat=0, div=(2, 2), deformar=rizo)
    mx.suavizar(bm, 80)
    return mx.objeto(NOMBRE, bm, [petalo])
