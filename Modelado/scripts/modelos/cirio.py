"""Cirio (vela alta de cera) sobre candelero de barro.

Jerarquía:  cirio (vacío)
              └── candelero (barro)
                    └── vela (cera con escurrimientos)
                          └── llama (emisiva)
"""
import mx

NOMBRE = "cirio"
VISTA = {"azimut": -25, "elevacion": 15}
BOCA = 0.098      # altura del borde del candelero
ALTO_VELA = 0.30


def construir():
    barro = mx.material("barro", textura="barro.png", rugosidad=0.85)
    cera = mx.material("cera_cirio", textura="cera.png", rugosidad=0.55)
    mecha = mx.material("mecha", color=mx.hex2lin("#2B2118"), rugosidad=0.9)
    llama = mx.material("llama", color=mx.hex2lin("#FFC46B"), emision=mx.hex2lin("#FFB347"), fuerza=4.0)

    raiz = mx.vacio(NOMBRE)

    # candelero torneado: pie, fuste con anillo y copa
    bm, uv = mx.nuevo_bm()
    perfil = [(0.0, 0.0), (0.072, 0.0), (0.076, 0.010), (0.064, 0.020), (0.030, 0.032), (0.020, 0.050),
              (0.028, 0.058), (0.019, 0.066), (0.022, 0.080), (0.040, 0.090), (0.046, BOCA),
              (0.040, BOCA), (0.027, BOCA - 0.012)]
    mx.torno(bm, uv, perfil, 12, mat=0, v_rango=(0.25, 0.75))
    mx.suavizar(bm, 35)
    candelero = mx.objeto("candelero", bm, [barro], padre=raiz)

    # vela: el origen queda en el fondo de la copa
    bm, uv = mx.nuevo_bm()
    r = 0.022
    mx.torno(bm, uv, [(r, 0.0), (r, ALTO_VELA), (r * 0.82, ALTO_VELA + 0.004), (0.0, ALTO_VELA + 0.002)], 10, mat=0,
             v_por_longitud=False)
    mx.caja(bm, uv, (-0.0013, -0.0013, ALTO_VELA), (0.0013, 0.0013, ALTO_VELA + 0.012), mat=1, quitar=("-z",))
    mx.suavizar(bm, 40)
    vela = mx.objeto("vela", bm, [cera, mecha], padre=candelero, loc=(0, 0, BOCA - 0.012))

    bm, uv = mx.nuevo_bm()
    mx.flama(bm, uv, alto=0.042, radio=0.010)
    mx.suavizar(bm, 80)
    mx.objeto("llama", bm, [llama], padre=vela, loc=(0, 0, ALTO_VELA + 0.008))
    return raiz
