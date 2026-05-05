"""

=============================================================================================

Name: reddit_auth.py
Description: Module for handling Reddit authentication and token management.
Author: GitHub Copilot
Date: April 2026
Version: 1.0

=============================================================================================

"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
import secrets
import threading
import urllib.parse
import webbrowser

import requests

from models.app_errors import ApiError, InputValueError

REDIRECT_URI = "http://localhost:8000/callback"
AUTHORIZATION_URL = "https://www.reddit.com/api/v1/authorize"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
USER_INFO_URL = "https://oauth.reddit.com/api/v1/me"
USER_AGENT = "OneSocial/1.0 (by /u/onesocial)"
REDDIT_SCOPES = ["identity", "submit"]

auth_code = None
auth_error = None
auth_state = None
server = None
auth_event = threading.Event()


class CallbackHandler(BaseHTTPRequestHandler):
    """
    - Input:
        - BaseHTTPRequestHandler: HTTP request handler for the OAuth callback.
    - Description:
        - Captures the authorization code returned by Reddit and closes the local server.
    """

    def log_message(self, format, *args):
        return

    def do_GET(self):
        """
        - Description:
            - Extracts the code and state from the callback request and stores the result globally.
        """

        global auth_code, auth_error, auth_state, server

        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)

        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]
        error = params.get("error", [None])[0]

        if error:
            auth_error = error
        elif auth_state and state != auth_state:
            auth_error = "invalid_state"
        else:
            auth_code = code

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        if auth_error:
            html_response = b"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Login Reddit Fallido</title>
            </head>
            <body>
                <h1>No se pudo completar la autenticacion</h1>
                <p>Puedes cerrar esta ventana y volver a OneSocial.</p>
            </body>
            </html>
            """
        else:
            html_response = b"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Login Reddit Completado</title>
            </head>
            <body>
                <h1>Login exitoso con Reddit</h1>
                <p>Puedes cerrar esta ventana y regresar a la aplicacion.</p>
            </body>
            </html>
            """

        self.wfile.write(html_response)
        auth_event.set()
        if server:
            threading.Thread(target=server.shutdown, daemon=True).start()


def _build_authorization_url(client_id, state, redirect_uri=REDIRECT_URI):
    params = {
        "client_id": client_id,
        "response_type": "code",
        "state": state,
        "redirect_uri": redirect_uri,
        "duration": "permanent",
        "scope": " ".join(REDDIT_SCOPES),
    }
    return f"{AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}"


def get_authorization_code(client_id, redirect_uri=REDIRECT_URI, timeout=600):
    """
    - Input:
        - client_id: str - The Reddit application client ID.
    - Output:
        - code: str - The authorization code returned by Reddit.
    - Description:
        - Starts a local callback server, opens the authorization URL, and waits for the user to approve access.
    """

    global server, auth_code, auth_error, auth_state

    if not client_id:
        raise InputValueError("No hay client_id para Reddit")

    auth_code = None
    auth_error = None
    auth_state = secrets.token_urlsafe(16)
    auth_event.clear()

    try:
        server = HTTPServer(("localhost", 8000), CallbackHandler)
    except OSError as error:
        raise ApiError("No se pudo iniciar el servidor local de Reddit.") from error

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    auth_url = _build_authorization_url(client_id, auth_state, redirect_uri=redirect_uri)
    if not webbrowser.open(auth_url, new=1, autoraise=True):
        print(f"Abre esta URL para autenticar Reddit: {auth_url}")

    if not auth_event.wait(timeout=timeout):
        try:
            server.shutdown()
        except Exception:
            pass
        raise ApiError("Tiempo de espera agotado esperando la autorizacion de Reddit.")

    if auth_error:
        raise ApiError(f"Error autenticando Reddit: {auth_error}")

    if not auth_code:
        raise ApiError("No se obtuvo code de Reddit")

    return auth_code


def exchange_code_for_token(client_id, client_secret, code, redirect_uri=REDIRECT_URI):
    """
    - Input:
        - client_id: str - The Reddit application client ID.
        - client_secret: str - The Reddit application client secret (optional for installed apps).
        - code: str - The authorization code returned by Reddit.
    - Output:
        - token_data: dict - Reddit token response.
    - Description:
        - Exchanges the authorization code for an access token.
    """

    try:
        response = requests.post(
            TOKEN_URL,
            auth=(client_id, client_secret or ""),
            headers={"User-Agent": USER_AGENT},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            timeout=30,
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo intercambiar el code por un token de Reddit.") from error

    if response.status_code != 200:
        raise ApiError(f"Error obteniendo token de Reddit: {response.text}")

    return response.json()


def refresh_access_token(client_id, client_secret, refresh_token):
    """
    - Input:
        - client_id: str - The Reddit application client ID.
        - client_secret: str - The Reddit application client secret (optional for installed apps).
        - refresh_token: str - The refresh token to exchange.
    - Output:
        - token_data: dict - Reddit token response.
    - Description:
        - Requests a new access token using a refresh token.
    """

    try:
        response = requests.post(
            TOKEN_URL,
            auth=(client_id, client_secret or ""),
            headers={"User-Agent": USER_AGENT},
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=30,
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo refrescar el token de Reddit.") from error

    if response.status_code != 200:
        raise ApiError(f"Error refrescando token de Reddit: {response.text}")

    return response.json()


def get_reddit_identity(access_token):
    """
    - Input:
        - access_token: str - The Reddit bearer token.
    - Output:
        - identity: dict - The authenticated Reddit user profile.
    - Description:
        - Fetches the current Reddit user identity for verification and storage.
    """

    try:
        response = requests.get(
            USER_INFO_URL,
            headers={
                "Authorization": f"bearer {access_token}",
                "User-Agent": USER_AGENT,
            },
            timeout=30,
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo consultar la identidad de Reddit.") from error

    if response.status_code != 200:
        raise ApiError(f"Error consultando la identidad de Reddit: {response.text}")

    return response.json()


def _apply_token_data(account, token_data):
    account.access_token = token_data.get("access_token")
    if "refresh_token" in token_data:
        account.refresh_token = token_data.get("refresh_token")
    account.token_type = token_data.get("token_type")
    account.scope = token_data.get("scope")

    expires_in = token_data.get("expires_in")
    if expires_in:
        now = datetime.now(timezone.utc)
        account.issued_at = now.isoformat()
        account.access_expires_at = (now + timedelta(seconds=int(expires_in))).isoformat()


def _is_access_token_expired(account):
    if not account.access_expires_at:
        return False

    try:
        expires_at = datetime.fromisoformat(account.access_expires_at)
    except ValueError:
        return False

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return datetime.now(timezone.utc) >= expires_at


def ensure_reddit_token(account):
    """
    - Input:
        - account: Token object for the Reddit account.
    - Output:
        - access_token: str - The Reddit access token.
    - Description:
        - Ensures that a Reddit access token exists, starting the OAuth flow if necessary.
    """

    if account.access_token and not _is_access_token_expired(account):
        return account.access_token

    if not account.client_id:
        raise InputValueError(f"No hay client_id en {account.username}")

    if account.refresh_token:
        token_data = refresh_access_token(account.client_id, account.client_secret, account.refresh_token)
        _apply_token_data(account, token_data)
        identity = get_reddit_identity(account.access_token)
        account.provider_user_id = identity.get("name")
        return account.access_token

    code = get_authorization_code(account.client_id)
    token_data = exchange_code_for_token(account.client_id, account.client_secret, code)

    _apply_token_data(account, token_data)
    identity = get_reddit_identity(account.access_token)
    account.provider_user_id = identity.get("name")

    return account.access_token


def verify_reddit_access(account):
    """
    - Input:
        - account: Token object for the Reddit account.
    - Output:
        - success: bool - True when the token is valid.
    - Description:
        - Verifies the stored token by calling Reddit's identity endpoint.
    """

    if (not account.access_token or _is_access_token_expired(account)) and account.refresh_token:
        token_data = refresh_access_token(account.client_id, account.client_secret, account.refresh_token)
        _apply_token_data(account, token_data)

    if not account.access_token:
        return False

    get_reddit_identity(account.access_token)
    return True