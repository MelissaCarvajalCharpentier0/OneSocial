"""

Name: instagram_auth.py
Description: Module for handling Instagram authentication and token management.
Author: Melissa Carvajal
Date: May 2026
Version: 1.1

=============================================================================================
"""

import requests

from datetime import datetime, timedelta
from urllib.parse import quote

from models.app_errors import ApiError, InputValueError
from models.token_auth import Token

AUTH_URL = "https://www.facebook.com/v23.0/dialog/oauth"

TOKEN_URL = (
"https://graph.facebook.com/v23.0/oauth/access_token"
)

GRAPH_BASE = "https://graph.facebook.com/v23.0"

REDIRECT_URI = (
"http://localhost:8080/instagram/callback.html"
)

def get_instagram_auth_url(client_id):
    """
    Generates the OAuth URL used to connect an Instagram
    Business or Creator account through Meta.
    """


    encoded_redirect = quote(
        REDIRECT_URI,
        safe=""
    )

    scopes = ",".join([
        "instagram_basic",
        "instagram_content_publish",
        "instagram_manage_comments",
        "instagram_manage_insights",
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_posts"
    ])

    return (
        f"{AUTH_URL}"
        f"?client_id={client_id}"
        f"&redirect_uri={encoded_redirect}"
        f"&response_type=code"
        f"&scope={scopes}"
    )


def create_instagram_token(
    client_id,
    client_secret,
    code,
    selected_page_id=None
    ):
    """
    Exchanges an authorization code for a long-lived
    Instagram Graph API token.
    """


    long_lived = request_instagram_long_lived_token(
        client_id,
        client_secret,
        code
    )

    access_token = long_lived.get("access_token")

    if not access_token:
        raise InputValueError("No access token received.")

    return build_instagram_account(
        access_token,
        client_id=client_id,
        client_secret=client_secret,
        expires_in=long_lived.get("expires_in"),
        selected_page_id=selected_page_id
    )


