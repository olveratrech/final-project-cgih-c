"""Farol de hojalata con vidrios de colores sobre poste de madera.

Jerarquía (pensada para animar el balanceo del farol y el parpadeo de la vela):
    farol (poste + base)
      └── brazo (ménsula de madera)
            └── lampara (pivote en el gancho)
                  └── llama
"""
import math

from mathutils import Matrix

import mx

NOMBRE = "farol"
VISTA = {"azimut": -35, "elevacion": 10}
ALTO_POSTE = 2.5
LARGO_BRAZO = 0.55


def construir():
    madera = mx.material("madera_oscura", textura="madera_oscura.jpg", rugosidad=0.8)
    cal = mx.material("cal", textura="cal.jpg", rugosidad=0.95)
    hojalata = mx.material("hojalata", textura="hojalata.png", rugosidad=0.35, metalico=0.85)
    vidrio = mx.material("vidrio_colores", textura="vidrio_colores.png", rugosidad=0.2,
                         emision=mx.hex2lin("#FFB45A"), fuerza=0.35)
    cera = mx.material("cera", color=mx.hex2lin("#F3EAD3"), rugosidad=0.6)
    llama = mx.material("llama", color=mx.hex2lin("#FFC46B"), emision=mx.hex2lin("#FFB347"), fuerza=4.0)

    # poste con base de mampostería encalada
    bm, uv = mx.nuevo_bm()
    mx.caja(bm, uv, (-0.15, -0.15, 0), (0.15, 0.15, 0.35), mat=1, quitar=("-z",))
    mx.caja(bm, uv, (-0.05, -0.05, 0.35), (0.05, 0.05, ALTO_POSTE), mat=0, quitar=("-z",), vertical=True,
            escala_uv=0.6)
    mx.caja(bm, uv, (-0.07, -0.07, ALTO_POSTE), (0.07, 0.07, ALTO_POSTE + 0.05), mat=0, escala_uv=0.6)
    mx.plano(bm)
    raiz = mx.objeto(NOMBRE, bm, [madera, cal])

    # brazo con tornapunta diagonal
    bm, uv = mx.nuevo_bm()
    mx.caja(bm, uv, (0.0, -0.03, -0.03), (LARGO_BRAZO, 0.03, 0.03), mat=0, escala_uv=0.6)
    M = Matrix.Translation((0.0, 0, -0.30)) @ Matrix.Rotation(math.radians(-45), 4, "Y")
    mx.caja(bm, uv, (0.0, -0.022, -0.022), (0.40, 0.022, 0.022), M=M, mat=0, escala_uv=0.6)
    mx.plano(bm)
    brazo = mx.objeto("brazo", bm, [madera], padre=raiz, loc=(0.05, 0, ALTO_POSTE - 0.10))

    # lámpara hexagonal: gancho, techo piramidal, cuerpo de vidrio y fondo
    bm, uv = mx.nuevo_bm()
    mx.caja(bm, uv, (-0.004, -0.004, -0.06), (0.004, 0.004, 0.0), mat=0)
    # los perfiles van de abajo hacia arriba para que las normales apunten hacia afuera
    mx.torno(bm, uv, [(0.105, -0.145), (0.125, -0.145), (0.125, -0.13), (0.012, -0.07), (0.022, -0.06),
                      (0.0, -0.045)], 6, mat=0, v_rango=(0.0, 0.3))
    mx.torno(bm, uv, [(0.10, -0.38), (0.10, -0.145)], 6, mat=1, u_rep=3.0, v_rango=(0.5, 1.0))
    mx.torno(bm, uv, [(0.0, -0.50), (0.012, -0.47), (0.04, -0.44), (0.112, -0.395), (0.112, -0.38),
                      (0.10, -0.38)], 6, mat=0, v_rango=(0.3, 0.6))
    mx.torno(bm, uv, [(0.0, -0.395), (0.016, -0.395), (0.016, -0.30), (0.0, -0.30)], 6, mat=2)  # vela
    mx.plano(bm)
    lampara = mx.objeto("lampara", bm, [hojalata, vidrio, cera], padre=brazo, loc=(LARGO_BRAZO - 0.06, 0, -0.03))

    bm, uv = mx.nuevo_bm()
    mx.flama(bm, uv, alto=0.035, radio=0.009)
    mx.suavizar(bm, 80)
    mx.objeto("llama", bm, [llama], padre=lampara, loc=(0, 0, -0.297))
    return raiz
