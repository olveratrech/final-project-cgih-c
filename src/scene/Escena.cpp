#include "scene/Escena.h"

#include "Registro.h"
#include "Rutas.h"

#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/quaternion.hpp>

#include <algorithm>
#include <cmath>
#include <random>

namespace {

// Catálogo de modelos: clave de archivo, título, descripción y origen.
struct Ficha {
    const char* clave;
    const char* titulo;
    const char* descripcion;
};

const Ficha kPropios[] = {
    {"altar_muertos", "Altar de muertos",
     "Tres niveles escalonados (tierra, purgatorio y cielo) con mantel bordado, estructura de madera biselada y "
     "petate. Cada nivel es hijo del anterior."},
    {"arco_cempasuchil", "Arco de cempasúchil",
     "Marco de carrizo cubierto de cempasúchil y mano de león; simboliza la puerta entre el mundo de los vivos y el "
     "de los muertos."},
    {"flor_cempasuchil", "Flor de cempasúchil", "Cabeza de 39 pétalos en 4 anillos, cáliz, tallo y hojas."},
    {"petalo_cempasuchil", "Pétalo de cempasúchil",
     "Pieza de 8 triángulos que forma el camino de flores; se dibuja miles de veces con instanciado."},
    {"veladora", "Veladora", "Vaso de vidrio pintado, cera, mecha y flama emisiva como nodo independiente."},
    {"cirio", "Cirio con candelero", "Vela alta con escurrimientos sobre un candelero de barro torneado."},
    {"pan_de_muerto", "Pan de muerto", "Domo de masa con cuatro huesitos y la bolita superior."},
    {"calaverita_azucar", "Calaverita de azúcar",
     "Esfera deformada con cuencas y mandíbula; textura decorada con proyección frontal."},
    {"papel_picado", "Papel picado",
     "Cordel en catenaria con 8 banderitas articuladas; una sola textura con recorte alfa y color por material."},
    {"sahumerio", "Sahumerio (popoxcomitl)", "Copalero de barro con mango, brasas emisivas y copal."},
    {"portarretrato", "Portarretrato", "Marco de hojalata repujada con la fotografía del difunto y pata trasera."},
    {"jarron_talavera", "Jarrón de Talavera", "Cerámica poblana esmaltada en azul cobalto (superficie de revolución)."},
    {"vaso_agua", "Vaso con agua", "Vidrio y agua translúcidos para calmar la sed de las ánimas."},
    {"maceta_cempasuchil", "Maceta con cempasúchil", "Maceta de barro con siete flores combinadas en una sola malla."},
    {"mariposa_monarca", "Mariposa monarca", "Cuerpo y alas articuladas con recorte alfa, listas para el aleteo."},
    {"farol", "Farol de hojalata", "Poste, brazo, lámpara hexagonal con vidrios de colores y vela (4 niveles)."},
    {"entrada_panteon", "Portada del panteón",
     "Pilastras, arco de medio punto, ático con letrero, cruz y reja de dos hojas con bisagras."},
    {"casa_adobe", "Casa de adobe con portal",
     "Muros con vanos, guardapolvo rojo, techo de teja a dos aguas, portal con horcones, puerta y ventana."},
};

const Ficha kLibreria[] = {
    {"grave", "Tumba de tierra", "Kenney Graveyard Kit (CC0)."},
    {"grave-border", "Tumba con bordillo", "Kenney Graveyard Kit (CC0)."},
    {"gravestone-cross", "Lápida con cruz", "Kenney Graveyard Kit (CC0)."},
    {"gravestone-round", "Lápida redonda", "Kenney Graveyard Kit (CC0)."},
    {"gravestone-bevel", "Lápida biselada", "Kenney Graveyard Kit (CC0)."},
    {"gravestone-decorative", "Lápida decorativa", "Kenney Graveyard Kit (CC0)."},
    {"cross-wood", "Cruz de madera", "Kenney Graveyard Kit (CC0)."},
    {"cross-column", "Cruz atrial", "Kenney Graveyard Kit (CC0)."},
    {"crypt", "Cripta", "Kenney Graveyard Kit (CC0)."},
    {"iron-fence", "Reja de hierro", "Kenney Graveyard Kit (CC0)."},
    {"stone-wall", "Barda de piedra", "Kenney Graveyard Kit (CC0)."},
    {"stone-wall-column", "Columna de barda", "Kenney Graveyard Kit (CC0)."},
    {"pine", "Ciprés", "Kenney Graveyard Kit (CC0)."},
    {"pine-crooked", "Ciprés torcido", "Kenney Graveyard Kit (CC0)."},
    {"bench", "Banca", "Kenney Graveyard Kit (CC0)."},
    {"urn-round", "Urna funeraria", "Kenney Graveyard Kit (CC0)."},
    {"pumpkin", "Calabaza de Castilla", "Kenney Graveyard Kit (CC0). Ingrediente de la calabaza en tacha."},
    {"pumpkin-tall", "Calabaza alargada", "Kenney Graveyard Kit (CC0)."},
    {"rocks", "Rocas", "Kenney Graveyard Kit (CC0)."},
    {"candle-multiple", "Velas", "Kenney Graveyard Kit (CC0)."},
    {"detail-bowl", "Cazuela", "Kenney Graveyard Kit (CC0). Representa la cazuela de mole."},
    {"detail-plate", "Plato", "Kenney Graveyard Kit (CC0)."},
    {"character-skeleton", "Esqueleto (calaca)", "Kenney Graveyard Kit (CC0). Personaje jerárquico de 8 nodos."},
    {"character-ghost", "Ánima", "Kenney Graveyard Kit (CC0). Personaje jerárquico."},
    {"character-keeper", "Panteonero", "Kenney Graveyard Kit (CC0). Personaje jerárquico de 8 nodos."},
};

// Generador pseudoaleatorio con semilla fija: la escena es idéntica en cada ejecución.
struct Azar {
    std::mt19937 gen{20261102u};
    float operator()(float a, float b) { return std::uniform_real_distribution<float>(a, b)(gen); }
    float normal(float sigma) { return std::normal_distribution<float>(0.0f, sigma)(gen); }
};

glm::mat4 trs(const glm::vec3& p, float rotYgrados, float escala = 1.0f) {
    return glm::translate(glm::mat4(1.0f), p) * glm::rotate(glm::mat4(1.0f), glm::radians(rotYgrados), {0, 1, 0}) *
           glm::scale(glm::mat4(1.0f), glm::vec3(escala));
}

// Ángulo (grados) que alinea el eje local +X con la dirección horizontal d.
float alinearX(const glm::vec3& d) { return glm::degrees(std::atan2(-d.z, d.x)); }
// Ángulo (grados) que alinea el eje local +Z (frente de los modelos) con d.
float alinearZ(const glm::vec3& d) { return glm::degrees(std::atan2(d.x, d.z)); }

}  // namespace

