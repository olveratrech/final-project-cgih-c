"""Maceta de barro con un ramo de cempasúchil.

Jerarquía:  maceta_cempasuchil (maceta + tierra)
              └── flores (7 flores combinadas en una sola malla: 2 materiales, 2 llamadas de dibujo)
"""
import math
import random

from mathutils import Matrix, Vector

import mx

NOMBRE = "maceta_cempasuchil"
VISTA = {"azimut": -30, "elevacion": 20}
TIERRA = 0.185


def construir():
    barro = mx.material("barro", textura="barro.png", rugosidad=0.85)
    tierra = mx.material("tierra_maceta", color=mx.hex2lin("#3B2A1E"), rugosidad=1.0)
    petalo = mx.material("cempasuchil_petalo", textura="petalo_cempasuchil.png", rugosidad=0.65, doble_cara=True)
    verde = mx.material("cempasuchil_verde", color=mx.hex2lin("#3F7A24"), rugosidad=0.7, doble_cara=True)

    bm, uv = mx.nuevo_bm()
    perfil = [(0.0, 0.0), (0.085, 0.0), (0.090, 0.006), (0.118, 0.180), (0.134, 0.188), (0.136, 0.212),
              (0.120, 0.214), (0.112, 0.196), (0.108, TIERRA)]
    mx.torno(bm, uv, perfil, 12, mat=0, v_rango=(0.0, 1.0))
    mx.torno(bm, uv, [(0.108, TIERRA), (0.0, TIERRA + 0.008)], 12, mat=1)
    mx.suavizar(bm, 40)
    raiz = mx.objeto(NOMBRE, bm, [barro, tierra])

    bm, uv = mx.nuevo_bm()
    rnd = random.Random(12)
    posiciones = [(0.0, 0.0)] + [(0.055 * math.cos(a), 0.055 * math.sin(a))
                                 for a in (0.3, 1.2, 2.2, 3.1, 4.1, 5.2)]
    for i, (x, y) in enumerate(posiciones):
        alto = rnd.uniform(0.17, 0.26) if i else 0.28
        incl = Vector((x, y, 0)) * 0.9
        cima = Vector((x, y, 0)) + incl + Vector((0, 0, alto))
        base = Vector((x * 0.6, y * 0.6, TIERRA))
        pts = [base + (cima - base) * t for t in (0.0, 0.5, 1.0)]
        mx.tubo(bm, uv, pts, 0.0035, lados=4, mat=1, tapas=False)
        M = Matrix.Translation(cima) @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ \
            Matrix.Rotation(math.atan2(incl.length, 0.25), 4, Vector((-y, x, 0)).normalized() if i else "Z")
        mx.flor_cempasuchil(bm, uv, M=M, radio=rnd.uniform(0.038, 0.048), mat_petalo=0, semilla=20 + i,
                            anillos=mx.ANILLOS_FLOR_LIGERA)
    mx.suavizar(bm, 70)
    mx.objeto("flores", bm, [petalo, verde], padre=raiz)
    return raiz
