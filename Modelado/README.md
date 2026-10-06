# Modelado (entrega 2)

Los 18 modelos propios se construyen con *scripts* de Python para Blender (modelado procedural con
`bpy` y `bmesh`). Así cada modelo es reproducible, se puede ajustar cambiando parámetros
(dimensiones, número de lados, pétalos, etc.) y el historial de cambios queda en Git.

```
Modelado/
├── scripts/
│   ├── mx.py                    utilidades: torno, cajas, tubos, extrusión de contornos,
│   │                            muros con vanos, UVs, materiales glTF, exportación y renders
│   ├── modelos/                 un script por modelo (función construir())
│   ├── construir_modelos.py     construye, guarda .blend, exporta glTF y renderiza
│   ├── generar_texturas.py      texturas propias (Python + Pillow + numpy)
│   ├── preparar_texturas_cc0.py texturas de Poly Haven reducidas a 512 px
│   ├── generar_skybox.py        HDRI equirectangular -> 6 caras del cube map
│   ├── inventario_modelos.py    tabla de triángulos, vértices, nodos y texturas
│   └── preparar_figuras.py      figuras de los modelos para la documentación
├── blend/                       archivo .blend de cada modelo (abrir con Blender 5.2)
└── render/                      vistas previas (se regeneran, no se versionan)
```

## Regenerar los modelos

Requiere **Blender 5.2** (la misma versión con la que se guardó el prototipo).

```bash
# todos los modelos (geometría, .blend, glTF y vistas previas)
blender -b --factory-startup -P Modelado/scripts/construir_modelos.py

# solo algunos, sin vistas previas
blender -b --factory-startup -P Modelado/scripts/construir_modelos.py -- altar_muertos farol --sin-render
```

En Windows, `blender` es `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"`.

## Convenciones

- Unidades en metros; en Blender Z apunta hacia arriba y el frente del modelo mira a −Y.
  El exportador glTF convierte a Y arriba, así que en OpenGL el frente queda hacia +Z.
- El origen del objeto raíz está en el centro de la base (el modelo se apoya en el suelo).
- Las piezas que se animarán tienen su propio nodo y su pivote en la articulación
  (alas, banderitas, hojas de la reja, puerta, brazo y lámpara del farol, flamas).
- Las texturas se referencian desde `assets/textures/` (glTF con texturas externas), así que
  varios modelos comparten el mismo archivo sin duplicarlo.
- Todas las caras tienen coordenadas UV; los materiales usan el modelo PBR de glTF
  (color base, metálico, rugosidad, emisión y modo alfa).