// ---------------------------------------------------------------------------
// Carga
// ---------------------------------------------------------------------------
bool Escena::cargar() {
    if (!cargarModelos()) return false;
    crearProcedurales();
    if (!cielo.iniciar(rutas::asset("skybox/atardecer"), texturas))
        registro::error("No se pudo cargar el skybox; se usará un color de fondo");

    raiz_ = std::make_unique<Nodo>("Escena");
    raiz_->categoria = "grupo";
    Nodo* terreno = raiz_->agregar("Terreno");
    Nodo* suelo = terreno->agregar("suelo");
    suelo->modelo = modelo("terreno");
    suelo->malla = 0;
    suelo->categoria = "procedural";
    info("terreno")->usos++;

    construirCasaYOfrenda();
    construirCamino();
    construirPanteon();
    construirAlrededores();

    for (auto& l : lotes_) l->subir();
    raiz_->actualizar(glm::mat4(1.0f));

    const glm::vec3 alto(0.0f, 1.0f, 0.0f);
    vistas_ = {
        {"Vista general", {-17.0f, 12.0f, 26.0f}, {0.0f, 0.0f, 2.0f}},
        {"Entrada del panteón", {1.2f, 1.7f, 8.5f}, {0.0f, 2.2f, 16.0f}},
        {"Camino de pétalos", camino.punto(3.0f) + camino.izquierda(3.0f) * 0.8f + alto * 1.5f,
         camino.punto(14.0f) + alto * 0.5f},
        {"Altar de muertos", {0.5f, 1.6f, -10.0f}, {0.0f, 1.15f, -15.2f}},
        {"Ofrenda (detalle)", {1.0f, 1.35f, -12.4f}, {0.0f, 0.95f, -15.1f}},
        {"Panteón", {-11.0f, 4.5f, 15.0f}, {0.0f, 0.5f, 26.0f}},
        {"Vista aérea", {0.0f, 60.0f, 21.0f}, {0.0f, 0.0f, 6.0f}},
    };
    for (const auto& i : catalogo_)
        if (i.usos == 0) registro::info("Aviso: el modelo %s no se usa en la escena", i.clave.c_str());
    registro::info("Escena lista: %d nodos, %d modelos distintos, %d instancias, %d texturas (%.1f MB)",
                   raiz_->contarNodos(), totalModelosDistintos(), totalInstancias(), texturas.cantidad(),
                   static_cast<double>(texturas.bytesGPU()) / (1024.0 * 1024.0));
    return true;
}

bool Escena::cargarModelos() {
    auto cargarUno = [&](const std::string& clave, const std::string& ruta, const Ficha& f, const char* origen) {
        auto m = std::make_unique<Modelo>();
        if (!m->cargar(ruta, texturas)) return false;
        catalogo_.push_back({clave, f.titulo, f.descripcion, origen, m.get(), 0});
        modelos_[clave] = std::move(m);
        return true;
    };
    for (const Ficha& f : kPropios)
        if (!cargarUno(f.clave, rutas::asset(std::string("models/propios/") + f.clave + ".gltf"), f, "Propio")) return false;
    for (const Ficha& f : kLibreria)
        if (!cargarUno(f.clave, rutas::asset(std::string("models/libreria/kenney_graveyard/") + f.clave + ".glb"), f,
                       "Librería"))
            return false;
    return true;
}

