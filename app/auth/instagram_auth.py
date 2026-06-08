"""
=============================================================================================

Name: instagram_auth.py
Description: Module for handling Instagram authentication and token management.
Author: Melissa Carvajal
Date: May 2026
Version: 1.2

=============================================================================================
"""

import requests

from datetime import datetime, timedelta

from models.app_errors import ApiError, InputValueError
from models.token_auth import Token

from auth.meta_auth import (
    GRAPH_BASE,
    get_meta_auth_url,
    request_meta_short_lived_token,
    exchange_long_lived_token,
    build_meta_account,
    get_meta_pages,
    get_meta_page,
    get_graph_object,
)

AUTH_REDIRECT_URI = "http://localhost:8080/instagram/callback.html"


def get_instagram_auth_url(client_id):
    """
    Generates the OAuth URL used to connect an Instagram
    Business or Creator account through Meta.
    """

    scopes = [
        "instagram_basic",
        "instagram_content_publish",
        "instagram_manage_comments",
        "instagram_manage_insights",
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_posts"
    ]

    return get_meta_auth_url(
        client_id=client_id,
        redirect_uri=AUTH_REDIRECT_URI,
        scopes=scopes
    )


def request_instagram_long_lived_token(
    client_id,
    client_secret,
    code
):
    """
    Exchanges an authorization code for a long-lived
    Instagram Graph API token payload.
    """

    token_data = request_meta_short_lived_token(
        client_id=client_id,
        client_secret=client_secret,
        code=code,
        redirect_uri=AUTH_REDIRECT_URI
    )

    short_lived_token = token_data.get("access_token")

    if not short_lived_token:
        raise InputValueError("No access token received.")

    return exchange_long_lived_token(
        client_id=client_id,
        client_secret=client_secret,
        short_lived_token=short_lived_token
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

    account = build_meta_account(
        provider="Instagram",
        access_token=access_token,
        client_id=client_id,
        client_secret=client_secret,
        expires_in=expires_in
    )

    enrich_instagram_account(account, selected_page_id)

    return account


def refresh_instagram_token(account):
    """
    Refreshes a long-lived Instagram token.
    """

    if not isinstance(account, Token):
        raise InputValueError("Invalid account.")

    try:
        response = requests.get(
            "https://graph.instagram.com/refresh_access_token",
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

    pages = get_meta_pages(access_token)

    available_accounts = []

    for page in pages:
        page_id = page.get("page_id")

        try:
            page_data = get_meta_page(
                access_token=access_token,
                page_id=page_id,
                fields="id,name,access_token,instagram_business_account"
            )
        except ApiError:
            continue

        instagram_account = page_data.get("instagram_business_account")

        if not instagram_account:
            continue

        instagram_user_id = instagram_account.get("id")

        try:
            profile = get_graph_object(
                access_token=access_token,
                object_id=instagram_user_id,
                fields="id,username,name"
            )
        except ApiError:
            continue

        available_accounts.append({
            "page_id": page_id,
            "page_name": page_data.get("name"),
            "facebook_page_token": page_data.get("access_token"),
            "instagram_user_id": instagram_user_id,
            "instagram_username": profile.get("username"),
            "instagram_name": profile.get("name")
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
                "No connected Instagram Business or Creator account found."
            )
        selected_page_id = accounts[0].get("page_id")

    page_data = get_meta_page(
        access_token=account.access_token,
        page_id=selected_page_id,
        fields="id,name,access_token,instagram_business_account"
    )

    instagram_account = page_data.get("instagram_business_account")

    if not instagram_account:
        raise InputValueError(
            "Selected page does not have an Instagram Business account."
        )

    instagram_user_id = instagram_account.get("id")

    profile = get_graph_object(
        access_token=account.access_token,
        object_id=instagram_user_id,
        fields="id,username,name"
    )

    account.facebook_page_id = page_data.get("id") or selected_page_id
    account.facebook_page_token = page_data.get("access_token")
    account.instagram_user_id = instagram_user_id
    account.provider_user_id = profile.get("id")
    account.username = profile.get("username")
    account.account_label = profile.get("name") or profile.get("username")

    return account