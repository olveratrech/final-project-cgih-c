// Camera.h - Cámara libre (vuelo) y cámara orbital para la galería de modelos.
#pragma once

#include <glm/glm.hpp>

class Camara {
public:
    // --- cámara libre ---------------------------------------------------------
    glm::vec3 posicion{0.0f, 1.7f, 10.0f};
    float guinada = -90.0f;  // yaw (grados): -90 mira hacia -Z
    float cabeceo = 0.0f;    // pitch (grados)
    float velocidad = 4.0f;  // m/s
    float sensibilidad = 0.12f;

    // --- proyección -------------------------------------------------------------
    float fov = 60.0f;
    float cerca = 0.05f;
    float lejos = 400.0f;

    // --- modo orbital (galería) -------------------------------------------------
    bool orbital = false;
    glm::vec3 objetivo{0.0f};
    float distancia = 3.0f;

    glm::vec3 frente() const;
    glm::vec3 derecha() const;
    glm::vec3 ojo() const;  // posición efectiva (libre u orbital)
    glm::mat4 vista() const;
    glm::mat4 proyeccion(float aspecto) const;

    void mirarHacia(const glm::vec3& punto);
    void girar(float dx, float dy);
    void desplazar(const glm::vec3& direccionLocal, float dt, float multiplicador);
    void acercar(float pasos);
};