void Escena::crearProcedurales() {
    // Terreno: un solo cuadrilátero de 200 x 200 m (2 triángulos) con la textura repetida.
    {
        const float m = 100.0f;
        std::vector<Vertice> vs = {{{-m, 0, -m}, {0, 1, 0}, {-m, -m}},
                                   {{m, 0, -m}, {0, 1, 0}, {m, -m}},
                                   {{m, 0, m}, {0, 1, 0}, {m, m}},
                                   {{-m, 0, m}, {0, 1, 0}, {-m, m}}};
        std::vector<uint32_t> idx = {0, 2, 1, 0, 3, 2};
        Material mat;
        mat.nombre = "tierra";
        mat.textura = texturas.cargar(rutas::asset("textures/tierra.jpg"));
        mat.escalaUV = glm::vec2(1.0f / 2.5f);  // una repetición cada 2.5 m
        mat.color = glm::vec4(0.92f, 0.86f, 0.80f, 1.0f);
        modelos_["terreno"] = Modelo::procedural("terreno", vs, idx, mat);
        catalogo_.push_back({"terreno", "Terreno", "Plano de 200 x 200 m con textura repetida (2 triángulos).",
                             "Procedural", modelos_["terreno"].get(), 0});
    }
    // Pedestal para la galería de modelos (cilindro de 24 lados)
    {
        std::vector<Vertice> vs;
        std::vector<uint32_t> idx;
        const int n = 24;
        const float r = 1.0f, h = 0.08f;
        for (int i = 0; i <= n; ++i) {
            float a = 6.2831853f * static_cast<float>(i) / n;
            glm::vec3 d(std::cos(a), 0, std::sin(a));
            vs.push_back({d * r + glm::vec3(0, 0, 0), d, {static_cast<float>(i) / n * 4.0f, 0}});
            vs.push_back({d * r + glm::vec3(0, h, 0), d, {static_cast<float>(i) / n * 4.0f, 0.1f}});
        }
        for (int i = 0; i < n; ++i) {
            uint32_t b = static_cast<uint32_t>(2 * i);
            idx.insert(idx.end(), {b, b + 1, b + 2, b + 1, b + 3, b + 2});
        }
        uint32_t centro = static_cast<uint32_t>(vs.size());
        vs.push_back({{0, h, 0}, {0, 1, 0}, {0.5f, 0.5f}});
        for (int i = 0; i <= n; ++i) {
            float a = 6.2831853f * static_cast<float>(i) / n;
            vs.push_back({{std::cos(a) * r, h, std::sin(a) * r}, {0, 1, 0}, {0.5f + std::cos(a) * 0.5f, 0.5f + std::sin(a) * 0.5f}});
        }
        for (int i = 0; i < n; ++i)
            idx.insert(idx.end(), {centro, centro + 2 + static_cast<uint32_t>(i), centro + 1 + static_cast<uint32_t>(i)});
        Material mat;
        mat.nombre = "pedestal";
        mat.textura = texturas.cargar(rutas::asset("textures/cal.jpg"));
        mat.color = glm::vec4(0.75f, 0.72f, 0.70f, 1.0f);
        modelos_["pedestal"] = Modelo::procedural("pedestal", vs, idx, mat);
    }
}

Modelo* Escena::modelo(const std::string& clave) {
    auto it = modelos_.find(clave);
    return it == modelos_.end() ? nullptr : it->second.get();
}

InfoModelo* Escena::info(const std::string& clave) {
    for (auto& i : catalogo_)
        if (i.clave == clave) return &i;
    return nullptr;
}

int Escena::totalInstancias() const {
    int total = 0;
    for (const auto& i : catalogo_) total += i.usos;
    return total;
}

int Escena::totalModelosDistintos() const {
    int n = 0;
    for (const auto& i : catalogo_)
        if (i.usos > 0) ++n;
    return n;
}

void Escena::liberar() {
    raiz_.reset();
    lotes_.clear();
    modelos_.clear();
    cielo.liberar();
    texturas.liberar();
}

// ---------------------------------------------------------------------------
// Instancias y lotes
// ---------------------------------------------------------------------------
void Escena::replicar(const Modelo& m, int indice, Nodo* padre) {
    const NodoModelo& nm = m.nodos[static_cast<size_t>(indice)];
    auto n = std::make_unique<Nodo>(nm.nombre);
    n->posicion = nm.traslacion;
    n->rotacion = glm::degrees(glm::eulerAngles(nm.rotacion));
    n->escala = nm.escala;
    n->modelo = &m;
    n->malla = nm.malla;
    n->categoria = padre->categoria;
    n->guardarInicial();
    Nodo* ptr = padre->agregar(std::move(n));
    for (int h : nm.hijos) replicar(m, h, ptr);
}

Nodo* Escena::instanciar(const std::string& clave, Nodo* padre, const std::string& nombre, const glm::vec3& pos,
                         float rotY, float escala, bool contar) {
    Modelo* m = modelo(clave);
    if (!m) {
        registro::error("Modelo desconocido: %s", clave.c_str());
        return padre;
    }
    auto n = std::make_unique<Nodo>(nombre);
    InfoModelo* i = info(clave);
    n->categoria = i ? (i->origen == "Propio" ? "propio" : i->origen == "Librería" ? "librería" : "procedural") : "grupo";
    n->colocar(pos, glm::vec3(0.0f, rotY, 0.0f), glm::vec3(escala));
    n->raizInstancia = true;
    Nodo* ptr = padre->agregar(std::move(n));
    for (int r : m->raices) replicar(*m, r, ptr);
    if (i && contar) i->usos++;
    return ptr;
}

