# Sky Detectives 🔭

**NASA Space Apps Challenge 2026 · Challenge: Planet X and SPHEREx · Uruguay**

Two kid detectives hunt for Planet X with **real NASA SPHEREx photos**.

- **Santi (9)** – programming
- **Marti (10)** – drawings

## What it does

Sky Detectives is a game. You pick a suspect in the sky, the game downloads its real
SPHEREx infrared photos from NASA's IRSA archive, and the photos **blink** so you can see
whether the suspect moved or changed its brightness. You solve a detective challenge,
read the report and give your verdict: **is it Planet X?**

## The science inside

1. Ask the SIMBAD catalog where the star was in the year 2000.
2. Move it to where it should be today (proper motion).
3. Download SPHEREx cut-outs from IRSA (collections `spherex_dr1` and `spherex_qr3`).
4. Align and stack the photos of each 6-month pass on a common north-up grid.
5. Find the star's center in each pass and measure how far it moved (arcseconds per year).

Test: for Kapteyn's Star we measured **6.9″/year**; the catalog says **8.7″/year**.

## The suspects

| Suspect | Nickname |
|---|---|
| Barnard's Star | The Runner |
| Epsilon Indi B | The Twins |
| WISE 0855 | The Cold Ghost |
| RW Aurigae | The Blinking Baby |
| R Draconis | The Giant Heart |

## How to run it

Needs **Python 3.13** (newer versions can't install astropy/reproject yet).

```
python3.13 -m pip install numpy pygame astropy pyvo astroquery reproject matplotlib
python3.13 juego.py
```

On Windows you can double-click `INSTALAR.bat` once, then `EMPEZAR.bat` to play.

## Data and tools

- **SPHEREx** – NASA / IRSA (Caltech-IPAC): the photos
- **WISE / WiseView** – NASA: a second witness with photos from 2010–2024
- **SIMBAD** (CDS) and **Gaia** (ESA): the true motion, to check our measurement
- Python, pygame, astropy, astroquery, reproject
- Fonts: Patrick Hand and Titillium Web (SIL Open Font License)
