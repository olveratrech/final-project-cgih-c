#include "render/Renderer.h"

#include "Registro.h"
#include "Rutas.h"

#include <glm/gtc/matrix_inverse.hpp>

#include <algorithm>
#include <cmath>

bool Renderer::iniciar() {
    bool ok = shader_.cargar(rutas::shader("escena.vert"), rutas::shader("escena.frag"));
    ok = ok && shaderInst_.cargar(rutas::shader("escena.vert"), rutas::shader("escena.frag"), "#define INSTANCIADO\n");
    ok = ok && shaderLinea_.cargar(rutas::shader("linea.vert"), rutas::shader("linea.frag"));
    if (!ok) return false;
    glGenVertexArrays(1, &vaoLinea_);
    glGenBuffers(1, &vboLinea_);
    glBindVertexArray(vaoLinea_);
    glBindBuffer(GL_ARRAY_BUFFER, vboLinea_);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), nullptr);
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), reinterpret_cast<void*>(3 * sizeof(float)));
    glBindVertexArray(0);
    return true;
}

void Renderer::liberar() {
    shader_.liberar();
    shaderInst_.liberar();
    shaderLinea_.liberar();
    if (vaoLinea_) glDeleteVertexArrays(1, &vaoLinea_);
    if (vboLinea_) glDeleteBuffers(1, &vboLinea_);
    vaoLinea_ = vboLinea_ = 0;
}

// Extrae los 6 planos del volumen de visión de la matriz vista-proyección
// (método de Gribb y Hartmann).
static void extraerPlanos(const glm::mat4& m, glm::vec4 p[6]) {
    glm::vec4 f0(m[0][0], m[1][0], m[2][0], m[3][0]);
    glm::vec4 f1(m[0][1], m[1][1], m[2][1], m[3][1]);
    glm::vec4 f2(m[0][2], m[1][2], m[2][2], m[3][2]);
    glm::vec4 f3(m[0][3], m[1][3], m[2][3], m[3][3]);
    p[0] = f3 + f0;
    p[1] = f3 - f0;
    p[2] = f3 + f1;
    p[3] = f3 - f1;
    p[4] = f3 + f2;
    p[5] = f3 - f2;
}

bool Renderer::visible(const glm::vec3& c, float r) const {
    if (!descartar) return true;
    for (const Plano& p : frustum_)
        if (glm::dot(p.n, c) + p.d < -r) return false;
    return true;
}

static float escalaMaxima(const glm::mat4& m) {
    return std::max({glm::length(glm::vec3(m[0])), glm::length(glm::vec3(m[1])), glm::length(glm::vec3(m[2]))});
}

void Renderer::recolectar(Nodo* n, const glm::vec3& ojo, const glm::vec4& tintePadre) {
    if (!n->visible) return;
    const glm::vec4 tinte = tintePadre * n->tinte;
    if (n->modelo && n->malla >= 0) {
        const Malla& malla = n->modelo->mallas[static_cast<size_t>(n->malla)];
        float esc = escalaMaxima(n->mundo);
        for (const Primitiva& p : malla.primitivas) {
            glm::vec3 c = glm::vec3(n->mundo * glm::vec4((p.min + p.max) * 0.5f, 1.0f));
            float r = glm::length(p.max - p.min) * 0.5f * esc;
            if (!visible(c, r)) {
                stats.descartados++;
                continue;
            }
            Dibujo d;
            d.prim = &p;
            d.mat = &n->modelo->materiales[static_cast<size_t>(p.material)];
            d.matriz = n->mundo;
            d.distancia = glm::length(c - ojo);
            d.tinte = tinte;
            (d.mat->alfa == ModoAlfa::Mezcla ? mezcla_ : opacos_).push_back(d);
        }
    }
    if (n->lote && n->lote->instancias() > 0) {
        const Lote& L = *n->lote;
        glm::vec3 c = glm::vec3(n->mundo * glm::vec4((L.min + L.max) * 0.5f, 1.0f));
        float r = glm::length(L.max - L.min) * 0.5f * escalaMaxima(n->mundo);
        if (visible(c, r)) {
            for (size_t e = 0; e < L.modelo->plano.size(); ++e) {
                const auto& entrada = L.modelo->plano[e];
                const Malla& malla = L.modelo->mallas[static_cast<size_t>(entrada.malla)];
                for (size_t k = 0; k < malla.primitivas.size(); ++k) {
                    Dibujo d;
                    d.prim = &malla.primitivas[k];
                    d.mat = &L.modelo->materiales[static_cast<size_t>(d.prim->material)];
                    d.matriz = entrada.matriz;
                    d.padre = n->mundo;
                    d.lote = &L;
                    d.vaoInstancias = L.vaosDe(e)[k];
                    d.distancia = glm::length(c - ojo);
                    d.tinte = tinte;
                    (d.mat->alfa == ModoAlfa::Mezcla ? mezcla_ : opacos_).push_back(d);
                }
            }
        } else {
            stats.descartados += static_cast<int>(L.modelo->plano.size());
        }
    }
    for (auto& h : n->hijos) recolectar(h.get(), ojo, tinte);
}

