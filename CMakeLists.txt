cmake_minimum_required(VERSION 3.16...3.31)

project(CaminoCempasuchil
    VERSION 0.2.0
    DESCRIPTION "Camino de Cempasuchil - Proyecto final CGeIHC, FI UNAM"
    LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Tipo de compilación" FORCE)
endif()

# En Windows se enlaza el runtime de MSVC de forma estática para que el .exe
# funcione en equipos sin el paquete redistribuible de Visual C++.
if(MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif()

# --------------------------------------------------------------------------
# Dependencias (incluidas en external/, no requieren conexión a internet)
# --------------------------------------------------------------------------
set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(GLFW_INSTALL OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_WAYLAND OFF CACHE BOOL "" FORCE)
set(USE_MSVC_RUNTIME_LIBRARY_DLL OFF CACHE BOOL "" FORCE)
add_subdirectory(external/glfw EXCLUDE_FROM_ALL)

add_library(glad STATIC external/glad/src/glad.c)
target_include_directories(glad PUBLIC external/glad/include)

add_library(imgui STATIC
    external/imgui/imgui.cpp
    external/imgui/imgui_draw.cpp
    external/imgui/imgui_tables.cpp
    external/imgui/imgui_widgets.cpp
    external/imgui/backends/imgui_impl_glfw.cpp
    external/imgui/backends/imgui_impl_opengl3.cpp)
target_include_directories(imgui PUBLIC external/imgui external/imgui/backends)
target_link_libraries(imgui PUBLIC glfw)

# --------------------------------------------------------------------------
# Programa
# --------------------------------------------------------------------------
add_executable(CaminoCempasuchil
    src/main.cpp
    src/App.cpp
    src/Interfaz.cpp
    src/Registro.cpp
    src/Rutas.cpp
    src/render/Shader.cpp
    src/render/Texture.cpp
    src/render/Model.cpp
    src/render/Renderer.cpp
    src/render/Skybox.cpp
    src/scene/Camera.cpp
    src/scene/SceneNode.cpp
    src/scene/Camino.cpp
    src/scene/Escena.cpp
    src/bibliotecas.cpp)

target_include_directories(CaminoCempasuchil PRIVATE
    src
    external/glm
    external/cgltf
    external/stb)

target_link_libraries(CaminoCempasuchil PRIVATE glfw glad imgui)
target_compile_definitions(CaminoCempasuchil PRIVATE GLM_ENABLE_EXPERIMENTAL)

if(MSVC)
    target_compile_options(CaminoCempasuchil PRIVATE /W3 /utf-8)
    target_compile_definitions(CaminoCempasuchil PRIVATE _CRT_SECURE_NO_WARNINGS NOMINMAX)
    # aplicación de ventana (sin consola); los mensajes se guardan en registro.txt
    set_target_properties(CaminoCempasuchil PROPERTIES
        WIN32_EXECUTABLE TRUE
        VS_DEBUGGER_WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}")
    target_link_options(CaminoCempasuchil PRIVATE /ENTRY:mainCRTStartup)
else()
    target_compile_options(CaminoCempasuchil PRIVATE -Wall -Wextra -Wno-unused-parameter)
    if(WIN32)
        target_link_options(CaminoCempasuchil PRIVATE -mwindows -static)
    endif()
endif()

# Las bibliotecas de un solo encabezado se compilan sin advertencias (código de terceros)
if(MSVC)
    set_source_files_properties(src/bibliotecas.cpp PROPERTIES COMPILE_OPTIONS "/W0")
else()
    set_source_files_properties(src/bibliotecas.cpp PROPERTIES COMPILE_OPTIONS "-w")
endif()

# Copia assets/ y shaders/ junto al ejecutable para que la carpeta de salida
# se pueda empaquetar directamente (InstallForge).
add_custom_command(TARGET CaminoCempasuchil POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/assets $<TARGET_FILE_DIR:CaminoCempasuchil>/assets
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/shaders $<TARGET_FILE_DIR:CaminoCempasuchil>/shaders
    COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_SOURCE_DIR}/readme.txt $<TARGET_FILE_DIR:CaminoCempasuchil>/readme.txt
    COMMENT "Copiando assets, shaders y readme.txt junto al ejecutable")
