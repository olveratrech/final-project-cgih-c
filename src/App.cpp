#include "App.h"

#include "Registro.h"
#include "Rutas.h"

#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>
#include <stb_image_write.h>

#include <glm/gtc/matrix_transform.hpp>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <ctime>
#include <filesystem>
#include <limits>
#include <vector>

namespace fs = std::filesystem;

static App* g_app = nullptr;

int App::ejecutar(const Opciones& opciones) {
    op_ = opciones;
    if (!iniciar()) {
        terminar();
        return 1;
    }

    int cuadros = 0;
    double anterior = glfwGetTime(), acumulado = 0.0;
    int cuadrosFps = 0;
    while (!glfwWindowShouldClose(ventana_)) {
        double ahora = glfwGetTime();
        float dt = static_cast<float>(std::min(ahora - anterior, 0.1));
        anterior = ahora;
        acumulado += dt;
        ++cuadrosFps;
        if (acumulado >= 0.5) {
            fps_ = static_cast<float>(cuadrosFps / acumulado);
            msCuadro_ = static_cast<float>(acumulado * 1000.0 / cuadrosFps);
            acumulado = 0.0;
            cuadrosFps = 0;
        }

        glfwPollEvents();
        glfwGetFramebufferSize(ventana_, &anchoFb_, &altoFb_);
        if (anchoFb_ == 0 || altoFb_ == 0) {  // ventana minimizada
            glfwWaitEvents();
            continue;
        }
        procesarEntrada(dt);
        if (tiempoMensaje_ > 0.0f) tiempoMensaje_ -= dt;

        if (modo_ == Modo::Escena) {
            escena_.raiz()->actualizar(glm::mat4(1.0f));
            renderer_.dibujar(escena_.raiz(), camara_, anchoFb_, altoFb_, mostrarCielo_ ? &escena_.cielo : nullptr);
            if (mostrarSeleccion_ && seleccion_) renderer_.dibujarSeleccion(seleccion_, camara_, anchoFb_, altoFb_);
        } else {
            actualizarGaleria(dt);
            renderer_.dibujar(vitrina_.get(), camaraGaleria_, anchoFb_, altoFb_, mostrarCielo_ ? &escena_.cielo : nullptr);
        }

        dibujarInterfaz();

        ++cuadros;
        if (!op_.captura.empty() && cuadros == op_.frames) {
            capturar(op_.captura);
            glfwSetWindowShouldClose(ventana_, GLFW_TRUE);
        }
        glfwSwapBuffers(ventana_);
    }
    terminar();
    return 0;
}

bool App::iniciar() {
    g_app = this;
    glfwSetErrorCallback([](int codigo, const char* desc) { registro::error("GLFW %d: %s", codigo, desc); });
    if (!glfwInit()) {
        registro::fatal("No se pudo iniciar GLFW.");
        return false;
    }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
    if (op_.msaa > 0) glfwWindowHint(GLFW_SAMPLES, op_.msaa);
    if (op_.ancho <= 0 || op_.alto <= 0) {
        // tamaño inicial: 80 % del área de trabajo del monitor principal
        int x = 0, y = 0, w = 1280, h = 720;
        if (GLFWmonitor* mon = glfwGetPrimaryMonitor()) glfwGetMonitorWorkarea(mon, &x, &y, &w, &h);
        op_.ancho = std::max(960, w * 4 / 5);
        op_.alto = std::max(540, h * 4 / 5);
    }
    ventana_ = glfwCreateWindow(op_.ancho, op_.alto, "Camino de Cempasúchil - Día de Muertos | CGeIHC FI UNAM",
                               nullptr, nullptr);
    if (!ventana_) {
        registro::fatal("No se pudo crear la ventana. Se requiere una tarjeta gráfica compatible con OpenGL 3.3.");
        return false;
    }
    glfwMakeContextCurrent(ventana_);
    glfwSwapInterval(1);  // sincronía vertical: evita trabajo de más en la GPU
    if (!gladLoadGLLoader(reinterpret_cast<GLADloadproc>(glfwGetProcAddress))) {
        registro::fatal("No se pudieron cargar las funciones de OpenGL.");
        return false;
    }
    registro::info("OpenGL %s | GLSL %s | %s", glGetString(GL_VERSION), glGetString(GL_SHADING_LANGUAGE_VERSION),
                   glGetString(GL_RENDERER));
    if (op_.msaa > 0) glEnable(GL_MULTISAMPLE);

    if (!renderer_.iniciar()) {
        registro::fatal("No se pudieron compilar los shaders (carpeta shaders/).");
        return false;
    }
    auto t0 = std::chrono::steady_clock::now();
    if (!escena_.cargar()) {
        registro::fatal("No se pudieron cargar los modelos (carpeta assets/).");
        return false;
    }
    double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
    registro::info("Carga de modelos y texturas: %.0f ms", ms);

    renderer_.alambre = op_.alambre;
    // ImGui instala sus callbacks primero; los nuestros reemplazan teclado, rueda y
    // botones del ratón y le reenvían los eventos.
    iniciarInterfaz();
    glfwSetKeyCallback(ventana_, alTeclear);
    glfwSetScrollCallback(ventana_, alDesplazar);
    glfwSetMouseButtonCallback(ventana_, alPulsar);
    mostrarInterfaz_ = !op_.sinInterfaz;
    aplicarVista(op_.vista >= 1 ? op_.vista - 1 : 0);
    if (!op_.seleccion.empty()) seleccion_ = escena_.raiz()->buscar(op_.seleccion);
    if (!op_.galeria.empty()) {
        for (size_t i = 0; i < escena_.catalogo().size(); ++i)
            if (escena_.catalogo()[i].clave == op_.galeria) modeloGaleria_ = static_cast<int>(i);
        cambiarModo(Modo::Galeria);
    }
    return true;
}