Lote* Escena::nuevoLote(const std::string& clave, Nodo* dueno) {
    auto l = std::make_unique<Lote>();
    l->modelo = modelo(clave);
    dueno->lote = l.get();
    lotes_.push_back(std::move(l));
    return lotes_.back().get();
}

Nodo* Escena::nodoLote(const std::string& clave, Nodo* padre, const std::string& nombre) {
    Nodo* n = padre->agregar(nombre);
    InfoModelo* i = info(clave);
    n->categoria = i && i->origen == "Propio" ? "propio" : "librería";
    nuevoLote(clave, n);
    return n;
}

// ---------------------------------------------------------------------------
// Casa con portal y ofrenda
// ---------------------------------------------------------------------------
void Escena::construirCasaYOfrenda() {
    Azar azar;
    Nodo* casa = raiz_->agregar("Casa");
    casa->colocar({0.0f, 0.0f, -16.0f});
    instanciar("casa_adobe", casa, "casa_adobe", {0, 0, 0});

    // La ofrenda se coloca sobre la banqueta del portal (0.15 m), frente al muro.
    Nodo* ofrenda = casa->agregar("Ofrenda");
    ofrenda->colocar({0.0f, 0.15f, 0.95f});
    Nodo* altar = instanciar("altar_muertos", ofrenda, "altar", {0, 0, 0});
    instanciar("arco_cempasuchil", ofrenda, "arco", {0.0f, 0.0f, -0.55f}, 0.0f, 0.95f);

    Nodo* n1 = altar->buscar("nivel_1");
    Nodo* n2 = altar->buscar("nivel_2");
    Nodo* n3 = altar->buscar("nivel_3");
    const float sup = 0.455f;  // superficie del mantel en el marco local de cada nivel

    // Nivel 1 (tierra): cirios, pan, veladoras, cazuela de mole y calaveritas
    for (float s : {-1.0f, 1.0f}) {
        instanciar("cirio", n1, s < 0 ? "cirio_izq" : "cirio_der", {s * 1.05f, sup, 0.58f});
        instanciar("pan_de_muerto", n1, s < 0 ? "pan_izq" : "pan_der", {s * 0.70f, sup, 0.58f}, azar(0, 90));
        instanciar("veladora", n1, s < 0 ? "veladora_n1_izq" : "veladora_n1_der", {s * 0.40f, sup, 0.60f});
        instanciar("calaverita_azucar", n1, s < 0 ? "calaverita_n1_izq" : "calaverita_n1_der",
                   {s * 0.20f, sup, 0.62f}, -s * 12.0f, 0.8f);
    }
    instanciar("detail-bowl", n1, "cazuela_mole", {0.10f, sup, 0.50f}, 0.0f, 0.9f);

    // Nivel 2 (purgatorio): jarrón con flores, agua, calaveritas y plato con pan
    Nodo* jarron = instanciar("jarron_talavera", n2, "jarron", {-0.72f, sup, 0.22f}, 20.0f);
    for (int k = 0; k < 3; ++k) {
        float a = 120.0f * static_cast<float>(k);
        Nodo* f = instanciar("flor_cempasuchil", jarron, "flor_jarron_" + std::to_string(k + 1),
                             {0.02f * std::cos(glm::radians(a)), 0.18f, 0.02f * std::sin(glm::radians(a))}, a);
        f->rotacion.x = 12.0f;
        f->escala = glm::vec3(1.25f);
        f->guardarInicial();
    }
    instanciar("vaso_agua", n2, "vaso_agua", {0.72f, sup, 0.22f});
    for (float s : {-1.0f, 1.0f})
        instanciar("calaverita_azucar", n2, s < 0 ? "calaverita_n2_izq" : "calaverita_n2_der", {s * 0.38f, sup, 0.24f},
                   -s * 8.0f);
    Nodo* plato = instanciar("detail-plate", n2, "plato", {0.0f, sup, 0.22f});
    instanciar("pan_de_muerto", plato, "pan_plato", {0.0f, 0.03f, 0.0f}, 30.0f, 0.75f);

    // Nivel 3 (cielo): fotografías de los difuntos, cruz, veladoras y calaveritas
    instanciar("cross-wood", n3, "cruz", {0.0f, sup, -0.62f}, 0.0f, 0.5f);
    instanciar("portarretrato", n3, "foto_izq", {-0.42f, sup, -0.30f}, 14.0f);
    instanciar("portarretrato", n3, "foto_centro", {0.0f, sup, -0.36f});
    instanciar("portarretrato", n3, "foto_der", {0.42f, sup, -0.30f}, -14.0f);
    for (float s : {-1.0f, 1.0f}) {
        instanciar("veladora", n3, s < 0 ? "veladora_n3_izq" : "veladora_n3_der", {s * 0.60f, sup, -0.05f});
        instanciar("calaverita_azucar", n3, s < 0 ? "calaverita_n3_izq" : "calaverita_n3_der", {s * 0.22f, sup, -0.02f},
                   -s * 10.0f, 0.75f);
    }

    // Piso frente al altar: sahumerio, veladoras, macetas, calabazas y cruz de pétalos
    instanciar("sahumerio", ofrenda, "sahumerio", {0.0f, 0.012f, 1.20f}, 35.0f);
    int k = 0;
    for (const glm::vec3& p : {glm::vec3(-0.55f, 0.012f, 1.0f), glm::vec3(0.55f, 0.012f, 1.0f),
                               glm::vec3(-0.75f, 0.012f, 1.6f), glm::vec3(0.75f, 0.012f, 1.6f)})
        instanciar("veladora", ofrenda, "veladora_piso_" + std::to_string(++k), p);
    for (float s : {-1.0f, 1.0f}) {
        instanciar("maceta_cempasuchil", ofrenda, s < 0 ? "maceta_izq" : "maceta_der", {s * 1.55f, 0.0f, 0.25f}, s * 40.0f);
        instanciar(s < 0 ? "pumpkin" : "pumpkin-tall", ofrenda, s < 0 ? "calabaza_izq" : "calabaza_der",
                   {s * 1.55f, 0.0f, 0.95f}, s * 25.0f, 0.85f);
    }
    Nodo* cruzPetalos = nodoLote("petalo_cempasuchil", ofrenda, "cruz_de_petalos");
    for (int i = 0; i < 520; ++i) {
        glm::vec3 p;
        if (i % 3 == 0) p = {azar(-0.42f, 0.42f), 0.0f, 1.30f + azar(-0.07f, 0.07f)};
        else p = {azar(-0.07f, 0.07f), 0.0f, azar(0.95f, 1.95f)};
        p.y = 0.014f + azar(0.0f, 0.004f);
        cruzPetalos->lote->agregar(trs(p, azar(0, 360), azar(0.8f, 1.2f)));
    }
    info("petalo_cempasuchil")->usos += 520;

    // Papel picado colgado bajo el techo del portal
    k = 0;
    for (float z : {1.75f, 2.75f})
        for (float x : {-1.6f, 1.6f}) {
            Nodo* p = instanciar("papel_picado", casa, "papel_picado_portal_" + std::to_string(++k), {x, 2.45f, z});
            p->rotacion.y = azar(-4.0f, 4.0f);
            p->guardarInicial();
        }

    // Faroles a los lados de la entrada del portal (el brazo apunta al centro)
    instanciar("farol", casa, "farol_portal_izq", {-4.3f, 0.0f, 3.7f}, 0.0f);
    instanciar("farol", casa, "farol_portal_der", {4.3f, 0.0f, 3.7f}, 180.0f);
    instanciar("pumpkin", casa, "calabaza_portal_1", {-2.6f, 0.15f, 2.9f}, 15.0f);
    instanciar("pumpkin", casa, "calabaza_portal_2", {-2.25f, 0.15f, 3.05f}, 70.0f, 0.75f);
    instanciar("pumpkin-tall", casa, "calabaza_portal_3", {2.5f, 0.15f, 2.95f}, -30.0f, 0.9f);
    instanciar("maceta_cempasuchil", casa, "maceta_portal_1", {-3.2f, 0.15f, 2.4f}, 10.0f);
    instanciar("maceta_cempasuchil", casa, "maceta_portal_2", {3.2f, 0.15f, 2.4f}, -20.0f);

    // Mariposas monarca alrededor del arco
    k = 0;
    for (const glm::vec3& p : {glm::vec3(-1.1f, 2.5f, 1.6f), glm::vec3(0.8f, 2.2f, 2.3f), glm::vec3(1.7f, 1.6f, 1.2f)}) {
        Nodo* m = instanciar("mariposa_monarca", casa, "mariposa_portal_" + std::to_string(++k), p, azar(0, 360), 1.5f);
        m->rotacion.x = azar(-15.0f, 15.0f);
        m->guardarInicial();
    }
}

