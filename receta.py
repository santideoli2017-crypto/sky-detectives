"""Receta SPHEREx: buscar, bajar, alinear y agrupar recortes por pasada.

Práctica de Misión Planeta X. Todas las funciones son cortas a propósito:
leelas de arriba hacia abajo.
"""
import time
import warnings

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.utils.data import conf
from astropy.wcs import WCS, FITSFixedWarning
import astropy.units as u

warnings.simplefilter("ignore", FITSFixedWarning)
conf.remote_timeout = 120          # los archivos de SPHEREx tardan en llegar

PIXEL = 6.2 / 3600                 # tamaño de un pixel de SPHEREx, en grados


def posicion_hoy(ra, dec, pm_ra_mas=0.0, pm_dec_mas=0.0, fecha="2026-01-01"):
    """Mueve una estrella desde su posición del año 2000 hasta `fecha`.

    pm_ra_mas y pm_dec_mas son el movimiento propio en milisegundos de arco
    por año (lo da SIMBAD). Sin movimiento propio devuelve la misma posición.
    """
    c = SkyCoord(ra=ra, dec=dec, unit=(u.hourangle, u.deg) if isinstance(ra, str) else u.deg,
                 pm_ra_cosdec=pm_ra_mas * u.mas / u.yr, pm_dec=pm_dec_mas * u.mas / u.yr,
                 obstime=Time("J2000"), frame="icrs")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        nueva = c.apply_space_motion(new_obstime=Time(fecha))
    return SkyCoord(nueva.ra, nueva.dec, frame="icrs")


servidor_caido = False                           # se vuelve True si la NASA no contesta
colecciones_fallidas = []                        # las colecciones que no contestaron en la última búsqueda
COLECCIONES = ["spherex_dr1", "spherex_qr3"]     # dr1 tiene las fotos viejas, qr3 las nuevas


def colecciones_de_hoy():
    """Pregunta a la NASA qué colecciones de SPHEREx existen hoy.

    La NASA a veces cambia los nombres (qr2 se convirtió en dr1). Nos quedamos con las
    fotos del cielo entero: sin las de calibración (_cal), las profundas (_deep) ni los cubos (_cube).
    Si no puede preguntar, usa la lista de arriba.
    """
    try:
        from astroquery.ipac.irsa import Irsa
        todas = [str(c) for c in Irsa.list_collections(servicetype="SIA")["collection"]]
        buenas = [c for c in todas if c.startswith("spherex_")
                  and not c.endswith(("_cal", "_deep", "_cube"))]
        return sorted(buenas) or COLECCIONES
    except Exception:
        return COLECCIONES


def buscar(coord, coleccion="todas", detector=None):
    """Lista de imágenes de SPHEREx que cubren `coord`, ordenadas por fecha.

    Con coleccion="todas" junta las fotos viejas y las nuevas.
    """
    from astroquery.ipac.irsa import Irsa
    from astropy.table import unique, vstack
    global servidor_caido
    nombres = colecciones_de_hoy() if coleccion == "todas" else [coleccion]
    tablas, fallas = [], 0
    colecciones_fallidas.clear()
    for nombre in nombres:
        for intento in range(1, 4):                # si la NASA está ocupada, probamos 3 veces
            try:
                t = Irsa.query_sia(pos=(coord, 2 * u.arcsec), collection=nombre)
                if len(t):
                    tablas.append(t)
                break
            except Exception as error:
                print(f"  (could not search {nombre}, try {intento}: {str(error)[:80]})")
                if intento == 3:
                    fallas += 1
                    colecciones_fallidas.append(nombre)
                else:
                    time.sleep(5 * intento)
    servidor_caido = fallas == len(nombres)        # ninguna colección contestó
    if not tablas:
        from astropy.table import Table
        return Table(names=["access_url", "t_min"], dtype=[str, float])
    tabla = vstack(tablas, join_type="inner", metadata_conflicts="silent")
    if "obs_id" in tabla.colnames and len(tablas) > 1:
        tabla = unique(tabla, keys="obs_id", keep="last")   # la misma foto en dos colecciones cuenta una vez
    if detector is not None and "energy_bandpassname" in tabla.colnames:
        tabla = tabla[tabla["energy_bandpassname"] == f"SPHEREx-D{detector}"]
    if "t_min" in tabla.colnames:
        tabla.sort("t_min")
    return tabla


