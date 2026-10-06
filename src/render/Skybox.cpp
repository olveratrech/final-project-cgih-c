#include "render/Skybox.h"

#include "Registro.h"
#include "Rutas.h"

bool Skybox::iniciar(const std::string& carpetaCaras, CacheTexturas& texturas) {
    if (!shader_.cargar(rutas::shader("cielo.vert"), rutas::shader("cielo.frag"))) return false;
    cubo_ = texturas.cubemap(carpetaCaras);
    if (!cubo_) return false;

    // 36 vértices del cubo unitario (las caras miran hacia adentro)
    static const float v[] = {
        -1, 1,  -1, -1, -1, -1, 1,  -1, -1, 1,  -1, -1, 1,  1,  -1, -1, 1,  -1,
        -1, -1, 1,  -1, -1, -1, -1, 1,  -1, -1, 1,  -1, -1, 1,  1,  -1, -1, 1,
        1,  -1, -1, 1,  -1, 1,  1,  1,  1,  1,  1,  1,  1,  1,  -1, 1,  -1, -1,
        -1, -1, 1,  -1, 1,  1,  1,  1,  1,  1,  1,  1,  1,  -1, 1,  -1, -1, 1,
        -1, 1,  -1, 1,  1,  -1, 1,  1,  1,  1,  1,  1,  -1, 1,  1,  -1, 1,  -1,
        -1, -1, -1, -1, -1, 1,  1,  -1, -1, 1,  -1, -1, -1, -1, 1,  1,  -1, 1,
    };
    glGenVertexArrays(1, &vao_);
    glGenBuffers(1, &vbo_);
    glBindVertexArray(vao_);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    glBufferData(GL_ARRAY_BUFFER, sizeof(v), v, GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(float), nullptr);
    glBindVertexArray(0);
    return true;
}

void Skybox::dibujar(const glm::mat4& vista, const glm::mat4& proyeccion) const {
    if (!cubo_) return;
    // se dibuja al final de los opacos: solo pasa la prueba de profundidad donde
    // no hay geometría (ahorra sombreado de fragmentos ocultos)
    glDepthFunc(GL_LEQUAL);
    glDisable(GL_CULL_FACE);
    shader_.usar();
    shader_.set("uVistaSinTraslacion", glm::mat4(glm::mat3(vista)));
    shader_.set("uProyeccion", proyeccion);
    shader_.set("uExposicion", exposicion);
    shader_.set("uCielo", 0);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_CUBE_MAP, cubo_);
    glBindVertexArray(vao_);
    glDrawArrays(GL_TRIANGLES, 0, 36);
    glBindVertexArray(0);
    glEnable(GL_CULL_FACE);
    glDepthFunc(GL_LESS);
}

void Skybox::liberar() {
    if (vao_) glDeleteVertexArrays(1, &vao_);
    if (vbo_) glDeleteBuffers(1, &vbo_);
    vao_ = vbo_ = 0;
    shader_.liberar();
}
