"""
=============================================================================================

Name: facebook_auth.py
Description: Module for handling Facebook authentication and token management.
Author: OneSocial Team
Date: June 2026
Version: 1.0

=============================================================================================
"""

from models.app_errors import ApiError, InputValueError
from models.token_auth import Token

from auth.meta_auth import (
    build_meta_account,
    get_graph_object,
    get_meta_auth_url,
    get_meta_page,
    get_meta_pages,
    is_access_token_expired,
    request_meta_short_lived_token,
    exchange_long_lived_token,
    verify_meta_page_access,
)

AUTH_REDIRECT_URI = "http://localhost:8080/facebook/callback.html"


def get_facebook_auth_url(client_id):
    """
    Generates the OAuth URL used to connect a Facebook Page through Meta.
    """

    scopes = [
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_posts"
    ]

    return get_meta_auth_url(
        client_id=client_id,
        redirect_uri=AUTH_REDIRECT_URI,
        scopes=scopes
    )


def request_facebook_long_lived_token(
    client_id,
    client_secret,
    code
):
    """
    Exchanges an authorization code for a long-lived Facebook Graph API token payload.
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


def create_facebook_token(
    client_id,
    client_secret,
    code,
    selected_page_id=None
):
    """
    Exchanges an authorization code for a long-lived Facebook token.
    """

    long_lived = request_facebook_long_lived_token(
        client_id,
        client_secret,
        code
    )

    access_token = long_lived.get("access_token")

    if not access_token:
        raise InputValueError("No access token received.")

    return build_facebook_account(
        access_token,
        client_id=client_id,
        client_secret=client_secret,
        expires_in=long_lived.get("expires_in"),
        selected_page_id=selected_page_id
    )


def build_facebook_account(
    access_token,
    client_id=None,
    client_secret=None,
    expires_in=None,
    selected_page_id=None
):
    """
    Builds a Token object from a long-lived Facebook access token.
    """

    account = build_meta_account(
        provider="Facebook",
        access_token=access_token,
        client_id=client_id,
        client_secret=client_secret,
        expires_in=expires_in
    )

    enrich_facebook_account(account, selected_page_id)

    return account


def get_facebook_pages(access_token):
    """
    Returns all Facebook Pages available to the authenticated user.
    """

    return get_meta_pages(access_token)


def enrich_facebook_account(account, selected_page_id=None):
    """
    Enriches a Facebook Token using a specific page selected by the user.
    """

    if not isinstance(account, Token):
        raise InputValueError("Invalid account.")

    if not account.access_token:
        raise InputValueError("No access token stored for Facebook.")

    if not selected_page_id:
        pages = get_facebook_pages(account.access_token)
        if not pages:
            raise InputValueError("No connected Facebook Pages found.")
        selected_page_id = pages[0].get("page_id")

    page_data = get_meta_page(
        access_token=account.access_token,
        page_id=selected_page_id,
        fields="id,name,access_token"
    )

    page_token = page_data.get("access_token")

    if not page_token:
        raise ApiError("No page access token returned from Facebook.")

    account.facebook_page_id = page_data.get("id") or selected_page_id
    account.facebook_page_token = page_token
    account.provider_user_id = account.facebook_page_id
    account.username = page_data.get("name")
    account.account_label = page_data.get("name")

    return account


def verify_facebook_access(account):
    """
    Verifies that the stored Facebook Page credentials are still valid.
    """

    if not isinstance(account, Token):
        raise InputValueError("Invalid account.")

    if not account.facebook_page_id:
        raise InputValueError("No Facebook Page linked.")

    if not account.access_token:
        raise InputValueError("No access token stored for Facebook.")

    if is_access_token_expired(account):
        raise ApiError("Facebook token expired. Reconnect the account.")

    verify_meta_page_access(account.access_token, account.facebook_page_id)
    return True


def get_facebook_page_by_id(access_token, page_id):
    """
    Returns a Facebook Page object for callers that need explicit page metadata.
    """

    return get_meta_page(
        access_token=access_token,
        page_id=page_id,
        fields="id,name,access_token"
    )


def get_facebook_page_profile(access_token, page_id):
    """
    Returns profile details for the selected Facebook Page.
    """

    page = get_facebook_page_by_id(access_token, page_id)

    return {
        "page_id": page.get("id") or page_id,
        "page_name": page.get("name"),
        "facebook_page_token": page.get("access_token"),
    }