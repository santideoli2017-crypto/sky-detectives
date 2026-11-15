"""Detectives del Cielo · Misión Planeta X

Un juego de detectives con fotos reales del telescopio SPHEREx de la NASA.
Elegís un sospechoso del cielo, examinás sus fotos de distintas fechas y
el informe del detective te dice si se movió o si cambió de brillo.

Equipo: Santi (programación) y Marti (dibujos).

Cómo jugar:
  · Flechas izquierda/derecha o los botones de abajo: cambiar de sospechoso.
  · Flechas arriba/abajo o las flechitas del recuadro: cambiar de detector.
  · Barra espaciadora o el botón "Examine evidence": buscar las fotos.
  · Después aparece un desafío del detective: si acertás, ganás XP.
  · Al final, el veredicto: ¿es un planeta? Sí o No. El caso se resuelve igual,
    pero solo si acertás ganás XP.

Los dibujos de Marti van en la carpeta "dibujos" (ver dibujos/LEEME.txt):
  barnard.png, epsindi.png, wise0855.png, rwaur.png, rdra.png  (los sospechosos)
  santi.png, martina.png                                        (los detectives)
  spherex.png                                                   (el telescopio)
  logo.png                                                      (el título, opcional)
"""
import math
import os
import queue
import random
import sys
import threading
import time
import webbrowser

import numpy as np
import pygame

import receta

# ------------------------------------------------------------------
# 0. COLORES
# ------------------------------------------------------------------
# La paleta del equipo
GRIS_PIZARRA = (40, 61, 59)     # #283D3B  Gris pizarra oscuro
VERDE_AZULADO = (25, 114, 120)  # #197278  Verde azulado tormentoso
VERDE_APAGADO = (156, 191, 167) # #9CBFA7  Verde azulado apagado
TOMATE = (196, 69, 54)          # #C44536  Mermelada de tomate
AZUL_LASER = (0, 95, 209)       # #005FD1  Azul láser

# Los nombres que usa el resto del juego (así no hay que cambiar todo el código)
PINO = VERDE_AZULADO            # botones principales y títulos
PIZARRA = GRIS_PIZARRA          # textos oscuros
INDIGO = (22, 38, 44)           # el cielo de noche (ventanas y fotos)
OLIVA = TOMATE                  # botones secundarios y detalles
INDIGO_MEDIO = AZUL_LASER       # etiquetas azules
OLIVA_CLARO = (240, 168, 150)   # tomate clarito: estrellitas y marcas
OLIVA_OSCURO = (150, 46, 36)    # tomate oscuro
PINO_HOVER = (38, 140, 147)
OLIVA_HOVER = (216, 94, 78)
SOMBRA = (104, 140, 118)

NOCHE = VERDE_APAGADO           # el "empapelado" del fondo
NOCHE_DIBUJO = (130, 170, 145)  # los dibujitos del empapelado
TAPA = GRIS_PIZARRA             # tapa del cuaderno
PAPEL = (247, 243, 238)
PAPEL_BORDE = (222, 212, 206)
LINEA_PAPEL = (234, 226, 220)
TINTA = GRIS_PIZARRA
TINTA_SUAVE = (100, 114, 112)
CINTA = TOMATE
NOTA = (216, 236, 236)          # verde azulado muy clarito
NOTA_SOMBRA = (150, 196, 198)
BLANCO = (255, 255, 255)
VERDE = VERDE_AZULADO           # caso resuelto
OCRE = (204, 128, 40)           # pista dudosa
FOTO_OSCURO = np.array([20, 32, 36], dtype=float)     # cielo de las fotos
FOTO_CLARO = np.array([255, 246, 236], dtype=float)   # estrellas de las fotos

# ------------------------------------------------------------------
# 1. LOS SOSPECHOSOS
# ------------------------------------------------------------------
# Las coordenadas y movimientos se buscan en SIMBAD al examinar.
# Los números de acá son de respaldo, por si SIMBAD no contesta
# (valores aproximados: confírmenlos en SIMBAD).

SOSPECHOSOS = [
    {
        "es_planeta": False,
        "por_que": "It is a star: it shines with its own light because it burns hydrogen in its core. Planets don't shine on their own.",
        "clave": "barnard", "nombre": "Barnard's Star", "apodo": "The Runner",
        "simbad": "Barnard's star",
        "ra": 269.4521, "dec": 4.6934, "pm_ra": -802.8, "pm_dec": 10362.4,
        "detector": 1, "pista": "movimiento", "color": PINO,
        "etiquetas": [("Fast", PINO), ("Nearby", INDIGO_MEDIO), ("Red star", OLIVA_OSCURO)],
        "dato": "It is the star that crosses the sky the fastest. It is only 6 light-years away: "
                "after the Alpha Centauri stars, it is the closest one to the Sun.",
    },
    {
        "es_planeta": False,
        "por_que": "They are brown dwarfs: they were born from a gas cloud like stars, and they weigh dozens of times more than Jupiter. No planet is that heavy.",
        "clave": "epsindi", "nombre": "Epsilon Indi B", "apodo": "The Twins",
        "simbad": "eps Ind B",
        "ra": 331.0439, "dec": -56.7827, "pm_ra": 3966.7, "pm_dec": -2536.2,
        "detector": 3, "pista": "movimiento", "color": INDIGO_MEDIO,
        "etiquetas": [("Brown dwarfs", INDIGO_MEDIO), ("Pair", OLIVA_OSCURO), ("Travelers", PINO)],
        "dato": "Two brown dwarfs that spin around each other, and together they "
                "travel with the star Epsilon Indi. They are too small to "
                "shine like a star.",
    },
    {
        "es_planeta": False,
        "por_que": "It weighs almost as much as a giant planet, but it travels alone through space without orbiting any star. Astronomers call it a brown dwarf.",
        "clave": "wise0855", "nombre": "WISE 0855", "apodo": "The Cold Ghost",
        "simbad": "WISE J085510.83-071442.5",
        "ra": 133.7951, "dec": -7.2451, "pm_ra": -8118.0, "pm_dec": 673.0,
        "detector": 6, "pista": "movimiento", "color": OLIVA_CLARO,
        "etiquetas": [("Very cold", OLIVA_CLARO), ("Infrared", PIZARRA), ("Fast", PINO)],
        "dato": "A brown dwarf as cold as a freezer. It is almost invisible in short "
                "light: it shows up in the long-light detectors, like 5 and 6. "
                "Try changing the detector.",
    },
    {
        "es_planeta": False,
        "por_que": "It is a baby star that shines with its own light. What changes is the dust that covers and uncovers it.",
        "clave": "rwaur", "nombre": "RW Aurigae", "apodo": "The Blinking Baby",
        "simbad": "RW Aur",
        "ra": 76.9564, "dec": 30.4014, "pm_ra": 1.0, "pm_dec": -24.0,
        "detector": 1, "pista": "brillo", "color": OLIVA,
        "etiquetas": [("Young", OLIVA), ("Variable", PINO), ("Dusty", INDIGO_MEDIO)],
        "dato": "A newborn star, surrounded by gas and dust. That dust covers "
                "and uncovers it, so its brightness changes.",
    },
    {
        "es_planeta": False,
        "por_que": "It is an old giant star. It shines with its own light and beats because it puffs up and shrinks.",
        "clave": "rdra", "nombre": "R Draconis", "apodo": "The Giant Heart",
        "simbad": "R Dra",
        "ra": 248.1675, "dec": 66.7550, "pm_ra": -15.0, "pm_dec": 35.0,
        "detector": 1, "pista": "brillo", "color": OLIVA_OSCURO,
        "etiquetas": [("Red giant", OLIVA_OSCURO), ("Variable", PINO), ("Beats", INDIGO_MEDIO)],
        "dato": "An old giant star that puffs up and shrinks like a "
                "heart. About every 8 months it gets very bright and then fades.",
    },
]

DETECTORES = {1: "0.75–1.1 µm", 2: "1.1–1.6 µm", 3: "1.6–2.4 µm",
              4: "2.4–3.8 µm", 5: "3.8–4.4 µm", 6: "4.4–5.0 µm"}

# ------------------------------------------------------------------
# 2. COLORES, PANTALLA Y LETRAS
# ------------------------------------------------------------------
ANCHO, ALTO = 1280, 720


pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Sky Detectives · Mission Planet X")
reloj = pygame.time.Clock()

CARPETA = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(CARPETA, "fuentes")


def letra(tam, negrita=False, titulo=False):
    """Patrick Hand para títulos y Titillium Web para textos (están en la carpeta fuentes)."""
    if titulo:
        archivo = "PatrickHand-Regular.ttf"
    else:
        archivo = "TitilliumWeb-SemiBold.ttf" if negrita else "TitilliumWeb-Regular.ttf"
    for ruta in (os.path.join(FUENTES, archivo), os.path.join(CARPETA, archivo)):   # en "fuentes" o suelta
        if os.path.exists(ruta):
            return pygame.font.Font(ruta, tam)
    return pygame.font.SysFont("trebuchetms,verdana,arial", tam, bold=negrita)   # por si falta la carpeta


F_ENORME = letra(66, titulo=True)
F_TITULO = letra(38, titulo=True)
F_GRANDE = letra(30, titulo=True)
F_MEDIA = letra(25, titulo=True)
F_TEXTO = letra(17)
F_CHICA = letra(14)
F_CHICA_N = letra(14, True)


def coma(numero, decimales=1):
    return f"{numero:.{decimales}f}"


# ------------------------------------------------------------------
# 3. LA CIENCIA (corre "en segundo plano" para que la ventana no se congele)
# ------------------------------------------------------------------
def datos_simbad(nombre):
    """Pregunta a SIMBAD posición (año 2000) y movimiento propio. Devuelve None si falla."""
    from astroquery.simbad import Simbad
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    buscador = Simbad()
    buscador.add_votable_fields("pmra", "pmdec")
    tabla = buscador.query_object(nombre)
    if tabla is None or len(tabla) == 0:
        return None
    col = {c.lower(): c for c in tabla.colnames}
    ra, dec = tabla[col["ra"]][0], tabla[col["dec"]][0]
    pm_ra, pm_dec = tabla[col["pmra"]][0], tabla[col["pmdec"]][0]
    if np.ma.is_masked(pm_ra) or np.ma.is_masked(pm_dec):
        return None
    if isinstance(ra, (str, bytes)):                # versiones viejas de astroquery
        c = SkyCoord(str(ra), str(dec), unit=(u.hourangle, u.deg))
        ra, dec = c.ra.deg, c.dec.deg
    return float(ra), float(dec), float(pm_ra), float(pm_dec)


def brillo_centro(imagen, radio=3):
    """Suma la luz de los pixeles del centro (donde está el sospechoso)."""
    c = imagen.shape[0] // 2
    return float(np.nansum(imagen[c - radio:c + radio + 1, c - radio:c + radio + 1]))


def se_ve(imagen):
    """¿El sospechoso se distingue del fondo? (señal contra ruido mayor a 5)"""
    c = imagen.shape[0] // 2
    pico = np.nanmax(imagen[c - 3:c + 4, c - 3:c + 4])
    ruido = 1.4826 * np.nanmedian(np.abs(imagen - np.nanmedian(imagen)))
    return bool(ruido > 0 and pico / ruido > 5)


CARPETA_GUARDADAS = os.path.join(CARPETA, "fotos_guardadas")


