// Interfaz.cpp - Paneles de Dear ImGui: rendimiento, vistas, jerarquía de la
// escena, inspector de transformaciones geométricas, galería de modelos y ayuda.
#include "App.h"

#include "Rutas.h"

#include <GLFW/glfw3.h>
#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>

#include <glm/gtc/type_ptr.hpp>

#include <cstdio>
#include <filesystem>
#include <functional>
#include <set>

namespace {

const ImVec4 kNaranja(0.98f, 0.55f, 0.10f, 1.0f);
const ImVec4 kRosa(0.89f, 0.05f, 0.49f, 1.0f);
const ImVec4 kMorado(0.48f, 0.17f, 0.75f, 1.0f);
const ImVec4 kAzul(0.40f, 0.65f, 1.0f, 1.0f);
const ImVec4 kVerde(0.45f, 0.85f, 0.45f, 1.0f);
const ImVec4 kGris(0.70f, 0.70f, 0.72f, 1.0f);

ImVec4 colorCategoria(const std::string& c) {
    if (c == "propio") return kNaranja;
    if (c == "librería") return kAzul;
    if (c == "procedural") return kVerde;
    return kGris;
}

void estiloMexicano() {
    ImGuiStyle& s = ImGui::GetStyle();
    ImGui::StyleColorsDark(&s);
    s.WindowRounding = 6.0f;
    s.FrameRounding = 4.0f;
    s.GrabRounding = 4.0f;
    s.WindowBorderSize = 0.0f;
    s.WindowPadding = ImVec2(10, 8);
    ImVec4* c = s.Colors;
    c[ImGuiCol_WindowBg] = ImVec4(0.09f, 0.06f, 0.10f, 0.88f);
    c[ImGuiCol_TitleBg] = ImVec4(0.36f, 0.10f, 0.40f, 0.95f);
    c[ImGuiCol_TitleBgActive] = ImVec4(0.55f, 0.12f, 0.45f, 1.0f);
    c[ImGuiCol_TitleBgCollapsed] = ImVec4(0.30f, 0.08f, 0.32f, 0.8f);
    c[ImGuiCol_Header] = ImVec4(0.75f, 0.35f, 0.05f, 0.45f);
    c[ImGuiCol_HeaderHovered] = ImVec4(0.90f, 0.45f, 0.08f, 0.70f);
    c[ImGuiCol_HeaderActive] = ImVec4(0.98f, 0.55f, 0.10f, 0.90f);
    c[ImGuiCol_Button] = ImVec4(0.55f, 0.12f, 0.45f, 0.70f);
    c[ImGuiCol_ButtonHovered] = ImVec4(0.89f, 0.05f, 0.49f, 0.85f);
    c[ImGuiCol_ButtonActive] = ImVec4(0.98f, 0.55f, 0.10f, 1.0f);
    c[ImGuiCol_FrameBg] = ImVec4(0.22f, 0.12f, 0.24f, 0.85f);
    c[ImGuiCol_FrameBgHovered] = ImVec4(0.38f, 0.16f, 0.38f, 0.85f);
    c[ImGuiCol_CheckMark] = kNaranja;
    c[ImGuiCol_SliderGrab] = kNaranja;
    c[ImGuiCol_SliderGrabActive] = kRosa;
    c[ImGuiCol_Separator] = ImVec4(0.55f, 0.25f, 0.50f, 0.6f);
}

void tablaMatriz(const char* id, const glm::mat4& m) {
    if (ImGui::BeginTable(id, 4, ImGuiTableFlags_Borders | ImGuiTableFlags_SizingStretchSame)) {
        for (int fila = 0; fila < 4; ++fila) {
            ImGui::TableNextRow();
            for (int col = 0; col < 4; ++col) {
                ImGui::TableSetColumnIndex(col);
                ImGui::Text("%7.3f", m[col][fila]);  // GLM guarda por columnas
            }
        }
        ImGui::EndTable();
    }
}

int contarTriangulos(const Nodo* n) {
    int t = 0;
    if (n->modelo && n->malla >= 0)
        for (const auto& p : n->modelo->mallas[static_cast<size_t>(n->malla)].primitivas) t += p.indices / 3;
    if (n->lote && n->lote->modelo) t += n->lote->modelo->triangulos * n->lote->instancias();
    for (const auto& h : n->hijos) t += contarTriangulos(h.get());
    return t;
}

}  // namespace

