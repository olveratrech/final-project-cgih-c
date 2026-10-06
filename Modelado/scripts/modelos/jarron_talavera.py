"""Jarrón de Talavera poblana (cerámica esmaltada en azul cobalto)."""
import mx

NOMBRE = "jarron_talavera"
VISTA = {"azimut": -25, "elevacion": 15}


def construir():
    talavera = mx.material("talavera", textura="talavera.png", rugosidad=0.22)
    interior = mx.material("talavera_interior", color=mx.hex2lin("#E9E4D4"), rugosidad=0.3)
    bm, uv = mx.nuevo_bm()
    exterior = [(0.0, 0.0), (0.058, 0.0), (0.064, 0.008), (0.090, 0.055), (0.110, 0.115), (0.106, 0.165),
                (0.078, 0.215), (0.052, 0.250), (0.050, 0.275), (0.064, 0.295), (0.076, 0.305)]
    mx.torno(bm, uv, exterior, 14, mat=0)
    mx.torno(bm, uv, [(0.076, 0.305), (0.066, 0.303), (0.046, 0.280), (0.044, 0.250)], 14, mat=1)
    mx.suavizar(bm, 40)
    return mx.objeto(NOMBRE, bm, [talavera, interior])
