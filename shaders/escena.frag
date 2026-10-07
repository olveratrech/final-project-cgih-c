#version 330 core

in vec3 vPosMundo;
in vec3 vNormal;
in vec2 vUV;
in vec4 vTinte;

uniform sampler2D uTextura;
uniform bool uTieneTextura;
uniform vec4 uColor;
uniform vec3 uEmision;
uniform int uModoAlfa;
uniform float uCorte;

uniform float uMetalico;
uniform float uRugosidad;
uniform float uCapa;
uniform float uRugosidadCapa;

uniform samplerCube uEntorno;
uniform bool uTieneEntorno;
uniform float uExposicionEntorno;

uniform vec3 uDirLuz;
uniform vec3 uColorLuz;
uniform vec3 uAmbienteCielo;
uniform vec3 uAmbienteSuelo;
uniform vec3 uPosCamara;
uniform vec3 uColorNiebla;
uniform float uDensidadNiebla;

uniform bool uAlambre;
uniform vec3 uColorAlambre;

out vec4 FragColor;

const float PI = 3.14159265359;

// Más reflexión cuando vemos la superficie de lado.
vec3 fresnel(float coseno, vec3 f0) {
    float t = 1.0 - clamp(coseno, 0.0, 1.0);
    return f0 + (1.0 - f0) * pow(t, 5.0);
}

// Reflejo especular GGX con visibilidad Smith.
vec3 especular(
    vec3 N,
    vec3 V,
    vec3 L,
    vec3 f0,
    float rugosidad
) {
    float nv = max(dot(N, V), 0.0001);
    float nl = max(dot(N, L), 0.0);

    if (nl <= 0.0 ||
        dot(V + L, V + L) < 0.000001) {
        return vec3(0.0);
    }

    vec3 H = normalize(V + L);
    float nh = max(dot(N, H), 0.0);

    float a = max(rugosidad * rugosidad, 0.0025);
    float a2 = a * a;

    float denominador = nh * nh * (a2 - 1.0) + 1.0;
    float D = a2 / max(
        PI * denominador * denominador,
        0.00000001
    );

    float gv = 2.0 * nv /
        (nv + sqrt(a2 + (1.0 - a2) * nv * nv));

    float gl = 2.0 * nl /
        (nl + sqrt(a2 + (1.0 - a2) * nl * nl));

    return D * gv * gl * fresnel(dot(V, H), f0)
        / max(4.0 * nv * nl, 0.0001);
}

// Aproximación de reflejos del entorno mediante mipmaps.
// No incluye reflejos de los otros objetos de la escena.
vec3 entorno(vec3 direccion, float rugosidad) {
    if (!uTieneEntorno) {
        return mix(
            uAmbienteSuelo,
            uAmbienteCielo,
            direccion.y * 0.5 + 0.5
        );
    }

    float maxLod =
        log2(float(textureSize(uEntorno, 0).x));

    return textureLod(
        uEntorno,
        direccion,
        rugosidad * maxLod
    ).rgb * uExposicionEntorno;
}

void main() {
    if (uAlambre) {
        FragColor = vec4(uColorAlambre, 1.0);
        return;
    }

    vec4 base = uColor * vTinte;

    if (uTieneTextura) {
        base *= texture(uTextura, vUV);
    }

    if (uModoAlfa == 1 && base.a < uCorte) {
        discard;
    }

    vec3 N = normalize(vNormal);

    if (!gl_FrontFacing) {
        N = -N;
    }

    vec3 V = normalize(uPosCamara - vPosMundo);
    vec3 L = normalize(uDirLuz);
    vec3 R = reflect(-V, N);

    float nv = max(dot(N, V), 0.0);
    float nl = max(dot(N, L), 0.0);

    float metal = clamp(uMetalico, 0.0, 1.0);
    float rug = clamp(uRugosidad, 0.05, 1.0);
    float capa = clamp(uCapa, 0.0, 1.0);
    float rugCapa = clamp(uRugosidadCapa, 0.05, 1.0);

    // Los metales tiñen el reflejo con su color base.
    vec3 f0 = mix(vec3(0.04), base.rgb, metal);
    vec3 F = fresnel(nv, f0);

    vec3 ambiente = mix(
        uAmbienteSuelo,
        uAmbienteCielo,
        N.y * 0.5 + 0.5
    );

    // Conserva la intensidad difusa de la escena original.
    vec3 color = base.rgb
        * (1.0 - metal)
        * (1.0 - F)
        * (ambiente + uColorLuz * nl);

    color += PI
        * especular(N, V, L, f0, rug)
        * uColorLuz * nl;

    vec3 fEntorno = f0
        + (max(vec3(1.0 - rug), f0) - f0)
        * pow(1.0 - nv, 5.0);

    color += entorno(R, rug)
        * fEntorno
        * (1.0 - 0.5 * rug);

    // Capa transparente: reflejo blanco sobre el material.
    float fCapa = fresnel(nv, vec3(0.04)).r;

    color *= (1.0 - capa * fCapa)
        * (1.0 - capa * fresnel(nl, vec3(0.04)).r);

    color += capa * PI
        * especular(N, V, L, vec3(0.04), rugCapa)
        * uColorLuz * nl;

    color += capa
        * entorno(R, rugCapa)
        * fCapa
        * (1.0 - 0.5 * rugCapa);

    color += uEmision;

    float distancia = length(vPosMundo - uPosCamara);
    float niebla = 1.0 - exp(
        -pow(uDensidadNiebla * distancia, 1.5)
    );

    color = mix(
        color,
        uColorNiebla,
        clamp(niebla, 0.0, 1.0)
    );

    // Conversión de color lineal a pantalla.
    color = pow(
        max(color, vec3(0.0)),
        vec3(1.0 / 2.2)
    );

    FragColor = vec4(
        color,
        uModoAlfa == 2 ? base.a : 1.0
    );
}