void App::iniciarInterfaz() {
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = nullptr;  // no se escribe imgui.ini (la carpeta de instalación puede ser de solo lectura)
    std::string fuente = rutas::asset("fuentes/LiberationSans-Regular.ttf");
    if (std::filesystem::exists(std::filesystem::u8path(fuente)))
        io.Fonts->AddFontFromFileTTF(fuente.c_str(), 16.0f, nullptr, io.Fonts->GetGlyphRangesDefault());
    estiloMexicano();
    ImGui_ImplGlfw_InitForOpenGL(ventana_, true);
    ImGui_ImplOpenGL3_Init("#version 330 core");
}

void App::dibujarInterfaz() {
    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();
    cambioSeleccion_ = seleccion_ != seleccionAnterior_;
    seleccionAnterior_ = seleccion_;
    if (mostrarInterfaz_) {
        panelPrincipal();
        if (modo_ == Modo::Escena) {
            panelJerarquia();
            panelInspector();
        } else {
            panelGaleria();
        }
        if (mostrarAyuda_) panelAyuda();
    }
    if (tiempoMensaje_ > 0.0f && !mensaje_.empty()) {
        ImGuiViewport* vp = ImGui::GetMainViewport();
        ImGui::SetNextWindowPos(ImVec2(vp->Size.x * 0.5f, vp->Size.y - 40.0f), ImGuiCond_Always, ImVec2(0.5f, 0.5f));
        ImGui::SetNextWindowBgAlpha(0.75f);
        ImGui::Begin("##mensaje", nullptr,
                     ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_AlwaysAutoResize | ImGuiWindowFlags_NoInputs);
        ImGui::TextUnformatted(mensaje_.c_str());
        ImGui::End();
    }
    ImGui::Render();
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
}

void App::panelPrincipal() {
    ImGui::SetNextWindowPos(ImVec2(10, 10), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(330, 0), ImGuiCond_FirstUseEver);
    ImGui::Begin("Camino de Cempasúchil", nullptr, ImGuiWindowFlags_AlwaysAutoResize);
    ImGui::TextColored(kNaranja, "Día de Muertos  |  CGeIHC - FI UNAM");
    ImGui::TextColored(kGris, "Entrega 2: modelado geométrico y jerárquico");
    ImGui::Separator();

    const Estadisticas& st = renderer_.stats;
    ImGui::Text("%.0f FPS  (%.2f ms por cuadro)", fps_, msCuadro_);
    ImGui::Text("Llamadas de dibujo: %d   Descartadas: %d", st.llamadas, st.descartados);
    ImGui::Text("Triángulos: %d   Instancias: %d", st.triangulos, st.instancias);
    ImGui::Text("Texturas: %d (%.1f MB en GPU)", escena_.texturas.cantidad(),
                static_cast<double>(escena_.texturas.bytesGPU()) / (1024.0 * 1024.0));
    ImGui::Separator();

    int modo = modo_ == Modo::Escena ? 0 : 1;
    if (ImGui::RadioButton("Escena", modo == 0)) cambiarModo(Modo::Escena);
    ImGui::SameLine();
    if (ImGui::RadioButton("Galería de modelos [G]", modo == 1)) cambiarModo(Modo::Galeria);

    if (modo_ == Modo::Escena) {
        if (ImGui::CollapsingHeader("Vistas de cámara [1-7]", ImGuiTreeNodeFlags_DefaultOpen)) {
            const auto& vistas = escena_.vistas();
            for (size_t i = 0; i < vistas.size(); ++i) {
                char etiqueta[96];
                std::snprintf(etiqueta, sizeof(etiqueta), "%zu. %s", i + 1, vistas[i].nombre.c_str());
                if (ImGui::Selectable(etiqueta, vistaActual_ == static_cast<int>(i))) aplicarVista(static_cast<int>(i));
            }
            ImGui::SliderFloat("Velocidad (m/s)", &camara_.velocidad, 0.5f, 40.0f, "%.1f", ImGuiSliderFlags_Logarithmic);
            ImGui::Text("Cámara: (%.1f, %.1f, %.1f)", camara_.posicion.x, camara_.posicion.y, camara_.posicion.z);
        }
    }
    if (ImGui::CollapsingHeader("Visualización")) {
        ImGui::Checkbox("Malla de alambre [F2]", &renderer_.alambre);
        ImGui::Checkbox("Resaltar selección y ejes locales [F3]", &mostrarSeleccion_);
        ImGui::Checkbox("Skybox (cube map)", &mostrarCielo_);
        ImGui::Checkbox("Niebla atmosférica", &renderer_.niebla);
        ImGui::Checkbox("Descarte por frustum", &renderer_.descartar);
    }
    if (ImGui::Button("Ayuda [F1]")) mostrarAyuda_ = !mostrarAyuda_;
    ImGui::SameLine();
    if (ImGui::Button("Captura [F12]")) capturar(capturaAutomatica());
    ImGui::SameLine();
    if (ImGui::Button("Ocultar [F4]")) mostrarInterfaz_ = false;
    ImGui::End();
}