void App::terminar() {
    if (ImGui::GetCurrentContext()) {
        ImGui_ImplOpenGL3_Shutdown();
        ImGui_ImplGlfw_Shutdown();
        ImGui::DestroyContext();
    }
    vitrina_.reset();
    escena_.liberar();
    renderer_.liberar();
    if (ventana_) glfwDestroyWindow(ventana_);
    ventana_ = nullptr;
    glfwTerminate();
}

// ---------------------------------------------------------------------------
// Entrada
// ---------------------------------------------------------------------------
void App::procesarEntrada(float dt) {
    ImGuiIO& io = ImGui::GetIO();
    double x, y;
    glfwGetCursorPos(ventana_, &x, &y);
    float dx = static_cast<float>(x - ultimoX_), dy = static_cast<float>(y - ultimoY_);
    ultimoX_ = x;
    ultimoY_ = y;

    Camara& cam = modo_ == Modo::Escena ? camara_ : camaraGaleria_;
    if (arrastrando_) cam.girar(dx, dy);

    if (clicPendiente_) {
        clicPendiente_ = false;
        if (modo_ == Modo::Escena) {
            Nodo* n = seleccionarConRayo(clicX_, clicY_);
            if (n) {
                bool exacto = glfwGetKey(ventana_, GLFW_KEY_LEFT_CONTROL) == GLFW_PRESS;
                if (!exacto)
                    while (n->padre && !n->raizInstancia) n = n->padre;
                seleccion_ = n;
            }
        }
    }

    if (io.WantCaptureKeyboard) return;
    auto tecla = [&](int k) { return glfwGetKey(ventana_, k) == GLFW_PRESS; };

    if (modo_ == Modo::Escena) {
        glm::vec3 d(0.0f);
        if (tecla(GLFW_KEY_W)) d.z += 1;
        if (tecla(GLFW_KEY_S)) d.z -= 1;
        if (tecla(GLFW_KEY_D)) d.x += 1;
        if (tecla(GLFW_KEY_A)) d.x -= 1;
        if (tecla(GLFW_KEY_E)) d.y += 1;
        if (tecla(GLFW_KEY_Q)) d.y -= 1;
        float mult = tecla(GLFW_KEY_LEFT_SHIFT) ? 3.0f : tecla(GLFW_KEY_LEFT_CONTROL) ? 0.3f : 1.0f;
        if (d != glm::vec3(0.0f)) camara_.desplazar(d, dt, mult);

        // transformaciones geométricas del nodo seleccionado (relativas a la cámara)
        if (seleccion_) {
            glm::vec3 f = camara_.frente();
            f.y = 0;
            f = glm::length(f) > 1e-4f ? glm::normalize(f) : glm::vec3(0, 0, -1);
            glm::vec3 r(-f.z, 0, f.x);
            glm::vec3 mov(0.0f);
            if (tecla(GLFW_KEY_UP)) mov += f;
            if (tecla(GLFW_KEY_DOWN)) mov -= f;
            if (tecla(GLFW_KEY_RIGHT)) mov += r;
            if (tecla(GLFW_KEY_LEFT)) mov -= r;
            if (tecla(GLFW_KEY_PAGE_UP)) mov.y += 1;
            if (tecla(GLFW_KEY_PAGE_DOWN)) mov.y -= 1;
            if (mov != glm::vec3(0.0f)) {
                // el desplazamiento en mundo se convierte al espacio del padre
                glm::mat4 invPadre = seleccion_->padre ? glm::inverse(seleccion_->padre->mundo) : glm::mat4(1.0f);
                seleccion_->posicion += glm::vec3(invPadre * glm::vec4(mov * 1.5f * mult * dt, 0.0f));
            }
            if (tecla(GLFW_KEY_Z)) seleccion_->rotacion.y += 60.0f * mult * dt;
            if (tecla(GLFW_KEY_X)) seleccion_->rotacion.y -= 60.0f * mult * dt;
            if (tecla(GLFW_KEY_V)) seleccion_->escala *= std::pow(1.5f, dt * mult);
            if (tecla(GLFW_KEY_C)) seleccion_->escala /= std::pow(1.5f, dt * mult);
        }
    }
}

