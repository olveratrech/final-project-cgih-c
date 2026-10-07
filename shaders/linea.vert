#version 330 core
// Líneas de apoyo: caja envolvente del nodo seleccionado y sus ejes locales.

layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aColor;

uniform mat4 uVistaProy;

out vec3 vColor;

void main() {
    vColor = aColor;
    gl_Position = uVistaProy * vec4(aPos, 1.0);
}
