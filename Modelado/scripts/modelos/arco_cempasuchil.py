"""Arco de cempasúchil: marco de carrizo cubierto de flores.

El arco simboliza la puerta entre el mundo de los vivos y el de los
muertos. Las cabezas de flor se combinan en una sola malla (batching
estático) para dibujar todo el follaje con dos llamadas.

Jerarquía:  arco_cempasuchil (marco de carrizo)
              └── flores (cempasúchil + mano de león)
"""
import math
import random

from mathutils import Matrix, Vector

import mx

NOMBRE = "arco_cempasuchil"
VISTA = {"azimut": -25, "elevacion": 10}
MEDIO_ANCHO = 1.3
ALTO_POSTE = 1.2


def recorrido(paso):
    """Muestras (punto, normal hacia afuera) sobre postes y medio punto."""
    pts = []
    n_poste = max(2, int(ALTO_POSTE / paso))
    for i in range(n_poste):
        z = ALTO_POSTE * i / n_poste
        pts.append((Vector((-MEDIO_ANCHO, 0, z)), Vector((-1, 0, 0))))
    n_arco = int(math.pi * MEDIO_ANCHO / paso)
    for i in range(n_arco + 1):
        t = math.pi - math.pi * i / n_arco
        n = Vector((math.cos(t), 0, math.sin(t)))
        pts.append((Vector((0, 0, ALTO_POSTE)) + n * MEDIO_ANCHO, n))
    for i in range(n_poste - 1, -1, -1):
        z = ALTO_POSTE * i / n_poste
        pts.append((Vector((MEDIO_ANCHO, 0, z)), Vector((1, 0, 0))))
    return pts


def construir():
    carrizo = mx.material("carrizo", textura="madera_clara.jpg", tinte=mx.hex2lin("#C9B07A"), rugosidad=0.8)
    petalo = mx.material("cempasuchil_petalo", textura="petalo_cempasuchil.png", rugosidad=0.65, doble_cara=True)
    mano_leon = mx.material("mano_de_leon", textura="petalo_cempasuchil.png", tinte=mx.hex2lin("#C2185B"),
                            rugosidad=0.7, doble_cara=True)

    # marco: un tubo que recorre poste izquierdo, medio punto y poste derecho
    bm, uv = mx.nuevo_bm()
    linea = [p for p, _ in recorrido(0.25)]
    mx.tubo(bm, uv, linea, 0.04, lados=6, mat=0, v_escala=0.5)
    mx.suavizar(bm, 50)
    raiz = mx.objeto(NOMBRE, bm, [carrizo])

    bm, uv = mx.nuevo_bm()
    rnd = random.Random(8)
    frente = Vector((0, -1, 0))
    for i, (p, n) in enumerate(recorrido(0.12)):
        if p.z < 0.2:
            continue  # el pie del arco queda libre
        # flor principal mirando al frente (ligeramente hacia afuera del arco)
        mira = (frente * 0.8 + n * 0.5).normalized()
        giro = Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z")
        M = Matrix.Translation(p + n * 0.03 + frente * 0.05) @ \
            Vector((0, 0, 1)).rotation_difference(mira).to_matrix().to_4x4() @ giro
        mx.flor_cempasuchil(bm, uv, M=M, radio=rnd.uniform(0.072, 0.085), mat_petalo=0, semilla=100 + i,
                            anillos=mx.ANILLOS_FLOR_LIGERA)
        # relleno: pompón de cempasúchil hacia atrás y hacia afuera para dar volumen
        M2 = Matrix.Translation(p + n * 0.06 - frente * 0.04) @ \
            Vector((0, 0, 1)).rotation_difference((n - frente * 0.3).normalized()).to_matrix().to_4x4()
        mx.pompon(bm, uv, M=M2, radio=rnd.uniform(0.05, 0.06), mat=0, semilla=200 + i, seg=6, anillos=4)
        if i % 3 == 1:  # mano de león intercalada en el borde exterior
            M3 = Matrix.Translation(p + n * 0.10 + frente * 0.02) @ \
                Vector((0, 0, 1)).rotation_difference(n).to_matrix().to_4x4()
            mx.pompon(bm, uv, M=M3, radio=rnd.uniform(0.04, 0.05), mat=1, semilla=i, seg=6, anillos=4)
    mx.suavizar(bm, 70)
    mx.objeto("flores", bm, [petalo, mano_leon], padre=raiz)
    return raiz
