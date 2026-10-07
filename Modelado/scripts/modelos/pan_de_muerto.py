"""Pan de muerto: domo de masa con cuatro "huesitos" en cruz y la "bolita" (cráneo).

Se modela como una sola malla con un material para que se dibuje en una
sola llamada (los huesitos y la bolita no se animan por separado).
"""
import math

from mathutils import Matrix, Vector

import mx

NOMBRE = "pan_de_muerto"
VISTA = {"azimut": -30, "elevacion": 32}

# perfil del domo (radio, altura)
DOMO = [(0.0, 0.0), (0.096, 0.0), (0.106, 0.010), (0.104, 0.026), (0.092, 0.044), (0.072, 0.060),
        (0.045, 0.071), (0.018, 0.076), (0.0, 0.077)]


def superficie(r):
    """Altura del domo para un radio dado (interpolación del perfil)."""
    for (r0, z0), (r1, z1) in zip(DOMO[::-1], DOMO[::-1][1:]):
        if r0 <= r <= r1:
            t = (r - r0) / (r1 - r0) if r1 > r0 else 0.0
            return z0 + (z1 - z0) * t
    return 0.0


def construir():
    pan = mx.material("pan", textura="pan_de_muerto.png", rugosidad=0.75)
    bm, uv = mx.nuevo_bm()
    mx.torno(bm, uv, DOMO, 14, mat=0, v_por_longitud=True)

    # huesitos: tubos con radio ondulado que siguen la curvatura del domo
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = Vector((math.cos(a), math.sin(a), 0))
        puntos, radios = [], []
        n = 9
        for i in range(n):
            t = i / (n - 1)
            r = 0.098 * (1 - t) + 0.012 * t
            z = superficie(r) + 0.008
            puntos.append(d * r + Vector((0, 0, z)))
            radios.append(0.0105 * (1.0 + 0.4 * math.cos(t * math.pi * 6)))
        mx.tubo(bm, uv, puntos, radios, lados=5, mat=0, tapas=True, v_escala=0.15)

    # bolita superior
    perfil = [(0.0, 0.0)]
    for i in range(1, 6):
        ang = -math.pi / 2 + math.pi * i / 6
        perfil.append((math.cos(ang) * 0.019, (math.sin(ang) + 1) * 0.017))
    perfil.append((0.0, 0.034))
    mx.torno(bm, uv, perfil, 8, M=Matrix.Translation((0, 0, 0.074)), mat=0, v_rango=(0.6, 1.0))
    mx.suavizar(bm, 55)
    return mx.objeto(NOMBRE, bm, [pan])
