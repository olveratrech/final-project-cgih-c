"""
Construye todos los modelos propios del proyecto dentro de Blender.

Por cada modelo de Modelado/scripts/modelos/:
  1. Genera la geometría procedural (bmesh) con UVs, materiales y jerarquía.
  2. Guarda el archivo fuente  Modelado/blend/<modelo>.blend
  3. Exporta a glTF 2.0        assets/models/propios/<modelo>.gltf (+ .bin)
  4. Renderiza vistas previas  Modelado/render/<modelo>.png y <modelo>_malla.png

Uso:
    blender -b --factory-startup -P Modelado/scripts/construir_modelos.py
    blender -b --factory-startup -P Modelado/scripts/construir_modelos.py -- altar_muertos veladora
    (agregar --sin-render para omitir las vistas previas)
"""
import importlib
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mx  # noqa: E402

MODELOS = [
    "altar_muertos",
    "arco_cempasuchil",
    "flor_cempasuchil",
    "petalo_cempasuchil",
    "veladora",
    "cirio",
    "pan_de_muerto",
    "calaverita_azucar",
    "papel_picado",
    "sahumerio",
    "portarretrato",
    "jarron_talavera",
    "vaso_agua",
    "maceta_cempasuchil",
    "mariposa_monarca",
    "farol",
    "entrada_panteon",
    "casa_adobe",
]


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sin_render = "--sin-render" in args
    elegidos = [a for a in args if not a.startswith("--")] or MODELOS
    for nombre in elegidos:
        t0 = time.time()
        mod = importlib.import_module("modelos." + nombre)
        mx.reiniciar()
        raiz = mod.construir()
        mx.guardar_blend(nombre)
        mx.exportar_gltf(raiz, nombre)
        if not sin_render:
            mx.render_preview(raiz, nombre, malla=False, **getattr(mod, "VISTA", {}))
            mx.render_preview(raiz, nombre, malla=True, **getattr(mod, "VISTA", {}))
        print(f"[modelo] {nombre:22s} listo en {time.time() - t0:5.1f} s")


if __name__ == "__main__":
    main()
