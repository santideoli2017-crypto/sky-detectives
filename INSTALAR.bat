@echo off
cd /d "%~dp0"
echo ==================================================
echo  SKY DETECTIVES - Instalacion
echo  Puede tardar unos 10 minutos. NO cierres esta ventana.
echo  Si te pregunta algo, escribi  y  y apreta Enter.
echo ==================================================
echo.
where py >/dev/null 2>nul
if errorlevel 1 goto SINPYTHON
py -3.13 --version >/dev/null 2>nul
if not errorlevel 1 goto LIBRERIAS
echo Instalando Python 3.13...
py install 3.13
py -3.13 --version >/dev/null 2>nul
if not errorlevel 1 goto LIBRERIAS
:SINPYTHON
echo.
echo  Esta compu no tiene Python 3.13.
echo  Se va a abrir la pagina de Python: baja "Python 3.13" para Windows,
echo  instalalo (marca la casilla "Add python.exe to PATH")
echo  y despues hace doble clic en INSTALAR otra vez.
start https://www.python.org/downloads/windows/
pause
exit /b
:LIBRERIAS
py -3.13 --version
echo.
echo Instalando las librerias del juego...
py -3.13 -m pip install --no-warn-script-location numpy pygame astropy pyvo astroquery reproject matplotlib
echo.
echo ===== Revisando =====
py -3.13 -c "import numpy, pygame, astropy, astroquery, reproject; print('TODO LISTO! Ahora hace doble clic en EMPEZAR.')"
if errorlevel 1 echo Algo no se instalo. Saca una foto de esta ventana y mandasela a un adulto.
echo.
pause
