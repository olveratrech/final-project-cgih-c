// Renderer.h - Dibuja el grafo de escena.
//
// Optimizaciones aplicadas:
//   * Descarte por frustum con esferas envolventes (no se envían a la GPU los
//     objetos fuera de la vista).
//   * Dibujo instanciado para objetos repetidos (una llamada por primitiva).
//   * Orden de dibujo: opacos agrupados por textura -> cielo (solo donde no hay
//     geometría) -> transparentes de atrás hacia adelante.
#pragma once

#include "render/Shader.h"
#include "render/Skybox.h"
#include "scene/Camera.h"
#include "scene/SceneNode.h"

#include <glm/glm.hpp>

#include <vector>

struct Estadisticas {
    int llamadas = 0;     // draw calls
    int triangulos = 0;
    int instancias = 0;
    int descartados = 0;  // primitivas fuera del frustum
};

struct Iluminacion {
    glm::vec3 direccion = glm::normalize(glm::vec3(-0.55f, 0.42f, 0.55f));  // hacia el sol del atardecer
    glm::vec3 color = glm::vec3(1.0f, 0.82f, 0.62f) * 2.3f;
    glm::vec3 ambienteCielo = glm::vec3(0.36f, 0.40f, 0.52f);
    glm::vec3 ambienteSuelo = glm::vec3(0.20f, 0.15f, 0.12f);
    glm::vec3 colorNiebla = glm::vec3(0.62f, 0.62f, 0.66f);
    float densidadNiebla = 0.011f;
};

class Renderer {
public:
    bool iniciar();
    void liberar();

    void dibujar(Nodo* raiz, const Camara& camara, int ancho, int alto, const Skybox* cielo);
    void dibujarSeleccion(const Nodo* nodo, const Camara& camara, int ancho, int alto);

    Iluminacion luz;
    bool alambre = false;
    bool niebla = true;
    bool descartar = true;  // descarte por frustum activado
    Estadisticas stats;

private:
    struct Dibujo {
        const Primitiva* prim = nullptr;
        const Material* mat = nullptr;
        glm::mat4 matriz{1.0f};   // mundo (o matriz del nodo dentro del modelo si es instanciado)
        glm::mat4 padre{1.0f};    // mundo del dueño del lote
        const Lote* lote = nullptr;
        GLuint vaoInstancias = 0;
        float distancia = 0.0f;
        glm::vec4 tinte{1.0f};
    };
    struct Plano {
        glm::vec3 n;
        float d;
    };

    void recolectar(Nodo* n, const glm::vec3& ojo, const glm::vec4& tinte);
    bool visible(const glm::vec3& centro, float radio) const;
    void emitir(const Dibujo& d);
    void aplicarMaterial(const Shader& s, const Material& m);

    Shader shader_, shaderInst_, shaderLinea_;
    GLuint vaoLinea_ = 0, vboLinea_ = 0;
    std::vector<Dibujo> opacos_, mezcla_;
    Plano frustum_[6];
    glm::mat4 vistaProy_{1.0f};
    glm::vec3 ojo_{0.0f};
};
