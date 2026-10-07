"""Vaso de vidrio con agua (la ofrenda de agua para calmar la sed de las ánimas).

Jerarquía:  vaso_agua (vidrio translúcido, alphaMode BLEND)
              └── agua (volumen de agua translúcido)
Ambos materiales son candidatos para el sombreado Fresnel de la siguiente entrega.
"""
import mx

NOMBRE = "vaso_agua"
VISTA = {"azimut": -25, "elevacion": 20}
NIVEL = 0.085


def construir():
    vidrio = mx.material("vidrio", color=mx.hex2lin("#E6F2FF"), alfa=0.28, rugosidad=0.05)
    agua = mx.material("agua", color=mx.hex2lin("#7FB7E6"), alfa=0.45, rugosidad=0.02)
    bm, uv = mx.nuevo_bm()
    perfil = [(0.0, 0.0), (0.029, 0.0), (0.034, 0.11), (0.031, 0.11), (0.026, 0.006), (0.0, 0.006)]
    mx.torno(bm, uv, perfil, 12, mat=0)
    mx.suavizar(bm, 40)
    raiz = mx.objeto(NOMBRE, bm, [vidrio])

    bm, uv = mx.nuevo_bm()
    r_sup = 0.026 + (0.031 - 0.026) * (NIVEL - 0.006) / (0.11 - 0.006) - 0.0005
    mx.torno(bm, uv, [(0.0, 0.007), (0.0255, 0.007), (r_sup, NIVEL), (0.0, NIVEL)], 12, mat=0)
    mx.suavizar(bm, 40)
    mx.objeto("agua", bm, [agua], padre=raiz)
    return raiz