void Renderer::aplicarMaterial(const Shader& s, const Material& m) {
    s.set("uColor", m.color);
    s.set("uEmision", m.emision);
    s.set("uMetalico", m.metalico);
    s.set("uRugosidad", m.rugosidad);
    s.set("uCapa", m.capa);
    s.set("uRugosidadCapa", m.rugosidadCapa);
    s.set("uModoAlfa", m.alfa == ModoAlfa::Opaco ? 0 : m.alfa == ModoAlfa::Recorte ? 1 : 2);
    s.set("uCorte", m.corte);
    s.set("uEscalaUV", m.escalaUV);
    s.set("uTieneTextura", m.textura ? 1 : 0);
    if (m.textura) {
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, m.textura->id);
    }
    if (m.dobleCara || alambre) glDisable(GL_CULL_FACE);
    else glEnable(GL_CULL_FACE);
}

void Renderer::emitir(const Dibujo& d) {
    const Shader& s = d.lote ? shaderInst_ : shader_;
    aplicarMaterial(s, *d.mat);
    s.set("uTinte", d.tinte);
    if (d.lote) {
        s.set("uPadre", d.padre);
        s.set("uModelo", d.matriz);
        glBindVertexArray(d.vaoInstancias);
        glDrawElementsInstanced(GL_TRIANGLES, d.prim->indices, d.prim->tipoIndice, nullptr, d.lote->instancias());
        stats.instancias += d.lote->instancias();
        stats.triangulos += d.prim->indices / 3 * d.lote->instancias();
    } else {
        s.set("uModelo", d.matriz);
        s.set("uNormal", glm::inverseTranspose(glm::mat3(d.matriz)));
        glBindVertexArray(d.prim->vao);
        glDrawElements(GL_TRIANGLES, d.prim->indices, d.prim->tipoIndice, nullptr);
        stats.triangulos += d.prim->indices / 3;
    }
    stats.llamadas++;
}

void Renderer::dibujar(Nodo* raiz, const Camara& camara, int ancho, int alto, const Skybox* cielo) {
    stats = Estadisticas{};
    float aspecto = alto > 0 ? static_cast<float>(ancho) / static_cast<float>(alto) : 1.0f;
    glm::mat4 vista = camara.vista();
    glm::mat4 proy = camara.proyeccion(aspecto);
    vistaProy_ = proy * vista;
    ojo_ = camara.ojo();

    glm::vec4 planos[6];
    extraerPlanos(vistaProy_, planos);
    for (int i = 0; i < 6; ++i) {
        float l = glm::length(glm::vec3(planos[i]));
        frustum_[i] = {glm::vec3(planos[i]) / l, planos[i].w / l};
    }

    opacos_.clear();
    mezcla_.clear();
    recolectar(raiz, ojo_, glm::vec4(1.0f));
    // agrupar por textura reduce cambios de estado en la GPU
    std::sort(opacos_.begin(), opacos_.end(), [](const Dibujo& a, const Dibujo& b) {
        if ((a.lote != nullptr) != (b.lote != nullptr)) return a.lote == nullptr;
        return a.mat->textura < b.mat->textura;
    });
    std::sort(mezcla_.begin(), mezcla_.end(), [](const Dibujo& a, const Dibujo& b) { return a.distancia > b.distancia; });

    glViewport(0, 0, ancho, alto);
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LESS);
    glEnable(GL_CULL_FACE);
    glCullFace(GL_BACK);
    if (alambre) {
        glClearColor(0.07f, 0.06f, 0.08f, 1.0f);
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
    } else {
        glm::vec3 n = glm::pow(luz.colorNiebla, glm::vec3(1.0f / 2.2f));
        glClearColor(n.r, n.g, n.b, 1.0f);
    }
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    const bool hayEntorno = cielo && cielo->listo();

    // La unidad 0 queda para las texturas de los modelos.
    glActiveTexture(GL_TEXTURE1);
    glBindTexture(
        GL_TEXTURE_CUBE_MAP,
        hayEntorno ? cielo->textura() : 0
    );
    glEnable(GL_TEXTURE_CUBE_MAP_SEAMLESS);
    glActiveTexture(GL_TEXTURE0);

    for (const Shader* s : {&shader_, &shaderInst_}) {
        s->usar();
        s->set("uVistaProy", vistaProy_);
        s->set("uDirLuz", glm::normalize(luz.direccion));
        s->set("uColorLuz", luz.color);
        s->set("uAmbienteCielo", luz.ambienteCielo);
        s->set("uAmbienteSuelo", luz.ambienteSuelo);
        s->set("uPosCamara", ojo_);
        s->set("uColorNiebla", luz.colorNiebla);
        // la niebla se adelgaza al subir la cámara (aproximación de niebla por altura)
        float densidad = luz.densidadNiebla / (1.0f + std::max(ojo_.y, 0.0f) / 15.0f);
        s->set("uDensidadNiebla", niebla ? densidad : 0.0f);
        s->set("uTextura", 0);
        s->set("uEntorno", 1);
        s->set("uTieneEntorno", hayEntorno ? 1 : 0);
        s->set(
            "uExposicionEntorno",
            hayEntorno ? cielo->exposicion : 1.0f
        );
        s->set("uAlambre", alambre ? 1 : 0);
        s->set("uColorAlambre", glm::vec3(0.98f, 0.62f, 0.18f));
    }

    const Shader* actual = nullptr;
    for (const Dibujo& d : opacos_) {
        const Shader* s = d.lote ? &shaderInst_ : &shader_;
        if (s != actual) {
            s->usar();
            actual = s;
        }
        emitir(d);
    }

    if (alambre) {
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
    } else if (cielo) {
        cielo->dibujar(vista, proy);
        actual = nullptr;
    }

    if (!mezcla_.empty() && !alambre) {
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glDepthMask(GL_FALSE);
        for (const Dibujo& d : mezcla_) {
            const Shader* s = d.lote ? &shaderInst_ : &shader_;
            if (s != actual) {
                s->usar();
                actual = s;
            }
            emitir(d);
        }
        glDepthMask(GL_TRUE);
        glDisable(GL_BLEND);
    }
    glBindVertexArray(0);
    glEnable(GL_CULL_FACE);
}

