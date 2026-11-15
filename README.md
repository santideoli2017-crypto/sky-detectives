# Sky Detectives 🔭

**NASA Space Apps Challenge 2026 · Challenge: Planet X & SPHEREx · Team Planet MS'X · Uruguay**

A detective game where anyone can investigate the sky with **real data from NASA's SPHEREx telescope**.

## Why we made it

In 1930, Pluto was discovered by blinking two photos of the same patch of sky and spotting the one dot that jumped.
Today, NASA's SPHEREx telescope photographs the whole sky every six months: far too many images for anyone to check alone.
Sky Detectives turns that search into a spot-the-difference detective game that anyone can play.

## What it does

1. **Pick a suspect.** Five real objects, the targets of the challenge, each one a character drawn by Marti.
2. **Examine the evidence.** The game downloads real SPHEREx infrared images of that spot, taken on different dates.
3. **Watch the clues blink.** The photos blink like a flipbook, and a difference image shows anything that moved as a black-and-white pair.
4. **Solve the challenge.** Point at the suspect, say what it did or which way it moved, and earn XP.
5. **Give your verdict.** The report compares your measurement with the astronomers' catalog. Then decide: is it a planet?

A second witness is built in: a button opens NASA **WISE** images (2010–2024) of the same suspect in WiseView.

## Result

For **Epsilon Indi B**, the game measured **1.05 pixels of motion in 1.40 years: 4.7″ per year**.
The SIMBAD catalog says **4.7″ per year** (1% difference; values rounded). Case solved!

## The suspects

| Suspect | Nickname | What to look for |
|---|---|---|
| Barnard's Star | The Runner | Moves fast |
| Epsilon Indi B | The Twins | Moves (two brown dwarfs) |
| WISE 0855 | The Cold Ghost | Moves; very cold, try detectors 5 and 6 |
| RW Aurigae | The Blinking Baby | Changes brightness |
| R Draconis | The Giant Heart | Changes brightness |

## The science inside

1. Ask the SIMBAD catalog where the suspect was in the year 2000.
2. Move it to where it should be today, using its proper motion.
3. Download SPHEREx cut-outs from NASA's IRSA archive (collections `spherex_dr1` and `spherex_qr3`).
4. Align and stack the photos of each 6-month pass on a common north-up grid.
5. Find the suspect's center in each pass and measure how far it moved (arcseconds per year), or how much its brightness changed.
6. If the measurement doesn't match the catalog, the game reports a "doubtful clue" instead of a solved case.

The game saves the photos it downloads, so it keeps working when the archive is busy.

## How to run it

Needs **Python 3.13** (newer versions can't install astropy/reproject yet).

```
python3.13 -m pip install numpy pygame astropy pyvo astroquery reproject matplotlib
python3.13 juego.py
```

On Windows you can double-click `INSTALAR.bat` once, then `EMPEZAR.bat` to play.
The first search of each suspect takes a few minutes, because the game downloads real NASA data.

**Controls:** left/right arrows change the suspect, up/down arrows change the infrared detector, and Space examines the evidence.

## Team

- **Santi (9)** programmed and tested the game. This is his fourth NASA Space Apps Challenge.
- **Marti (10)** drew all the characters by hand. This is her first NASA Space Apps Challenge.

> "For me, the hardest part was improving the game by thinking of improvements that are really useful." — Santi, 9

## Data, tools and credits

**NASA data**
- SPHEREx images – NASA / IRSA (Caltech-IPAC): https://irsa.ipac.caltech.edu/Missions/spherex.html
- IRSA SPHEREx tutorials: https://caltech-ipac.github.io/irsa-tutorials/spherex/
- WISE images via WiseView (Backyard Worlds): http://byw.tools/wiseview

**Other data**
- SIMBAD (CDS, Strasbourg): https://simbad.cds.unistra.fr
- Gaia (ESA), via MAST: https://archive.stsci.edu/missions-and-data/gaia

**Tools**
- Python, pygame, NumPy, Astropy, Astroquery, pyvo, reproject, matplotlib
- Fonts: Patrick Hand and Titillium Web (SIL Open Font License, files included)

**Drawings:** by Marti, drawn by hand, then digitized and enhanced with Canva's AI tools.

## Use of AI (Super Intelligence)

We used an AI assistant (**Claude, by Anthropic**) to help write and debug parts of the Python code and to help draft and translate the texts.
Marti's drawings were digitized and enhanced with Canva's AI tools.
All measurements come from real SPHEREx and SIMBAD data.
