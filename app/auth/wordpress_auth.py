"""

=============================================================================================

Name: wordpress_auth.py
Description: Module for handling WordPress authentication and token management.
Author: Pamela Fernández
Date: March 2026
Version: 1.0

=============================================================================================

"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import webbrowser
import threading
import requests

REDIRECT_URI = "http://localhost:8000/callback"

# Variables globales para capturar el code OAuth
auth_code = None
server = None

def get_sites(token):
    """
    - Input: 
        - token: str - The access token for authenticating with the WordPress API.
    - Output: 
        - site_id: str - The ID of the first site associated with the authenticated account.
    - Description: 
        - Makes a GET request to the WordPress API to retrieve the list of sites associated with the authenticated account.
        - Parses the response to extract and return the ID of the first site found. If no sites are found, it prints a message and returns None.    
    """

    url = "https://public-api.wordpress.com/rest/v1.1/me/sites"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    sites = data.get("sites", [])

    if not sites:
        print("No se encontraron sitios")
        return None

    site_id = sites[0]["ID"] 
    return site_id


def get_primary_site(token):
    url = "https://public-api.wordpress.com/rest/v1.1/me/sites"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Error obteniendo sitios:", response.text)
        return None, None

    data = response.json()
    sites = data.get("sites", [])

    if not sites:
        print("No se encontraron sitios")
        return None, None

    site = sites[0]

    return site["ID"], site["URL"]


class CallbackHandler(BaseHTTPRequestHandler):
    """
    - Input: 
        - baseHTTPRequestHandler: Class from http.server for handling HTTP requests
    - Description: 
        - Handler for the OAuth callback that captures the authorization code and sends a response to the user.
    """

    def do_GET(self):
        """
        - Input: 
            - self: Instance of CallbackHandler that handles the GET request from the OAuth redirect
        - Output: 
            - HTTP response - Sends an HTML response to the user's browser confirming successful login and allowing them to close the window.
        - Description: 
            - Parses the incoming GET request to extract the authorization code from the query parameters.
            - Sends a simple HTML response to the user's browser confirming that the login was successful and they can close the window.
            - Shuts down the local HTTP server after processing the request to stop listening for further requests.
        """
        
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
    """
    - Input: 
        - client_id: str - The WordPress application's client ID used for OAuth authentication
    - Output: 
        - auth_code: str - The authorization code received from WordPress after user login, used to exchange for an access token
    - Description: 
        - Starts a local HTTP server to listen for the OAuth redirect from WordPress after the user logs in.
        - Opens the user's default web browser to the WordPress authorization URL where they can log in and authorize the application.
        - Waits for the incoming request to capture the authorization code, then shuts down the server and returns the code.
    """

    global server, auth_code
    auth_code = None

    server = HTTPServer(('localhost', 8000), CallbackHandler)

    auth_url = (
        f"https://public-api.wordpress.com/oauth2/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=global"
    )

    print("Abriendo navegador para login WordPress...")
    webbrowser.open(auth_url)

    print("Esperando autorización...")
    server.serve_forever()

    return auth_code


def exchange_code_for_token(client_id, client_secret, code):
    """
    - Input: 
        - client_id: str - The WordPress application's client ID used for OAuth authentication
        - client_secret: str - The WordPress application's client secret used for OAuth authentication
        - code: str - The authorization code received from WordPress after user login, used to exchange for an access token 
    - Output: 
        - response.json(): dict - The JSON response containing the access token and related information received from WordPress after exchanging the authorization code
    - Description: 
        - Makes a POST request to the WordPress token endpoint to exchange the authorization code for an access token.
        - Sends the client ID, client secret, authorization code, grant type, and redirect URI as form data in the request.
        - If the request is successful, returns the JSON response containing the access token; otherwise, prints an error message and returns None.
    """
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
    """
    - Input:
        - account: Token - The account object for which to ensure a valid WordPress access token is available. 
        This object should contain the client ID and client secret needed for OAuth authentication if an access token is not already present.
    - Output:
        - account.access_token: str - The access token for the WordPress account, obtained through OAuth authentication if not already present
    - Description: 
        - Checks if the account already has an access token; if so, returns it.
        - If not, verifies that the account has the necessary client ID and client secret to perform OAuth authentication.
        - Initiates the OAuth flow to obtain an authorization code, then exchanges it for an access token.
        - Stores the obtained access token and related information in the account object and returns the access token.
    """

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
    site_id, base_url = get_primary_site(account.access_token)
    account.site_id = str(site_id)
    account.base_url = base_url
    account.refresh_token = token_data.get("refresh_token")
    account.token_type = token_data.get("token_type")
    account.scope = token_data.get("scope")

    return account.access_token



def verify_wordpress_access(account):
    """
    - Input: 
        - account: Token - The account object for which to verify access. This object should contain the access token needed to access the WordPress API.
    - Output: 
        - True if the access token is valid and can be used to access the WordPress API, False otherwise
    - Description: 
        - Checks if the access token for the given WordPress account is valid and can be used to access the WordPress API.
    """

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