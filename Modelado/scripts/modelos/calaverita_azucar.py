"""Calaverita de azúcar.

Se parte de una esfera UV de baja resolución y se deforma vértice por
vértice (mandíbula angosta, cara plana, pómulos y cuencas de ojos/nariz).
Las UVs combinan dos proyecciones que coinciden con calaverita.png:
  * Caras frontales: proyección plana  u = 0.25 + x/ANCHO*0.5,  v = z/ALTO
  * Resto:           proyección cilíndrica en la mitad derecha de la textura
"""
import math

from mathutils import Vector

import mx

NOMBRE = "calaverita_azucar"
VISTA = {"azimut": -28, "elevacion": 12}
ANCHO, ALTO, FONDO = 0.10, 0.11, 0.095


def suave(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def construir():
    mat = mx.material("calaverita", textura="calaverita.png", rugosidad=0.45)
    bm, uv = mx.nuevo_bm()
    perfil = []
    anillos = 11
    for i in range(anillos + 1):
        a = -math.pi / 2 + math.pi * i / anillos
        perfil.append((math.cos(a), math.sin(a)))
    mx.torno(bm, uv, [(r, z) for r, z in perfil], 16, mat=0)
    mx.soldar(bm)

    ojos = [Vector((s * 0.42, -1.0, 0.21)) for s in (-1, 1)]
    for v in bm.verts:
        x, y, z = v.co
        frente = suave(0.1, -0.6, y)              # 1 en la cara frontal
        abajo = suave(0.0, -0.9, z)                # 1 en la parte inferior
        x *= 1.0 - 0.42 * abajo * (0.5 + 0.5 * frente)     # mandíbula angosta
        y = max(y, -0.80) if z > -0.25 else y * (1.0 - 0.25 * abajo)  # cara plana, barbilla hacia atrás
        if y > 0:
            y *= 1.10                                # cráneo más amplio atrás
        z = max(z, -0.82)                            # base plana para apoyarse
        p = Vector((x, y, z))
        for o in ojos:                               # cuencas de los ojos
            dd = (Vector((x, y, z)) - o).length
            p.y += 0.16 * max(0.0, 1 - dd / 0.42) ** 2
        dn = (Vector((x, y, z)) - Vector((0, -1.0, -0.10))).length   # nariz
        p.y += 0.10 * max(0.0, 1 - dn / 0.25) ** 2
        for s in (-1, 1):                            # pómulos
            dp = (Vector((x, y, z)) - Vector((s * 0.7, -0.6, -0.18))).length
            p.x += s * 0.10 * max(0.0, 1 - dp / 0.45)
        v.co = p

    # normaliza a las dimensiones reales con la base en z=0
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    sx, sy, sz = ANCHO / (max(xs) - min(xs)), FONDO / (max(ys) - min(ys)), ALTO / (max(zs) - min(zs))
    cy, z0 = (max(ys) + min(ys)) / 2, min(zs)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, (v.co.y - cy) * sy, (v.co.z - z0) * sz))
    bm.normal_update()

    # UVs: frontal plana + cilíndrica
    for f in bm.faces:
        if f.normal.y < -0.35:
            for loop in f.loops:
                p = loop.vert.co
                loop[uv].uv = (0.25 + p.x / ANCHO * 0.5, p.z / ALTO)
        else:
            for loop in f.loops:
                p = loop.vert.co
                a = (math.atan2(p.x, p.y) / math.pi + 1) / 2   # 0..1 alrededor
                loop[uv].uv = (0.52 + 0.46 * a, p.z / ALTO)
    mx.suavizar(bm, 60)
    return mx.objeto(NOMBRE, bm, [mat])
