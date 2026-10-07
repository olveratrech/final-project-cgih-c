// Texture.h - Carga de texturas con caché: cada archivo se sube a la GPU una sola vez
// aunque lo usen varios modelos (p. ej. la paleta colormap.png de Kenney o el
// pétalo de cempasúchil que comparten la flor, el arco, la maceta y el camino).
#pragma once

#include <glad/glad.h>

#include <memory>
#include <string>
#include <unordered_map>

struct Textura {
    GLuint id = 0;
    int ancho = 0, alto = 0, canales = 0;
    size_t bytes = 0;  // memoria estimada en GPU (incluye mipmaps)
    std::string ruta;
};

class CacheTexturas {
public:
    // srgb = true para mapas de color (se convierten a espacio lineal al muestrear).
    const Textura* cargar(const std::string& ruta, bool srgb = true, bool cercano = false);
    const Textura* desdeMemoria(const std::string& clave, const unsigned char* datos, int largo, bool srgb = true);
    // Cube map a partir de una carpeta con px, nx, py, ny, pz, nz (.jpg o .png).
    GLuint cubemap(const std::string& carpeta, size_t* bytes = nullptr);

    size_t bytesGPU() const;
    int cantidad() const { return static_cast<int>(texturas_.size()); }
    void liberar();
    ~CacheTexturas() { liberar(); }

private:
    const Textura* subir(const std::string& clave, unsigned char* pixeles, int w, int h, int c, bool srgb, bool cercano);
    std::unordered_map<std::string, std::unique_ptr<Textura>> texturas_;
    std::unordered_map<std::string, GLuint> cubos_;
    size_t bytesCubos_ = 0;
};