void App::alTeclear(GLFWwindow* v, int tecla, int codigo, int accion, int mods) {
    ImGui_ImplGlfw_KeyCallback(v, tecla, codigo, accion, mods);
    App& a = *g_app;
    if (accion != GLFW_PRESS) return;
    if (ImGui::GetIO().WantCaptureKeyboard && tecla != GLFW_KEY_F1 && tecla != GLFW_KEY_F4) return;
    switch (tecla) {
        case GLFW_KEY_ESCAPE:
            if (a.modo_ == Modo::Galeria) a.cambiarModo(Modo::Escena);
            else if (a.seleccion_) a.seleccion_ = nullptr;
            else glfwSetWindowShouldClose(v, GLFW_TRUE);
            break;
        case GLFW_KEY_F1: a.mostrarAyuda_ = !a.mostrarAyuda_; break;
        case GLFW_KEY_F2: a.renderer_.alambre = !a.renderer_.alambre; break;
        case GLFW_KEY_F3: a.mostrarSeleccion_ = !a.mostrarSeleccion_; break;
        case GLFW_KEY_F4: a.mostrarInterfaz_ = !a.mostrarInterfaz_; break;
        case GLFW_KEY_F12:
        case GLFW_KEY_P: a.capturar(a.capturaAutomatica()); break;
        case GLFW_KEY_G: a.cambiarModo(a.modo_ == Modo::Escena ? Modo::Galeria : Modo::Escena); break;
        case GLFW_KEY_SPACE:
            if (a.modo_ == Modo::Galeria) a.girar_ = !a.girar_;
            break;
        case GLFW_KEY_BACKSPACE:
            if (a.seleccion_) a.seleccion_->restablecer();
            break;
        case GLFW_KEY_N:
            if (a.seleccion_ && a.seleccion_->padre) a.seleccion_ = a.seleccion_->padre;
            break;
        case GLFW_KEY_F:
            if (a.seleccion_) a.enfocar(a.seleccion_);
            break;
        case GLFW_KEY_LEFT:
        case GLFW_KEY_RIGHT:
            if (a.modo_ == Modo::Galeria)
                a.seleccionarModeloGaleria(a.modeloGaleria_ + (tecla == GLFW_KEY_RIGHT ? 1 : -1));
            break;
        default:
            if (tecla >= GLFW_KEY_1 && tecla <= GLFW_KEY_9 && a.modo_ == Modo::Escena) a.aplicarVista(tecla - GLFW_KEY_1);
            break;
    }
}

void App::alDesplazar(GLFWwindow* v, double dx, double dy) {
    ImGui_ImplGlfw_ScrollCallback(v, dx, dy);
    if (ImGui::GetIO().WantCaptureMouse) return;
    App& a = *g_app;
    (a.modo_ == Modo::Escena ? a.camara_ : a.camaraGaleria_).acercar(static_cast<float>(dy));
}

void App::alPulsar(GLFWwindow* v, int boton, int accion, int mods) {
    ImGui_ImplGlfw_MouseButtonCallback(v, boton, accion, mods);
    App& a = *g_app;
    if (boton == GLFW_MOUSE_BUTTON_RIGHT) {
        if (accion == GLFW_PRESS && !ImGui::GetIO().WantCaptureMouse) {
            a.arrastrando_ = true;
            glfwSetInputMode(v, GLFW_CURSOR, GLFW_CURSOR_DISABLED);
        } else if (accion == GLFW_RELEASE) {
            a.arrastrando_ = false;
            glfwSetInputMode(v, GLFW_CURSOR, GLFW_CURSOR_NORMAL);
        }
    }
    if (boton == GLFW_MOUSE_BUTTON_LEFT && accion == GLFW_PRESS && !ImGui::GetIO().WantCaptureMouse) {
        glfwGetCursorPos(v, &a.clicX_, &a.clicY_);
        a.clicPendiente_ = true;
    }
}

