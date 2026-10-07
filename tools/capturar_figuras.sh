#!/usr/bin/env bash
# Genera las capturas del programa que se usan en la documentación (docs/img).
# Uso: tools/capturar_figuras.sh [ruta_del_ejecutable]
# En Linux sin pantalla se ejecuta con xvfb-run automáticamente.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
EXE="${1:-$RAIZ/build/CaminoCempasuchil}"
TMP="$(mktemp -d)"
X=""
if [ -z "${DISPLAY:-}" ] && command -v xvfb-run > /dev/null; then X="xvfb-run -a -s '-screen 0 1920x1080x24'"; fi
correr() { eval $X "\"$EXE\"" "$@" > /dev/null 2>&1; }

mkdir -p "$RAIZ/docs/img/escena" "$RAIZ/docs/img/interfaz" "$RAIZ/docs/img/libreria"

# Vistas predefinidas sin interfaz
for v in 1 2 3 4 5 6 7; do
    correr --ancho 1600 --alto 900 --vista $v --sin-interfaz --captura "$TMP/vista_$v.png" --cuadros 4
done

# Interfaz: selección con inspector, modo alambre y galería
correr --ancho 1600 --alto 900 --vista 4 --seleccion nivel_2 --captura "$TMP/interfaz_inspector.png" --cuadros 4
correr --ancho 1600 --alto 900 --vista 4 --alambre --sin-interfaz --captura "$TMP/alambre_altar.png" --cuadros 4
correr --ancho 1600 --alto 900 --vista 1 --alambre --sin-interfaz --captura "$TMP/alambre_general.png" --cuadros 4
correr --ancho 1600 --alto 900 --galeria farol --captura "$TMP/interfaz_galeria.png" --cuadros 4

# Modelos de librería vistos en la galería del programa
for m in grave grave-border gravestone-cross gravestone-round gravestone-bevel gravestone-decorative cross-wood \
         cross-column crypt iron-fence stone-wall stone-wall-column pine pine-crooked bench urn-round pumpkin \
         pumpkin-tall rocks candle-multiple detail-bowl detail-plate character-skeleton character-ghost character-keeper; do
    correr --ancho 480 --alto 480 --galeria "$m" --sin-interfaz --captura "$TMP/lib_$m.png" --cuadros 3
done

python3 - "$TMP" "$RAIZ" <<'EOF'
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont
tmp, raiz = sys.argv[1], sys.argv[2]
def guardar(origen, destino, ancho=None):
    im = Image.open(origen).convert("RGB")
    if ancho and im.width > ancho:
        im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
    im.save(destino, quality=88, optimize=True)
for p in glob.glob(os.path.join(tmp, "vista_*.png")):
    guardar(p, os.path.join(raiz, "docs/img/escena", os.path.basename(p)[:-4] + ".jpg"), 1280)
for n in ("interfaz_inspector", "interfaz_galeria", "alambre_altar", "alambre_general"):
    guardar(os.path.join(tmp, n + ".png"), os.path.join(raiz, "docs/img/interfaz", n + ".jpg"), 1280)
# hoja de contacto de la librería
nombres = {"grave": "Tumba de tierra", "grave-border": "Bordillo", "gravestone-cross": "Lápida con cruz",
           "gravestone-round": "Lápida redonda", "gravestone-bevel": "Lápida biselada",
           "gravestone-decorative": "Lápida decorativa", "cross-wood": "Cruz de madera", "cross-column": "Cruz atrial",
           "crypt": "Cripta", "iron-fence": "Reja de hierro", "stone-wall": "Barda de piedra",
           "stone-wall-column": "Columna de barda", "pine": "Ciprés", "pine-crooked": "Ciprés torcido",
           "bench": "Banca", "urn-round": "Urna", "pumpkin": "Calabaza", "pumpkin-tall": "Calabaza alargada",
           "rocks": "Rocas", "candle-multiple": "Velas", "detail-bowl": "Cazuela", "detail-plate": "Plato",
           "character-skeleton": "Calaca", "character-ghost": "Ánima", "character-keeper": "Panteonero"}
celda, txt, cols = 240, 28, 5
claves = list(nombres)
filas = (len(claves) + cols - 1) // cols
hoja = Image.new("RGB", (cols * celda, filas * (celda + txt)), (40, 36, 46))
d = ImageDraw.Draw(hoja)
f = None
for c in ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"):
    if os.path.exists(c):
        f = ImageFont.truetype(c, 16)
        break
for i, k in enumerate(claves):
    p = os.path.join(tmp, "lib_" + k + ".png")
    if not os.path.exists(p):
        continue
    x, y = (i % cols) * celda, (i // cols) * (celda + txt)
    hoja.paste(Image.open(p).convert("RGB").resize((celda, celda), Image.LANCZOS), (x, y))
    t = f"{i + 1}. {nombres[k]}"
    w = d.textlength(t, font=f)
    d.text((x + (celda - w) / 2, y + celda + 5), t, fill=(220, 230, 255), font=f)
hoja.save(os.path.join(raiz, "docs/img/libreria/catalogo_libreria.jpg"), quality=88, optimize=True)
EOF
rm -rf "$TMP"
echo "Capturas actualizadas en docs/img/"
