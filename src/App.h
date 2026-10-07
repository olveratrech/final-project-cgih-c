// App.h - Ventana, bucle principal, entrada del usuario e interfaz.
#pragma once

#include "render/Renderer.h"
#include "scene/Camera.h"
#include "scene/Escena.h"

#include <memory>
#include <string>

struct GLFWwindow;

struct Opciones {
    int ancho = 0;              // 0 = automático (80 % del monitor)
    int alto = 0;
    int msaa = 4;               // muestras de antialiasing (0 = desactivado)
    std::string captura;        // si no está vacío: guarda una imagen y termina
    int frames = 4;             // cuadros a dibujar antes de la captura automática
    int vista = -1;             // vista inicial (1..7)
    std::string galeria;        // modelo inicial de la galería
    bool sinInterfaz = false;
    bool alambre = false;
    std::string seleccion;      // nodo seleccionado al iniciar (para capturas)
};

enum class Modo { Escena, Galeria };

class App {
public:
    int ejecutar(const Opciones& opciones);

private:
    bool iniciar();
    void terminar();
    void procesarEntrada(float dt);
    void actualizarGaleria(float dt);
    void seleccionarModeloGaleria(int indice);
    void aplicarVista(int indice);
    void cambiarModo(Modo m);
    void capturar(const std::string& ruta);
    std::string capturaAutomatica() const;
    Nodo* seleccionarConRayo(double x, double y);
    void enfocar(Nodo* n);

    // interfaz (Interfaz.cpp)
    void iniciarInterfaz();
    void dibujarInterfaz();
    void panelPrincipal();
    void panelJerarquia();
    void panelInspector();
    void panelGaleria();
    void panelAyuda();
    void arbolNodo(Nodo* n, int profundidad);

    static void alTeclear(GLFWwindow* v, int tecla, int codigo, int accion, int mods);
    static void alDesplazar(GLFWwindow* v, double dx, double dy);
    static void alPulsar(GLFWwindow* v, int boton, int accion, int mods);

    GLFWwindow* ventana_ = nullptr;
    Opciones op_;
    Escena escena_;
    Renderer renderer_;
    Camara camara_;
    Camara camaraGaleria_;
    Modo modo_ = Modo::Escena;
    Nodo* seleccion_ = nullptr;
    Nodo* seleccionAnterior_ = nullptr;  // para abrir el árbol solo cuando cambia la selección
    bool cambioSeleccion_ = false;

    std::unique_ptr<Nodo> vitrina_;
    Nodo* giro_ = nullptr;
    int modeloGaleria_ = 0;
    bool girar_ = true;

    bool mostrarInterfaz_ = true;
    bool mostrarAyuda_ = false;
    bool mostrarSeleccion_ = true;
    bool mostrarCielo_ = true;
    bool arrastrando_ = false;
    bool clicPendiente_ = false;
    double ultimoX_ = 0.0, ultimoY_ = 0.0, clicX_ = 0.0, clicY_ = 0.0;
    int anchoFb_ = 1, altoFb_ = 1;
    float fps_ = 0.0f, msCuadro_ = 0.0f;
    int vistaActual_ = 0;
    std::string mensaje_;
    float tiempoMensaje_ = 0.0f;
};