// ---------------------------------------------------------------------------
// Camino de cempasúchil
// ---------------------------------------------------------------------------
void Escena::construirCamino() {
    Azar azar;
    Nodo* grupo = raiz_->agregar("Camino de cempasúchil");

    camino.construir({{0.0f, 0.0f, 19.0f},
                      {0.0f, 0.0f, 14.0f},
                      {-2.2f, 0.0f, 8.5f},
                      {1.6f, 0.0f, 2.5f},
                      {-1.3f, 0.0f, -3.5f},
                      {0.6f, 0.0f, -8.5f},
                      {0.0f, 0.0f, -12.5f}});
    const float L = camino.longitud();

    // Franja empedrada (malla procedural)
    {
        std::vector<Vertice> vs;
        std::vector<uint32_t> idx;
        camino.malla(2.7f, 1.6f, 0.008f, vs, idx);
        Material mat;
        mat.nombre = "empedrado";
        mat.textura = texturas.cargar(rutas::asset("textures/empedrado.jpg"));
        mat.color = glm::vec4(0.85f, 0.83f, 0.80f, 1.0f);
        modelos_["camino_empedrado"] = Modelo::procedural("camino_empedrado", vs, idx, mat);
        catalogo_.push_back({"camino_empedrado", "Camino empedrado",
                             "Franja generada en código a partir de una spline Catmull-Rom centrípeta.", "Procedural",
                             modelos_["camino_empedrado"].get(), 1});
        Nodo* n = grupo->agregar("empedrado");
        n->modelo = modelos_["camino_empedrado"].get();
        n->malla = 0;
        n->categoria = "procedural";
    }

    // Alfombra de pétalos: franja con textura de recorte alfa (2 triángulos por tramo)
    {
        std::vector<Vertice> vs;
        std::vector<uint32_t> idx;
        const float ancho = 2.0f;
        camino.malla(ancho, ancho, 0.011f, vs, idx);
        Material mat;
        mat.nombre = "alfombra_petalos";
        mat.textura = texturas.cargar(rutas::asset("textures/alfombra_petalos.png"));
        mat.alfa = ModoAlfa::Recorte;
        modelos_["alfombra_petalos"] = Modelo::procedural("alfombra_petalos", vs, idx, mat);
        catalogo_.push_back({"alfombra_petalos", "Alfombra de pétalos",
                             "Franja procedural con textura de pétalos y recorte alfa; los pétalos 3D instanciados "
                             "agregan el relieve cercano.",
                             "Procedural", modelos_["alfombra_petalos"].get(), 1});
        Nodo* n = grupo->agregar("alfombra");
        n->modelo = modelos_["alfombra_petalos"].get();
        n->malla = 0;
        n->categoria = "procedural";
    }

    // Pétalos 3D: distribución normal alrededor del eje del camino (más densa al centro)
    Nodo* petalos = nodoLote("petalo_cempasuchil", grupo, "petalos");
    const int nPetalos = 7000;
    for (int i = 0; i < nPetalos; ++i) {
        float s = azar(0.3f, L - 0.2f);
        float lateral = std::clamp(azar.normal(0.36f), -1.05f, 1.05f);
        glm::vec3 p = camino.punto(s) + camino.izquierda(s) * lateral;
        p.y = 0.016f + azar(0.0f, 0.006f);
        glm::mat4 m = trs(p, azar(0, 360), azar(1.0f, 1.6f));
        m = m * glm::rotate(glm::mat4(1.0f), glm::radians(azar(-14.0f, 14.0f)), {1, 0, 0});
        glm::vec4 tinte(1.0f, azar(0.88f, 1.05f), azar(0.85f, 1.0f), 1.0f);
        if (azar(0, 1) < 0.05f) tinte = glm::vec4(0.95f, 0.30f, 0.45f, 1.0f);  // pétalos de mano de león
        petalos->lote->agregar(m, tinte);
    }
    info("petalo_cempasuchil")->usos += nPetalos;

    // Veladoras a ambos lados, cada 2.2 m
    Nodo* veladoras = nodoLote("veladora", grupo, "veladoras");
    int nVel = 0;
    for (float s = 1.2f; s < L - 0.8f; s += 2.2f)
        for (float lado : {-1.0f, 1.0f}) {
            glm::vec3 p = camino.punto(s + lado * 0.35f) + camino.izquierda(s) * (lado * 1.22f);
            p.y = 0.008f;
            veladoras->lote->agregar(trs(p, azar(0, 360)));
            ++nVel;
        }
    info("veladora")->usos += nVel;

    // Pares de faroles con una tira de papel picado entre ellos
    int k = 0;
    for (float s : {5.0f, 11.5f, 18.0f, 24.5f}) {
        ++k;
        glm::vec3 c = camino.punto(s);
        glm::vec3 izq = camino.izquierda(s);
        Nodo* par = grupo->agregar("faroles_" + std::to_string(k));
        par->colocar(c);
        // los brazos apuntan en el sentido del camino para no cruzarse con el papel picado
        float haciaCasa = alinearX(camino.tangente(s));
        instanciar("farol", par, "farol_izq", izq * 1.55f, haciaCasa);
        instanciar("farol", par, "farol_der", -izq * 1.55f, haciaCasa);
        Nodo* papel = instanciar("papel_picado", par, "papel_picado", {0.0f, 2.52f, 0.0f}, alinearX(-izq));
        papel->escala = glm::vec3(3.1f / 3.0f, 1.0f, 1.0f);  // claro de 3.1 m entre postes
        papel->guardarInicial();
    }

    // Bancas para descansar junto al camino
    for (const auto& [s, lado] : {std::pair<float, float>{8.0f, 1.0f}, {20.5f, -1.0f}}) {
        glm::vec3 izq = camino.izquierda(s);
        glm::vec3 p = camino.punto(s) + izq * (lado * 2.7f);
        instanciar("bench", grupo, "banca_" + std::to_string(static_cast<int>(s)), p, alinearZ(-izq * lado), 1.8f);
    }

    // Mariposas monarca sobre el camino (almas que regresan)
    k = 0;
    for (float s : {3.0f, 7.5f, 9.0f, 13.0f, 16.5f, 21.0f, 23.0f, 27.5f, 30.0f}) {
        glm::vec3 p = camino.punto(s) + camino.izquierda(s) * azar(-1.3f, 1.3f);
        p.y = azar(1.0f, 2.4f);
        Nodo* m = instanciar("mariposa_monarca", grupo, "mariposa_" + std::to_string(++k), p, azar(0, 360), 1.5f);
        m->rotacion.x = azar(-20.0f, 20.0f);
        m->rotacion.z = azar(-15.0f, 15.0f);
        m->guardarInicial();
    }

    // Personajes: una calaca camina hacia la ofrenda y un ánima la sigue
    {
        float s = 13.0f;
        Nodo* c = instanciar("character-skeleton", grupo, "calaca_caminante", camino.punto(s),
                             alinearZ(camino.tangente(s)), 2.0f);
        (void)c;
        float s2 = 9.0f;
        glm::vec3 p = camino.punto(s2) - camino.izquierda(s2) * 1.9f;
        p.y = 0.35f;
        instanciar("character-ghost", grupo, "anima", p, alinearZ(camino.tangente(s2)), 1.7f);
    }
}

