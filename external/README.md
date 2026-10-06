# Bibliotecas de terceros

Se incluyen en el repositorio para compilar sin conexión a internet y con las mismas versiones en
todos los equipos del equipo.

| Biblioteca | Versión | Uso | Licencia | Contenido incluido |
|---|---|---|---|---|
| [GLFW](https://www.glfw.org) | 3.4 | Ventana, contexto OpenGL y entrada | zlib/libpng (`glfw/LICENSE.md`) | `CMakeLists.txt`, `CMake/`, `include/`, `src/`, `deps/mingw`, `deps/wayland` (sin documentación, ejemplos ni pruebas) |
| [GLAD](https://github.com/Dav1dde/glad) | 0.1.36 (generador) | Cargador de funciones OpenGL 3.3 core **sin extensiones** (108 KB en lugar de 915 KB con todas) | Generador MIT; especificación de Khronos Apache 2.0; `khrplatform.h` con licencia tipo MIT de Khronos (`glad/LICENSE`) | `glad/include`, `glad/src` |
| [GLM](https://github.com/g-truc/glm) | 1.0.1 | Matemáticas (vectores, matrices, cuaterniones) | Happy Bunny / MIT (`glm/copying.txt`) | Solo encabezados (`glm/glm`) |
| [cgltf](https://github.com/jkuhlmann/cgltf) | 1.15 | Lectura de modelos glTF 2.0 (.gltf/.glb) | MIT (al final de `cgltf.h`) | `cgltf/cgltf.h` |
| [stb_image](https://github.com/nothings/stb) | 2.30 | Decodificación de PNG y JPEG | MIT o dominio público | `stb/stb_image.h` |
| [stb_image_write](https://github.com/nothings/stb) | 1.16 | Capturas de pantalla en PNG | MIT o dominio público | `stb/stb_image_write.h` |
| [Dear ImGui](https://github.com/ocornut/imgui) | 1.91.9b | Interfaz gráfica de usuario | MIT (`imgui/LICENSE.txt`) | Núcleo y respaldos GLFW + OpenGL 3 |

Las fuentes de GLFW 3.4 y GLM 1.0.1 se tomaron de los paquetes fuente de Ubuntu
(`glfw3_3.4.orig.tar.gz`, `glm_1.0.1+ds.orig.tar.xz`) y se verificaron con las sumas SHA-256
publicadas en sus archivos `.dsc`.