def guardar_fotos(clave, detector, fotos):
    """Guarda las pasadas en la compu, para poder jugar aunque la NASA esté caída."""
    try:
        os.makedirs(CARPETA_GUARDADAS, exist_ok=True)
        np.savez_compressed(os.path.join(CARPETA_GUARDADAS, f"{clave}_d{detector}.npz"),
                            fechas=np.array([f[0] for f in fotos]),
                            imagenes=np.array([f[1] for f in fotos]),
                            mjd=np.array([f[2] for f in fotos]),
                            guardado=np.array(time.strftime("%d/%m %H:%M")))
    except Exception:
        pass


def cargar_fotos(clave, detector):
    """Devuelve (fotos, cuándo se guardaron) o ([], None) si no hay."""
    ruta = os.path.join(CARPETA_GUARDADAS, f"{clave}_d{detector}.npz")
    try:
        d = np.load(ruta)
        fotos = [(str(f), img, float(m)) for f, img, m in zip(d["fechas"], d["imagenes"], d["mjd"])]
        return fotos, str(d["guardado"])
    except Exception:
        return [], None


class Investigacion(threading.Thread):
    """Busca las pruebas de un sospechoso sin congelar el juego."""

    def __init__(self, sospechoso, detector):
        super().__init__(daemon=True)
        self.sospechoso, self.detector = sospechoso, detector
        self.mensajes = queue.Queue()
        self.resultado = None
        self.porcentaje = 0           # para la barrita del cohete (0 a 100)

    def avisar(self, texto):
        self.mensajes.put(texto.strip())

    def run(self):
        s = self.sospechoso
        try:
            self.avisar("Checking the SIMBAD catalog…")
            try:
                datos = datos_simbad(s["simbad"])
            except Exception:
                datos = None
            self.porcentaje = 5
            origen = "SIMBAD" if datos else "saved values"
            ra, dec, pm_ra, pm_dec = datos or (s["ra"], s["dec"], s["pm_ra"], s["pm_dec"])

            self.avisar("Working out where it is today…")
            hoy = receta.posicion_hoy(ra, dec, pm_ra, pm_dec)
            self.porcentaje = 8
            self.avisar("Searching for SPHEREx photos…")

            def avance(hechas, total):            # bajar las fotos es lo que más tarda: del 12 % al 95 %
                self.porcentaje = 12 + 83 * hechas / max(total, 1)

            fotos, _ = receta.pasadas(hoy, detector=self.detector, aviso=self.avisar, progreso=avance)
            de_reserva = None
            if len(fotos) >= 2:
                guardar_fotos(s["clave"], self.detector, fotos)       # por si la NASA se cae después
            else:
                guardadas, cuando = cargar_fotos(s["clave"], self.detector)
                if len(guardadas) > len(fotos):
                    fotos, de_reserva = guardadas, cuando
                    self.avisar("NASA is not answering: using the saved photos.")
            if not fotos and receta.servidor_caido:
                self.porcentaje = 100
                self.resultado = {"fotos": [], "titulo": "NASA is not answering",
                                  "lineas": ["The IRSA archive is busy (error 502).",
                                             "It's not the game's fault.",
                                             "Press \"Try again\" in a minute."],
                                  "resuelto": False, "reintentar": True}
                return
            self.avisar("Comparing the photos…")
            self.resultado = analizar(s, fotos, math.hypot(pm_ra, pm_dec) / 1000, origen)
            if de_reserva:
                self.resultado["lineas"] = self.resultado["lineas"][:3] + [f"(Photos saved on {de_reserva})"]
            if not self.resultado.get("pistas") and receta.colecciones_fallidas:
                # faltaron fechas porque una parte del archivo de la NASA no contestó: se puede reintentar
                self.resultado["lineas"] = [self.resultado["lineas"][0],
                                            "Part of NASA's archive didn't answer.",
                                            "Press \"Try again\" in a minute."]
                self.resultado["reintentar"] = True
            self.porcentaje = 100
        except Exception as error:
            self.porcentaje = 100
            self.resultado = {"fotos": [], "titulo": "Could not investigate",
                              "lineas": [f"Error: {error}"[:90], "Check your internet connection and try again."],
                              "resuelto": False}


def analizar(s, fotos, esperado, origen):
    """Arma el informe del detective a partir de las fotos de cada pasada."""
    r = {"fotos": fotos, "resuelto": False, "origen": origen, "pistas": None}
    if len(fotos) < 2:
        r["titulo"] = "Not enough evidence"
        r["lineas"] = [f"SPHEREx has {len(fotos)} pass(es) of this spot.",
                       "We need 2 dates to compare."]
        return r
    brillos = [brillo_centro(img) for _, img, _ in fotos]
    cambio = (max(brillos) - min(brillos)) / max(abs(np.mean(brillos)), 1e-9) * 100
    visible = se_ve(fotos[-1][1])
    r["pistas"] = {"visible": visible, "brillos": brillos, "cambio": cambio,
                   "fechas": [f for f, _, _ in fotos], "se_movio": False, "dx": 0.0, "dy": 0.0,
                   "centro": (fotos[-1][1].shape[1] / 2, fotos[-1][1].shape[0] / 2)}
    if visible:
        x1, y1 = receta.centroide(fotos[0][1])
        x2, y2 = receta.centroide(fotos[-1][1])
        r["pistas"].update({"dx": x2 - x1, "dy": y2 - y1, "centro": (x2, y2),
                            "se_movio": math.hypot(x2 - x1, y2 - y1) >= 0.5})
    if not visible:
        r["titulo"] = "Not visible in this detector"
        r["lineas"] = ["The suspect barely shows up in these photos.",
                       "Try another detector with the arrows."]
        return r
    anios = (fotos[-1][2] - fotos[0][2]) / 365.25
    if s["pista"] == "movimiento":
        m = receta.medir_movimiento(fotos)
        diferencia = abs(m["por_anio"] - esperado) / esperado * 100
        r["lineas"] = [f"In {coma(anios, 2)} years it moved {coma(m['pixeles'], 2)} pixels.",
                       f"Measured by us: {coma(m['por_anio'])}\" per year.",
                       f"According to {origen}: {coma(esperado)}\" per year.",
                       f"Difference: {diferencia:.0f}%"]
        r["resuelto"] = diferencia <= 25
        r["titulo"] = "Case solved! It moved" if r["resuelto"] else "Doubtful clue"
    else:
        r["lineas"] = [f"We compared {len(fotos)} passes over {coma(anios, 2)} years.",
                       f"Its brightness changed by {cambio:.0f}%.",
                       "It doesn't move: it blinks!" if cambio > 15 else "Its brightness barely changed."]
        r["resuelto"] = cambio > 15
        r["titulo"] = "Case solved! Its brightness changes" if r["resuelto"] else "Doubtful clue"
    return r


# ------------------------------------------------------------------
# 3b. LOS DESAFÍOS DEL DETECTIVE
# ------------------------------------------------------------------
# Cada vez que se examina un sospechoso, antes del informe aparece un
# desafío armado con las fotos reales que se bajaron.

def crear_desafio(resultado, anterior=None):
    p = resultado.get("pistas")
    if not p:
        return None
    if not p["visible"]:
        tipos = ["detector"]
    else:
        tipos = ["que_hizo", "senialar"]
        if p["se_movio"]:
            tipos.append("direccion")
        if p["cambio"] > 15 and len(p["brillos"]) >= 2:
            tipos.append("mas_brillo")
    candidatos = [t for t in tipos if t != anterior] or tipos
    tipo = random.choice(candidatos)

    if tipo == "que_hizo":
        correcta = 0 if p["se_movio"] else 1 if p["cambio"] > 15 else 2
        motivos = [f"It shifted {coma(math.hypot(p['dx'], p['dy']), 1)} little squares between the first and the last photo.",
                   f"Its brightness changed by {p['cambio']:.0f}% between passes.",
                   "It didn't move and its brightness didn't change much."]
        return {"tipo": tipo, "pregunta": "Look at the blink and the difference. What did the suspect do?",
                "opciones": ["It moved!", "Brightness changed", "Nothing happened"],
                "correcta": correcta, "explicacion": motivos[correcta]}
    if tipo == "direccion":
        dx, dy = p["dx"], p["dy"]       # en la foto, y para arriba es el norte
        if min(abs(dx), abs(dy)) > 0.6 * max(abs(dx), abs(dy)):     # se movió en diagonal
            opciones = ["Up and left", "Up and right", "Down and left", "Down and right"]
            correcta = (0 if dy > 0 else 2) + (1 if dx > 0 else 0)
        else:
            opciones = ["Up", "Down", "Left", "Right"]
            correcta = (3 if dx > 0 else 2) if abs(dx) > abs(dy) else (0 if dy > 0 else 1)
        return {"tipo": tipo, "pregunta": "In the photo, which way did the suspect move?",
                "opciones": opciones, "correcta": correcta,
                "explicacion": f"In the difference, the white spot (now) ended up \"{opciones[correcta].lower()}\" from the black one (before)."}
    if tipo == "mas_brillo":
        n = min(len(p["brillos"]), 4)
        correcta = int(np.argmax(p["brillos"][:n]))
        return {"tipo": tipo, "pregunta": "Watch the blink closely. In which pass was it brightest?",
                "opciones": [f"Pass {i + 1}" for i in range(n)], "correcta": correcta,
                "explicacion": f"It was brightest in pass {correcta + 1}, on {p['fechas'][correcta]}."}
    if tipo == "senialar":
        return {"tipo": tipo, "pregunta": "Click on the big photo right where the suspect is now.",
                "opciones": [], "objetivo": p["centro"], "clic": None,
                "explicacion": "It was near the center, where the little lines cross."}
    return {"tipo": "detector", "pregunta": "The suspect barely shows up in this photo. What does a good detective do?",
            "opciones": ["Try another detector", "Close the case", "Delete the photo"], "correcta": 0,
            "explicacion": "Each detector sees a different color of infrared light. Some suspects only show up in long light."}


def nuevo_desafio(resultado):
    anterior = resultado.get("desafio", {}).get("tipo") if resultado.get("desafio") else None
    resultado["desafio"] = crear_desafio(resultado, anterior)
    resultado["respuesta"] = None
    resultado["informe_visible"] = resultado["desafio"] is None


# ------------------------------------------------------------------
# 4. DE FOTO ASTRONÓMICA A IMAGEN DEL JUEGO
# ------------------------------------------------------------------
def a_superficie(imagen, lado, bajo, alto, es_resta=False):
    """Convierte una foto (números) en una imagen de pygame, con cuadraditos grandes."""
    datos = np.nan_to_num(np.asarray(imagen, dtype=float)[::-1], nan=0.0)  # el norte arriba
    if es_resta:
        v = np.clip(datos / alto * 0.5 + 0.5, 0, 1)
        color = v[..., None] * 255 * np.ones(3)
    else:
        v = np.clip((datos - bajo) / max(alto - bajo, 1e-9), 0, 1) ** 0.6
        color = FOTO_OSCURO + v[..., None] * (FOTO_CLARO - FOTO_OSCURO)
    sup = pygame.surfarray.make_surface(color.transpose(1, 0, 2).astype(np.uint8))
    return pygame.transform.scale(sup, (lado, lado))


