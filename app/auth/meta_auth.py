"""
=============================================================================================

Name: meta_auth.py
Description: Shared module for Meta authentication and token helpers for Facebook/Instagram.
Author: OneSocial Team
Date: June 2026
Version: 1.0

=============================================================================================
"""

import requests

from datetime import datetime, timedelta
from urllib.parse import quote

from models.app_errors import ApiError, InputValueError
from models.token_auth import Token

AUTH_URL = "https://www.facebook.com/v23.0/dialog/oauth"
TOKEN_URL = "https://graph.facebook.com/v23.0/oauth/access_token"
GRAPH_BASE = "https://graph.facebook.com/v23.0"


def _extract_graph_error_message(response, fallback_message):
    """
    Normalizes common Graph API failure payloads into a readable error string.
    """

    message = fallback_message

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    error = payload.get("error") or {}
    error_message = error.get("message") or response.text
    error_code = error.get("code")
    error_subcode = error.get("error_subcode")

    if error_message:
        message = error_message

    if error_code == 190:
        if error_subcode in {463, 467}:
            return "Meta token expired."
        return "Invalid Meta token or missing permissions."

    if response.status_code in {401, 403}:
        return "Missing Meta permissions."

    return message


def _raise_for_graph_error(response, fallback_message):
    raise ApiError(_extract_graph_error_message(response, fallback_message))


def get_meta_auth_url(client_id, redirect_uri, scopes):
    """
    Builds a Meta OAuth authorization URL.
    """

    if not client_id:
        raise InputValueError("Client id invalid.")

    if not redirect_uri:
        raise InputValueError("Redirect uri invalid.")

    if not scopes:
        raise InputValueError("Scopes invalid.")

    if isinstance(scopes, (list, tuple, set)):
        scope_value = ",".join(scopes)
    else:
        scope_value = str(scopes)

    encoded_redirect = quote(
        redirect_uri,
        safe=""
    )

    return (
        f"{AUTH_URL}"
        f"?client_id={client_id}"
        f"&redirect_uri={encoded_redirect}"
        f"&response_type=code"
        f"&scope={scope_value}"
    )


def request_meta_short_lived_token(
    client_id,
    client_secret,
    code,
    redirect_uri
):
    """
    Exchanges an authorization code for a short-lived Meta access token.
    """

    try:
        response = requests.get(
            TOKEN_URL,
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": code
            },
            timeout=30
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo solicitar el token de Meta.") from error

    if response.status_code != 200:
        _raise_for_graph_error(response, "No se pudo solicitar el token de Meta.")

    token_data = response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise InputValueError("No access token received.")

    return token_data


def exchange_long_lived_token(
    client_id,
    client_secret,
    short_lived_token
):
    """
    Converts a short-lived token into a long-lived Meta token.
    """

    try:
        response = requests.get(
            TOKEN_URL,
            params={
                "grant_type": "fb_exchange_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "fb_exchange_token": short_lived_token
            },
            timeout=30
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo solicitar el token de larga duracion.") from error

    if response.status_code != 200:
        _raise_for_graph_error(response, "No se pudo solicitar el token de larga duracion.")

    data = response.json()

    if not data.get("access_token"):
        raise InputValueError("No access token received.")

    return data


def build_meta_account(
    provider,
    access_token,
    client_id=None,
    client_secret=None,
    expires_in=None
):
    """
    Builds a Token object from a Meta access token.
    """

    if not provider:
        raise InputValueError("Provider invalid.")

    if not access_token:
        raise InputValueError("No access token received.")

    now = datetime.utcnow()

    account = Token(
        provider=provider,
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        token_type="Bearer",
        issued_at=now.isoformat()
    )

    if expires_in:
        try:
            expires_seconds = int(expires_in)
        except (TypeError, ValueError):
            expires_seconds = 0

        if expires_seconds > 0:
            account.access_expires_at = (
                now + timedelta(seconds=expires_seconds)
            ).isoformat()

    return account


def _is_access_token_expired(account) -> bool:
    """
    Checks whether a token is expired.
    """

    if not account.access_expires_at:
        return False

    try:
        expires_at = datetime.fromisoformat(account.access_expires_at)
    except ValueError:
        return False

    return datetime.utcnow() >= expires_at


def is_access_token_expired(account) -> bool:
    """
    Public wrapper for checking whether a Meta access token is expired.
    """

    return _is_access_token_expired(account)


def ensure_access_token(account, refresh_callback=None):
    """
    Ensures the token is still valid and refreshes it if needed.
    """

    if not isinstance(account, Token):
        raise InputValueError("Invalid account.")

    if account.access_token and not _is_access_token_expired(account):
        return account.access_token

    if not account.access_token:
        raise InputValueError("No access token stored.")

    if refresh_callback is None:
        raise InputValueError("Refresh callback required for expired token.")

    refresh_callback(account)
    return account.access_token


def get_meta_pages(access_token):
    """
    Returns all Facebook Pages available to the user.
    """

    if not access_token:
        raise InputValueError("Access token invalid.")

    try:
        response = requests.get(
            f"{GRAPH_BASE}/me/accounts",
            params={
                "fields": "id,name,access_token",
                "access_token": access_token
            },
            timeout=30
        )
    except requests.RequestException as error:
        raise ApiError("No se pudieron obtener las paginas de Facebook.") from error

    if response.status_code != 200:
        _raise_for_graph_error(response, "No se pudieron obtener las paginas de Facebook.")

    pages = []

    for page in response.json().get("data", []):
        pages.append({
            "page_id": page.get("id"),
            "page_name": page.get("name"),
            "facebook_page_token": page.get("access_token")
        })

    return pages


def get_meta_page(access_token, page_id, fields="id,name,access_token"):
    """
    Fetches a specific Facebook Page object from Graph API.
    """

    return get_graph_object(access_token, page_id, fields)


def get_meta_page_token(access_token, page_id):
    """
    Returns a page access token for the given Facebook Page.
    """

    page = get_meta_page(
        access_token=access_token,
        page_id=page_id,
        fields="id,name,access_token"
    )

    page_token = page.get("access_token")

    if not page_token:
        raise ApiError("No page access token returned from Facebook.")

    return page_token


def verify_meta_page_access(access_token, page_id):
    """
    Verifies access to the selected Facebook Page.
    """

    if not access_token:
        raise InputValueError("Access token invalid.")

    if not page_id:
        raise InputValueError("Page id invalid.")

    get_meta_page(access_token, page_id, fields="id,name")
    return True


def get_graph_object(access_token, object_id, fields):
    """
    Fetches a Graph API object by id with the requested fields.
    """

    if not access_token:
        raise InputValueError("Access token invalid.")

    if not object_id:
        raise InputValueError("Object id invalid.")

    if not fields:
        raise InputValueError("Fields invalid.")

    try:
        response = requests.get(
            f"{GRAPH_BASE}/{object_id}",
            params={
                "fields": fields,
                "access_token": access_token
            },
            timeout=30
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo consultar el objeto Graph.") from error

    if response.status_code != 200:
        _raise_for_graph_error(response, "No se pudo consultar el objeto Graph.")

    return response.json()