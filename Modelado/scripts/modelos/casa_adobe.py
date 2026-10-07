"""Casa de adobe con portal y techo de teja (arquitectura vernácula mexicana).

El altar se coloca bajo el portal, frente al muro principal; el camino de
cempasúchil termina en la banqueta del portal.

Jerarquía:  casa_adobe (muros, hastiales y guardapolvo rojo)
              ├── techo   (techo a dos aguas de teja)
              ├── portal  (banqueta, horcones, viga madrina y cubierta)
              ├── puerta  (pivote en la bisagra)
              └── ventana (postigos y herrería)
"""
import mx

NOMBRE = "casa_adobe"
VISTA = {"azimut": -32, "elevacion": 16}
ANCHO, FONDO, ALTO, MURO = 7.0, 4.5, 3.0, 0.4
PUERTA = (1.6, 0.0, 2.6, 2.1)
VENTANA = (-2.8, 1.0, -1.8, 1.9)
PORTAL = 3.2


def construir():
    adobe = mx.material("adobe", textura="adobe.jpg", rugosidad=0.95)
    rojo = mx.material("aplanado_rojo", textura="aplanado_rojo.jpg", rugosidad=0.9)
    teja = mx.material("tejas", textura="tejas.jpg", rugosidad=0.85)
    madera = mx.material("madera_oscura", textura="madera_oscura.jpg", rugosidad=0.8)
    madera_c = mx.material("madera_clara", textura="madera_clara.jpg", rugosidad=0.8)
    cal = mx.material("cal", textura="cal.jpg", rugosidad=0.95)
    hierro = mx.material("hierro", color=mx.hex2lin("#232326"), rugosidad=0.45, metalico=0.75)

    w = ANCHO / 2
    # --- muros -------------------------------------------------------------
    bm, uv = mx.nuevo_bm()
    mx.muro_con_huecos(bm, uv, ANCHO, ALTO, MURO, [PUERTA, VENTANA], mat=0, escala_uv=2.0)
    mx.caja(bm, uv, (-w, MURO, 0), (-w + MURO, FONDO, ALTO), mat=0, escala_uv=2.0, quitar=("-z", "-y"))
    mx.caja(bm, uv, (w - MURO, MURO, 0), (w, FONDO, ALTO), mat=0, escala_uv=2.0, quitar=("-z", "-y"))
    mx.caja(bm, uv, (-w + MURO, FONDO - MURO, 0), (w - MURO, FONDO, ALTO), mat=0, escala_uv=2.0, quitar=("-z",))
    # hastiales (triángulos bajo el techo a dos aguas)
    cumbrera = ALTO + 1.1
    for x, orden in ((-w, (0, 1, 2)), (w, (2, 1, 0))):
        pts = [(x, 0, ALTO), (x, FONDO / 2, cumbrera), (x, FONDO, ALTO)]
        vv = [bm.verts.new(pts[i]) for i in orden]
        mx._cara(bm, vv, [(pts[i][1] / 2, pts[i][2] / 2) for i in orden], uv, 0)
    # guardapolvo rojo (zócalo pintado) a ambos lados de la puerta
    for x0, x1 in ((-w - 0.01, PUERTA[0]), (PUERTA[2], w + 0.01)):
        mx.caja(bm, uv, (x0, -0.012, 0), (x1, 0.0, 0.7), mat=1, quitar=("-z", "+y"))
    mx.plano(bm)
    raiz = mx.objeto(NOMBRE, bm, [adobe, rojo])

    # --- techo a dos aguas -----------------------------------------------------
    bm, uv = mx.nuevo_bm()
    alero = 0.35
    for y_a, z_a, y_b in ((-alero, ALTO - 0.15, FONDO / 2), (FONDO + alero, ALTO - 0.15, FONDO / 2)):
        # cada faldón es un plano inclinado con espesor; la teja se repite cada 1.5 m
        pts = [(-w - alero, y_a, z_a), (w + alero, y_a, z_a), (w + alero, y_b, cumbrera + 0.05),
               (-w - alero, y_b, cumbrera + 0.05)]
        if y_a > y_b:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        vv = [bm.verts.new(p) for p in pts]
        largo = ((y_b - y_a) ** 2 + (cumbrera - z_a) ** 2) ** 0.5
        mx._cara(bm, vv, [(pts[0][0] / 1.5, 0), (pts[1][0] / 1.5, 0), (pts[2][0] / 1.5, largo / 1.5),
                          (pts[3][0] / 1.5, largo / 1.5)], uv, 0)
        # cara inferior (tejamanil de madera visible desde abajo)
        vv2 = [bm.verts.new((p[0], p[1], p[2] - 0.06)) for p in reversed(pts)]
        mx._cara(bm, vv2, [(0, 0), (1, 0), (1, 1), (0, 1)], uv, 1)
    mx.plano(bm)
    mx.objeto("techo", bm, [teja, madera_c], padre=raiz)

    # --- portal -------------------------------------------------------------------
    bm, uv = mx.nuevo_bm()
    mx.caja(bm, uv, (-w - 0.1, -PORTAL - 0.1, 0), (w + 0.1, 0.0, 0.15), mat=1, escala_uv=1.5, quitar=("-z", "+y"))
    for x in (-w + 0.1, -1.15, 1.15, w - 0.1):
        mx.caja(bm, uv, (x - 0.14, -PORTAL + 0.06, 0.15), (x + 0.14, -PORTAL + 0.34, 0.32), mat=2)  # basa
        mx.caja(bm, uv, (x - 0.08, -PORTAL + 0.12, 0.32), (x + 0.08, -PORTAL + 0.28, 2.38), mat=0, vertical=True,
                escala_uv=0.8)
        mx.caja(bm, uv, (x - 0.25, -PORTAL + 0.12, 2.38), (x + 0.25, -PORTAL + 0.28, 2.46), mat=0, escala_uv=0.8)
    mx.caja(bm, uv, (-w - 0.25, -PORTAL + 0.10, 2.46), (w + 0.25, -PORTAL + 0.30, 2.62), mat=0, escala_uv=0.8)
    # cubierta del portal: teja arriba, madera abajo
    pts = [(-w - 0.35, -PORTAL - 0.25, 2.62), (w + 0.35, -PORTAL - 0.25, 2.62), (w + 0.35, 0.0, ALTO - 0.2),
           (-w - 0.35, 0.0, ALTO - 0.2)]
    vv = [bm.verts.new(p) for p in pts]
    largo = ((PORTAL + 0.25) ** 2 + (ALTO - 0.2 - 2.62) ** 2) ** 0.5
    mx._cara(bm, vv, [(p[0] / 1.5, (p[1] + PORTAL + 0.25) / 1.5 * (largo / (PORTAL + 0.25))) for p in pts], uv, 3)
    vv2 = [bm.verts.new((p[0], p[1], p[2] - 0.05)) for p in reversed(pts)]
    mx._cara(bm, vv2, [(p[0] / 1.2, p[1] / 1.2) for p in reversed(pts)], uv, 4)
    mx.plano(bm)
    mx.objeto("portal", bm, [madera, rojo, cal, teja, madera_c], padre=raiz)

    # --- puerta (dos tableros de madera clara) -------------------------------------
    bm, uv = mx.nuevo_bm()
    ancho_p = PUERTA[2] - PUERTA[0]
    mx.caja(bm, uv, (0.0, -0.03, 0.0), (ancho_p, 0.03, PUERTA[3]), mat=0, vertical=True, escala_uv=1.0)
    for z0, z1 in ((0.25, 0.95), (1.15, 1.85)):
        mx.caja(bm, uv, (0.12, -0.05, z0), (ancho_p - 0.12, -0.03, z1), mat=0, vertical=True, quitar=("+y",))
    mx.caja(bm, uv, (ancho_p - 0.16, -0.08, 1.0), (ancho_p - 0.12, -0.05, 1.12), mat=1)
    mx.plano(bm)
    mx.objeto("puerta", bm, [madera_c, hierro], padre=raiz, loc=(PUERTA[0], MURO * 0.5, 0))

    # --- ventana: postigos y herrería ---------------------------------------------
    bm, uv = mx.nuevo_bm()
    x0, z0, x1, z1 = VENTANA
    mx.caja(bm, uv, (x0, MURO * 0.6, z0), (x1, MURO * 0.6 + 0.05, z1), mat=0, vertical=True)
    mx.caja(bm, uv, (x0 - 0.06, -0.06, z0 - 0.08), (x1 + 0.06, 0.04, z0), mat=2)          # repisa
    for k in range(5):
        x = x0 + (k + 0.5) * (x1 - x0) / 5
        mx.caja(bm, uv, (x - 0.012, 0.03, z0), (x + 0.012, 0.055, z1), mat=1, quitar=("-z", "+z"))
    mx.caja(bm, uv, (x0, 0.03, (z0 + z1) / 2 - 0.012), (x1, 0.055, (z0 + z1) / 2 + 0.012), mat=1)
    mx.plano(bm)
    mx.objeto("ventana", bm, [madera_c, hierro, cal], padre=raiz)
    return raiz
