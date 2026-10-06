"""Altar de muertos de tres niveles (tierra, purgatorio y cielo) con mantel y petate.

Evoluciona el altar del prototipo (Prototipo/Untitled.blend): mismas tres
gradas, pero escalonadas hacia atrás para colocar ofrendas en cada huella,
con mantel bordado y estructura de madera biselada.

Jerarquía (cada nivel es hijo del anterior y su origen está sobre la
superficie del nivel inferior, de modo que las ofrendas se cuelgan del
nivel en el que descansan):

    altar_muertos (vacío en la base)
      ├── petate
      └── nivel_1
            └── nivel_2
                  └── nivel_3
"""
import math

import bmesh

import mx

NOMBRE = "altar_muertos"
VISTA = {"azimut": -32, "elevacion": 18}
# (ancho, y_frente, y_fondo, alto) en coordenadas locales de cada nivel
NIVELES = [(2.4, -0.75, 0.75, 0.45), (1.9, -0.40, 0.75, 0.45), (1.4, -0.05, 0.75, 0.45)]
CAIDA = 0.17   # largo del mantel que cuelga


def nivel(ancho, yf, yb, alto, madera_i, mantel_i):
    bm, uv = mx.nuevo_bm()
    a = ancho / 2
    caras = mx.caja(bm, uv, (-a, yf, 0), (a, yb, alto), mat=madera_i, quitar=("-z", "+z"), escala_uv=1.2)
    verticales = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6]
    mx.biselar(bm, 0.025, 1, verticales)
    # mantel: cubierta superior y faldones con la cenefa bordada en el dobladillo
    m, ztop, zbot = 0.025, alto + 0.004, alto - CAIDA

    def vcaida(z):
        return 0.45 * (z - zbot) / (ztop - zbot)

    mx.tarjeta(bm, uv, [(-a - m, yf - m, ztop), (a + m, yf - m, ztop), (a + m, yb, ztop), (-a - m, yb, ztop)],
               uvs=((-a * 0.8, 0.35), (a * 0.8, 0.35), (a * 0.8, 0.35 + (yb - yf) * 0.4),
                    (-a * 0.8, 0.35 + (yb - yf) * 0.4)), mat=mantel_i)
    mx.tarjeta(bm, uv, [(-a - m, yf - m, zbot), (a + m, yf - m, zbot), (a + m, yf - m, ztop), (-a - m, yf - m, ztop)],
               uvs=((-a * 0.8, 0), (a * 0.8, 0), (a * 0.8, vcaida(ztop)), (-a * 0.8, vcaida(ztop))), mat=mantel_i)
    for s in (-1, 1):
        x = s * (a + m)
        esq = [(x, yf - m, zbot), (x, yb, zbot), (x, yb, ztop), (x, yf - m, ztop)]
        uvs = [(yf * 0.8, 0), (yb * 0.8, 0), (yb * 0.8, 0.45), (yf * 0.8, 0.45)]
        if s < 0:
            esq = [esq[1], esq[0], esq[3], esq[2]]
            uvs = [uvs[1], uvs[0], uvs[3], uvs[2]]
        mx.tarjeta(bm, uv, esq, uvs=uvs, mat=mantel_i)
    mx.plano(bm)
    return bm


def construir():
    madera = mx.material("madera_oscura", textura="madera_oscura.jpg", rugosidad=0.8)
    mantel = mx.material("mantel", textura="mantel.png", rugosidad=0.9)
    petate = mx.material("petate", textura="petate.png", rugosidad=0.95)

    raiz = mx.vacio(NOMBRE)
    bm, uv = mx.nuevo_bm()
    mx.caja(bm, uv, (-0.95, -1.95, 0), (0.95, -0.85, 0.012), mat=0, escala_uv=0.6, quitar=("-z",))
    mx.plano(bm)
    mx.objeto("petate", bm, [petate], padre=raiz)

    padre, z = raiz, 0.0
    for i, (ancho, yf, yb, alto) in enumerate(NIVELES):
        ob = mx.objeto(f"nivel_{i + 1}", nivel(ancho, yf, yb, alto, 0, 1), [madera, mantel], padre=padre,
                       loc=(0, 0, z))
        padre, z = ob, alto
    return raiz
