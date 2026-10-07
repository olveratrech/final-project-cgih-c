"""Mariposa monarca (Danaus plexippus).

Según la tradición, las monarcas que llegan a Michoacán a inicios de
noviembre son las almas que regresan. El modelo es jerárquico para el
aleteo procedural de la entrega de animación:

    mariposa_monarca (cuerpo + antenas)
      ├── ala_izquierda  (pivote sobre el eje del cuerpo)
      └── ala_derecha
"""
import math

from mathutils import Matrix

import mx

NOMBRE = "mariposa_monarca"
VISTA = {"azimut": -20, "elevacion": 55}
DIEDRO = math.radians(18)


def ala(lado, mat):
    """Ala anterior + posterior como dos tarjetas con recorte alfa."""
    bm, uv = mx.nuevo_bm()
    s = 1 if lado > 0 else -1
    wf, hf, y0 = 0.052, 0.026, -0.008      # ala anterior (mitad superior de la textura)
    wh, hh, y1 = 0.045, 0.0225, -0.001     # ala posterior (mitad inferior)
    if s > 0:
        mx.tarjeta(bm, uv, [(0, y0, 0), (wf, y0, 0), (wf, y0 + hf, 0), (0, y0 + hf, 0)],
                   uvs=((0, 0.5), (1, 0.5), (1, 1), (0, 1)))
        mx.tarjeta(bm, uv, [(0, y1 - hh, 0), (wh, y1 - hh, 0), (wh, y1, 0), (0, y1, 0)],
                   uvs=((0, 0), (1, 0), (1, 0.5), (0, 0.5)))
    else:
        mx.tarjeta(bm, uv, [(-wf, y0, 0), (0, y0, 0), (0, y0 + hf, 0), (-wf, y0 + hf, 0)],
                   uvs=((1, 0.5), (0, 0.5), (0, 1), (1, 1)))
        mx.tarjeta(bm, uv, [(-wh, y1 - hh, 0), (0, y1 - hh, 0), (0, y1, 0), (-wh, y1, 0)],
                   uvs=((1, 0), (0, 0), (0, 0.5), (1, 0.5)))
    mx.plano(bm)
    return bm


def construir():
    alas = mx.material("mariposa_alas", textura="mariposa_monarca.png", rugosidad=0.6, recorte=True, doble_cara=True)
    cuerpo = mx.material("mariposa_cuerpo", color=mx.hex2lin("#1E1A18"), rugosidad=0.7)

    # cuerpo: huso torneado sobre Z y girado para quedar a lo largo de Y
    bm, uv = mx.nuevo_bm()
    perfil = [(0.0, -0.024), (0.0028, -0.018), (0.0034, -0.006), (0.0042, 0.003), (0.0032, 0.010),
              (0.0030, 0.013), (0.0026, 0.017), (0.0, 0.020)]
    mx.torno(bm, uv, perfil, 6, M=Matrix.Rotation(-math.pi / 2, 4, "X"), mat=0)
    for s in (-1, 1):  # antenas
        mx.tubo(bm, uv, [(0.0012 * s, 0.017, 0.001), (0.006 * s, 0.032, 0.006), (0.009 * s, 0.040, 0.009)],
                [0.0006, 0.0005, 0.0009], lados=3, mat=0)
    mx.suavizar(bm, 60)
    raiz = mx.objeto(NOMBRE, bm, [cuerpo])

    mx.objeto("ala_izquierda", ala(-1, alas), [alas], padre=raiz, rot=(0, -DIEDRO, 0))
    mx.objeto("ala_derecha", ala(1, alas), [alas], padre=raiz, rot=(0, DIEDRO, 0))
    return raiz
