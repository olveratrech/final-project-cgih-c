// Skybox.h - Cielo con cube map (texturizado de ambiente).
#pragma once

#include "render/Shader.h"
#include "render/Texture.h"

#include <glm/glm.hpp>

#include <string>

class Skybox {
public:
    bool iniciar(const std::string& carpetaCaras, CacheTexturas& texturas);
    void dibujar(const glm::mat4& vista, const glm::mat4& proyeccion) const;
    void liberar();

    float exposicion = 1.0f;
    bool listo() const { return cubo_ != 0; }

private:
    Shader shader_;
    GLuint vao_ = 0, vbo_ = 0, cubo_ = 0;
};
