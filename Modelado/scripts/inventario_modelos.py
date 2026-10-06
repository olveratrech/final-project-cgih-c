"""
Inventario de modelos glTF: triángulos, vértices, materiales, texturas y nodos.

Lee los archivos exportados (no los .blend), así que las cifras son las que
realmente se envían a la GPU. Genera una tabla en Markdown para la
documentación.

Uso:
    python Modelado/scripts/inventario_modelos.py > docs/inventario_modelos.md
"""
import glob
import json
import os
import struct

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def leer_gltf(ruta):
    if ruta.endswith(".glb"):
        datos = open(ruta, "rb").read()
        largo = struct.unpack("<I", datos[12:16])[0]
        return json.loads(datos[20:20 + largo]), len(datos)
    j = json.load(open(ruta, encoding="utf-8"))
    tam = os.path.getsize(ruta)
    for b in j.get("buffers", []):
        if "uri" in b and not b["uri"].startswith("data:"):
            tam += os.path.getsize(os.path.join(os.path.dirname(ruta), b["uri"]))
    return j, tam


def estadisticas(ruta):
    j, tam = leer_gltf(ruta)
    tris = verts = prims = 0
    for m in j.get("meshes", []):
        for p in m["primitives"]:
            prims += 1
            n = j["accessors"][p["attributes"]["POSITION"]]["count"]
            verts += n
            tris += (j["accessors"][p["indices"]]["count"] if "indices" in p else n) // 3
    imgs = sorted({os.path.basename(i.get("uri", i.get("name", "embebida"))) for i in j.get("images", [])})
    return {
        "archivo": os.path.basename(ruta),
        "triangulos": tris,
        "vertices": verts,
        "primitivas": prims,
        "materiales": len(j.get("materials", [])),
        "nodos": len(j.get("nodes", [])),
        "texturas": imgs,
        "kb": tam / 1024.0,
    }


def tabla(carpeta, titulo):
    filas = [estadisticas(r) for r in sorted(glob.glob(os.path.join(carpeta, "*.gl*")))
             if r.endswith((".gltf", ".glb"))]
    print(f"\n### {titulo}\n")
    print("| Modelo | Triángulos | Vértices | Nodos | Materiales | Texturas | Tamaño (KB) |")
    print("|---|---:|---:|---:|---:|---|---:|")
    for f in filas:
        print(f"| {f['archivo']} | {f['triangulos']} | {f['vertices']} | {f['nodos']} | {f['materiales']} | "
              f"{', '.join(f['texturas']) or '—'} | {f['kb']:.1f} |")
    tot_t = sum(f["triangulos"] for f in filas)
    tot_v = sum(f["vertices"] for f in filas)
    print(f"| **Total ({len(filas)} modelos)** | **{tot_t}** | **{tot_v}** | | | | "
          f"**{sum(f['kb'] for f in filas):.1f}** |")
    return filas


if __name__ == "__main__":
    tabla(os.path.join(RAIZ, "assets", "models", "propios"), "Modelos propios")
    lib = os.path.join(RAIZ, "assets", "models", "libreria")
    for sub in sorted(glob.glob(os.path.join(lib, "*"))):
        if os.path.isdir(sub):
            tabla(sub, "Librería: " + os.path.basename(sub))
