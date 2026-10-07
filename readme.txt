CAMINO DE CEMPASUCHIL - Altar de Dia de Muertos interactivo
Computacion Grafica e Interaccion Humano-Computadora
Facultad de Ingenieria, UNAM - Semestre 2027-1

Equipo:
  Basilio Illescas Andres
  Trejo Olvera Emmanuel
  Perez Olvera Alexis Abraham
  Cruz Macedo Samuel Santiago

---------------------------------------------------------------------
REQUISITOS
---------------------------------------------------------------------
  - Windows 10 u 11 de 64 bits.
  - Tarjeta grafica (o grafica integrada) compatible con OpenGL 3.3.
  - 200 MB de memoria RAM y 64 MB de memoria de video libres.
  - No requiere instalar bibliotecas adicionales.

---------------------------------------------------------------------
INSTALACION
---------------------------------------------------------------------
  1. Ejecutar el instalador y seguir las instrucciones, o bien
     descomprimir la carpeta del programa en cualquier ubicacion.
  2. La carpeta debe conservar juntos estos elementos:
        CaminoCempasuchil.exe
        assets\
        shaders\
        readme.txt
  3. Abrir CaminoCempasuchil.exe (o el acceso directo del menu Inicio).

  Si el programa no abre, revisar el archivo registro.txt que se crea
  junto al ejecutable: ahi se indica la version de OpenGL detectada y
  cualquier error de carga. Actualizar el controlador de video suele
  resolver los problemas de OpenGL.

---------------------------------------------------------------------
USO
---------------------------------------------------------------------
  El programa abre en la vista general del pueblo: la casa con la
  ofrenda al norte, el camino de petalos de cempasuchil al centro y el
  panteon al sur.

  CAMARA
    W A S D ............ moverse
    Q / E .............. bajar / subir
    Shift / Ctrl ....... mas rapido / mas lento
    Clic derecho ....... mantener presionado y mover el raton para mirar
    Rueda del raton .... cambiar la velocidad
    1 a 7 .............. vistas predefinidas:
                         1 general, 2 entrada del panteon,
                         3 camino de petalos, 4 altar de muertos,
                         5 ofrenda (detalle), 6 panteon, 7 aerea

  SELECCION Y TRANSFORMACIONES
    Clic izquierdo ..... seleccionar un objeto
    Ctrl + clic ........ seleccionar la pieza exacta del modelo
    Flechas ............ trasladar el objeto en el plano del suelo
    RePag / AvPag ...... subir / bajar el objeto
    Z / X .............. rotar el objeto
    C / V .............. reducir / aumentar la escala
    Retroceso .......... regresar el objeto a su posicion original
    N .................. seleccionar el nodo padre en la jerarquia
    F .................. acercar la camara al objeto
    Esc ................ quitar la seleccion; sin seleccion, cierra el programa

  GALERIA DE MODELOS
    G o Esc ............ entrar / salir de la galeria
    Flechas izq/der .... modelo anterior / siguiente
    Espacio ............ detener o reanudar el giro
    Clic derecho ....... orbitar alrededor del modelo
    Rueda .............. acercar / alejar

  VISUALIZACION
    F1 ................. ayuda en pantalla
    F2 ................. malla de alambre (topologia de los modelos)
    F3 ................. resaltar la seleccion y sus ejes locales
    F4 ................. ocultar / mostrar la interfaz
    F12 o P ............ captura de pantalla (carpeta Imagenes)

  Los paneles de la interfaz muestran el rendimiento, el arbol de la
  jerarquia de la escena, las matrices de transformacion del objeto
  seleccionado y la informacion de cada modelo.

---------------------------------------------------------------------
OPCIONES DE LINEA DE COMANDOS (opcional)
---------------------------------------------------------------------
  --vista N             vista inicial (1 a 7)
  --galeria MODELO      abrir la galeria en un modelo (p. ej. altar_muertos)
  --ancho N --alto N    tamano de la ventana
  --alambre             iniciar en modo de malla de alambre
  --sin-interfaz        ocultar los paneles
  --msaa N              muestras de antialiasing (0 lo desactiva)
  --captura ARCHIVO     guardar una imagen y cerrar

---------------------------------------------------------------------
CREDITOS
---------------------------------------------------------------------
  Modelos propios, texturas propias y codigo: equipo del proyecto.
  Modelos de libreria: Kenney, Graveyard Kit 5.0 (CC0) - kenney.nl
  Texturas y cielo: Poly Haven (CC0) - polyhaven.com
  Fuente: Liberation Sans (SIL Open Font License 1.1)
  Bibliotecas: GLFW, GLAD, GLM, cgltf, stb, Dear ImGui
