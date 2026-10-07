"""
mx.py - Utilidades de modelado procedural para Blender (bpy + bmesh).

Contiene las operaciones geométricas que comparten todos los modelos del
proyecto: revolución de perfiles (torno), cajas, tubos por barrido,
proyecciones UV, suavizado por ángulo, materiales glTF y exportación.

Convenciones de todos los modelos:
  * Unidades en metros, eje Z hacia arriba (Blender).
  * El origen del objeto raíz está en el centro de la base (apoya en Z=0).
  * El frente del modelo mira hacia -Y (vista frontal de Blender), que en
    glTF/OpenGL (Y arriba) corresponde a +Z.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEXTURAS = os.path.join(RAIZ, "assets", "textures")
SALIDA_GLTF = os.path.join(RAIZ, "assets", "models", "propios")
SALIDA_BLEND = os.path.join(RAIZ, "Modelado", "blend")
SALIDA_RENDER = os.path.join(RAIZ, "Modelado", "render")

TAU = 2.0 * math.pi


# ---------------------------------------------------------------------------
# Escena
# ---------------------------------------------------------------------------
def reiniciar():
    """Escena vacía con unidades métricas."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    random.seed(1)


def vacio(nombre, padre=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Nodo vacío (pivote) para agrupar jerárquicamente."""
    ob = bpy.data.objects.new(nombre, None)
    ob.empty_display_type = "PLAIN_AXES"
    ob.empty_display_size = 0.1
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    if padre:
        ob.parent = padre
    return ob


def objeto(nombre, bm, materiales, padre=None, loc=(0, 0, 0), rot=(0, 0, 0), escala=(1, 1, 1)):
    """Convierte un bmesh en un objeto de malla enlazado a la escena."""
    me = bpy.data.meshes.new(nombre)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    for m in materiales:
        me.materials.append(m)
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = escala
    if padre:
        ob.parent = padre
    return ob


def nuevo_bm():
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    return bm, uv


# ---------------------------------------------------------------------------
# Materiales (se traducen a materiales PBR de glTF)
# ---------------------------------------------------------------------------
def _imagen(nombre):
    ruta = os.path.join(TEXTURAS, nombre)
    for img in bpy.data.images:
        if os.path.abspath(bpy.path.abspath(img.filepath)) == ruta:
            return img
    return bpy.data.images.load(ruta)


def material(nombre, color=(0.8, 0.8, 0.8), textura=None, tinte=None, rugosidad=0.8,
             metalico=0.0, emision=None, fuerza=1.0, alfa=None, recorte=False, doble_cara=False):
    """Crea (o reutiliza) un material Principled BSDF exportable a glTF.

    textura   -> baseColorTexture (archivo en assets/textures)
    tinte     -> baseColorFactor que multiplica a la textura
    recorte   -> alphaMode MASK (papel picado, alas, hojas)
    alfa      -> alphaMode BLEND (vidrio, agua)
    emision   -> emissiveFactor (flamas, brasas)
    """
    if nombre in bpy.data.materials:
        return bpy.data.materials[nombre]
    m = bpy.data.materials.new(nombre)
    m.use_backface_culling = not doble_cara
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rugosidad
    b.inputs["Metallic"].default_value = metalico
    if textura:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _imagen(textura)
        t.location = (-600, 300)
        salida = t.outputs["Color"]
        if tinte is not None:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.inputs[7].default_value = tuple(tinte[:3]) + (1.0,)
            mix.location = (-300, 300)
            nt.links.new(salida, mix.inputs[6])
            salida = mix.outputs[2]
        nt.links.new(salida, b.inputs["Base Color"])
        if recorte:
            r = nt.nodes.new("ShaderNodeMath")
            r.operation = "ROUND"
            r.location = (-300, 0)
            nt.links.new(t.outputs["Alpha"], r.inputs[0])
            nt.links.new(r.outputs[0], b.inputs["Alpha"])
    else:
        b.inputs["Base Color"].default_value = tuple(color[:3]) + (1.0,)
    if alfa is not None:
        b.inputs["Alpha"].default_value = alfa
    if emision is not None:
        b.inputs["Emission Color"].default_value = tuple(emision[:3]) + (1.0,)
        b.inputs["Emission Strength"].default_value = fuerza
    return m


def hex2lin(h):
    """Color hexadecimal sRGB -> lineal (Blender y glTF trabajan en lineal)."""
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ---------------------------------------------------------------------------
# Primitivas geométricas con UVs
# ---------------------------------------------------------------------------
def _cara(bm, verts, uvs, uv, mat=0):
    f = bm.faces.new(verts)
    f.material_index = mat
    for loop, coord in zip(f.loops, uvs):
        loop[uv].uv = coord
    return f


def torno(bm, uv, perfil, lados, M=Matrix(), mat=0, tapa_inf=False, tapa_sup=False,
          u_rep=1.0, v_rango=(0.0, 1.0), v_por_longitud=True):
    """Superficie de revolución alrededor de Z.

    perfil: lista de (radio, z) de abajo hacia arriba. Un radio 0 crea un polo.
    El parámetro u=0.5 queda al frente (-Y) para que los motivos de las
    texturas se vean de frente.
    """
    # coordenada v por longitud de arco del perfil (evita estirar la textura)
    acum = [0.0]
    for (r0, z0), (r1, z1) in zip(perfil, perfil[1:]):
        acum.append(acum[-1] + math.hypot(r1 - r0, z1 - z0))
    total = acum[-1] or 1.0
    vs = []
    for i, (r, z) in enumerate(perfil):
        t = acum[i] / total if v_por_longitud else (z - perfil[0][1]) / ((perfil[-1][1] - perfil[0][1]) or 1)
        vs.append(v_rango[0] + (v_rango[1] - v_rango[0]) * t)

    anillos = []
    for r, z in perfil:
        if r < 1e-6:
            anillos.append([bm.verts.new(M @ Vector((0, 0, z)))])
        else:
            fila = []
            for j in range(lados):
                a = TAU * j / lados - 1.5 * math.pi
                fila.append(bm.verts.new(M @ Vector((math.cos(a) * r, math.sin(a) * r, z))))
            anillos.append(fila)

    for i in range(len(perfil) - 1):
        A, B = anillos[i], anillos[i + 1]
        va, vb = vs[i], vs[i + 1]
        for j in range(lados):
            u0, u1 = j / lados * u_rep, (j + 1) / lados * u_rep
            j1 = (j + 1) % lados
            if len(A) == 1 and len(B) == 1:
                continue
            if len(A) == 1:
                _cara(bm, [A[0], B[j], B[j1]], [((u0 + u1) / 2, va), (u0, vb), (u1, vb)], uv, mat)
            elif len(B) == 1:
                _cara(bm, [A[j], A[j1], B[0]], [(u0, va), (u1, va), ((u0 + u1) / 2, vb)], uv, mat)
            else:
                _cara(bm, [A[j], A[j1], B[j1], B[j]], [(u0, va), (u1, va), (u1, vb), (u0, vb)], uv, mat)

    def tapa(fila, z, invertir):
        if len(fila) < 3:
            return
        r = perfil[0][0] if not invertir else perfil[-1][0]
        uvs = []
        for j in range(lados):
            a = TAU * j / lados - 1.5 * math.pi
            uvs.append((0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
        vv = list(fila)
        if not invertir:
            vv.reverse()
            uvs.reverse()
        _cara(bm, vv, uvs, uv, mat)

    if tapa_inf:
        tapa(anillos[0], perfil[0][1], False)
    if tapa_sup:
        tapa(anillos[-1], perfil[-1][1], True)
    return anillos


def caja(bm, uv, minimo, maximo, M=Matrix(), mat=0, escala_uv=1.0, quitar=(), mats=None, vertical=False):
    """Prisma rectangular con UVs proyectados por cara (escala en metros).

    quitar: caras omitidas ('-z', '+z', '-y', '+y', '-x', '+x') para ahorrar triángulos ocultos.
    mats: diccionario opcional cara->índice de material.
    vertical: intercambia u/v en las caras laterales (veta de madera vertical en postes).
    """
    x0, y0, z0 = minimo
    x1, y1, z1 = maximo
    # coordenadas locales (antes de la matriz) para proyectar UVs con densidad uniforme
    loc = {(i, j, k): Vector((x1 if i else x0, y1 if j else y0, z1 if k else z0))
           for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    p = {key: bm.verts.new(M @ v) for key, v in loc.items()}
    s = 1.0 / escala_uv
    caras = {
        "-z": ([(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)], lambda v: (v.x * s, v.y * s)),
        "+z": ([(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], lambda v: (v.x * s, v.y * s)),
        "-y": ([(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], lambda v: (v.x * s, v.z * s)),
        "+y": ([(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)], lambda v: (-v.x * s, v.z * s)),
        "-x": ([(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)], lambda v: (-v.y * s, v.z * s)),
        "+x": ([(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], lambda v: (v.y * s, v.z * s)),
    }
    creadas = {}
    for nombre, (claves, f_uv) in caras.items():
        if nombre in quitar:
            continue
        m = mats.get(nombre, mat) if mats else mat
        uvs = [f_uv(loc[c]) for c in claves]
        if vertical and nombre[1] != "z":
            uvs = [(v, u) for u, v in uvs]
        creadas[nombre] = _cara(bm, [p[c] for c in claves], uvs, uv, m)
    return creadas


def tubo(bm, uv, puntos, radios, lados=6, mat=0, tapas=True, v_escala=1.0, u_rep=1.0):
    """Barrido de un círculo a lo largo de una polilínea (marcos con transporte paralelo)."""
    if not isinstance(radios, (list, tuple)):
        radios = [radios] * len(puntos)
    pts = [Vector(p) for p in puntos]
    tangentes = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tangentes.append((b - a).normalized())
    ref = Vector((0, 0, 1)) if abs(tangentes[0].z) < 0.9 else Vector((1, 0, 0))
    normal = tangentes[0].cross(ref).normalized()
    anillos, vcoord = [], []
    largo = 0.0
    for i, (p, t) in enumerate(zip(pts, tangentes)):
        if i > 0:
            largo += (p - pts[i - 1]).length
            # transporte paralelo del marco
            eje = tangentes[i - 1].cross(t)
            if eje.length > 1e-6:
                ang = tangentes[i - 1].angle(t)
                normal = Matrix.Rotation(ang, 3, eje.normalized()) @ normal
        binormal = t.cross(normal).normalized()
        fila = []
        for j in range(lados):
            a = TAU * j / lados
            d = normal * math.cos(a) + binormal * math.sin(a)
            fila.append(bm.verts.new(p + d * radios[i]))
        anillos.append(fila)
        vcoord.append(largo / v_escala)
    for i in range(len(pts) - 1):
        for j in range(lados):
            j1 = (j + 1) % lados
            u0, u1 = j / lados * u_rep, (j + 1) / lados * u_rep
            _cara(bm, [anillos[i][j], anillos[i][j1], anillos[i + 1][j1], anillos[i + 1][j]],
                  [(u0, vcoord[i]), (u1, vcoord[i]), (u1, vcoord[i + 1]), (u0, vcoord[i + 1])], uv, mat)
    if tapas:
        for fila, inv in ((anillos[0], True), (anillos[-1], False)):
            vv = list(reversed(fila)) if inv else list(fila)
            uvs = [(0.5 + 0.5 * math.cos(TAU * j / lados), 0.5 + 0.5 * math.sin(TAU * j / lados)) for j in range(lados)]
            if inv:
                uvs.reverse()
            _cara(bm, vv, uvs, uv, mat)
    return anillos


def tarjeta(bm, uv, esquinas, uvs=((0, 0), (1, 0), (1, 1), (0, 1)), mat=0, div=(1, 1), deformar=None):
    """Cuadrilátero subdividido (pétalos, hojas, banderitas, alas).

    esquinas: 4 vectores en orden (inf-izq, inf-der, sup-der, sup-izq).
    deformar: función opcional f(s, t, punto) -> punto para curvar la tarjeta.
    """
    a, b, c, d = (Vector(e) for e in esquinas)
    (ua, va), (ub, vb), (uc, vc), (ud, vd) = uvs
    nx, ny = div
    grid = []
    for j in range(ny + 1):
        t = j / ny
        fila = []
        for i in range(nx + 1):
            s = i / nx
            p = (a * (1 - s) + b * s) * (1 - t) + (d * (1 - s) + c * s) * t
            if deformar:
                p = deformar(s, t, p)
            u = (ua * (1 - s) + ub * s) * (1 - t) + (ud * (1 - s) + uc * s) * t
            v = (va * (1 - s) + vb * s) * (1 - t) + (vd * (1 - s) + vc * s) * t
            fila.append((bm.verts.new(p), (u, v)))
        grid.append(fila)
    for j in range(ny):
        for i in range(nx):
            q = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
            _cara(bm, [x[0] for x in q], [x[1] for x in q], uv, mat)


def poligono_extruido(bm, uv, contorno, y0, y1, mat_frente=0, mat_lados=0, escala_uv=1.0, M=Matrix()):
    """Extruye en Y un contorno 2D (x, z) posiblemente cóncavo (p.ej. un arco).

    La cara frontal queda en y0 (mirando a -Y) y la trasera en y1.
    """
    s = 1.0 / escala_uv
    fr = [bm.verts.new(M @ Vector((x, y0, z))) for x, z in contorno]
    at = [bm.verts.new(M @ Vector((x, y1, z))) for x, z in contorno]
    n = len(contorno)
    # orientación: el contorno debe ir en sentido antihorario visto desde -Y
    area = sum(contorno[i][0] * contorno[(i + 1) % n][1] - contorno[(i + 1) % n][0] * contorno[i][1] for i in range(n))
    orden = list(range(n)) if area > 0 else list(reversed(range(n)))
    f1 = _cara(bm, [fr[i] for i in orden], [(contorno[i][0] * s, contorno[i][1] * s) for i in orden], uv, mat_frente)
    f2 = _cara(bm, [at[i] for i in reversed(orden)], [(-contorno[i][0] * s, contorno[i][1] * s) for i in reversed(orden)], uv, mat_frente)
    largo = 0.0
    for k in range(n):
        i, j = orden[k], orden[(k + 1) % n]
        seg = math.hypot(contorno[j][0] - contorno[i][0], contorno[j][1] - contorno[i][1])
        _cara(bm, [fr[j], fr[i], at[i], at[j]],
              [((largo + seg) * s, y0 * s), (largo * s, y0 * s), (largo * s, y1 * s), ((largo + seg) * s, y1 * s)],
              uv, mat_lados)
        largo += seg
    # triangulación explícita para contornos cóncavos
    bmesh.ops.triangulate(bm, faces=[f1, f2], quad_method="BEAUTY", ngon_method="EAR_CLIP")


def muro_con_huecos(bm, uv, ancho, alto, grosor, huecos, M=Matrix(), mat=0, mat_jamba=None, escala_uv=1.0):
    """Muro (plano XZ, frente en y=0, fondo en y=grosor) con vanos rectangulares.

    huecos: lista de (x0, z0, x1, z1) en coordenadas del muro (x desde -ancho/2).
    Se descompone en una retícula y se omiten las celdas dentro de un vano.
    """
    s = 1.0 / escala_uv
    xs = sorted({-ancho / 2, ancho / 2} | {h[0] for h in huecos} | {h[2] for h in huecos})
    zs = sorted({0.0, alto} | {h[1] for h in huecos} | {h[3] for h in huecos})

    def dentro(cx, cz):
        return any(h[0] < cx < h[2] and h[1] < cz < h[3] for h in huecos)

    mj = mat if mat_jamba is None else mat_jamba
    for yy, signo in ((0.0, 1), (grosor, -1)):
        for i in range(len(xs) - 1):
            for k in range(len(zs) - 1):
                cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[k] + zs[k + 1]) / 2
                if dentro(cx, cz):
                    continue
                q = [(xs[i], zs[k]), (xs[i + 1], zs[k]), (xs[i + 1], zs[k + 1]), (xs[i], zs[k + 1])]
                if signo < 0:
                    q.reverse()
                vv = [bm.verts.new(M @ Vector((x, yy, z))) for x, z in q]
                _cara(bm, vv, [(x * s * signo, z * s) for x, z in q], uv, mat)
    # cantos exteriores del muro
    caja_bordes = [
        ((-ancho / 2, 0, 0), (-ancho / 2, grosor, alto), "-x"),
        ((ancho / 2, 0, 0), (ancho / 2, grosor, alto), "+x"),
    ]
    for (xa, ya, za), (xb, yb, zb), lado in caja_bordes:
        if lado == "-x":
            q = [(xa, yb, 0), (xa, ya, 0), (xa, ya, alto), (xa, yb, alto)]
        else:
            q = [(xa, ya, 0), (xa, yb, 0), (xa, yb, alto), (xa, ya, alto)]
        vv = [bm.verts.new(M @ Vector(p)) for p in q]
        _cara(bm, vv, [(p[1] * s, p[2] * s) for p in q], uv, mat)
    q = [(-ancho / 2, 0, alto), (ancho / 2, 0, alto), (ancho / 2, grosor, alto), (-ancho / 2, grosor, alto)]
    vv = [bm.verts.new(M @ Vector(p)) for p in q]
    _cara(bm, vv, [(p[0] * s, p[1] * s) for p in q], uv, mat)
    # jambas (derrames) de cada vano
    for x0, z0, x1, z1 in huecos:
        lados = [
            ([(x0, 0, z0), (x0, grosor, z0), (x0, grosor, z1), (x0, 0, z1)]),   # izquierda (mira +x)
            ([(x1, grosor, z0), (x1, 0, z0), (x1, 0, z1), (x1, grosor, z1)]),   # derecha (mira -x)
            ([(x0, 0, z1), (x0, grosor, z1), (x1, grosor, z1), (x1, 0, z1)]),   # dintel (mira -z)
        ]
        if z0 > 1e-4:
            lados.append([(x0, grosor, z0), (x0, 0, z0), (x1, 0, z0), (x1, grosor, z0)])  # alféizar
        for q in lados:
            vv = [bm.verts.new(M @ Vector(p)) for p in q]
            _cara(bm, vv, [((p[0] + p[1]) * s, (p[2] + p[1]) * s) for p in q], uv, mj)


# ---------------------------------------------------------------------------
# Post-proceso de mallas
# ---------------------------------------------------------------------------
def soldar(bm, distancia=1e-5):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distancia)


def suavizar(bm, angulo=40.0):
    """Sombreado suave con aristas duras donde el ángulo diedro supera el umbral."""
    lim = math.radians(angulo)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if e.is_manifold:
            e.smooth = e.calc_face_angle(0.0) <= lim


def plano(bm):
    for f in bm.faces:
        f.smooth = False


def biselar(bm, ancho, segmentos=1, aristas=None):
    aristas = aristas if aristas is not None else [e for e in bm.edges]
    bmesh.ops.bevel(bm, geom=aristas, offset=ancho, segments=segmentos, affect="EDGES",
                    profile=0.5, clamp_overlap=True)


def uv_esferica(bm, uv, centro=(0, 0, 0), u_rep=1.0, faces=None):
    """Proyección esférica (u=0.5 al frente) con corrección de la costura."""
    c = Vector(centro)
    for f in (faces if faces is not None else bm.faces):
        us = []
        for loop in f.loops:
            d = (loop.vert.co - c)
            d = d.normalized() if d.length > 1e-9 else Vector((0, -1, 0))
            u = (math.atan2(d.y, d.x) + 1.5 * math.pi) / TAU % 1.0
            v = 0.5 + math.asin(max(-1, min(1, d.z))) / math.pi
            us.append([u, v])
        # si la cara cruza la costura (u de 0 a 1) se desplazan los u pequeños
        if max(x[0] for x in us) - min(x[0] for x in us) > 0.5:
            for x in us:
                if x[0] < 0.5:
                    x[0] += 1.0
        for loop, (u, v) in zip(f.loops, us):
            loop[uv].uv = (u * u_rep, v)


def uv_plana(bm, uv, eje="y", escala=1.0, offset=(0, 0), faces=None):
    s = 1.0 / escala
    for f in (faces if faces is not None else bm.faces):
        for loop in f.loops:
            p = loop.vert.co
            if eje == "y":
                loop[uv].uv = (p.x * s + offset[0], p.z * s + offset[1])
            elif eje == "x":
                loop[uv].uv = (p.y * s + offset[0], p.z * s + offset[1])
            else:
                loop[uv].uv = (p.x * s + offset[0], p.y * s + offset[1])


# ---------------------------------------------------------------------------
# Elementos reutilizables
# ---------------------------------------------------------------------------
def flama(bm, uv, M=Matrix(), alto=0.035, radio=0.009, mat=0):
    """Llama en forma de gota (revolución de 6 lados)."""
    perfil = [(0.0, 0.0), (radio * 0.7, alto * 0.12), (radio, alto * 0.35), (radio * 0.75, alto * 0.6),
              (radio * 0.3, alto * 0.85), (0.0, alto)]
    torno(bm, uv, perfil, 6, M=M, mat=mat)


ANILLOS_FLOR = (  # (pétalos, largo relativo, elevación en grados, radio interno relativo, altura relativa)
    (12, 1.00, -4, 0.30, 0.00),
    (11, 0.95, 24, 0.24, 0.18),
    (9, 0.85, 48, 0.17, 0.40),
    (7, 0.70, 70, 0.08, 0.58),
)
ANILLOS_FLOR_LIGERA = (
    (9, 1.00, 10, 0.28, 0.00),
    (7, 0.85, 42, 0.18, 0.30),
    (5, 0.70, 68, 0.07, 0.55),
)


def flor_cempasuchil(bm, uv, M=Matrix(), radio=0.045, mat_petalo=0, mat_centro=None, semilla=0,
                     anillos=ANILLOS_FLOR, div=(2, 1)):
    """Cabeza de cempasúchil: anillos de pétalos en copa alrededor de un centro.

    Cada pétalo es una tarjeta doblada en "V" (4 triángulos); los anillos
    interiores se elevan para formar el pompón característico de la flor.
    """
    rnd = random.Random(semilla)
    mc = mat_petalo if mat_centro is None else mat_centro
    arriba = Vector((0, 0, 1))
    for n, largo, elev, r0, z0 in anillos:
        desfase = rnd.random() * TAU
        for k in range(n):
            th = desfase + TAU * k / n + rnd.uniform(-0.15, 0.15)
            L = radio * largo * rnd.uniform(0.9, 1.1)
            e = math.radians(elev + rnd.uniform(-7, 7))
            d = Vector((math.cos(th), math.sin(th), 0.0))
            lado = Vector((-math.sin(th), math.cos(th), 0.0))
            base = d * radio * r0 + arriba * radio * z0
            dirp = d * math.cos(e) + arriba * math.sin(e)
            w = L * 0.78
            punta = base + dirp * L
            normal = dirp.cross(lado).normalized()  # cara interior del pétalo (hacia afuera de la flor)

            def copa(s, t, p, normal=normal, w=w):
                # los bordes del pétalo se levantan (forma de cuchara)
                return p + normal * ((abs(s - 0.5) * 2) ** 2 * w * 0.22)

            esquinas = [base + lado * w * 0.30, base - lado * w * 0.30,
                        punta - lado * w * 0.5, punta + lado * w * 0.5]
            tarjeta(bm, uv, [M @ q for q in esquinas], mat=mat_petalo, div=div,
                    deformar=lambda s, t, p, f=copa: M @ f(s, t, M.inverted() @ p))
    # centro: botón bajo
    h = anillos[-1][4] * radio
    perfil = [(radio * 0.20, h), (radio * 0.12, h + radio * 0.12), (0.0, h + radio * 0.18)]
    torno(bm, uv, perfil, 6, M=M, mat=mc, v_rango=(0.05, 0.25))


def pompon(bm, uv, M=Matrix(), radio=0.05, mat=0, semilla=0, seg=7, anillos=5):
    """Flor esquemática de bajo costo (esfera irregular) para arcos y coronas."""
    rnd = random.Random(semilla)
    perfil = []
    for i in range(anillos + 1):
        t = i / anillos
        a = -math.pi / 2 + math.pi * t
        r = math.cos(a) * radio
        z = (math.sin(a) + 1) * radio * 0.85
        perfil.append((r, z))
    filas = torno(bm, uv, perfil, seg, M=M, mat=mat, v_rango=(0.15, 1.0), u_rep=2.0)
    for fila in filas[1:-1]:
        for v in fila:
            v.co += (v.co - (M @ Vector((0, 0, radio * 0.85)))) * rnd.uniform(-0.12, 0.18)


# ---------------------------------------------------------------------------
# Exportación y renders de vista previa
# ---------------------------------------------------------------------------
def jerarquia(raiz):
    return [raiz] + list(raiz.children_recursive)


def guardar_blend(nombre):
    os.makedirs(SALIDA_BLEND, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0  # sin respaldos .blend1
    ruta = os.path.join(SALIDA_BLEND, nombre + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=ruta, compress=True, relative_remap=True)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile(compress=True)
    return ruta


def exportar_gltf(raiz, nombre):
    os.makedirs(SALIDA_GLTF, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in jerarquia(raiz):
        ob.select_set(True)
    ruta = os.path.join(SALIDA_GLTF, nombre + ".gltf")
    bpy.ops.export_scene.gltf(
        filepath=ruta, export_format="GLTF_SEPARATE", export_keep_originals=True,
        use_selection=True, export_apply=True, export_yup=True,
        export_texcoords=True, export_normals=True, export_tangents=False,
        export_materials="EXPORT", export_cameras=False, export_lights=False,
        export_animations=False, export_extras=False, export_copyright="Equipo Camino de Cempasúchil - FI UNAM",
    )
    return ruta


def _limites(objs):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for ob in objs:
        if ob.type != "MESH":
            continue
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            mn = Vector((min(mn[i], w[i]) for i in range(3)))
            mx = Vector((max(mx[i], w[i]) for i in range(3)))
    return mn, mx


def render_preview(raiz, nombre, malla=False, tam=640, azimut=-35.0, elevacion=22.0, muestras=24, sombra=True):
    """Render de Cycles con fondo transparente y captador de sombras.

    malla=True genera la versión "arcilla + alambre" para documentar la topología.
    """
    os.makedirs(SALIDA_RENDER, exist_ok=True)
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    objs = jerarquia(raiz)
    mn, mx = _limites(objs)
    centro = (mn + mx) / 2
    radio = max((mx - mn).length / 2, 0.01)
    temporales = []

    # cámara
    cam_data = bpy.data.cameras.new("cam_preview")
    cam_data.lens = 50
    cam = bpy.data.objects.new("cam_preview", cam_data)
    sc.collection.objects.link(cam)
    temporales.append(cam)
    fov = 2 * math.atan(18 / cam_data.lens)
    dist = radio / math.sin(fov / 2) * 1.08
    cam_data.clip_start = dist * 0.01
    cam_data.clip_end = dist * 20
    az, el = math.radians(azimut), math.radians(elevacion)
    direc = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cam.location = centro + direc * dist
    cam.rotation_euler = (-direc).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam

    # luces: principal cálida, relleno frío y contraluz
    def luz(nombre_l, tipo, energia, color, rot):
        ld = bpy.data.lights.new(nombre_l, tipo)
        ld.energy = energia
        ld.color = color
        if tipo == "SUN":
            ld.angle = math.radians(8)
        lo = bpy.data.objects.new(nombre_l, ld)
        lo.rotation_euler = [math.radians(a) for a in rot]
        sc.collection.objects.link(lo)
        temporales.append(lo)

    luz("sol_clave", "SUN", 3.2, (1.0, 0.95, 0.88), (50, 0, -35))
    luz("sol_relleno", "SUN", 0.9, (0.75, 0.82, 1.0), (60, 0, 120))
    luz("sol_contra", "SUN", 1.4, (1.0, 1.0, 1.0), (60, 0, 200))

    # piso captador de sombras
    bm, uvl = nuevo_bm()
    s = radio * 8
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=s)
    piso = objeto("piso_preview", bm, [])
    piso.location = (centro.x, centro.y, mn.z - radio * 0.01)
    piso.is_shadow_catcher = True
    piso.hide_render = not sombra
    temporales.append(piso)

    # mundo
    mundo = bpy.data.worlds.new("mundo_preview")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.32, 0.33, 0.36, 1)
    mundo.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    sc.world = mundo

    # versión arcilla + alambre
    originales = {}
    if malla:
        arcilla = material("_arcilla", color=(0.78, 0.76, 0.72), rugosidad=0.9)
        alambre = material("_alambre", color=(0.02, 0.02, 0.025), rugosidad=0.6)
        for ob in objs:
            if ob.type != "MESH":
                continue
            originales[ob.name] = [m for m in ob.data.materials]
            for i in range(len(ob.data.materials)):
                ob.data.materials[i] = arcilla
            dup = ob.copy()
            dup.data = ob.data.copy()
            for i in range(len(dup.data.materials)):
                dup.data.materials[i] = alambre
            sc.collection.objects.link(dup)
            mod = dup.modifiers.new("alambre", "WIREFRAME")
            mod.thickness = radio * 0.006
            mod.use_relative_offset = False
            mod.use_even_offset = True
            temporales.append(dup)

    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = muestras
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x = tam
    sc.render.resolution_y = tam
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    sufijo = "_malla" if malla else ""
    sc.render.filepath = os.path.join(SALIDA_RENDER, nombre + sufijo + ".png")
    bpy.ops.render.render(write_still=True)

    # limpieza (la escena guardada no conserva cámara ni luces de vista previa)
    for nombre_o, mats in originales.items():
        ob = bpy.data.objects[nombre_o]
        for i, m in enumerate(mats):
            ob.data.materials[i] = m
    for ob in temporales:
        bpy.data.objects.remove(ob, do_unlink=True)
    return sc.render.filepath