def exchange_long_lived_token(
    client_id,
    client_secret,
    short_lived_token
    ):
    """
    Converts a short-lived token into a
    60-day long-lived token.
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
        raise ApiError(
            f"Long-lived token error: {response.text}"
        )

    return response.json()


def request_instagram_long_lived_token(
    client_id,
    client_secret,
    code
    ):
    """
    Exchanges an authorization code for a long-lived
    Instagram Graph API token payload.
    """

    try:
        response = requests.get(
            TOKEN_URL,
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": REDIRECT_URI,
                "code": code
            },
            timeout=30
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo solicitar el token de Instagram.") from error

    if response.status_code != 200:
        raise ApiError(
            f"Instagram token error: {response.text}"
        )

    token_data = response.json()

    short_lived_token = token_data.get(
        "access_token"
    )

    if not short_lived_token:
        raise InputValueError(
            "No access token received."
        )

    return exchange_long_lived_token(
        client_id,
        client_secret,
        short_lived_token
    )


def build_instagram_account(
    access_token,
    client_id=None,
    client_secret=None,
    expires_in=None,
    selected_page_id=None
    ):
    """
    Builds a Token object from a long-lived access token.
    """

    if not access_token:
        raise InputValueError("No access token received.")

    now = datetime.utcnow()

    account = Token(
        provider="Instagram",

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

    enrich_instagram_account(account, selected_page_id)

    return account


def refresh_instagram_token(account):
    """
    Refreshes a long-lived Instagram token.
    """

    if not isinstance(account, Token):
        raise InputValueError(
            "Invalid account."
        )

    try:
        response = requests.get(
            "https://graph.instagram.com/"
            "refresh_access_token",
            params={
                "grant_type": "ig_refresh_token",
                "access_token": account.access_token
            },
            timeout=30
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo refrescar el token de Instagram.") from error

    if response.status_code != 200:
        raise ApiError(
            f"Refresh failed: {response.text}"
        )

    data = response.json()

    account.access_token = data.get(
        "access_token",
        account.access_token
    )

    account.access_expires_at = (
        datetime.utcnow()
        + timedelta(
            seconds=data.get(
                "expires_in",
                0
            )
        )
    ).isoformat()

    return account


def _is_access_token_expired(account) -> bool:
    if not account.access_expires_at:
        return False

    try:
        expires_at = datetime.fromisoformat(account.access_expires_at)
    except ValueError:
        return False

    return datetime.utcnow() >= expires_at


def ensure_instagram_token(account):
    """
    Ensures the account has a valid long-lived token.
    """

    if not isinstance(account, Token):
        raise InputValueError("Invalid account.")

    if account.access_token and not _is_access_token_expired(account):
        return account.access_token

    if not account.access_token:
        raise InputValueError("No access token stored for Instagram.")

    refresh_instagram_token(account)
    return account.access_token


def verify_instagram_access(account):
    """
    Verifies the stored Instagram credentials by fetching profile data.
    """

    if not isinstance(account, Token):
        raise InputValueError("Invalid account.")

    if not account.instagram_user_id:
        raise InputValueError("No Instagram user id stored.")

    ensure_instagram_token(account)

    try:
        response = requests.get(
            f"{GRAPH_BASE}/{account.instagram_user_id}",
            params={
                "fields": "id,username",
                "access_token": account.access_token,
            },
            timeout=30
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo verificar el acceso a Instagram.") from error

    if response.status_code != 200:
        raise ApiError(f"Error verificando Instagram: {response.text}")

    return True

def get_instagram_accounts(access_token):
    """
    Returns all Instagram Business/Creator accounts
    available to the authenticated user.
    """

    headers = {
        "Authorization":
        f"Bearer {access_token}"
    }

    try:
        pages_response = requests.get(
            f"{GRAPH_BASE}/me/accounts",
            headers=headers,
            params={
                "fields": "id,name",
            },
            timeout=30
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo consultar las paginas de Facebook.") from error

    if pages_response.status_code != 200:
        raise ApiError(
            "Failed to retrieve Facebook Pages."
        )

    pages = pages_response.json().get(
        "data",
        []
    )

    available_accounts = []

    for page in pages:

        page_id = page.get("id")

        try:
            page_info = requests.get(
                f"{GRAPH_BASE}/{page_id}",
                headers=headers,
                params={
                    "fields":
                    "name,instagram_business_account"
                },
                timeout=30
            )
        except requests.RequestException:
            continue

        if page_info.status_code != 200:
            continue

        page_data = page_info.json()

        instagram_account = page_data.get(
            "instagram_business_account"
        )

        if not instagram_account:
            continue

        instagram_user_id = (
            instagram_account.get("id")
        )

        try:
            profile_response = requests.get(
                f"{GRAPH_BASE}/"
                f"{instagram_user_id}",
                headers=headers,
                params={
                    "fields":
                    "id,username,name"
                },
                timeout=30
            )
        except requests.RequestException:
            continue

        if profile_response.status_code != 200:
            continue

        profile = profile_response.json()

        available_accounts.append({
            "page_id": page_id,
            "page_name": page_data.get("name"),

            "instagram_user_id":
            instagram_user_id,

            "instagram_username":
            profile.get("username"),

            "instagram_name":
            profile.get("name")
        })

    return available_accounts


def enrich_instagram_account(
    account,
    selected_page_id=None
    ):
    """
    Enriches a Token object using a specific
    Facebook Page selected by the user.
    """


    if not isinstance(account, Token):
        raise InputValueError("Invalid account.")

    if not account.access_token:
        raise InputValueError("No access token stored for Instagram.")

    if not selected_page_id:
        accounts = get_instagram_accounts(account.access_token)
        if not accounts:
            raise InputValueError(
                "No connected Instagram Business "
                "or Creator account found."
            )
        selected_page_id = accounts[0].get("page_id")

    headers = {
        "Authorization":
        f"Bearer {account.access_token}"
    }

    try:
        page_response = requests.get(
            f"{GRAPH_BASE}/"
            f"{selected_page_id}",
            headers=headers,
            params={
                "fields":
                "name,instagram_business_account"
            },
            timeout=30
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo consultar la pagina seleccionada.") from error

    if page_response.status_code != 200:
        raise ApiError(
            "Selected page not accessible."
        )

    page_data = page_response.json()

    instagram_account = page_data.get(
        "instagram_business_account"
    )

    if not instagram_account:
        raise InputValueError(
            "Selected page does not have an "
            "Instagram Business account."
        )

    instagram_user_id = (
        instagram_account.get("id")
    )

    try:
        profile_response = requests.get(
            f"{GRAPH_BASE}/"
            f"{instagram_user_id}",
            headers=headers,
            params={
                "fields":
                "id,username,name"
            },
            timeout=30
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo consultar el perfil de Instagram.") from error

    if profile_response.status_code != 200:
        raise ApiError(
            "Failed to retrieve Instagram profile."
        )

    profile = profile_response.json()

    account.facebook_page_id = (
        selected_page_id
    )

    account.instagram_user_id = (
        instagram_user_id
    )

    account.provider_user_id = (
        profile.get("id")
    )

    account.username = (
        profile.get("username")
    )

    account.account_label = (
        profile.get("name")
        or profile.get("username")
    )

    return account

