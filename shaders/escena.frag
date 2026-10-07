#version 330 core
// Sombreado de la entrega de modelado: luz direccional difusa (Lambert) más
// luz ambiental hemisférica (cielo/suelo) y niebla exponencial.
// Las texturas de color se muestrean en formato sRGB, por lo que el cálculo
// de iluminación se hace en espacio lineal y al final se aplica la
// corrección gamma. Los modelos de iluminación Phong y Fresnel se integran
// en la entrega de texturizado, color e iluminación.

in vec3 vPosMundo;
in vec3 vNormal;
in vec2 vUV;
in vec4 vTinte;

uniform sampler2D uTextura;
uniform bool uTieneTextura;
uniform vec4 uColor;        // baseColorFactor (lineal)
uniform vec3 uEmision;
uniform int uModoAlfa;      // 0 opaco, 1 recorte, 2 mezcla
uniform float uCorte;

uniform vec3 uDirLuz;       // dirección HACIA la luz (normalizada)
uniform vec3 uColorLuz;
uniform vec3 uAmbienteCielo;
uniform vec3 uAmbienteSuelo;
uniform vec3 uPosCamara;
uniform vec3 uColorNiebla;
uniform float uDensidadNiebla;

uniform bool uAlambre;      // modo de malla de alambre (topología)
uniform vec3 uColorAlambre;

out vec4 FragColor;

void main() {
    if (uAlambre) {
        FragColor = vec4(uColorAlambre, 1.0);
        return;
    }
    vec4 base = uColor * vTinte;
    if (uTieneTextura) base *= texture(uTextura, vUV);
    if (uModoAlfa == 1 && base.a < uCorte) discard;

    vec3 N = normalize(vNormal);
    if (!gl_FrontFacing) N = -N;  // materiales de doble cara (pétalos, papel picado)

    float difusa = max(dot(N, uDirLuz), 0.0);
    vec3 ambiente = mix(uAmbienteSuelo, uAmbienteCielo, N.y * 0.5 + 0.5);
    vec3 color = base.rgb * (ambiente + uColorLuz * difusa) + uEmision;

    float d = length(vPosMundo - uPosCamara);
    float niebla = 1.0 - exp(-pow(uDensidadNiebla * d, 1.5));
    color = mix(color, uColorNiebla, clamp(niebla, 0.0, 1.0));

    color = pow(color, vec3(1.0 / 2.2));  // lineal -> sRGB
    FragColor = vec4(color, uModoAlfa == 2 ? base.a : 1.0);
}
