// bibliotecas.cpp - Implementación de las bibliotecas de un solo encabezado.
//
// Solo se habilitan los decodificadores PNG y JPEG de stb_image para reducir
// el tamaño del ejecutable.
#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_PNG
#define STBI_ONLY_JPEG
#include <stb_image.h>

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include <stb_image_write.h>

#define CGLTF_IMPLEMENTATION
#include <cgltf.h>