def agrupar_pasadas(fechas_mjd, separacion_dias=60):
    """Agrupa fechas en pasadas: si entre dos fotos hay más de 60 días, empieza otra."""
    orden = np.argsort(fechas_mjd)
    grupos, actual, anterior = [], [], None
    for i in orden:
        if anterior is not None and fechas_mjd[i] - anterior > separacion_dias:
            grupos.append(actual)
            actual = []
        actual.append(i)
        anterior = fechas_mjd[i]
    if actual:
        grupos.append(actual)
    return grupos


def url_recorte(url_imagen, coord, tamano_grados=0.05):
    """Dirección para bajar solo un pedacito de la imagen, centrado en `coord`."""
    return f"{url_imagen}?center={coord.ra.deg},{coord.dec.deg}&size={tamano_grados}"


def bajar_recorte(url, intentos=4):
    """Abre un recorte y devuelve (imagen, wcs, fecha MJD, detector).

    Si el servidor de la NASA está ocupado (error 503), espera y prueba de nuevo.
    """
    for intento in range(1, intentos + 1):
        try:
            return _bajar_una_vez(url)
        except Exception as error:
            if intento == intentos or "503" not in str(error) and "timed out" not in str(error):
                raise
            espera = 10 * intento
            print(f"    The server is busy. Waiting {espera} seconds and trying again…")
            time.sleep(espera)


def _bajar_una_vez(url):
    with fits.open(url, memmap=False) as hdul:
        hdu = hdul["IMAGE"]
        imagen = np.array(hdu.data, dtype=float)
        cab = hdu.header.copy()
    fecha = cab.get("MJD-AVG") or cab.get("MJD-OBS")
    if fecha is None and cab.get("DATE-OBS"):
        fecha = Time(cab["DATE-OBS"]).mjd
    return imagen, WCS(cab), fecha, cab.get("DETECTOR")


def grilla_comun(coord, lado_pixeles=31):
    """Una grilla fija en el cielo, con el norte arriba, para alinear todas las fotos."""
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [coord.ra.deg, coord.dec.deg]
    w.wcs.crpix = [(lado_pixeles + 1) / 2, (lado_pixeles + 1) / 2]
    w.wcs.cdelt = [-PIXEL, PIXEL]
    return w, (lado_pixeles, lado_pixeles)


def alinear(imagen, wcs, grilla, forma):
    """Gira y mueve la foto para que coincida con la grilla común."""
    from reproject import reproject_interp
    alineada, _ = reproject_interp((imagen, wcs), grilla, shape_out=forma)
    return alineada - np.nanmedian(alineada)     # restamos el fondo del cielo