void App::arbolNodo(Nodo* n, int profundidad) {
    ImGuiTreeNodeFlags f = ImGuiTreeNodeFlags_OpenOnArrow | ImGuiTreeNodeFlags_OpenOnDoubleClick |
                           ImGuiTreeNodeFlags_SpanAvailWidth;
    if (n->hijos.empty()) f |= ImGuiTreeNodeFlags_Leaf | ImGuiTreeNodeFlags_NoTreePushOnOpen;
    if (n == seleccion_) f |= ImGuiTreeNodeFlags_Selected;
    if (profundidad < 1) f |= ImGuiTreeNodeFlags_DefaultOpen;
    // al cambiar la selección se abre la rama que la contiene
    if (cambioSeleccion_ && seleccion_) {
        for (Nodo* p = seleccion_->padre; p; p = p->padre)
            if (p == n) ImGui::SetNextItemOpen(true, ImGuiCond_Always);
    }
    ImGui::PushStyleColor(ImGuiCol_Text, colorCategoria(n->categoria));
    std::string etiqueta = n->nombre;
    if (n->lote) etiqueta += "  (" + std::to_string(n->lote->instancias()) + " instancias)";
    bool abierto = ImGui::TreeNodeEx(static_cast<void*>(n), f, "%s", etiqueta.c_str());
    ImGui::PopStyleColor();
    if (ImGui::IsItemClicked() && !ImGui::IsItemToggledOpen()) seleccion_ = n;
    if (n == seleccion_ && cambioSeleccion_) ImGui::SetScrollHereY();
    if (abierto && !n->hijos.empty()) {
        for (auto& h : n->hijos) arbolNodo(h.get(), profundidad + 1);
        ImGui::TreePop();
    }
}

