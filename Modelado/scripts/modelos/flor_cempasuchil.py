"""Flor de cempasúchil (Tagetes erecta) con tallo y hojas.

Jerarquía:  flor_cempasuchil (vacío)
              ├── tallo   (tallo + hojas, verde)
              └── cabeza  (3 anillos de pétalos curvos + centro)
"""
import math

from mathutils import Matrix, Vector

import mx

NOMBRE = "flor_cempasuchil"
VISTA = {"azimut": -25, "elevacion": 28}
ALTO_TALLO = 0.22
RADIO = 0.048


def hoja(bm, uv, base, direccion, largo, ancho, mat):
    """Hoja lanceolada con nervadura central doblada en V."""
    d = Vector(direccion).normalized()
    lado = d.cross(Vector((0, 0, 1))).normalized()
    arriba = lado.cross(d).normalized()
    b = Vector(base)
    puntos = [
        (b, (0.5, 0.0)),
        (b + d * largo * 0.35 + lado * ancho * 0.5 + arriba * ancho * 0.15, (1.0, 0.35)),
        (b + d * largo, (0.5, 1.0)),
        (b + d * largo * 0.35 - lado * ancho * 0.5 + arriba * ancho * 0.15, (0.0, 0.35)),
        (b + d * largo * 0.45 - arriba * ancho * 0.08, (0.5, 0.45)),  # nervadura
    ]
    v = [bm.verts.new(p) for p, _ in puntos]
    uvs = [c for _, c in puntos]
    mx._cara(bm, [v[0], v[1], v[4]], [uvs[0], uvs[1], uvs[4]], uv, mat)
    mx._cara(bm, [v[4], v[1], v[2]], [uvs[4], uvs[1], uvs[2]], uv, mat)
    mx._cara(bm, [v[0], v[4], v[3]], [uvs[0], uvs[4], uvs[3]], uv, mat)
    mx._cara(bm, [v[4], v[2], v[3]], [uvs[4], uvs[2], uvs[3]], uv, mat)


def construir():
    petalo = mx.material("cempasuchil_petalo", textura="petalo_cempasuchil.png", rugosidad=0.65, doble_cara=True)
    verde = mx.material("cempasuchil_verde", color=mx.hex2lin("#3F7A24"), rugosidad=0.7, doble_cara=True)

    raiz = mx.vacio(NOMBRE)

    # tallo ligeramente curvo con dos hojas
    bm, uv = mx.nuevo_bm()
    pts = [(0.008 * math.sin(t * 2.2), 0.0, ALTO_TALLO * t) for t in (0.0, 0.3, 0.6, 0.85, 1.0)]
    mx.tubo(bm, uv, pts, [0.0045, 0.004, 0.0037, 0.0035, 0.0033], lados=5, mat=0)
    hoja(bm, uv, (0.004, 0, 0.08), (1.0, -0.3, 0.6), 0.075, 0.03, 0)
    hoja(bm, uv, (-0.003, 0, 0.12), (-1.0, 0.4, 0.5), 0.065, 0.028, 0)
    # cáliz: copa verde bajo la cabeza
    mx.torno(bm, uv, [(0.0033, ALTO_TALLO - 0.012), (0.012, ALTO_TALLO - 0.002), (0.016, ALTO_TALLO + 0.004)],
             6, mat=0)
    mx.suavizar(bm, 50)
    mx.objeto("tallo", bm, [verde], padre=raiz)

    # cabeza de la flor
    bm, uv = mx.nuevo_bm()
    mx.flor_cempasuchil(bm, uv, radio=RADIO, semilla=3)
    mx.suavizar(bm, 70)
    mx.objeto("cabeza", bm, [petalo], padre=raiz, loc=(0.008 * math.sin(2.2), 0, ALTO_TALLO))
    return raiz
