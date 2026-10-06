"""Veladora: vaso de vidrio pintado con cera y flama.

Jerarquía:  veladora (vaso)
              ├── cera   (superficie de cera + mecha)
              └── llama  (flama emisiva; punto de luz en la entrega de iluminación)
"""
from mathutils import Matrix

import mx

NOMBRE = "veladora"
VISTA = {"azimut": -20, "elevacion": 18}
ALTO = 0.14
NIVEL_CERA = 0.122


def construir():
    vidrio = mx.material("veladora_vidrio", textura="veladora.png", rugosidad=0.25)
    interior = mx.material("veladora_interior", color=mx.hex2lin("#5A0A1E"), rugosidad=0.3)
    cera = mx.material("cera", color=mx.hex2lin("#F3EAD3"), rugosidad=0.6)
    mecha = mx.material("mecha", color=mx.hex2lin("#2B2118"), rugosidad=0.9)
    llama = mx.material("llama", color=mx.hex2lin("#FFC46B"), emision=mx.hex2lin("#FFB347"), fuerza=4.0)

    # vaso: exterior con la textura impresa, borde e interior
    bm, uv = mx.nuevo_bm()
    mx.torno(bm, uv, [(0.0, 0.0), (0.029, 0.0), (0.032, 0.004), (0.033, ALTO)], 12, mat=0)
    mx.torno(bm, uv, [(0.033, ALTO), (0.030, ALTO), (0.030, NIVEL_CERA)], 12, mat=1)
    mx.suavizar(bm, 50)
    raiz = mx.objeto(NOMBRE, bm, [vidrio, interior])

    # cera y mecha
    bm, uv = mx.nuevo_bm()
    mx.torno(bm, uv, [(0.030, NIVEL_CERA), (0.012, NIVEL_CERA - 0.002), (0.0, NIVEL_CERA - 0.003)], 12, mat=0)
    mx.caja(bm, uv, (-0.0012, -0.0012, NIVEL_CERA - 0.003), (0.0012, 0.0012, NIVEL_CERA + 0.008), mat=1, quitar=("-z",))
    mx.suavizar(bm, 40)
    mx.objeto("cera", bm, [cera, mecha], padre=raiz)

    # llama (con su propio origen en la base para animarla después)
    bm, uv = mx.nuevo_bm()
    mx.flama(bm, uv, alto=0.03, radio=0.0075)
    mx.suavizar(bm, 80)
    mx.objeto("llama", bm, [llama], padre=raiz, loc=(0, 0, NIVEL_CERA + 0.006))
    return raiz