// ---------------------------------------------------------------------------
// Selección con el ratón: se lanza un rayo desde la cámara y, para cada malla,
// se transforma al espacio local del nodo (inversa de su matriz de mundo).
// Primero se descarta con la caja envolvente (método de las placas) y después
// se prueba contra cada triángulo (algoritmo de Möller-Trumbore).
// ---------------------------------------------------------------------------
static bool rayoCaja(const glm::vec3& o, const glm::vec3& d, const glm::vec3& mn, const glm::vec3& mx, float tMax) {
    float t0 = 0.0f, t1 = tMax;
    for (int k = 0; k < 3; ++k) {
        if (std::abs(d[k]) < 1e-12f) {
            if (o[k] < mn[k] || o[k] > mx[k]) return false;
            continue;
        }
        float ta = (mn[k] - o[k]) / d[k], tb = (mx[k] - o[k]) / d[k];
        if (ta > tb) std::swap(ta, tb);
        t0 = std::max(t0, ta);
        t1 = std::min(t1, tb);
        if (t0 > t1) return false;
    }
    return true;
}

static bool rayoTriangulo(const glm::vec3& o, const glm::vec3& d, const glm::vec3& a, const glm::vec3& b,
                          const glm::vec3& c, float& t) {
    glm::vec3 e1 = b - a, e2 = c - a;
    glm::vec3 p = glm::cross(d, e2);
    float det = glm::dot(e1, p);
    if (std::abs(det) < 1e-14f) return false;  // rayo paralelo al triángulo
    float inv = 1.0f / det;
    glm::vec3 s = o - a;
    float u = glm::dot(s, p) * inv;
    if (u < 0.0f || u > 1.0f) return false;
    glm::vec3 q = glm::cross(s, e1);
    float v = glm::dot(d, q) * inv;
    if (v < 0.0f || u + v > 1.0f) return false;
    t = glm::dot(e2, q) * inv;
    return t > 0.0f;
}

Nodo* App::seleccionarConRayo(double x, double y) {
    int w, h;
    glfwGetWindowSize(ventana_, &w, &h);
    if (w <= 0 || h <= 0) return nullptr;
    float nx = static_cast<float>(2.0 * x / w - 1.0), ny = static_cast<float>(1.0 - 2.0 * y / h);
    glm::mat4 inv = glm::inverse(camara_.proyeccion(static_cast<float>(anchoFb_) / altoFb_) * camara_.vista());
    glm::vec4 a = inv * glm::vec4(nx, ny, -1.0f, 1.0f), b = inv * glm::vec4(nx, ny, 1.0f, 1.0f);
    glm::vec3 origen = glm::vec3(a) / a.w, fin = glm::vec3(b) / b.w;
    glm::vec3 dir = fin - origen;  // el parámetro t va de 0 (plano cercano) a 1 (plano lejano)

    Nodo* mejor = nullptr;
    float tMejor = 1.0f;
    std::vector<Nodo*> pila = {escena_.raiz()};
    while (!pila.empty()) {
        Nodo* n = pila.back();
        pila.pop_back();
        if (!n->visible) continue;
        for (auto& hijo : n->hijos) pila.push_back(hijo.get());
        if (!n->modelo || n->malla < 0 || n->categoria == "procedural") continue;
        glm::mat4 invM = glm::inverse(n->mundo);
        glm::vec3 o = glm::vec3(invM * glm::vec4(origen, 1.0f));
        glm::vec3 d = glm::vec3(invM * glm::vec4(dir, 0.0f));
        for (const Primitiva& p : n->modelo->mallas[static_cast<size_t>(n->malla)].primitivas) {
            if (!rayoCaja(o, d, p.min, p.max, tMejor)) continue;
            for (size_t k = 0; k + 2 < p.triangulos.size(); k += 3) {
                float t;
                if (rayoTriangulo(o, d, p.posiciones[p.triangulos[k]], p.posiciones[p.triangulos[k + 1]],
                                  p.posiciones[p.triangulos[k + 2]], t) &&
                    t < tMejor) {
                    tMejor = t;
                    mejor = n;
                }
            }
        }
    }
    return mejor;
}