// ---------------------------------------------------------------------------
// Panteón
// ---------------------------------------------------------------------------
void Escena::construirPanteon() {
    Azar azar;
    Nodo* panteon = raiz_->agregar("Panteón");
    instanciar("entrada_panteon", panteon, "portada", {0.0f, 0.0f, 16.0f}, 180.0f);
    instanciar("character-keeper", panteon, "panteonero", {3.4f, 0.0f, 14.6f}, 200.0f, 2.0f);

    // Pasillo central empedrado
    {
        Camino pasillo;
        pasillo.construir({{0.0f, 0.0f, 16.5f}, {0.0f, 0.0f, 31.5f}}, 4);
        std::vector<Vertice> vs;
        std::vector<uint32_t> idx;
        pasillo.malla(2.4f, 1.6f, 0.007f, vs, idx);
        Material mat = modelo("camino_empedrado")->materiales[0];
        modelos_["pasillo_panteon"] = Modelo::procedural("pasillo_panteon", vs, idx, mat);
        Nodo* n = panteon->agregar("pasillo");
        n->modelo = modelos_["pasillo_panteon"].get();
        n->malla = 0;
        n->categoria = "procedural";
    }

    // Reja frontal (12 tramos instanciados) y bardas de piedra (32 tramos)
    Nodo* reja = nodoLote("iron-fence", panteon, "reja_frontal");
    for (int i = 0; i < 6; ++i)
        for (float s : {-1.0f, 1.0f}) reja->lote->agregar(trs({s * (3.0f + 2.0f * i), 0.0f, 16.65f}, 0.0f, 2.0f));
    info("iron-fence")->usos += 12;

    Nodo* bardas = nodoLote("stone-wall", panteon, "bardas");
    for (int i = 0; i < 9; ++i) {
        float z = 17.0f + 2.0f * i;
        bardas->lote->agregar(trs({-13.2f, 0.0f, z}, 90.0f, 2.0f));
        bardas->lote->agregar(trs({13.2f, 0.0f, z}, -90.0f, 2.0f));
    }
    for (int i = 0; i < 14; ++i) bardas->lote->agregar(trs({-13.0f + 2.0f * i, 0.0f, 33.2f}, 180.0f, 2.0f));
    info("stone-wall")->usos += 32;
    Nodo* columnas = nodoLote("stone-wall-column", panteon, "columnas_barda");
    for (const glm::vec3& p : {glm::vec3(-14.0f, 0, 16.6f), glm::vec3(14.0f, 0, 16.6f), glm::vec3(-14.0f, 0, 34.0f),
                               glm::vec3(14.0f, 0, 34.0f)})
        columnas->lote->agregar(trs(p + glm::vec3(0, 0, 0.8f), 0.0f, 2.0f));
    info("stone-wall-column")->usos += 4;

    // Tumbas en tres filas a cada lado del pasillo, adornadas con flores y veladoras
    Nodo* tumbas = panteon->agregar("Tumbas");
    Nodo* flores = nodoLote("flor_cempasuchil", tumbas, "flores_tumbas");
    Nodo* velas = nodoLote("veladora", tumbas, "veladoras_tumbas");
    const char* lapidas[] = {"gravestone-cross", "gravestone-round", "gravestone-bevel", "gravestone-decorative",
                             "cross-wood"};
    int k = 0, nFlores = 0, nVelas = 0;
    for (float z : {19.8f, 23.6f, 27.4f}) {
        for (float x : {-11.0f, -7.5f, -4.0f, 4.0f, 7.5f, 11.0f}) {
            ++k;
            Nodo* t = tumbas->agregar("tumba_" + std::to_string(k));
            t->colocar({x + azar(-0.2f, 0.2f), 0.0f, z + azar(-0.2f, 0.2f)}, {0.0f, azar(-4.0f, 4.0f), 0.0f});
            Nodo* monticulo = instanciar("grave", t, "monticulo", {0, 0, 0.05f}, 180.0f, 2.0f);
            monticulo->tinte = glm::vec4(0.62f, 0.46f, 0.38f, 1.0f);  // tierra recién removida
            Nodo* bordillo = instanciar("grave-border", t, "bordillo", {0, 0, 0}, 180.0f, 2.0f);
            bordillo->tinte = glm::vec4(0.80f, 0.74f, 0.70f, 1.0f);   // piedra de cantera
            const char* lap = lapidas[(k * 7) % 5];
            instanciar(lap, t, "lapida", {0.0f, 0.0f, 1.55f}, 180.0f, std::string(lap) == "cross-wood" ? 1.7f : 1.6f);
            // flores sembradas sobre el montículo
            for (int f = 0; f < 9; ++f) {
                glm::vec3 p(azar(-0.40f, 0.40f), 0.22f, azar(-0.9f, 0.85f));
                flores->lote->agregar(t->matrizLocal() * trs(p, azar(0, 360), azar(1.1f, 1.5f)));
                ++nFlores;
            }
            for (float s : {-1.0f, 1.0f}) {
                velas->lote->agregar(t->matrizLocal() * trs({s * 0.95f, 0.0f, -1.35f}, azar(0, 360)));
                ++nVelas;
            }
            if (k % 4 == 1) instanciar("candle-multiple", t, "velas", {0.55f, 0.0f, 1.25f}, azar(0, 360), 1.2f);
            if (k % 5 == 2) instanciar("urn-round", t, "urna", {-0.55f, 0.0f, 1.3f}, 0.0f, 1.4f);
            if (k % 6 == 3) instanciar("calaverita_azucar", t, "calaverita", {0.0f, 0.22f, -0.95f}, 0.0f, 1.2f);
            if (k % 6 == 0) instanciar("pan_de_muerto", t, "pan", {0.25f, 0.2f, -0.6f}, azar(0, 90));
        }
    }
    info("flor_cempasuchil")->usos += nFlores;
    info("veladora")->usos += nVelas;

    // Criptas y cruz atrial al fondo
    instanciar("crypt", panteon, "cripta_izq", {-9.0f, 0.0f, 31.0f}, 180.0f, 3.0f);
    instanciar("crypt", panteon, "cripta_der", {9.0f, 0.0f, 31.0f}, 180.0f, 3.0f);
    instanciar("cross-column", panteon, "cruz_atrial", {0.0f, 0.0f, 32.2f}, 180.0f, 2.2f);

    // Cipreses dentro y detrás del panteón
    Nodo* cipreses = nodoLote("pine", panteon, "cipreses");
    for (float z : {18.5f, 25.0f, 30.0f})
        for (float x : {-12.4f, 12.4f})
            cipreses->lote->agregar(trs({x, 0.0f, z}, azar(0, 360), azar(2.5f, 3.0f)), glm::vec4(0.62f, 0.76f, 0.64f, 1.0f));
    for (float x : {-10.0f, -4.0f, 3.0f, 9.5f})
        cipreses->lote->agregar(trs({x, 0.0f, 36.0f}, azar(0, 360), azar(2.6f, 3.2f)), glm::vec4(0.62f, 0.76f, 0.64f, 1.0f));
    info("pine")->usos += cipreses->lote->instancias();
}