def preparar_imagenes(resultado):
    fotos = resultado["fotos"]
    if not fotos:
        resultado["cuadros"], resultado["resta"] = [], None
        return
    todas = np.concatenate([np.ravel(f[1]) for f in fotos])
    bajo, alto = np.nanpercentile(todas, [5, 99.7])
    resultado["cuadros"] = [(fecha, a_superficie(img, 200, bajo, alto)) for fecha, img, _ in fotos]
    resta = fotos[-1][1] - fotos[0][1]
    tope = np.nanpercentile(np.abs(resta), 99.5) or 1
    resultado["resta"] = a_superficie(resta, 140, 0, tope, es_resta=True)


# ------------------------------------------------------------------
# 5. HERRAMIENTAS DE DIBUJO (estilo cuaderno)
# ------------------------------------------------------------------
def texto(sup, contenido, fuente, color, pos, centro=False):
    img = fuente.render(contenido, True, color)
    rect = img.get_rect(center=pos) if centro else img.get_rect(topleft=pos)
    sup.blit(img, rect)
    return rect


def parrafo(sup, contenido, fuente, color, x, y, ancho, interlineado=2):
    """Escribe un texto largo cortándolo en renglones."""
    palabras, renglon = contenido.split(), ""
    for palabra in palabras:
        prueba = (renglon + " " + palabra).strip()
        if fuente.size(prueba)[0] > ancho and renglon:
            texto(sup, renglon, fuente, color, (x, y))
            y += int(fuente.get_height() * 0.8) + interlineado
            renglon = palabra
        else:
            renglon = prueba
    if renglon:
        texto(sup, renglon, fuente, color, (x, y))
        y += int(fuente.get_height() * 0.8) + interlineado
    return y