void App::enfocar(Nodo* n) {
    glm::vec3 c = glm::vec3(n->mundo[3]);
    glm::vec3 desde = camara_.posicion - c;
    desde.y = 0.0f;
    if (glm::length(desde) < 1e-3f) desde = glm::vec3(0, 0, 1);
    camara_.posicion = c + glm::normalize(desde) * 2.5f + glm::vec3(0.0f, 1.2f, 0.0f);
    camara_.mirarHacia(c + glm::vec3(0.0f, 0.3f, 0.0f));
}

void App::aplicarVista(int indice) {
    const auto& vistas = escena_.vistas();
    if (indice < 0 || indice >= static_cast<int>(vistas.size())) return;
    vistaActual_ = indice;
    camara_.posicion = vistas[static_cast<size_t>(indice)].posicion;
    camara_.mirarHacia(vistas[static_cast<size_t>(indice)].objetivo);
}

// ---------------------------------------------------------------------------
// Galería de modelos (vitrina giratoria)
// ---------------------------------------------------------------------------
void App::cambiarModo(Modo m) {
    modo_ = m;
    if (m == Modo::Galeria) seleccionarModeloGaleria(modeloGaleria_);
}

void App::seleccionarModeloGaleria(int indice) {
    auto& cat = escena_.catalogo();
    if (cat.empty()) return;
    int n = static_cast<int>(cat.size());
    modeloGaleria_ = ((indice % n) + n) % n;
    const InfoModelo& info = cat[static_cast<size_t>(modeloGaleria_)];
    const Modelo& m = *info.modelo;

    vitrina_ = std::make_unique<Nodo>("Vitrina");
    float radioXZ = std::max(glm::length(glm::vec2(m.max.x - m.min.x, m.max.z - m.min.z)) * 0.5f, 0.05f);
    Nodo* pedestal = vitrina_->agregar("pedestal");
    pedestal->modelo = escena_.modelo("pedestal");
    pedestal->malla = 0;
    float esc = radioXZ * 1.25f + 0.05f;
    pedestal->escala = glm::vec3(esc, std::min(esc, 1.0f), esc);
    float tope = 0.08f * pedestal->escala.y;
    giro_ = vitrina_->agregar("giro");
    escena_.instanciar(info.clave, giro_, info.clave, {-m.centro().x, tope - m.min.y, -m.centro().z}, 0.0f, 1.0f, false);
    vitrina_->actualizar(glm::mat4(1.0f));

    camaraGaleria_.orbital = true;
    camaraGaleria_.objetivo = glm::vec3(0.0f, tope + (m.max.y - m.min.y) * 0.5f, 0.0f);
    float r = std::max(m.radio(), 0.05f);
    camaraGaleria_.distancia = r / std::sin(glm::radians(camaraGaleria_.fov * 0.5f)) * 1.15f;
    camaraGaleria_.cerca = std::max(0.005f, camaraGaleria_.distancia * 0.01f);
    camaraGaleria_.guinada = -60.0f;
    camaraGaleria_.cabeceo = -18.0f;
}

void App::actualizarGaleria(float dt) {
    if (!vitrina_) seleccionarModeloGaleria(modeloGaleria_);
    if (girar_ && giro_) giro_->rotacion.y += 25.0f * dt;
    vitrina_->actualizar(glm::mat4(1.0f));
}

// ---------------------------------------------------------------------------
// Capturas de pantalla
// ---------------------------------------------------------------------------
std::string App::capturaAutomatica() const {
    std::time_t t = std::time(nullptr);
    char nombre[64];
    std::strftime(nombre, sizeof(nombre), "cempasuchil_%Y%m%d_%H%M%S.png", std::localtime(&t));
    return (fs::u8path(rutas::carpetaCapturas()) / nombre).u8string();
}

void App::capturar(const std::string& ruta) {
    std::vector<unsigned char> px(static_cast<size_t>(anchoFb_) * altoFb_ * 3);
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadBuffer(GL_BACK);
    glReadPixels(0, 0, anchoFb_, altoFb_, GL_RGB, GL_UNSIGNED_BYTE, px.data());
    stbi_flip_vertically_on_write(1);
    bool ok = stbi_write_png(ruta.c_str(), anchoFb_, altoFb_, 3, px.data(), anchoFb_ * 3) != 0;
    if (ok) {
        registro::info("Captura guardada en %s", ruta.c_str());
        mensaje_ = "Captura guardada: " + ruta;
    } else {
        registro::error("No se pudo guardar la captura en %s", ruta.c_str());
        mensaje_ = "No se pudo guardar la captura";
    }
    tiempoMensaje_ = 4.0f;
}
