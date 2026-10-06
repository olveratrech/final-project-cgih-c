"""Sahumerio (popoxcomitl) de barro con brasas y copal.

Jerarquía:  sahumerio (cuerpo torneado + mango)
              └── brasas (brasas emisivas y trozos de copal; origen del humo)
"""
import math
import random

from mathutils import Matrix

import mx

NOMBRE = "sahumerio"
VISTA = {"azimut": -40, "elevacion": 30}
FONDO = 0.112


def construir():
    barro = mx.material("barro", textura="barro.png", rugosidad=0.85)
    brasa = mx.material("brasa", color=mx.hex2lin("#C2410C"), emision=mx.hex2lin("#FF5A1F"), fuerza=2.5, rugosidad=0.9)
    copal = mx.material("copal", color=mx.hex2lin("#F2E3A0"), rugosidad=0.4)

    bm, uv = mx.nuevo_bm()
    exterior = [(0.0, 0.0), (0.055, 0.0), (0.058, 0.008), (0.040, 0.020), (0.022, 0.040), (0.020, 0.068),
                (0.034, 0.084), (0.068, 0.104), (0.084, 0.128), (0.083, 0.140)]
    interior = [(0.083, 0.140), (0.072, 0.140), (0.060, 0.120), (0.0, FONDO)]
    mx.torno(bm, uv, exterior, 12, mat=0, v_rango=(0.1, 0.62))
    mx.torno(bm, uv, interior, 12, mat=0, v_rango=(0.62, 0.7))
    # mango largo y ligeramente inclinado (como los popoxcomitl prehispánicos)
    mx.tubo(bm, uv, [(0.066, 0, 0.112), (0.13, 0, 0.122), (0.20, 0, 0.134)], [0.013, 0.011, 0.009],
            lados=6, mat=0, v_escala=0.2)
    mx.suavizar(bm, 45)
    raiz = mx.objeto(NOMBRE, bm, [barro])

    bm, uv = mx.nuevo_bm()
    rnd = random.Random(4)
    for i in range(7):
        r = rnd.uniform(0.0, 0.045)
        a = rnd.uniform(0, 6.283)
        M = Matrix.Translation((r * math.cos(a), r * math.sin(a), 0.0)) @ Matrix.Rotation(a, 4, "Z")
        mx.pompon(bm, uv, M=M, radio=rnd.uniform(0.010, 0.015), mat=0 if i < 4 else 1, semilla=i, seg=5, anillos=3)
    mx.plano(bm)
    mx.objeto("brasas", bm, [brasa, copal], padre=raiz, loc=(0, 0, FONDO - 0.004))
    return raiz