// ---------------------------------------------------------------------------
// Alrededores: árboles, rocas y casas del pueblo
// ---------------------------------------------------------------------------
void Escena::construirAlrededores() {
    Azar azar;
    Nodo* grupo = raiz_->agregar("Alrededores");
    Nodo* arboles = nodoLote("pine-crooked", grupo, "arboles");
    for (const glm::vec3& p : {glm::vec3(-7.0f, 0, 10.0f), glm::vec3(6.5f, 0, 6.0f), glm::vec3(-6.5f, 0, -1.0f),
                               glm::vec3(7.0f, 0, -7.0f), glm::vec3(-7.5f, 0, -10.0f), glm::vec3(8.0f, 0, 12.0f),
                               glm::vec3(-9.5f, 0, 3.0f), glm::vec3(10.5f, 0, 0.5f), glm::vec3(-17.0f, 0, 14.0f),
                               glm::vec3(18.0f, 0, 10.0f), glm::vec3(-12.0f, 0, -20.0f), glm::vec3(12.0f, 0, -21.0f)})
        arboles->lote->agregar(trs(p, azar(0, 360), azar(2.4f, 3.2f)), glm::vec4(0.72f, 0.82f, 0.70f, 1.0f));
    info("pine-crooked")->usos += arboles->lote->instancias();

    Nodo* rocas = nodoLote("rocks", grupo, "rocas");
    for (int i = 0; i < 14; ++i) {
        float a = azar(0, 6.2831f), r = azar(5.0f, 22.0f);
        glm::vec3 p(std::cos(a) * r, 0.0f, std::sin(a) * r * 1.2f);
        if (std::abs(p.x) < 3.5f) p.x += p.x < 0 ? -3.5f : 3.5f;
        if (p.z > 15.0f && p.z < 35.0f && std::abs(p.x) < 15.0f) p.x = p.x < 0 ? -16.5f : 16.5f;
        float g = azar(0.55f, 0.75f);
        rocas->lote->agregar(trs(p, azar(0, 360), azar(1.0f, 2.0f)), glm::vec4(g, g * 0.95f, g * 0.9f, 1.0f));
    }
    info("rocks")->usos += rocas->lote->instancias();

    // Casas vecinas (instancias del mismo modelo, sin costo extra de memoria)
    instanciar("casa_adobe", grupo, "casa_vecina_1", {-14.5f, 0.0f, -6.0f}, 75.0f);
    instanciar("casa_adobe", grupo, "casa_vecina_2", {15.5f, 0.0f, -3.0f}, -80.0f);
}
