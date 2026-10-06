#include "render/Texture.h"

#include "Registro.h"

#include <stb_image.h>

#include <filesystem>

namespace fs = std::filesystem;

static std::string normalizar(const std::string& ruta) {
    std::error_code ec;
    fs::path p = fs::weakly_canonical(fs::u8path(ruta), ec);
    return ec ? ruta : p.u8string();
}

// Lee una imagen admitiendo rutas UTF-8 con acentos también en Windows.
static unsigned char* leerImagen(const std::string& ruta, int* w, int* h, int* c, int deseados) {
#ifdef _WIN32
    FILE* f = _wfopen(fs::u8path(ruta).wstring().c_str(), L"rb");
    if (!f) return nullptr;
    unsigned char* px = stbi_load_from_file(f, w, h, c, deseados);
    fclose(f);
    return px;
#else
    return stbi_load(ruta.c_str(), w, h, c, deseados);
#endif
}

const Textura* CacheTexturas::cargar(const std::string& ruta, bool srgb, bool cercano) {
    const std::string clave = normalizar(ruta);
    auto it = texturas_.find(clave);
    if (it != texturas_.end()) return it->second.get();

    int w = 0, h = 0, c = 0;
    // glTF define el origen UV en la esquina superior izquierda, igual que el
    // orden de filas de stb_image, por eso NO se invierte la imagen.
    stbi_set_flip_vertically_on_load(0);
    unsigned char* px = leerImagen(clave, &w, &h, &c, 0);
    if (!px) {
        registro::error("No se pudo cargar la textura %s (%s)", ruta.c_str(), stbi_failure_reason());
        return nullptr;
    }
    const Textura* t = subir(clave, px, w, h, c, srgb, cercano);
    stbi_image_free(px);
    return t;
}

const Textura* CacheTexturas::desdeMemoria(const std::string& clave, const unsigned char* datos, int largo, bool srgb) {
    auto it = texturas_.find(clave);
    if (it != texturas_.end()) return it->second.get();
    int w = 0, h = 0, c = 0;
    unsigned char* px = stbi_load_from_memory(datos, largo, &w, &h, &c, 0);
    if (!px) {
        registro::error("No se pudo decodificar la textura embebida %s", clave.c_str());
        return nullptr;
    }
    const Textura* t = subir(clave, px, w, h, c, srgb, false);
    stbi_image_free(px);
    return t;
}

const Textura* CacheTexturas::subir(const std::string& clave, unsigned char* px, int w, int h, int c, bool srgb,
                                    bool cercano) {
    GLenum formato = c == 4 ? GL_RGBA : c == 3 ? GL_RGB : c == 2 ? GL_RG : GL_RED;
    GLenum interno;
    if (c == 4) interno = srgb ? GL_SRGB8_ALPHA8 : GL_RGBA8;
    else if (c == 3) interno = srgb ? GL_SRGB8 : GL_RGB8;
    else if (c == 2) interno = GL_RG8;
    else interno = GL_R8;

    auto t = std::make_unique<Textura>();
    t->ancho = w;
    t->alto = h;
    t->canales = c;
    t->ruta = clave;
    glGenTextures(1, &t->id);
    glBindTexture(GL_TEXTURE_2D, t->id);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glTexImage2D(GL_TEXTURE_2D, 0, static_cast<GLint>(interno), w, h, 0, formato, GL_UNSIGNED_BYTE, px);
    glGenerateMipmap(GL_TEXTURE_2D);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, cercano ? GL_NEAREST_MIPMAP_LINEAR : GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, cercano ? GL_NEAREST : GL_LINEAR);
    if (c == 1) {  // escala de grises: se replica en RGB
        GLint swz[4] = {GL_RED, GL_RED, GL_RED, GL_ONE};
        glTexParameteriv(GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_RGBA, swz);
    }
    glBindTexture(GL_TEXTURE_2D, 0);
    // tamaño estimado: base * 4/3 por la cadena de mipmaps
    t->bytes = static_cast<size_t>(w) * h * (c == 3 ? 4 : c) * 4 / 3;
    Textura* ptr = t.get();
    texturas_.emplace(clave, std::move(t));
    return ptr;
}

GLuint CacheTexturas::cubemap(const std::string& carpeta, size_t* bytes) {
    auto it = cubos_.find(carpeta);
    if (it != cubos_.end()) return it->second;
    static const char* caras[6] = {"px", "nx", "py", "ny", "pz", "nz"};
    GLuint id = 0;
    glGenTextures(1, &id);
    glBindTexture(GL_TEXTURE_CUBE_MAP, id);
    stbi_set_flip_vertically_on_load(0);
    size_t total = 0;
    for (int i = 0; i < 6; ++i) {
        int w = 0, h = 0, c = 0;
        unsigned char* px = nullptr;
        for (const char* ext : {".jpg", ".png"}) {
            std::string ruta = (fs::u8path(carpeta) / (std::string(caras[i]) + ext)).u8string();
            if (fs::exists(fs::u8path(ruta))) {
                px = leerImagen(ruta, &w, &h, &c, 3);
                break;
            }
        }
        if (!px) {
            registro::error("Falta la cara %s del cube map en %s", caras[i], carpeta.c_str());
            glDeleteTextures(1, &id);
            return 0;
        }
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
        glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_SRGB8, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, px);
        stbi_image_free(px);
        total += static_cast<size_t>(w) * h * 4;
    }
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE);
    glBindTexture(GL_TEXTURE_CUBE_MAP, 0);
    cubos_.emplace(carpeta, id);
    bytesCubos_ += total;
    if (bytes) *bytes = total;
    return id;
}

size_t CacheTexturas::bytesGPU() const {
    size_t total = bytesCubos_;
    for (const auto& [clave, t] : texturas_) total += t->bytes;
    return total;
}

void CacheTexturas::liberar() {
    for (auto& [clave, t] : texturas_) glDeleteTextures(1, &t->id);
    for (auto& [clave, id] : cubos_) glDeleteTextures(1, &id);
    texturas_.clear();
    cubos_.clear();
    bytesCubos_ = 0;
}
