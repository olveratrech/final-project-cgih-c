// Camino de Cempasúchil - Proyecto final de Computación Gráfica e Interacción
// Humano-Computadora, Facultad de Ingeniería, UNAM (semestre 2027-1).
//
// Opciones de línea de comandos (útiles para generar las figuras del reporte):
//   --ancho N --alto N      tamaño de la ventana
//   --vista N               vista inicial (1..7)
//   --galeria CLAVE         abre la galería con un modelo (p. ej. altar_muertos)
//   --seleccion NOMBRE      selecciona un nodo de la escena al iniciar
//   --alambre               inicia en modo de malla de alambre
//   --sin-interfaz          oculta los paneles
//   --msaa N                muestras de antialiasing (0 lo desactiva)
//   --captura ARCHIVO.png   dibuja unos cuadros, guarda la imagen y termina
#include "App.h"
#include "Registro.h"
#include "Rutas.h"

#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <string>

int main(int argc, char** argv) {
    Opciones op;
    for (int i = 1; i < argc; ++i) {
        auto siguiente = [&](const char* nombre) -> const char* {
            if (std::strcmp(argv[i], nombre) == 0 && i + 1 < argc) return argv[++i];
            return nullptr;
        };
        if (const char* v = siguiente("--ancho")) op.ancho = std::atoi(v);
        else if (const char* v2 = siguiente("--alto")) op.alto = std::atoi(v2);
        else if (const char* v3 = siguiente("--vista")) op.vista = std::atoi(v3);
        else if (const char* v4 = siguiente("--galeria")) op.galeria = v4;
        else if (const char* v5 = siguiente("--seleccion")) op.seleccion = v5;
        else if (const char* v6 = siguiente("--captura")) op.captura = v6;
        else if (const char* v7 = siguiente("--cuadros")) op.frames = std::atoi(v7);
        else if (const char* v8 = siguiente("--msaa")) op.msaa = std::atoi(v8);
        else if (std::strcmp(argv[i], "--alambre") == 0) op.alambre = true;
        else if (std::strcmp(argv[i], "--sin-interfaz") == 0) op.sinInterfaz = true;
    }

    if (!rutas::inicializar(argc > 0 ? argv[0] : nullptr)) {
        registro::fatal("No se encontraron las carpetas assets/ y shaders/ junto al programa.");
        return 1;
    }
    registro::abrir((std::filesystem::u8path(rutas::base()) / "registro.txt").u8string());
    registro::info("Carpeta base: %s", rutas::base().c_str());

    App app;
    int codigo = app.ejecutar(op);
    registro::cerrar();
    return codigo;
}
