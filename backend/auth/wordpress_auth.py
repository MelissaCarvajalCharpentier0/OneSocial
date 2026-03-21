from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import webbrowser
import threading
import requests

REDIRECT_URI = "http://localhost:8000/callback"

# Variables globales para capturar el code OAuth
auth_code = None
server = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code

        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        auth_code = params.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        html_response = b"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Login WordPress Completado</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f0f0f0; text-align: center; padding-top: 50px; }
                h1 { color: #2c3e50; }
                p { font-size: 18px; }
                .box { background-color: #fff; display: inline-block; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
            </style>
        </head>
        <body>
            <div class="box">
                <h1> Login Exitoso</h1>
                <p>Puedes cerrar esta ventana y regresar a la aplicacion.</p>
            </div>
        </body>
        </html>
        """

        self.wfile.write(html_response)

        # detener servidor después de recibir code
        threading.Thread(target=server.shutdown).start()


def get_authorization_code(client_id):
    """Levanta servidor temporal y abre navegador para capturar el code OAuth"""
    global server, auth_code
    auth_code = None

    server = HTTPServer(('localhost', 8000), CallbackHandler)

    auth_url = (
        f"https://public-api.wordpress.com/oauth2/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
    )

    print("Abriendo navegador para login WordPress...")
    webbrowser.open(auth_url)

    print("Esperando autorización...")
    server.serve_forever()

    return auth_code


def exchange_code_for_token(client_id, client_secret, code):
    response = requests.post(
        "https://public-api.wordpress.com/oauth2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI
        }
    )

    if response.status_code != 200:
        print("Error obteniendo token:", response.text)
        return None

    return response.json()


def ensure_wordpress_token(account):
    """Devuelve el access_token; si no existe, lo genera con OAuth"""

    if account.access_token:
        return account.access_token

    if not account.client_id or not account.client_secret:
        print(f"No hay client_id/client_secret en {account.username}")
        return None

    print(f"Obteniendo token para {account.username}...")

    code = get_authorization_code(account.client_id)

    if not code:
        print("No se obtuvo code")
        return None

    token_data = exchange_code_for_token(account.client_id, account.client_secret, code)

    if not token_data:
        return None

    account.access_token = token_data.get("access_token")
    return account.access_token



def verify_wordpress_access(account):
    """Verifica que el token funcione"""

    if not account.access_token:
        print("No hay token")
        return False

    url = "https://public-api.wordpress.com/rest/v1.1/me"
    headers = {
        "Authorization": f"Bearer {account.access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Acceso válido")
        return True
    else:
        print("Error de acceso:", response.status_code)
        print(response.text)
        return False