// Caja envolvente en mundo de un subárbol (para resaltar la selección).
static void acumularCaja(const Nodo* n, glm::vec3& mn, glm::vec3& mx) {
    auto agregarCaja = [&](const glm::vec3& a, const glm::vec3& b, const glm::mat4& m) {
        for (int k = 0; k < 8; ++k) {
            glm::vec3 c((k & 1) ? b.x : a.x, (k & 2) ? b.y : a.y, (k & 4) ? b.z : a.z);
            glm::vec3 w = glm::vec3(m * glm::vec4(c, 1.0f));
            mn = glm::min(mn, w);
            mx = glm::max(mx, w);
        }
    };
    if (n->modelo && n->malla >= 0)
        for (const auto& p : n->modelo->mallas[static_cast<size_t>(n->malla)].primitivas) agregarCaja(p.min, p.max, n->mundo);
    if (n->lote && n->lote->instancias() > 0) agregarCaja(n->lote->min, n->lote->max, n->mundo);
    for (const auto& h : n->hijos) acumularCaja(h.get(), mn, mx);
}

void Renderer::dibujarSeleccion(const Nodo* nodo, const Camara& camara, int ancho, int alto) {
    if (!nodo) return;
    glm::vec3 mn(1e30f), mx(-1e30f);
    acumularCaja(nodo, mn, mx);
    std::vector<float> v;
    auto linea = [&](const glm::vec3& a, const glm::vec3& b, const glm::vec3& c) {
        v.insert(v.end(), {a.x, a.y, a.z, c.r, c.g, c.b, b.x, b.y, b.z, c.r, c.g, c.b});
    };
    if (mn.x <= mx.x) {
        const glm::vec3 amarillo(1.0f, 0.85f, 0.1f);
        glm::vec3 p[8];
        for (int k = 0; k < 8; ++k) p[k] = glm::vec3((k & 1) ? mx.x : mn.x, (k & 2) ? mx.y : mn.y, (k & 4) ? mx.z : mn.z);
        const int aristas[12][2] = {{0, 1}, {2, 3}, {4, 5}, {6, 7}, {0, 2}, {1, 3}, {4, 6}, {5, 7}, {0, 4}, {1, 5}, {2, 6}, {3, 7}};
        for (const auto& a : aristas) linea(p[a[0]], p[a[1]], amarillo);
    }
    // ejes locales del nodo (rojo X, verde Y, azul Z): muestran su transformación
    glm::vec3 o = glm::vec3(nodo->mundo[3]);
    float largo = std::max(0.35f, glm::length(mx - mn) * 0.35f);
    if (!(mn.x <= mx.x)) largo = 0.5f;
    linea(o, o + glm::normalize(glm::vec3(nodo->mundo[0])) * largo, {1.0f, 0.2f, 0.2f});
    linea(o, o + glm::normalize(glm::vec3(nodo->mundo[1])) * largo, {0.2f, 1.0f, 0.2f});
    linea(o, o + glm::normalize(glm::vec3(nodo->mundo[2])) * largo, {0.3f, 0.5f, 1.0f});

    float aspecto = alto > 0 ? static_cast<float>(ancho) / static_cast<float>(alto) : 1.0f;
    shaderLinea_.usar();
    shaderLinea_.set("uVistaProy", camara.proyeccion(aspecto) * camara.vista());
    glDisable(GL_DEPTH_TEST);
    glBindVertexArray(vaoLinea_);
    glBindBuffer(GL_ARRAY_BUFFER, vboLinea_);
    glBufferData(GL_ARRAY_BUFFER, static_cast<GLsizeiptr>(v.size() * sizeof(float)), v.data(), GL_STREAM_DRAW);
    glDrawArrays(GL_LINES, 0, static_cast<GLsizei>(v.size() / 6));
    glBindVertexArray(0);
    glEnable(GL_DEPTH_TEST);
}
