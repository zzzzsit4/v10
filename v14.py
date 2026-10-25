import urllib.request
import json

WEBHOOK_URL = "https://discord.com/api/webhooks/1563727658859241472/p2MOJw31vebuO-5i0V5iZDUg-ynAfeFa6ZPZP5BEx9tFtQH8tt0d5PMoQU-nUNiHv88R"

def probar_webhook():
    payload = {
        "content": "¡Prueba exitosa! DiscordHookUpdater está en línea y funcionando correctamente."
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 204 or response.status == 200:
                print("Mensaje enviado con éxito al webhook.")
            else:
                print(f"Respuesta inesperada del servidor: {response.status}")
                
    except Exception as e:
        print(f"Error al conectar con el webhook: {e}")

if __name__ == "__main__":
    probar_webhook()