void App::panelJerarquia() {
    ImGuiViewport* vp = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(ImVec2(vp->Size.x - 370, vp->Size.y * 0.50f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(360, vp->Size.y * 0.48f), ImGuiCond_FirstUseEver);
    ImGui::Begin("Jerarquía de la escena");
    ImGui::TextColored(kNaranja, "propio");
    ImGui::SameLine();
    ImGui::TextColored(kAzul, "librería");
    ImGui::SameLine();
    ImGui::TextColored(kVerde, "procedural");
    ImGui::SameLine();
    ImGui::TextColored(kGris, "grupo");
    ImGui::TextColored(kGris, "Clic en la escena o en el árbol para seleccionar");
    ImGui::Separator();
    ImGui::BeginChild("arbol");
    arbolNodo(escena_.raiz(), 0);
    ImGui::EndChild();
    ImGui::End();
}

void App::panelInspector() {
    ImGuiViewport* vp = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(ImVec2(vp->Size.x - 370, 10), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(360, 0), ImGuiCond_FirstUseEver);
    ImGui::Begin("Transformaciones geométricas", nullptr, ImGuiWindowFlags_AlwaysAutoResize);
    if (!seleccion_) {
        ImGui::TextWrapped("Selecciona un objeto con clic izquierdo (Ctrl + clic selecciona la pieza exacta) o "
                           "desde el árbol de jerarquía.");
        ImGui::End();
        return;
    }
    Nodo* n = seleccion_;
    ImGui::TextColored(colorCategoria(n->categoria), "%s", n->nombre.c_str());
    if (n->modelo) ImGui::Text("Modelo: %s", n->modelo->nombre.c_str());
    ImGui::Text("Padre: %s   Hijos: %zu", n->padre ? n->padre->nombre.c_str() : "(ninguno)", n->hijos.size());
    ImGui::Text("Triángulos del subárbol: %d", contarTriangulos(n));
    ImGui::Separator();

    ImGui::DragFloat3("Traslación (m)", glm::value_ptr(n->posicion), 0.01f);
    ImGui::DragFloat3("Rotación (°)", glm::value_ptr(n->rotacion), 0.5f, -360.0f, 360.0f);
    static bool uniforme = true;
    if (uniforme) {
        float e = n->escala.x;
        if (ImGui::DragFloat("Escala", &e, 0.005f, 0.01f, 50.0f)) n->escala = glm::vec3(e);
    } else {
        ImGui::DragFloat3("Escala", glm::value_ptr(n->escala), 0.005f, 0.01f, 50.0f);
    }
    ImGui::Checkbox("Escala uniforme", &uniforme);
    ImGui::SameLine();
    ImGui::Checkbox("Visible", &n->visible);
    if (ImGui::Button("Restablecer [Retroceso]")) n->restablecer();
    ImGui::SameLine();
    if (ImGui::Button("Padre [N]") && n->padre) seleccion_ = n->padre;
    ImGui::SameLine();
    if (ImGui::Button("Enfocar [F]")) enfocar(n);

    if (ImGui::CollapsingHeader("Matrices (M = T · R · S)", ImGuiTreeNodeFlags_DefaultOpen)) {
        ImGui::TextColored(kGris, "Local (relativa al padre):");
        tablaMatriz("local", n->local);
        ImGui::TextColored(kGris, "Mundo = Mundo(padre) · Local:");
        tablaMatriz("mundo", n->mundo);
    }
    ImGui::TextColored(kGris, "Flechas/RePág/AvPág: mover   Z/X: girar   C/V: escalar");
    ImGui::End();
}

void App::panelGaleria() {
    auto& cat = escena_.catalogo();
    ImGuiViewport* vp = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(ImVec2(vp->Size.x - 390, 10), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(380, vp->Size.y - 20), ImGuiCond_FirstUseEver);
    ImGui::Begin("Galería de modelos");
    int propios = 0, libreria = 0;
    for (const auto& i : cat) {
        if (i.origen == "Propio") ++propios;
        else if (i.origen == "Librería") ++libreria;
    }
    ImGui::Text("%d modelos propios  |  %d de librería", propios, libreria);
    ImGui::TextColored(kGris, "Flechas izquierda/derecha: cambiar   Espacio: girar");
    ImGui::Separator();

    const InfoModelo& sel = cat[static_cast<size_t>(modeloGaleria_)];
    const Modelo& m = *sel.modelo;
    ImGui::TextColored(sel.origen == "Propio" ? kNaranja : sel.origen == "Librería" ? kAzul : kVerde, "%s",
                       sel.titulo.c_str());
    ImGui::TextWrapped("%s", sel.descripcion.c_str());
    ImGui::Text("Origen: %s   Archivo: %s", sel.origen.c_str(), sel.clave.c_str());
    ImGui::Text("Triángulos: %d   Vértices: %d", m.triangulos, m.vertices);
    ImGui::Text("Nodos: %zu   Mallas: %zu   Materiales: %zu", m.nodos.size(), m.mallas.size(), m.materiales.size());
    glm::vec3 tam = m.max - m.min;
    ImGui::Text("Tamaño: %.2f x %.2f x %.2f m", tam.x, tam.y, tam.z);
    ImGui::Text("Usos en la escena: %d", sel.usos);
    std::set<std::string> tex;
    for (const auto& mat : m.materiales)
        if (mat.textura) tex.insert(std::filesystem::u8path(mat.textura->ruta).filename().u8string());
    std::string lista;
    for (const auto& t : tex) lista += (lista.empty() ? "" : ", ") + t;
    ImGui::TextWrapped("Texturas: %s", lista.empty() ? "(solo color de material)" : lista.c_str());
    ImGui::Checkbox("Girar [Espacio]", &girar_);
    ImGui::SameLine();
    ImGui::Checkbox("Alambre [F2]", &renderer_.alambre);

    if (ImGui::CollapsingHeader("Jerarquía del modelo", ImGuiTreeNodeFlags_DefaultOpen)) {
        std::function<void(int)> rama = [&](int i) {
            const NodoModelo& nm = m.nodos[static_cast<size_t>(i)];
            ImGuiTreeNodeFlags f = ImGuiTreeNodeFlags_DefaultOpen;
            if (nm.hijos.empty()) f |= ImGuiTreeNodeFlags_Leaf;
            if (ImGui::TreeNodeEx(nm.nombre.c_str(), f, "%s%s", nm.nombre.c_str(), nm.malla >= 0 ? "  [malla]" : "")) {
                for (int h : nm.hijos) rama(h);
                ImGui::TreePop();
            }
        };
        for (int r : m.raices) rama(r);
    }
    ImGui::Separator();
    ImGui::BeginChild("lista");
    const char* grupos[] = {"Propio", "Librería", "Procedural"};
    const char* titulos[] = {"Modelos propios (Blender)", "Librería: Kenney Graveyard Kit (CC0)", "Procedurales (código)"};
    for (int g = 0; g < 3; ++g) {
        ImGui::TextColored(g == 0 ? kNaranja : g == 1 ? kAzul : kVerde, "%s", titulos[g]);
        for (size_t i = 0; i < cat.size(); ++i) {
            if (cat[i].origen != grupos[g]) continue;
            char etiqueta[160];
            std::snprintf(etiqueta, sizeof(etiqueta), "  %s  (%d tri)", cat[i].titulo.c_str(), cat[i].modelo->triangulos);
            if (ImGui::Selectable(etiqueta, static_cast<int>(i) == modeloGaleria_))
                seleccionarModeloGaleria(static_cast<int>(i));
        }
    }
    ImGui::EndChild();
    ImGui::End();
}

void App::panelAyuda() {
    ImGuiViewport* vp = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(ImVec2(vp->Size.x * 0.5f, vp->Size.y * 0.5f), ImGuiCond_FirstUseEver, ImVec2(0.5f, 0.5f));
    ImGui::Begin("Ayuda - controles", &mostrarAyuda_, ImGuiWindowFlags_AlwaysAutoResize);
    auto fila = [](const char* tecla, const char* accion) {
        ImGui::TableNextRow();
        ImGui::TableSetColumnIndex(0);
        ImGui::TextColored(kNaranja, "%s", tecla);
        ImGui::TableSetColumnIndex(1);
        ImGui::TextUnformatted(accion);
    };
    if (ImGui::BeginTable("ayuda", 2, ImGuiTableFlags_RowBg | ImGuiTableFlags_Borders)) {
        fila("W A S D", "Moverse (adelante, izquierda, atrás, derecha)");
        fila("Q / E", "Bajar / subir");
        fila("Shift / Ctrl", "Más rápido / más lento");
        fila("Clic derecho + ratón", "Mirar alrededor (en la galería: orbitar)");
        fila("Rueda del ratón", "Velocidad de la cámara (galería: acercar)");
        fila("Clic izquierdo", "Seleccionar objeto (Ctrl + clic: pieza exacta)");
        fila("Flechas, RePág, AvPág", "Trasladar el objeto seleccionado");
        fila("Z / X", "Rotar el objeto seleccionado sobre Y");
        fila("C / V", "Reducir / aumentar escala");
        fila("Retroceso", "Restablecer transformación");
        fila("N  /  F", "Seleccionar el padre  /  enfocar la cámara");
        fila("1 ... 7", "Vistas predefinidas");
        fila("G", "Galería de modelos (flechas para cambiar)");
        fila("F2 / F3 / F4", "Alambre / resaltar selección / ocultar interfaz");
        fila("F12 o P", "Captura de pantalla (carpeta Imágenes)");
        fila("Esc", "Salir de la galería / quitar selección / cerrar");
        ImGui::EndTable();
    }
    ImGui::End();
}