def apilar(imagenes):
    """Combina varias fotos alineadas de la misma pasada en una más limpia."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmedian(np.array(imagenes), axis=0)


def pasadas(coord, detector=1, coleccion="todas", fotos_por_pasada=5,
            lado_pixeles=31, aviso=print, progreso=None):
    """Todo junto: una imagen limpia y alineada por cada pasada de SPHEREx.

    Devuelve una lista de (fecha en texto, imagen, fecha MJD) y la grilla usada.
    """
    tabla = buscar(coord, coleccion, detector)
    aviso(f"{len(tabla)} images from detector {detector} ({coleccion})")
    if len(tabla) == 0:
        return [], None
    fechas = np.array(tabla["t_min"], dtype=float)
    grupos = agrupar_pasadas(fechas)
    grilla, forma = grilla_comun(coord, lado_pixeles)
    tamano = lado_pixeles * PIXEL * 1.6          # un poco más grande para poder girarla
    resultado = []
    total = sum(min(len(g), fotos_por_pasada) for g in grupos)   # cuántas fotos vamos a bajar
    hechas = 0
    if progreso:
        progreso(hechas, total)
    for n, grupo in enumerate(grupos, start=1):
        elegidas = grupo[:fotos_por_pasada]
        aviso(f"Pass {n}: downloading {len(elegidas)} of {len(grupo)} photos…")
        alineadas = []
        for i in elegidas:
            try:
                img, w, _, _ = bajar_recorte(url_recorte(tabla["access_url"][i], coord, tamano))
                alineadas.append(alinear(img, w, grilla, forma))
            except Exception as error:            # una foto que falla no frena todo
                aviso(f"  (skipped a photo: {error})")
            hechas += 1
            if progreso:
                progreso(hechas, total)               # para la barrita del cohete
            time.sleep(1)                         # una pausa corta para no saturar al servidor
        if alineadas:
            mjd = float(np.mean(fechas[elegidas]))
            fecha = Time(mjd, format="mjd").to_value("iso", subfmt="date")
            resultado.append((fecha, apilar(alineadas), mjd))
    return resultado, grilla


def centroide(imagen, radio=3):
    """Centro de la estrella más brillante cerca del medio de la imagen, en pixeles."""
    alto, ancho = imagen.shape
    cy, cx = alto // 2, ancho // 2
    zona = np.nan_to_num(imagen[cy - 6:cy + 7, cx - 6:cx + 7])
    py, px = np.unravel_index(np.argmax(zona), zona.shape)
    py, px = py + cy - 6, px + cx - 6
    caja = np.nan_to_num(imagen[py - radio:py + radio + 1, px - radio:px + radio + 1]).clip(min=0)
    yy, xx = np.mgrid[py - radio:py + radio + 1, px - radio:px + radio + 1]
    total = caja.sum()
    return float((xx * caja).sum() / total), float((yy * caja).sum() / total)


def medir_movimiento(fotos):
    """Cuántos segundos de arco por año se movió la estrella entre la primera y la última pasada."""
    (_, img1, t1), (_, img2, t2) = fotos[0], fotos[-1]
    x1, y1 = centroide(img1)
    x2, y2 = centroide(img2)
    pixeles = float(np.hypot(x2 - x1, y2 - y1))
    anios = (t2 - t1) / 365.25
    return {"pixeles": pixeles, "segundos_de_arco": pixeles * 6.2,
            "anios": anios, "por_anio": pixeles * 6.2 / anios if anios > 0 else float("nan")}


def parpadeo_gif(fotos, archivo="parpadeo.gif", cuadros_por_segundo=2):
    """Guarda un GIF que alterna las pasadas, como el comparador de Plutón."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    tope = max(np.nanpercentile(f[1], 99.5) for f in fotos)
    fig, ax = plt.subplots(figsize=(4, 4.4))
    ax.set_xticks([]); ax.set_yticks([])
    cuadro = ax.imshow(fotos[0][1], origin="lower", cmap="gray", vmin=0, vmax=tope)
    medio = fotos[0][1].shape[0] // 2
    ax.axhline(medio, color="tab:orange", lw=0.6, alpha=0.6)
    ax.axvline(medio, color="tab:orange", lw=0.6, alpha=0.6)
    titulo = ax.set_title(fotos[0][0])

    def dibujar(i):
        cuadro.set_data(fotos[i % len(fotos)][1])
        titulo.set_text(fotos[i % len(fotos)][0])
        return [cuadro, titulo]

    anim = FuncAnimation(fig, dibujar, frames=len(fotos))
    anim.save(archivo, writer=PillowWriter(fps=cuadros_por_segundo))
    plt.close(fig)
    return archivo
