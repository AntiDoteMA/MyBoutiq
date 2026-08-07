@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul 2>&1

echo ============================================
echo   Boutique Manager - Lancement local
echo ============================================
echo.

rem --- Check Python ---
where python >nul 2>&1
if errorlevel 1 goto nopython

rem --- Install dependencies on first run ---
python -c "import flask, flask_sqlalchemy, pandas, openpyxl" >nul 2>&1
if errorlevel 1 goto installdeps

rem --- Seed the database on first run ---
if not exist "data\shop.db" goto seed
goto run

:nopython
echo [ERREUR] Python 3 est introuvable.
echo Installez Python 3.11 depuis https://www.python.org/downloads/
echo puis relancez ce fichier.
pause
exit /b 1

:installdeps
echo Installation des dependances (une seule fois)...
python -m pip install -r requirements.txt
if errorlevel 1 goto pipfail
if not exist "data\shop.db" goto seed
goto run

:pipfail
echo [ERREUR] Echec de l'installation des dependances.
pause
exit /b 1

:seed
echo Premiere execution : import des donnees du tableau existant...
python seed.py
if errorlevel 1 goto seedfail
goto run

:seedfail
echo [ERREUR] Echec de l'import des donnees.
pause
exit /b 1

:run
echo Demarrage du serveur...
echo Ne fermez pas cette fenetre.
echo L'application s'ouvre dans le navigateur sous quelques secondes.
python app.py
pause