def etiqueta(sup, contenido, color, x, y):
    """Una pastilla de color, como las etiquetas del cuaderno."""
    claro = sum(color) / 3 > 165
    img = F_CHICA_N.render(contenido, True, PIZARRA if claro else BLANCO)
    rect = pygame.Rect(x, y, img.get_width() + 22, img.get_height() + 4)
    pygame.draw.rect(sup, color, rect, border_radius=rect.height // 2)
    sup.blit(img, img.get_rect(center=rect.center))
    return rect


def rect_punteado(sup, color, rect, largo=10, hueco=7, grosor=2):
    for x1, y1, x2, y2 in [(rect.left, rect.top, rect.right, rect.top), (rect.right, rect.top, rect.right, rect.bottom),
                           (rect.right, rect.bottom, rect.left, rect.bottom), (rect.left, rect.bottom, rect.left, rect.top)]:
        distancia = math.hypot(x2 - x1, y2 - y1)
        pasos = int(distancia // (largo + hueco)) + 1
        for i in range(pasos):
            a = i * (largo + hueco) / distancia
            b = min((i * (largo + hueco) + largo) / distancia, 1)
            pygame.draw.line(sup, color, (x1 + (x2 - x1) * a, y1 + (y2 - y1) * a),
                             (x1 + (x2 - x1) * b, y1 + (y2 - y1) * b), grosor)


def clip(sup, x, y, angulo=-20, color=PINO):
    """Un clip de papel."""
    capa = pygame.Surface((30, 70), pygame.SRCALPHA)
    pygame.draw.rect(capa, color, (3, 3, 22, 62), 4, border_radius=11)
    pygame.draw.rect(capa, color, (9, 14, 12, 40), 4, border_radius=7)
    capa = pygame.transform.rotate(capa, angulo)
    sup.blit(capa, capa.get_rect(center=(x, y)))


def estrellita(sup, color, x, y, r):
    pygame.draw.line(sup, color, (x - r, y), (x + r, y), 2)
    pygame.draw.line(sup, color, (x, y - r), (x, y + r), 2)
    pygame.draw.line(sup, color, (x - r * 0.5, y - r * 0.5), (x + r * 0.5, y + r * 0.5), 1)
    pygame.draw.line(sup, color, (x - r * 0.5, y + r * 0.5), (x + r * 0.5, y - r * 0.5), 1)


def estrella5(sup, color, cx, cy, r):
    puntos = []
    for i in range(10):
        radio = r if i % 2 == 0 else r * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        puntos.append((cx + radio * math.cos(a), cy + radio * math.sin(a)))
    pygame.draw.polygon(sup, color, puntos)


def crear_empapelado():
    """El fondo: un empapelado de noche con estrellitas y planetas."""
    sup = pygame.Surface((ANCHO, ALTO))
    sup.fill(NOCHE)
    for fila, y in enumerate(range(-20, ALTO + 80, 90)):
        for x in range(-40 + (fila % 2) * 60, ANCHO + 80, 120):
            if (x // 120 + fila) % 3 == 0:
                pygame.draw.circle(sup, NOCHE_DIBUJO, (x, y), 9, 2)
                pygame.draw.ellipse(sup, NOCHE_DIBUJO, (x - 18, y - 4, 36, 8), 2)
            else:
                estrellita(sup, NOCHE_DIBUJO, x, y, 8)
            pygame.draw.circle(sup, NOCHE_DIBUJO, (x + 45, y + 40), 2)
    return sup


EMPAPELADO = crear_empapelado()
random.seed(7)
TITILANTES = [(random.randrange(ANCHO), random.randrange(ALTO), random.random() * 6.3) for _ in range(40)]


def dibujar_fondo(sup, t):
    sup.blit(EMPAPELADO, (0, 0))
    for x, y, fase in TITILANTES:
        brillo = 120 + int(100 * (0.5 + 0.5 * math.sin(t * 2 + fase)))
        pygame.draw.circle(sup, (brillo, brillo, min(255, brillo + 30)), (x, y), 1)


def personaje(sup, s, rect, t):
    """Un personaje de reemplazo hasta que estén los dibujos de Marti."""
    cx, cy, r = rect.centerx, rect.centery + 6, 52
    color, clave = s["color"], s["clave"]
    if clave == "barnard":                          # líneas de velocidad
        for i in range(3):
            pygame.draw.line(sup, PAPEL_BORDE, (cx - r - 40, cy - 20 + i * 20), (cx - r - 8, cy - 20 + i * 20), 4)
    if clave == "epsindi":                          # dos mellizos girando
        a = t * 1.5
        for signo, tono in [(1, color), (-1, OLIVA)]:
            px, py = cx + signo * 34 * math.cos(a), cy + signo * 14 * math.sin(a)
            pygame.draw.circle(sup, tono, (px, py), 32)
            ojos(sup, px, py, 32)
        return
    if clave == "wise0855":                         # fantasma
        cuerpo = [(cx - r, cy)] + [(cx - r + i * (2 * r) / 6, cy + r + (10 if i % 2 else 0)) for i in range(7)] + [(cx + r, cy)]
        pygame.draw.polygon(sup, color, cuerpo)
        pygame.draw.circle(sup, color, (cx, cy), r)
    elif s["pista"] == "brillo":                    # parpadea: rayos que laten
        largo = 18 + 10 * (0.5 + 0.5 * math.sin(t * 3))
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(sup, OLIVA_CLARO, (cx + (r + 4) * math.cos(a), cy + (r + 4) * math.sin(a)),
                             (cx + (r + 4 + largo) * math.cos(a), cy + (r + 4 + largo) * math.sin(a)), 4)
        pygame.draw.circle(sup, color, (cx, cy), r)
    else:
        pygame.draw.circle(sup, color, (cx, cy), r)
    ojos(sup, cx, cy, r)


def ojos(sup, cx, cy, r):
    for dx in (-0.35, 0.35):
        pygame.draw.circle(sup, BLANCO, (cx + dx * r, cy - 0.15 * r), r * 0.22)
        pygame.draw.circle(sup, TINTA, (cx + dx * r + 2, cy - 0.12 * r), r * 0.11)
    pygame.draw.arc(sup, TINTA, (cx - r * 0.3, cy + r * 0.05, r * 0.6, r * 0.4), math.pi, 2 * math.pi, 3)


DIBUJOS = {}


def dibujo_de_martina(clave, lado=196, alto=None):
    """Carga dibujos/<clave>.png (o .jpg) si existe, achicado para entrar en una caja de `lado` x `alto`."""
    alto = alto or lado
    if (clave, lado, alto) not in DIBUJOS:
        DIBUJOS[(clave, lado, alto)] = None
        rutas = [os.path.join(carpeta, clave + ext)
                 for carpeta in (os.path.join(CARPETA, "dibujos"), CARPETA)    # en "dibujos" o suelto
                 for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg")]
        for ruta in rutas:
            if os.path.exists(ruta):
                try:
                    img = pygame.image.load(ruta).convert_alpha()
                except Exception:                  # si el archivo no se puede abrir, usamos el reemplazo
                    continue
                escala = min(lado / img.get_width(), alto / img.get_height())
                DIBUJOS[(clave, lado, alto)] = pygame.transform.smoothscale(
                    img, (int(img.get_width() * escala), int(img.get_height() * escala)))
                break
    return DIBUJOS[(clave, lado, alto)]


def detective(sup, cx, base, quien, t):
    """Un detective de reemplazo hasta que esté el dibujo de Marti."""
    pelo, remera = ((120, 72, 40), PINO) if quien == "santi" else ((70, 40, 30), OLIVA_OSCURO)
    piel = (240, 200, 170)
    pygame.draw.rect(sup, remera, (cx - 34, base - 96, 68, 80), border_radius=18)       # cuerpo
    pygame.draw.rect(sup, INDIGO, (cx - 28, base - 24, 22, 24), border_radius=6)  # piernas
    pygame.draw.rect(sup, INDIGO, (cx + 6, base - 24, 22, 24), border_radius=6)
    pygame.draw.circle(sup, piel, (cx, base - 126), 34)                                 # cabeza
    pygame.draw.ellipse(sup, pelo, (cx - 36, base - 166, 72, 40))                       # pelo
    if quien == "martina":
        pygame.draw.circle(sup, pelo, (cx - 36, base - 120), 12)
        pygame.draw.circle(sup, pelo, (cx + 36, base - 120), 12)
    ojos(sup, cx, base - 122, 30)
    lx, ly = cx + 46, base - 70 + 4 * math.sin(t * 2)                                    # lupa
    pygame.draw.line(sup, (120, 84, 50), (cx + 24, base - 50), (lx - 8, ly + 8), 6)
    pygame.draw.circle(sup, (200, 230, 250), (lx + 4, ly - 4), 16)
    pygame.draw.circle(sup, (120, 84, 50), (lx + 4, ly - 4), 16, 4)


def telescopio(sup, cx, cy, t):
    """SPHEREx de reemplazo: un cono que junta la luz y una caja con el detector."""
    cy += 6 * math.sin(t * 1.2)
    for i, ancho in enumerate((150, 126, 102)):                                        # los escudos
        y = cy - 70 + i * 26
        pygame.draw.polygon(sup, (205, 210, 225) if i % 2 else (230, 232, 240),
                            [(cx - ancho // 2, y), (cx + ancho // 2, y), (cx + ancho // 2 - 14, y + 26), (cx - ancho // 2 + 14, y + 26)])
        pygame.draw.lines(sup, (140, 146, 170), True,
                          [(cx - ancho // 2, y), (cx + ancho // 2, y), (cx + ancho // 2 - 14, y + 26), (cx - ancho // 2 + 14, y + 26)], 2)
    pygame.draw.rect(sup, OLIVA_CLARO, (cx - 34, cy + 8, 68, 40), border_radius=6)            # la caja dorada
    pygame.draw.rect(sup, OLIVA_OSCURO, (cx - 34, cy + 8, 68, 40), 2, border_radius=6)
    for lado in (-1, 1):                                                                 # paneles solares
        pygame.draw.rect(sup, INDIGO_MEDIO, (cx + lado * 40 - (52 if lado < 0 else 0), cy + 18, 52, 20))
    for i in range(3):                                                                   # la luz que entra
        x = cx - 40 + i * 40
        pygame.draw.line(sup, OLIVA_CLARO, (x, cy - 150), (x * 0.6 + cx * 0.4, cy - 76), 2)


# ------------------------------------------------------------------
# 6. BOTONES
# ------------------------------------------------------------------
class Boton:
    def __init__(self, rect, contenido, colores=(PINO, PINO_HOVER, PIZARRA), fuente=None, color_texto=BLANCO):
        self.color_texto = color_texto
        self.rect = pygame.Rect(rect)
        self.contenido = contenido
        self.color, self.color_hover, self.sombra = colores
        self.fuente = fuente or F_MEDIA
        self.hover = False
        self.activo = True

    def dibujar(self, sup):
        apretado = self.hover and pygame.mouse.get_pressed()[0] and self.activo
        caja = self.rect.move(0, 3 if apretado else 0)
        color = self.color_hover if self.hover and self.activo else self.color
        if not self.activo:
            color = (190, 200, 190)
        pygame.draw.rect(sup, self.sombra if self.activo else (150, 162, 156), self.rect.move(0, 5), border_radius=14)
        pygame.draw.rect(sup, color, caja, border_radius=14)
        pygame.draw.rect(sup, BLANCO, caja, 3, border_radius=14)
        texto(sup, self.contenido, self.fuente, self.color_texto, caja.center, centro=True)

    def tocado(self, pos):
        return self.activo and self.rect.collidepoint(pos)


class Flechita:
    def __init__(self, centro, hacia):
        self.rect = pygame.Rect(0, 0, 34, 40)
        self.rect.center = centro
        self.hacia = hacia            # -1 izquierda, 1 derecha
        self.hover = False

    def dibujar(self, sup):
        color = PINO if self.hover else TINTA
        cx, cy = self.rect.center
        d = self.hacia * 8
        pygame.draw.lines(sup, color, False, [(cx - d, cy - 14), (cx + d, cy), (cx - d, cy + 14)], 5)

    def tocado(self, pos):
        return self.rect.collidepoint(pos)


# ------------------------------------------------------------------
# 7. ESTADO DEL JUEGO
# ------------------------------------------------------------------
pantalla_actual = "menu"     # "menu", "como", "spherex", "fuentes" o "juego"
indice = 0
detector = {s["clave"]: s["detector"] for s in SOSPECHOSOS}
pruebas = {}                 # (clave, detector) -> resultado ya analizado
resueltos = set()
xp = 0                       # puntos de experiencia del detective
XP_DESAFIO = 10              # por cada desafío bien respondido
XP_VEREDICTO = 20            # por acertar si es un planeta o no
botones_desafio = []         # los botones de respuesta que se ven ahora
FOTO_GRANDE = pygame.Rect(709, 146, 200, 200)   # dónde queda la foto grande en la pantalla
investigacion = None         # el trabajo en segundo plano
cohete_pct = 0               # lo que muestra la barrita del cohete
ultimo_aviso = ""

PAGINA_IZQ = pygame.Rect(108, 76, 528, 600)
PAGINA_DER = pygame.Rect(644, 76, 528, 600)

btn_anterior = Boton((150, 606, 200, 50), "‹ Previous", (OLIVA, OLIVA_HOVER, OLIVA_OSCURO))
btn_siguiente = Boton((380, 606, 200, 50), "Next ›", (PINO, PINO_HOVER, PIZARRA))
btn_examinar = Boton((850, 612, 290, 50), "Examine evidence")
flecha_menos = Flechita((470, 535), -1)
flecha_mas = Flechita((590, 535), 1)
btn_ver_informe = Boton((990, 556, 140, 36), "See report ›", fuente=letra(22, titulo=True))
btn_menu = Boton((1144, 12, 120, 42), "‹ Menu", (PAPEL, BLANCO, PAPEL_BORDE), F_MEDIA, TINTA)
BOTONES = [btn_anterior, btn_siguiente, btn_examinar, flecha_menos, flecha_mas, btn_menu]

btn_jugar = Boton((290, 640, 220, 54), "Investigate!", fuente=F_GRANDE)
btn_como = Boton((530, 640, 220, 54), "How to play", (OLIVA, OLIVA_HOVER, OLIVA_OSCURO), F_MEDIA)
btn_spherex = Boton((770, 640, 220, 54), "What is SPHEREx?", (PAPEL, BLANCO, PAPEL_BORDE), F_MEDIA, PIZARRA)
BOTONES_MENU = [btn_jugar, btn_como, btn_spherex]

btn_info = Boton((930, 88, 168, 32), "What is SPHEREx?", (PAPEL, BLANCO, PAPEL_BORDE), letra(20, titulo=True), PINO)
BOTONES.append(btn_info)
btn_testigo = Boton((150, 456, 300, 34), "Call another witness: WISE ›", (AZUL_LASER, (30, 118, 228), (0, 60, 140)), letra(21, titulo=True))
BOTONES.append(btn_testigo)

btn_fuentes = Boton((1124, 12, 140, 42), "Sources", (PAPEL, BLANCO, PAPEL_BORDE), F_MEDIA, TINTA)
BOTONES_MENU.append(btn_fuentes)
btn_volver_f = Boton((530, 640, 220, 54), "‹ Back", (PAPEL, BLANCO, PAPEL_BORDE), F_MEDIA, TINTA)
BOTONES_FUENTES = [btn_volver_f]
fichas_fuentes = []          # (rectángulo, dirección web) de cada ficha, para poder hacer clic

btn_volver_s = Boton((300, 640, 220, 54), "‹ Back", (PAPEL, BLANCO, PAPEL_BORDE), F_MEDIA, TINTA)
btn_jugar3 = Boton((760, 640, 230, 54), "Investigate!", fuente=F_GRANDE)
BOTONES_SPHEREX = [btn_volver_s, btn_jugar3]
volver_a = "menu"            # a qué pantalla vuelve "‹ Back" desde SPHEREx

btn_volver = Boton((300, 620, 220, 54), "‹ Back", (PAPEL, BLANCO, PAPEL_BORDE), F_MEDIA, TINTA)
btn_jugar2 = Boton((760, 620, 230, 54), "Investigate!", fuente=F_GRANDE)
BOTONES_COMO = [btn_volver, btn_jugar2]


def actual():
    return SOSPECHOSOS[indice]


def clave_actual():
    return (actual()["clave"], detector[actual()["clave"]])


def investigando():
    return investigacion is not None and investigacion.is_alive()


def examinar():
    global investigacion, ultimo_aviso
    resultado = pruebas.get(clave_actual())
    if resultado is not None and resultado.get("reintentar") and not investigando():
        del pruebas[clave_actual()]             # borramos el intento incompleto y buscamos de nuevo
        resultado = None
    if resultado is not None:
        if resultado.get("informe_visible") and resultado.get("pistas"):
            if resultado.get("veredicto") is None and not resultado.get("en_veredicto"):
                empezar_veredicto()             # primero la pregunta final
            elif resultado.get("veredicto") is not None:
                resultado["en_veredicto"] = False
                nuevo_desafio(resultado)        # otro desafío con las mismas fotos
        return
    if investigando():
        return
    ultimo_aviso = ""
    investigacion = Investigacion(actual(), detector[actual()["clave"]])
    investigacion.clave = clave_actual()
    investigacion.start()


def responder(indice_opcion):
    """El jugador eligió una respuesta del desafío."""
    global xp
    resultado = pruebas.get(clave_actual())
    if not resultado or not resultado.get("desafio") or resultado["respuesta"] is not None:
        return
    acierto = indice_opcion == resultado["desafio"]["correcta"]
    resultado["respuesta"] = acierto
    if acierto:
        xp += XP_DESAFIO


def clic_en_foto(pos):
    """Para el desafío de señalar: ¿hizo clic cerca del sospechoso?"""
    global xp
    resultado = pruebas.get(clave_actual())
    if not resultado or not resultado.get("desafio") or resultado["respuesta"] is not None:
        return False
    d = resultado["desafio"]
    if d["tipo"] != "senialar" or not FOTO_GRANDE.collidepoint(pos):
        return False
    lado = resultado["fotos"][-1][1].shape[0]
    x = (pos[0] - FOTO_GRANDE.x) / FOTO_GRANDE.w * lado
    y = lado - (pos[1] - FOTO_GRANDE.y) / FOTO_GRANDE.h * lado      # la foto se muestra con el norte arriba
    d["clic"] = pos
    acierto = math.hypot(x - d["objetivo"][0], y - d["objetivo"][1]) <= 3.5
    resultado["respuesta"] = acierto
    if acierto:
        xp += XP_DESAFIO
    return True


def ver_informe():
    resultado = pruebas.get(clave_actual())
    if resultado and resultado.get("respuesta") is not None:
        resultado["informe_visible"] = True


def empezar_veredicto():
    resultado = pruebas.get(clave_actual())
    if resultado and resultado.get("informe_visible") and resultado.get("veredicto") is None:
        resultado["en_veredicto"] = True


def responder_veredicto(dijo_planeta):
    """¿Es un planeta? Acertar o no, el caso queda resuelto; solo acertar da XP."""
    global xp
    resultado = pruebas.get(clave_actual())
    if not resultado or not resultado.get("en_veredicto") or resultado.get("veredicto") is not None:
        return
    acierto = dijo_planeta == actual()["es_planeta"]
    resultado["veredicto"] = acierto
    resueltos.add(actual()["clave"])
    if acierto:
        xp += XP_VEREDICTO


def cambiar_sospechoso(paso):
    global indice
    indice = (indice + paso) % len(SOSPECHOSOS)


def cambiar_detector(paso):
    c = actual()["clave"]
    detector[c] = (detector[c] - 1 + paso) % 6 + 1


def revisar_investigacion():
    """Lee los avisos del trabajo en segundo plano y guarda el resultado cuando termina."""
    global investigacion, ultimo_aviso, cohete_pct
    if investigacion is None:
        cohete_pct = 0
        return
    while not investigacion.mensajes.empty():
        ultimo_aviso = investigacion.mensajes.get()
    meta = investigacion.porcentaje                      # el cohete avanza suavecito hacia la meta
    cohete_pct = min(meta, cohete_pct + max(0.4, (meta - cohete_pct) * 0.12))
    if not investigacion.is_alive() and investigacion.resultado is not None and cohete_pct >= 99.5:
        resultado = investigacion.resultado
        preparar_imagenes(resultado)
        nuevo_desafio(resultado)
        pruebas[investigacion.clave] = resultado
        investigacion = None


# ------------------------------------------------------------------
# 8. DIBUJAR CADA PARTE DE LA PANTALLA
# ------------------------------------------------------------------
def dibujar_contador(sup):
    caja = pygame.Rect(18, 14, 200, 46)
    pygame.draw.rect(sup, PIZARRA, caja, border_radius=16)
    pygame.draw.rect(sup, OLIVA_CLARO, (caja.x + 12, caja.y + 11, 26, 24), 3, border_radius=4)   # una carpeta de casos
    pygame.draw.line(sup, OLIVA_CLARO, (caja.x + 17, caja.y + 20), (caja.x + 33, caja.y + 20), 2)
    texto(sup, f"{len(resueltos)}/5 cases", F_GRANDE, BLANCO, (caja.x + 48, caja.y + 6))
    caja2 = pygame.Rect(caja.right + 10, caja.y, 140, 46)
    pygame.draw.rect(sup, PIZARRA, caja2, border_radius=16)
    estrella5(sup, OLIVA_CLARO, caja2.x + 26, caja2.centery, 15)
    texto(sup, f"{xp} XP", F_GRANDE, BLANCO, (caja2.x + 46, caja2.y + 6))


def dibujar_cuaderno(sup):
    tapa = pygame.Rect(88, 58, 1104, 638)
    pygame.draw.rect(sup, SOMBRA, tapa.move(6, 8), border_radius=22)
    pygame.draw.rect(sup, TAPA, tapa, border_radius=22)
    for pagina in (PAGINA_IZQ, PAGINA_DER):
        pygame.draw.rect(sup, PAPEL, pagina, border_radius=10)
        for y in range(pagina.top + 40, pagina.bottom - 20, 30):        # renglones suaves
            pygame.draw.line(sup, LINEA_PAPEL, (pagina.left + 20, y), (pagina.right - 20, y), 1)
    pygame.draw.line(sup, PAPEL_BORDE, (640, 76), (640, 676), 6)          # el lomo
    pygame.draw.rect(sup, CINTA, (628, 40, 18, 680))                      # la cinta del cuaderno
    pygame.draw.polygon(sup, CINTA, [(628, 720), (646, 720), (637, 708)])
    for x, y in [(140, 650), (1140, 104), (1150, 655)]:                  # garabatos de constelaciones
        puntos = [(x, y), (x + 14, y - 10), (x + 30, y - 4), (x + 40, y - 18)]
        pygame.draw.lines(sup, PAPEL_BORDE, False, puntos, 1)
        for p in puntos:
            pygame.draw.circle(sup, PAPEL_BORDE, p, 3)


def dibujar_pagina_izquierda(sup, t):
    s = actual()
    texto(sup, "DETECTIVE NOTEBOOK", F_CHICA_N, TINTA_SUAVE, (150, 96))
    texto(sup, f"Suspect {indice + 1} of 5", F_CHICA, TINTA_SUAVE, (470, 96))

    marco = pygame.Rect(150, 132, 216, 230)
    pygame.draw.rect(sup, BLANCO, marco, border_radius=12)
    rect_punteado(sup, PAPEL_BORDE, marco)
    dibujo = dibujo_de_martina(s["clave"])
    if dibujo:
        sup.blit(dibujo, dibujo.get_rect(center=marco.center))
    else:
        personaje(sup, s, pygame.Rect(marco.x, marco.y, marco.w, marco.h - 30), t)
    if s["clave"] in resueltos:
        sello = pygame.Rect(marco.right - 70, marco.top - 14, 84, 30)
        pygame.draw.rect(sup, VERDE, sello, border_radius=8)
        texto(sup, "SOLVED", F_CHICA_N, BLANCO, sello.center, centro=True)

    y = parrafo(sup, s["nombre"], F_TITULO, PINO, 386, 136, 230, 0)
    texto(sup, f"\"{s['apodo']}\"", F_MEDIA, TINTA, (386, y + 2))
    x, y = 386, y + 36
    for nombre, color in s["etiquetas"]:
        ancho = F_CHICA_N.size(nombre)[0] + 22
        if x + ancho > 616:
            x, y = 386, y + 32
        x = etiqueta(sup, nombre, color, x, y).right + 6

    parrafo(sup, s["dato"], F_TEXTO, TINTA, 150, 382, 450)

    caja = pygame.Rect(150, 500, 470, 72)
    pygame.draw.rect(sup, BLANCO, caja, border_radius=12)
    rect_punteado(sup, OLIVA, caja)
    d = detector[s["clave"]]
    texto(sup, "Detector", F_MEDIA, TINTA, (170, 510))
    texto(sup, DETECTORES[d] + " (infrared light)", F_CHICA, TINTA_SUAVE, (170, 540))
    texto(sup, str(d), F_GRANDE, TINTA, (530, 535), centro=True)
    flecha_menos.dibujar(sup)
    flecha_mas.dibujar(sup)

    btn_testigo.dibujar(sup)
    btn_anterior.dibujar(sup)
    btn_siguiente.dibujar(sup)


def polaroid(sup, contenido, centro, ancho, alto, angulo, pie):
    """Una foto instantánea pegada con un clip."""
    capa = pygame.Surface((ancho + 12, alto + 12), pygame.SRCALPHA)
    pygame.draw.rect(capa, (0, 0, 0, 60), (8, 10, ancho, alto), border_radius=6)
    pygame.draw.rect(capa, BLANCO, (0, 0, ancho, alto), border_radius=6)
    lado = contenido.get_width()
    margen = (ancho - lado) // 2
    capa.blit(contenido, (margen, margen))
    texto(capa, pie, F_CHICA_N, TINTA, (ancho // 2, margen + lado + (alto - margen - lado) // 2), centro=True)
    capa = pygame.transform.rotate(capa, angulo)
    sup.blit(capa, capa.get_rect(center=centro))


def foto_vacia(lado, t, mensaje, buscando=False):
    sup = pygame.Surface((lado, lado), pygame.SRCALPHA)        # con transparencia: así el texto se ve bien también en Mac
    sup.fill(tuple(int(v) for v in FOTO_OSCURO) + (255,))
    random.seed(lado)
    for _ in range(18):
        pygame.draw.circle(sup, (90, 132, 146), (random.randrange(lado), random.randrange(lado)), 1)
    if buscando:                                     # un satélite que da vueltas
        a = t * 3
        cx, cy = lado // 2, lado // 2 - 10
        pygame.draw.circle(sup, (74, 112, 124), (cx, cy), 34, 2)
        pygame.draw.circle(sup, OLIVA_CLARO, (cx + 34 * math.cos(a), cy + 34 * math.sin(a)), 7)
        mensaje = mensaje + "." * (int(t * 2) % 4)
    else:
        texto(sup, "?", letra(lado // 3, titulo=True), (90, 132, 146), (lado // 2, lado // 2 - 14), centro=True)
    if mensaje:
        texto(sup, mensaje, F_CHICA_N, (210, 220, 230), (lado // 2, lado - 26), centro=True)
    return sup


def crear_cohete(llama):
    """El cohete de la barrita, dibujado pixel por pixel (60 x 28) y agrandado al doble."""
    c = pygame.Surface((60, 28), pygame.SRCALPHA)
    negro, rojo, gris = (24, 24, 28), TOMATE, (170, 176, 184)
    largo = 0 if llama else 3                                       # la llama titila
    pygame.draw.polygon(c, (242, 120, 40), [(largo, 14), (9, 6), (17, 9), (17, 19), (9, 22)])
    pygame.draw.polygon(c, (255, 214, 64), [(largo + 6, 14), (11, 10), (17, 11), (17, 17), (11, 18)])
    pygame.draw.rect(c, gris, (16, 10, 4, 8))
    pygame.draw.rect(c, negro, (16, 10, 4, 8), 1)
    for signo in (1, -1):                                           # las aletas
        y0, y1 = 14 - signo * 8, 14 - signo * 14
        pts = [(19, y0), (23, y1), (31, y1), (31, y0)]
        pygame.draw.polygon(c, rojo, pts)
        pygame.draw.polygon(c, negro, pts, 1)
    pygame.draw.ellipse(c, (244, 244, 246), (18, 6, 32, 16))        # el cuerpo
    pygame.draw.ellipse(c, (206, 210, 216), (22, 14, 26, 8))        # la sombra de abajo
    pygame.draw.ellipse(c, negro, (18, 6, 32, 16), 1)
    pygame.draw.line(c, rojo, (21, 14), (31, 14), 2)
    pygame.draw.circle(c, (110, 200, 214), (38, 14), 4)              # la ventanita
    pygame.draw.circle(c, negro, (38, 14), 4, 1)
    pygame.draw.polygon(c, rojo, [(47, 8), (57, 14), (47, 20)])     # la punta
    pygame.draw.polygon(c, negro, [(47, 8), (57, 14), (47, 20)], 1)
    return pygame.transform.scale(c, (120, 56))


COHETES = [crear_cohete(True), crear_cohete(False)]


def barrita_cohete(sup, x, y, ancho, porcentaje, t):
    """La barrita de carga: un cohete que viaja de 0 % a 100 % dejando su estela."""
    alto = 34
    caja = pygame.Rect(x, y, ancho, alto)
    pygame.draw.rect(sup, BLANCO, caja, border_radius=alto // 2)
    pygame.draw.rect(sup, (24, 24, 28), caja, 4, border_radius=alto // 2)
    adentro = caja.inflate(-12, -12)
    viaje = adentro.w - 100                                         # cuánto puede avanzar el cohete
    punta = adentro.x + 100 + viaje * porcentaje / 100
    estela = pygame.Rect(adentro.x, adentro.y, max(adentro.h, punta - adentro.x - 60), adentro.h)
    pygame.draw.rect(sup, PIZARRA, estela, border_radius=adentro.h // 2)
    cohete = COHETES[int(t * 8) % 2]
    sup.blit(cohete, cohete.get_rect(midright=(punta + 8, caja.centery + 1)))
    texto(sup, f"{int(porcentaje)} %", F_GRANDE, PINO, (caja.right + 12, caja.centery - 18))


def dibujar_pagina_derecha(sup, t):
    texto(sup, "SPHEREx EVIDENCE", F_CHICA_N, TINTA_SUAVE, (680, 96))
    btn_info.dibujar(sup)
    resultado = pruebas.get(clave_actual())
    esta_buscando = investigando() and investigacion.clave == clave_actual()

    desafio = resultado.get("desafio") if resultado else None
    pendiente = bool(resultado) and not resultado.get("informe_visible") and desafio is not None
    if resultado and resultado["cuadros"]:
        cuadros = resultado["cuadros"]
        n = int(t / 0.7) % len(cuadros)               # el parpadeo
        if pendiente and desafio["tipo"] == "senialar":
            n = len(cuadros) - 1                      # quieta en la última pasada para señalar
        fecha, foto = cuadros[n]
        foto = foto.copy()
        medio = foto.get_width() // 2
        pygame.draw.line(foto, OLIVA_CLARO, (medio, 0), (medio, 18), 2)            # marcas del centro
        pygame.draw.line(foto, OLIVA_CLARO, (0, medio), (18, medio), 2)
        pie = f"Pass {n + 1} of {len(cuadros)} · {fecha}"
        resta = resultado["resta"]
        pie_resta = "Difference: last − first"
    else:
        foto = foto_vacia(200, t, "Searching" if esta_buscando else "No evidence yet", esta_buscando)
        pie = "Blinking photos"
        resta = foto_vacia(140, t, "")
        pie_resta = "Difference"
    if pendiente and desafio["tipo"] == "senialar" and resultado["respuesta"] is not None:
        lado = resultado["fotos"][-1][1].shape[0]
        ox = desafio["objetivo"][0] / lado * foto.get_width()
        oy = foto.get_height() - desafio["objetivo"][1] / lado * foto.get_height()
        pygame.draw.circle(foto, OLIVA_CLARO, (ox, oy), 16, 3)                   # dónde estaba
        cx, cy = desafio["clic"][0] - FOTO_GRANDE.x, desafio["clic"][1] - FOTO_GRANDE.y
        pygame.draw.line(foto, (230, 120, 90), (cx - 8, cy - 8), (cx + 8, cy + 8), 3)  # dónde hiciste clic
        pygame.draw.line(foto, (230, 120, 90), (cx - 8, cy + 8), (cx + 8, cy - 8), 3)
    polaroid(sup, foto, (815, 272), 236, 276, 2, pie)
    clip(sup, 895, 140, -15)
    polaroid(sup, resta, (1055, 258), 168, 210, -4, pie_resta)
    clip(sup, 1102, 158, 12, AZUL_LASER)

    nota = pygame.Rect(680, 422, 460, 180)
    pygame.draw.rect(sup, NOTA_SOMBRA, nota.move(4, 5), border_radius=10)
    pygame.draw.rect(sup, NOTA, nota, border_radius=10)
    cinta = pygame.Rect(nota.centerx - 50, nota.top - 10, 100, 22)
    pygame.draw.rect(sup, (240, 230, 224), cinta)
    botones_desafio.clear()
    titulo_nota = ("Detective challenge" if pendiente else
                   "Final verdict" if resultado and resultado.get("en_veredicto") else "Detective report")
    texto(sup, titulo_nota, F_MEDIA, PINO, (nota.x + 18, nota.y + 12))

    if pendiente:
        dibujar_desafio(sup, nota, resultado, desafio)
    elif resultado and resultado.get("en_veredicto"):
        dibujar_veredicto(sup, nota, resultado)
    elif esta_buscando:
        parrafo(sup, ultimo_aviso or "Starting the investigation…", F_TEXTO, TINTA, nota.x + 18, nota.y + 48, 420)
        barrita_cohete(sup, nota.x + 18, nota.y + 116, 350, cohete_pct, t)
    elif resultado:
        color = VERDE if resultado.get("resuelto") else OCRE
        texto(sup, resultado["titulo"], F_MEDIA, color, (nota.x + 18, nota.y + 42))
        y = nota.y + 72
        for linea in resultado["lineas"]:
            if not linea.startswith("Error"):
                estrella5(sup, color, nota.x + 25, y + 10, 6)
            texto(sup, linea, F_TEXTO, TINTA, (nota.x + 38, y))
            y += 22
    else:
        parrafo(sup, "Press \"Examine evidence\" to search for the suspect's photos "
                     "in NASA's SPHEREx telescope.", F_TEXTO, TINTA, nota.x + 18, nota.y + 52, 420)

    if investigando():
        btn_examinar.activo, btn_examinar.contenido = False, "Investigating…"
    elif resultado is None:
        btn_examinar.activo, btn_examinar.contenido = True, "Examine evidence"
    elif pendiente:
        btn_examinar.activo, btn_examinar.contenido = False, "Solve the challenge"
    elif resultado.get("pistas") and resultado.get("veredicto") is None and not resultado.get("en_veredicto"):
        btn_examinar.activo, btn_examinar.contenido = True, "Final verdict ›"
    elif resultado.get("en_veredicto") and resultado.get("veredicto") is None:
        btn_examinar.activo, btn_examinar.contenido = False, "Choose Yes or No"
    elif resultado.get("pistas"):
        btn_examinar.activo, btn_examinar.contenido = True, "Another challenge"
    elif resultado.get("reintentar"):
        btn_examinar.activo, btn_examinar.contenido = True, "Try again"
    else:
        btn_examinar.activo, btn_examinar.contenido = False, "Case examined"
    btn_examinar.dibujar(sup)


def dibujar_veredicto(sup, nota, resultado):
    """La pregunta final: ¿es un planeta?"""
    s = actual()
    pos = pygame.mouse.get_pos()
    if resultado.get("veredicto") is None:
        parrafo(sup, f"You checked all the clues. Is {s['nombre']} a planet?",
                F_TEXTO, TINTA, nota.x + 18, nota.y + 46, 424)
        for i, (texto_boton, valor) in enumerate([("Yes, it's a planet", True), ("No, it's not a planet", False)]):
            b = Boton((nota.x + 18 + i * 218, nota.y + 118, 206, 40), texto_boton,
                      (BLANCO, PAPEL, PAPEL_BORDE), letra(22, titulo=True), PIZARRA)
            b.hover = b.rect.collidepoint(pos)
            b.dibujar(sup)
            botones_desafio.append((b, ("planeta", valor)))
        return
    if resultado["veredicto"]:
        r = texto(sup, "Correct! Case solved", F_MEDIA, VERDE, (nota.x + 18, nota.y + 44))
        estrella5(sup, OLIVA_CLARO, r.right + 22, nota.y + 58, 12)
        texto(sup, f"+{XP_VEREDICTO} XP", F_MEDIA, VERDE, (r.right + 38, nota.y + 44))
    else:
        texto(sup, "Case solved, but no XP", F_MEDIA, OCRE, (nota.x + 18, nota.y + 44))
    respuesta = "It's not a planet. " if not s["es_planeta"] else "It's a planet! "
    parrafo(sup, respuesta + s["por_que"], F_TEXTO, TINTA, nota.x + 18, nota.y + 80, 424)


def dibujar_desafio(sup, nota, resultado, desafio):
    """La pregunta, los botones de respuesta y lo que pasó al responder."""
    pos = pygame.mouse.get_pos()
    if resultado["respuesta"] is None:
        y = parrafo(sup, desafio["pregunta"], F_TEXTO, TINTA, nota.x + 18, nota.y + 46, 424)
        if desafio["tipo"] == "senialar":
            parrafo(sup, "Hint: look for the bright dot. The little lines mark the center.",
                    F_CHICA, TINTA_SUAVE, nota.x + 18, y + 8, 424)
            return
        y = max(y + 8, nota.y + 100)
        for i, opcion in enumerate(desafio["opciones"]):
            col, fila = i % 2, i // 2
            b = Boton((nota.x + 18 + col * 218, y + fila * 40, 206, 34), opcion,
                      (BLANCO, PAPEL, PAPEL_BORDE), letra(22, titulo=True), PIZARRA)
            b.hover = b.rect.collidepoint(pos)
            b.dibujar(sup)
            botones_desafio.append((b, i))
        return
    if resultado["respuesta"]:
        r = texto(sup, "Well done, detective!", F_MEDIA, VERDE, (nota.x + 18, nota.y + 44))
        estrella5(sup, OLIVA_CLARO, r.right + 22, nota.y + 58, 12)          # la estrellita va justo después
        texto(sup, f"+{XP_DESAFIO} XP", F_MEDIA, VERDE, (r.right + 38, nota.y + 44))
    else:
        correcta = desafio["opciones"][desafio["correcta"]] if desafio["opciones"] else None
        texto(sup, "Almost!" + (f" It was: {correcta}" if correcta else ""), F_MEDIA, OCRE, (nota.x + 18, nota.y + 44))
    parrafo(sup, desafio["explicacion"], F_TEXTO, TINTA, nota.x + 18, nota.y + 80, 424)
    btn_ver_informe.hover = btn_ver_informe.rect.collidepoint(pos)
    btn_ver_informe.dibujar(sup)


PERFILES = {
    "santi": ("Detective Santi", [("Favorite color", "White", BLANCO),
                                  ("Gadget", "Alien detector", None),
                                  ("Favorite astronaut", "Yuri Gagarin", None),
                                  ("Favorite planet", "Saturn", None),
                                  ("Weakness", "Black holes", None)]),
    "martina": ("Detective Marti", [("Favorite color", "Magenta", (214, 30, 140)),
                                    ("Gadget", "Star flashlight", None),
                                    ("Favorite astronaut", "Christina Koch", None),
                                    ("Favorite planet", "Neptune", None),
                                    ("Weakness", "The void", None)]),
}
volteo = {"santi": 0.0, "martina": 0.0}        # 0 = foto, 1 = ficha (el valor va cambiando al girar)
volteo_meta = {"santi": 0.0, "martina": 0.0}
zonas_detectives = {}                           # dónde está cada foto, para hacer clic


def ficha_detective(clave):
    """El dorso de la foto: la ficha secreta del detective."""
    nombre, datos = PERFILES[clave]
    capa = pygame.Surface((220, 262), pygame.SRCALPHA)
    pygame.draw.rect(capa, (0, 0, 0, 70), (8, 10, 210, 250), border_radius=8)
    pygame.draw.rect(capa, PAPEL, (0, 0, 210, 250), border_radius=8)
    pygame.draw.rect(capa, PINO, (0, 0, 210, 44), border_top_left_radius=8, border_top_right_radius=8)
    texto(capa, "SECRET FILE", F_CHICA_N, NOTA, (105, 12), centro=True)
    texto(capa, nombre, letra(22, titulo=True), BLANCO, (105, 30), centro=True)
    y = 52
    for etiqueta_dato, valor, color in datos:
        texto(capa, etiqueta_dato.upper(), F_CHICA_N, TINTA_SUAVE, (14, y))
        x = 14
        if color:                                                   # una muestrita del color
            pygame.draw.rect(capa, color, (14, y + 20, 14, 14), border_radius=3)
            pygame.draw.rect(capa, TINTA, (14, y + 20, 14, 14), 1, border_radius=3)
            x = 34
        texto(capa, valor, F_TEXTO, TINTA, (x, y + 15))
        y += 39
    return capa


def polaroid_dibujo(sup, clave, centro, angulo, pie, reemplazo, t):
    """Una foto instantánea con un dibujo de Marti (o su reemplazo). Si la tocás, se da vuelta."""
    meta = volteo_meta.get(clave, 0)
    volteo[clave] += max(-0.08, min(0.08, meta - volteo[clave]))   # gira de a poquito
    giro = volteo[clave]
    zonas_detectives[clave] = pygame.Rect(0, 0, 230, 270)
    zonas_detectives[clave].center = centro
    if giro > 0.5:
        capa = ficha_detective(clave)
    else:
        capa = None
    if capa is None:
        capa = cara_detective(clave, pie, reemplazo, t)
    ancho = max(2, int(capa.get_width() * abs(math.cos(math.pi * giro))))
    capa = pygame.transform.smoothscale(capa, (ancho, capa.get_height()))
    capa = pygame.transform.rotate(capa, angulo)
    sup.blit(capa, capa.get_rect(center=centro))


def cara_detective(clave, pie, reemplazo, t):
    capa = pygame.Surface((220, 262), pygame.SRCALPHA)
    pygame.draw.rect(capa, (0, 0, 0, 70), (8, 10, 210, 250), border_radius=8)
    pygame.draw.rect(capa, BLANCO, (0, 0, 210, 250), border_radius=8)
    pygame.draw.rect(capa, PAPEL, (14, 14, 182, 182), border_radius=4)
    img = dibujo_de_martina(clave, 176)
    if img:
        capa.blit(img, img.get_rect(center=(105, 105)))
    else:
        reemplazo(capa, t)
    texto(capa, pie, F_MEDIA, TINTA, (105, 222), centro=True)
    return capa


SPACE_APPS = "https://www.spaceappschallenge.org/"
WEB_SPHEREX = "https://science.nasa.gov/mission/spherex/"     # la página oficial del telescopio
zona_telescopio = pygame.Rect(440, 150, 400, 300)
insignia = pygame.Rect(16, 12, 250, 62)


def dibujar_insignia_space_apps(sup):
    """Arriba a la izquierda: NASA Space Apps Challenge, con link a la página."""
    encima = insignia.collidepoint(pygame.mouse.get_pos())
    logo = dibujo_de_martina("spaceapps", 196, 76)
    if logo:                                   # el logo oficial es blanco: va sobre un cartel oscuro
        insignia.size = (220, 90)
        pygame.draw.rect(sup, SOMBRA, insignia.move(3, 5), border_radius=14)
        pygame.draw.rect(sup, PINO if encima else PIZARRA, insignia, border_radius=14)
        sup.blit(logo, logo.get_rect(center=insignia.center))
        return
    pygame.draw.rect(sup, SOMBRA, insignia.move(3, 5), border_radius=14)
    pygame.draw.rect(sup, BLANCO if encima else PAPEL, insignia, border_radius=14)
    pygame.draw.rect(sup, PAPEL_BORDE, insignia, 3, border_radius=14)
    if True:
        pygame.draw.circle(sup, AZUL_LASER, (insignia.x + 32, insignia.centery), 20)
        pygame.draw.ellipse(sup, BLANCO, (insignia.x + 10, insignia.centery - 6, 44, 12), 2)
        pygame.draw.circle(sup, BLANCO, (insignia.x + 40, insignia.centery - 9), 2)
        pygame.draw.circle(sup, BLANCO, (insignia.x + 24, insignia.centery + 9), 2)
        texto(sup, "NASA Space Apps", letra(24, titulo=True), PINO, (insignia.x + 62, insignia.y + 6))
        texto(sup, "Challenge 2026  ›", F_CHICA_N, TINTA_SUAVE, (insignia.x + 64, insignia.y + 36))


def dibujar_menu(sup, t):
    dibujar_fondo(sup, t)

    ventana = pygame.Rect(440, 150, 400, 300)                       # la ventana del observatorio
    pygame.draw.rect(sup, TAPA, ventana.inflate(28, 28), border_radius=200)
    cielo = pygame.Surface(ventana.size, pygame.SRCALPHA)
    for y in range(ventana.h):
        f = y / ventana.h
        cielo.fill((int(16 + 22 * f), int(28 + 34 * f), int(34 + 38 * f)), (0, y, ventana.w, 1))
    random.seed(3)
    for _ in range(60):
        x, y = random.randrange(ventana.w), random.randrange(ventana.h)
        b = 150 + int(100 * (0.5 + 0.5 * math.sin(t * 2 + x)))
        pygame.draw.circle(cielo, (b, b, min(255, b + 20)), (x, y), 1)
    mascara = pygame.Surface(ventana.size, pygame.SRCALPHA)
    pygame.draw.rect(mascara, (255, 255, 255, 255), mascara.get_rect(), border_radius=190)
    cielo = cielo.convert_alpha()
    cielo.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    sup.blit(cielo, ventana)
    pygame.draw.line(sup, TAPA, (ventana.centerx, ventana.top), (ventana.centerx, ventana.bottom), 6)
    pygame.draw.line(sup, TAPA, (ventana.left, ventana.centery + 40), (ventana.right, ventana.centery + 40), 6)
    nave = dibujo_de_martina("spherex", 220)
    if nave:
        sup.blit(nave, nave.get_rect(center=(ventana.centerx, ventana.centery + 6 * math.sin(t * 1.2))))
    else:
        telescopio(sup, ventana.centerx, ventana.centery + 10, t)
    encima = zona_telescopio.collidepoint(pygame.mouse.get_pos())
    etiqueta(sup, "SPHEREx Telescope · NASA  ›", AZUL_LASER if encima else PINO,
             ventana.centerx - 116, ventana.bottom - 40)

    cartel = pygame.Rect(300, 22, 680, 112)                          # el título
    pygame.draw.rect(sup, SOMBRA, cartel.move(5, 7), border_radius=24)
    pygame.draw.rect(sup, PAPEL, cartel, border_radius=24)
    pygame.draw.rect(sup, PAPEL_BORDE, cartel, 4, border_radius=24)
    logo = dibujo_de_martina("logo", 640, 90)
    if logo:                                                        # el logo del equipo
        sup.blit(logo, logo.get_rect(center=cartel.center))
    else:
        texto(sup, "Sky Detectives", F_ENORME, PINO, cartel.center, centro=True)

    polaroid_dibujo(sup, "santi", (210, 330), 5, "Detective Santi",
                    lambda c, tt: detective(c, 105, 190, "santi", tt), t)
    polaroid_dibujo(sup, "martina", (1070, 330), -5, "Detective Marti",
                    lambda c, tt: detective(c, 105, 190, "martina", tt), t)
    clip(sup, 262, 190, -18)
    clip(sup, 1020, 192, 18, AZUL_LASER)
    texto(sup, "Tap the photo to see their file", F_CHICA_N, PIZARRA, (210, 478), centro=True)
    texto(sup, "Tap the photo to see their file", F_CHICA_N, PIZARRA, (1070, 478), centro=True)
    dibujar_insignia_space_apps(sup)

    caja = pygame.Rect(300, 478, 680, 140)                           # el diálogo, como en los juegos
    pygame.draw.rect(sup, SOMBRA, caja.move(4, 6), border_radius=18)
    pygame.draw.rect(sup, PAPEL, caja, border_radius=18)
    pygame.draw.rect(sup, PINO, caja, 3, border_radius=18)
    nombre = pygame.Rect(caja.x + 24, caja.y - 22, 230, 40)
    pygame.draw.rect(sup, BLANCO, nombre, border_radius=20)
    pygame.draw.rect(sup, PINO, nombre, 3, border_radius=20)
    texto(sup, "SANTI AND MARTI", F_MEDIA, TINTA, nombre.center, centro=True)
    parrafo(sup, "Hi, detective! NASA's SPHEREx telescope takes pictures of the whole "
                 "sky every 6 months. We have five suspects: some of them move and others "
                 "change their brightness. Will you help us solve the cases?", F_TEXTO, TINTA, caja.x + 28, caja.y + 32, 624)
    if resueltos:
        texto(sup, f"Cases solved: {len(resueltos)} of 5", F_CHICA_N, VERDE, (caja.right - 190, caja.bottom - 26))
    for b in BOTONES_MENU:
        b.dibujar(sup)


def dibujar_como(sup, t):
    dibujar_fondo(sup, t)
    hoja = pygame.Rect(240, 40, 800, 560)
    pygame.draw.rect(sup, SOMBRA, hoja.move(6, 8), border_radius=20)
    pygame.draw.rect(sup, PAPEL, hoja, border_radius=20)
    for y in range(hoja.top + 90, hoja.bottom - 20, 30):
        pygame.draw.line(sup, LINEA_PAPEL, (hoja.left + 24, y), (hoja.right - 24, y), 1)
    clip(sup, hoja.right - 60, hoja.top + 4, -12)
    texto(sup, "How to play", F_TITULO, PINO, (hoja.x + 40, hoja.y + 30))

    pasos = [
        ("Pick a suspect", "Use Previous and Next (or the arrow keys) to switch between them. "
                                "If one doesn't show up, change the detector."),
        ("Examine the evidence", "Press \"Examine evidence\". The game searches for real SPHEREx photos "
                                "of that spot in the sky, from different dates. It takes a few minutes."),
        ("Watch them blink", "The photos take turns. If the suspect jumps to a new place, it moved! "
                                "In the difference, anything that moved shows up as a white and black pair."),
        ("Solve the challenge", "Before the report there's a detective challenge: point at the suspect, "
                               "say what it did or which way it moved. Get it right and you earn XP."),
        ("Read the report and give your verdict", "The report compares your measurement with the astronomers' "
                                             "catalog. At the end, decide: is it a planet? Get it right for more XP."),
    ]
    y = hoja.y + 100
    for n, (titulo, explicacion) in enumerate(pasos, start=1):
        pygame.draw.circle(sup, PINO, (hoja.x + 62, y + 14), 20)
        texto(sup, str(n), F_GRANDE, BLANCO, (hoja.x + 62, y + 14), centro=True)
        texto(sup, titulo, F_MEDIA, TINTA, (hoja.x + 96, y - 4))
        y = parrafo(sup, explicacion, F_TEXTO, TINTA, hoja.x + 96, y + 28, 640) + 8
    for b in BOTONES_COMO:
        b.dibujar(sup)


DATOS_SPHEREX = [
    ("What it is", "A NASA space telescope that circles around the Earth. "
               "It was launched on March 11, 2025."),
    ("What it sees", "Infrared light, which our eyes can't see. It splits it into 102 colors, "
               "from 0.75 to 5 microns."),
    ("How it works", "It photographs the whole sky every 6 months. That way it can compare the same "
                     "spot on different dates, just like we do in this game."),
    ("What it looks for", "How the universe grew after the Big Bang, how galaxies "
                  "formed and where there is water ice in our galaxy."),
    ("A huge number", "It will take pictures of more than a billion objects: stars, "
                         "galaxies, asteroids, comets and brown dwarfs."),
    ("Its name", "SPHEREx stands for: Spectro-Photometer for the History of "
                  "the Universe, Epoch of Reionization and Ices Explorer."),
]


def dibujar_spherex(sup, t):
    dibujar_fondo(sup, t)
    hoja = pygame.Rect(90, 30, 1100, 590)
    pygame.draw.rect(sup, SOMBRA, hoja.move(6, 8), border_radius=20)
    pygame.draw.rect(sup, PAPEL, hoja, border_radius=20)
    clip(sup, hoja.right - 60, hoja.top + 4, -12)
    texto(sup, "What is SPHEREx?", F_TITULO, PINO, (hoja.x + 40, hoja.y + 24))
    texto(sup, "The telescope that takes the pictures of our suspects", F_TEXTO, TINTA_SUAVE, (hoja.x + 42, hoja.y + 78))

    ventana = pygame.Rect(hoja.x + 40, hoja.y + 120, 330, 330)           # el telescopio en su ventana
    pygame.draw.rect(sup, TAPA, ventana.inflate(16, 16), border_radius=24)
    pygame.draw.rect(sup, INDIGO, ventana, border_radius=18)
    random.seed(11)
    for _ in range(50):
        x, y = ventana.x + random.randrange(ventana.w), ventana.y + random.randrange(ventana.h)
        b = 150 + int(100 * (0.5 + 0.5 * math.sin(t * 2 + x)))
        pygame.draw.circle(sup, (b, b, min(255, b + 20)), (x, y), 1)
    nave = dibujo_de_martina("spherex", 260)
    if nave:
        sup.blit(nave, nave.get_rect(center=(ventana.centerx, ventana.centery + 6 * math.sin(t * 1.2))))
    else:
        telescopio(sup, ventana.centerx, ventana.centery + 30, t)
    etiqueta(sup, "102 colors", PINO, ventana.x, ventana.bottom + 44)
    etiqueta(sup, "Whole sky", OLIVA_OSCURO, ventana.x + 118, ventana.bottom + 44)
    etiqueta(sup, "Every 6 months", INDIGO_MEDIO, ventana.x + 238, ventana.bottom + 44)

    x0, y = hoja.x + 420, hoja.y + 120                                     # las fichas con los datos
    for i, (titulo, explicacion) in enumerate(DATOS_SPHEREX):
        col, fila = i % 2, i // 2
        ficha = pygame.Rect(x0 + col * 330, y + fila * 150, 314, 138)
        pygame.draw.rect(sup, NOTA if col == fila % 2 else BLANCO, ficha, border_radius=12)
        rect_punteado(sup, PAPEL_BORDE, ficha)
        estrella5(sup, OLIVA, ficha.x + 20, ficha.y + 22, 9)
        texto(sup, titulo, F_MEDIA, PINO, (ficha.x + 36, ficha.y + 6))
        parrafo(sup, explicacion, F_CHICA, TINTA, ficha.x + 16, ficha.y + 44, 284)
    for b in BOTONES_SPHEREX:
        b.dibujar(sup)


# ------------------------------------------------------------------
# 8b. EL SEGUNDO TESTIGO (WISE) Y LAS FUENTES
# ------------------------------------------------------------------
WISEVIEW = ("http://byw.tools/wiseview#ra={ra:.6f}&dec={dec:.6f}&size=176&band=2&speed=500"
            "&minbright=-50.0000&maxbright=500.0000&window=0.5&diff_window=1&linear=1&color="
            "&zoom=9&border=0&gaia=0&invert=1&maxdyr=0&scandir=0&neowise=0&diff=0&outer_epochs=0"
            "&unique_window=1&smooth_scan=0&shift=0&pmra=0&pmdec=0")


def abrir_testigo():
    """Abre WiseView: las fotos del telescopio WISE de la NASA, de 2010 a 2024, parpadeando.

    WISE miró el cielo durante muchos años, así que centramos la foto en dónde estaba
    el sospechoso en 2017 (la mitad de esos años) usando su movimiento propio.
    """
    s = actual()
    anios = 17.0                                               # de 2000 a 2017
    ra = s["ra"] + s["pm_ra"] / 3.6e6 * anios / math.cos(math.radians(s["dec"]))
    dec = s["dec"] + s["pm_dec"] / 3.6e6 * anios
    webbrowser.open(WISEVIEW.format(ra=ra, dec=dec))


DATOS_FUENTES = [
    ("SPHEREx", "NASA · IRSA archive (Caltech)", "The photos", PINO,
     "All the photos in the game come from SPHEREx. We download them from the IRSA archive.",
     "irsa.ipac.caltech.edu/Missions/spherex.html"),
    ("IRSA tutorials", "NASA · Caltech-IPAC", "The method", PINO,
     "We followed their steps to search, cut out and open the SPHEREx photos.",
     "caltech-ipac.github.io/irsa-tutorials/spherex/"),
    ("WISE and WiseView", "NASA · Backyard Worlds", "Another witness", OLIVA_OSCURO,
     "WISE photographed the sky from 2010 to 2024. With more years, motion is easier to see.",
     "byw.tools/wiseview"),
    ("SIMBAD", "CDS · Strasbourg", "The answer", INDIGO_MEDIO,
     "It tells us how much each suspect really moves, to compare with what we measured.",
     "simbad.cds.unistra.fr"),
    ("Gaia", "ESA · archive at MAST", "The answer", INDIGO_MEDIO,
     "It measures stars with amazing precision. Much of SIMBAD's data comes from Gaia.",
     "archive.stsci.edu/missions-and-data/gaia"),
    ("NEOSSAT", "Canadian Space Agency", "Next step", OCRE,
     "A satellite that hunts asteroids. We want to add it as a third telescope.",
     "asc-csa.gc.ca/eng/satellites/neossat/"),
]


def dibujar_fuentes(sup, t):
    dibujar_fondo(sup, t)
    hoja = pygame.Rect(90, 30, 1100, 590)
    pygame.draw.rect(sup, SOMBRA, hoja.move(6, 8), border_radius=20)
    pygame.draw.rect(sup, PAPEL, hoja, border_radius=20)
    clip(sup, hoja.right - 60, hoja.top + 4, -12)
    texto(sup, "Sources", F_TITULO, PINO, (hoja.x + 40, hoja.y + 24))
    texto(sup, "The real data we used to solve the cases. Click a card to visit it.",
          F_TEXTO, TINTA_SUAVE, (hoja.x + 42, hoja.y + 78))
    fichas_fuentes.clear()
    pos = pygame.mouse.get_pos()
    x0, y0 = hoja.x + 40, hoja.y + 118
    for i, (nombre, quien, uso, color, explicacion, web) in enumerate(DATOS_FUENTES):
        col, fila = i % 3, i // 3
        ficha = pygame.Rect(x0 + col * 346, y0 + fila * 206, 330, 192)
        encima = ficha.collidepoint(pos)
        pygame.draw.rect(sup, NOTA if encima else BLANCO, ficha, border_radius=12)
        rect_punteado(sup, color if encima else PAPEL_BORDE, ficha)
        texto(sup, nombre, F_MEDIA, PINO, (ficha.x + 16, ficha.y + 6))
        texto(sup, quien, F_CHICA, TINTA_SUAVE, (ficha.x + 17, ficha.y + 40))
        etiqueta(sup, uso, color, ficha.x + 16, ficha.y + 64)
        parrafo(sup, explicacion, F_CHICA, TINTA, ficha.x + 16, ficha.y + 100, 298)
        texto(sup, web, F_CHICA, OLIVA_OSCURO, (ficha.x + 16, ficha.bottom - 28))
        fichas_fuentes.append((ficha, "https://" + web if not web.startswith("byw") else "http://" + web))
    texto(sup, "Made with Python, pygame, astropy, astroquery and reproject  ·  Fonts: Patrick Hand and Titillium Web",
          F_CHICA, TINTA_SUAVE, (hoja.centerx, hoja.bottom - 26), centro=True)
    for b in BOTONES_FUENTES:
        b.dibujar(sup)


def ir_a(nombre):
    global pantalla_actual, volver_a
    if nombre == "spherex":
        volver_a = pantalla_actual if pantalla_actual != "spherex" else volver_a
    pantalla_actual = nombre


# ------------------------------------------------------------------
# 9. EL BUCLE PRINCIPAL
# ------------------------------------------------------------------
def manejar_juego(evento, pos):
    if evento.type == pygame.KEYDOWN:
        if evento.key == pygame.K_LEFT:
            cambiar_sospechoso(-1)
        elif evento.key == pygame.K_RIGHT:
            cambiar_sospechoso(1)
        elif evento.key == pygame.K_UP:
            cambiar_detector(1)
        elif evento.key == pygame.K_DOWN:
            cambiar_detector(-1)
        elif evento.key in (pygame.K_SPACE, pygame.K_RETURN):
            examinar()
        elif evento.key == pygame.K_ESCAPE:
            ir_a("menu")
    if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
        for b, i in botones_desafio:
            if b.tocado(pos):
                if isinstance(i, tuple):
                    responder_veredicto(i[1])
                else:
                    responder(i)
                return
        if clic_en_foto(pos):
            return
        resultado = pruebas.get(clave_actual())
        if resultado and resultado.get("respuesta") is not None and not resultado.get("informe_visible") \
                and btn_ver_informe.tocado(pos):
            ver_informe()
            return
        if btn_anterior.tocado(pos):
            cambiar_sospechoso(-1)
        elif btn_siguiente.tocado(pos):
            cambiar_sospechoso(1)
        elif btn_examinar.tocado(pos):
            examinar()
        elif flecha_menos.tocado(pos):
            cambiar_detector(-1)
        elif flecha_mas.tocado(pos):
            cambiar_detector(1)
        elif btn_menu.tocado(pos):
            ir_a("menu")
        elif btn_info.tocado(pos):
            ir_a("spherex")
        elif btn_testigo.tocado(pos):
            abrir_testigo()


def manejar_menu(evento, pos):
    if evento.type == pygame.KEYDOWN:
        if evento.key in (pygame.K_SPACE, pygame.K_RETURN):
            ir_a("juego")
        elif evento.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
    if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
        if insignia.collidepoint(pos):
            webbrowser.open(SPACE_APPS)
            return
        if zona_telescopio.collidepoint(pos):
            webbrowser.open(WEB_SPHEREX)
            return
        for clave, zona in zonas_detectives.items():
            if zona.collidepoint(pos):
                volteo_meta[clave] = 0.0 if volteo_meta[clave] else 1.0   # se da vuelta
                return
        if btn_jugar.tocado(pos):
            ir_a("juego")
        elif btn_como.tocado(pos):
            ir_a("como")
        elif btn_spherex.tocado(pos):
            ir_a("spherex")
        elif btn_fuentes.tocado(pos):
            ir_a("fuentes")


def manejar_como(evento, pos):
    if evento.type == pygame.KEYDOWN:
        if evento.key == pygame.K_ESCAPE:
            ir_a("menu")
        elif evento.key in (pygame.K_SPACE, pygame.K_RETURN):
            ir_a("juego")
    if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
        if btn_volver.tocado(pos):
            ir_a("menu")
        elif btn_jugar2.tocado(pos):
            ir_a("juego")


def manejar_spherex(evento, pos):
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
        ir_a(volver_a)
    if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
        if btn_volver_s.tocado(pos):
            ir_a(volver_a)
        elif btn_jugar3.tocado(pos):
            ir_a("juego")


def manejar_fuentes(evento, pos):
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
        ir_a("menu")
    if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
        if btn_volver_f.tocado(pos):
            ir_a("menu")
            return
        for ficha, web in fichas_fuentes:
            if ficha.collidepoint(pos):
                webbrowser.open(web)


def principal():
    inicio = time.time()
    while True:
        t = time.time() - inicio
        pos = pygame.mouse.get_pos()
        pantalla_de_ahora = pantalla_actual
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if pantalla_de_ahora == "menu":
                manejar_menu(evento, pos)
            elif pantalla_de_ahora == "como":
                manejar_como(evento, pos)
            elif pantalla_de_ahora == "spherex":
                manejar_spherex(evento, pos)
            elif pantalla_de_ahora == "fuentes":
                manejar_fuentes(evento, pos)
            else:
                manejar_juego(evento, pos)

        revisar_investigacion()                     # la investigación sigue aunque estés en el menú
        botones = {"menu": BOTONES_MENU, "como": BOTONES_COMO, "spherex": BOTONES_SPHEREX,
                   "fuentes": BOTONES_FUENTES}.get(pantalla_actual, BOTONES)
        if pantalla_actual == "juego":
            botones = botones + [b for b, _ in botones_desafio]
        mano = False
        for b in botones:
            b.hover = b.rect.collidepoint(pos)
            mano = mano or (b.hover and getattr(b, "activo", True))
        if pantalla_actual == "fuentes":
            mano = mano or any(f.collidepoint(pos) for f, _ in fichas_fuentes)
        if pantalla_actual == "menu":
            mano = mano or insignia.collidepoint(pos) or zona_telescopio.collidepoint(pos) or any(z.collidepoint(pos) for z in zonas_detectives.values())
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if mano else pygame.SYSTEM_CURSOR_ARROW)

        if pantalla_actual == "menu":
            dibujar_menu(pantalla, t)
        elif pantalla_actual == "como":
            dibujar_como(pantalla, t)
        elif pantalla_actual == "spherex":
            dibujar_spherex(pantalla, t)
        elif pantalla_actual == "fuentes":
            dibujar_fuentes(pantalla, t)
        else:
            dibujar_fondo(pantalla, t)
            dibujar_cuaderno(pantalla)
            dibujar_pagina_izquierda(pantalla, t)
            dibujar_pagina_derecha(pantalla, t)
            dibujar_contador(pantalla)
            btn_menu.dibujar(pantalla)
        pygame.display.flip()
        reloj.tick(30)


if __name__ == "__main__":
    principal()
