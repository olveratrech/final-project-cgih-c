# Matriz de requisitos del documento de especificaciones

Seguimiento de cada punto del documento *Especificaciones del Proyecto Final 2027-1* y su estado
al cierre de la **entrega 2 (Modelado, 13 de octubre de 2026)**.

Simbología: ✅ cumplido · 🟡 avance parcial / base preparada · ⬜ pendiente (entrega indicada)

## Lineamientos

| # | Lineamiento | Estado | Evidencia |
|---|---|---|---|
| 1 | Equipo de hasta 4 integrantes | ✅ | 4 integrantes (`README.md`) |
| 2 | Tema con despliegue de datos en 3D; prototipo con diseño, modelado geométrico, modelado jerárquico y transformaciones geométricas | ✅ | [Entrega 2](entrega2_modelado.md), secciones 3, 5, 7 y 8 |
| 3 | Color, iluminación, sombreado, texturizado y animación con OpenGL 3+ y GLSL | 🟡 | OpenGL 3.3 core + GLSL 3.30; texturas y skybox listos; iluminación difusa básica. Phong/Fresnel en entrega 3, animación en entrega 4 |
| 3a | Al menos dos técnicas de iluminación (p. ej. Phong y Fresnel) | ⬜ 3 | Materiales con metálico/rugosidad/alfa ya exportados |
| 3b | Texturizado de ambiente (cube mapping, etc.) | ✅ | Skybox con cube map: `src/render/Skybox.cpp`, `assets/skybox/atardecer/` |
| 3c | Animaciones con jerarquías: básica, por keyframes y procedural | ⬜ 4 | Modelos con pivotes y nodos articulados (sección 7) |

## Requisitos mínimos del proyecto

| Requisito | Mínimo | Estado | Evidencia |
|---|---:|---|---|
| Modelos 3D de librerías o modelados | 8 | ✅ 25 | Kenney *Graveyard Kit* (CC0), `assets/models/libreria/` |
| Modelos creados por participantes | 8 | ✅ 18 | `Modelado/scripts/modelos/`, `Modelado/blend/`, `assets/models/propios/` |
| Interacciones con luces en tiempo real | 2 | ⬜ 3 | Flamas como nodos propios (veladoras, cirios, faroles) |
| Texturizado (skybox) | 1 | ✅ | Cube map de 6 caras |
| Texturizado demostrable en los modelos propios | 8 | ✅ 18 | Todos con UVs y textura (16 texturas propias + 8 CC0) |
| Animaciones de huesos | 2 | ⬜ 4 | Personajes de Kenney con animaciones; mariposa articulada |
| Animaciones por código | 3 | ⬜ 4 | Pivotes: alas, banderitas, flamas, faroles |
| Animaciones creadas en software externo | 3 | ⬜ 4 | Blender con *scripts* (exportación glTF con *keyframes*) |
| Interacción con animaciones a partir de input | 8 | 🟡 4 | Teclado/ratón ya conectados al grafo de escena (transformaciones interactivas) |
| Temática: México y su cultura | — | ✅ | Día de Muertos: ofrenda, camino de cempasúchil, panteón |

## Metodología basada en prototipos

| Fase | Estado | Evidencia |
|---|---|---|
| 1. Requisitos y planificación (tema, alcance, herramientas) | ✅ | Entrega 2: secciones 2 y 4 |
| 2. Diseño conceptual (bocetos, wireframes, gráficos, flujo de interacción) | ✅ | Entrega 2: sección 3 (Figuras 2 a 4) |
| 3. Prototipo inicial y pruebas internas | ✅ | Programa funcional; entrega 2: sección 11 |
| 4. Validación con usuarios y retroalimentación | ⬜ | Después de la entrega 3 |
| 5. Iteración y mejoras | ⬜ | Entregas 3 y 4 |
| 6. Implementación completa y pruebas del sistema | ⬜ | Versión final |
| 7. Validación final y entrega | ⬜ | Versión final |

## Entregables finales

| Entregable | Peso | Estado |
|---|---:|---|
| Software funcional (.exe empaquetado con InstallForge, `readme.txt` de instalación y uso) | 60 % | 🟡 El programa compila en Windows (CMake/Visual Studio) y genera el .exe con `assets/`, `shaders/` y `readme.txt`; falta el instalador |
| Código fuente en GitHub | — | ✅ Este repositorio |
| Reporte en español (20-35 páginas, portada, hoja de evidencias, resumen, introducción con citas, metodología, experimentos, resultados, conclusiones individuales, referencias APA) | 10 % | 🟡 Insumos: [entrega2_modelado.md](entrega2_modelado.md) (figuras y tablas tituladas y referenciadas) |
| Reporte en inglés | 10 % | ⬜ |
| Video demostrativo (3-5 min) | 10 % | ⬜ El modo sin interfaz (`F4`) y las vistas predefinidas facilitan la grabación |
| Presentación oral y digital | 10 % | ⬜ |
