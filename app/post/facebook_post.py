"""
=============================================================================================

Name: facebook_post.py
Description: Module for handling the creation of posts and their publication on Facebook
Author: OneSocial Team
Date: June 2026
Version: 1.0

=============================================================================================
"""

from pathlib import Path

import requests

from auth.meta_auth import get_meta_page_token
from models.app_errors import (
    ApiError,
    InputValueError,
    PublishError
)

GRAPH_BASE = "https://graph.facebook.com/v23.0"


def _get_page_access_token(account) -> str:
    """
    Returns a valid Facebook Page Token.
    """

    if account.facebook_page_token:
        return account.facebook_page_token

    if not account.facebook_page_id:
        raise InputValueError(
            "No Facebook Page configured."
        )

    return get_meta_page_token(account.access_token, account.facebook_page_id)


def _publish_text_post(
    page_id: str,
    page_token: str,
    message: str
) -> dict:
    """
    Publishes a text-only Facebook post.
    """

    try:
        response = requests.post(
            f"{GRAPH_BASE}/{page_id}/feed",
            data={
                "message": message,
                "access_token": page_token
            },
            timeout=60
        )

    except requests.RequestException as error:
        raise ApiError(
            "No se pudo publicar en Facebook."
        ) from error

    if response.status_code != 200:
        raise PublishError(
            f"Facebook publish error: {response.text}"
        )

    return response.json()


def _publish_photo_post(
    page_id: str,
    page_token: str,
    image_path: Path,
    message: str
) -> dict:
    """
    Publishes an image post on Facebook.
    """

    try:
        with open(image_path, "rb") as image_file:

            response = requests.post(
                f"{GRAPH_BASE}/{page_id}/photos",
                data={
                    "caption": message,
                    "access_token": page_token
                },
                files={
                    "source": image_file
                },
                timeout=120
            )

    except OSError as error:
        raise InputValueError(
            f"No se pudo leer la imagen: {image_path}"
        ) from error

    except requests.RequestException as error:
        raise ApiError(
            "No se pudo publicar la imagen."
        ) from error

    if response.status_code != 200:
        raise PublishError(
            f"Facebook image publish error: {response.text}"
        )

    return response.json()


def publish_post_facebook(
    account,
    title,
    text,
    image_path=None
):
    """
    - Input:
        - account: Token
        - title: str
        - text: str
        - image_path: Path | None

    - Description:
        Publishes a Facebook Page post.
        If image_path exists -> photo post.
        Otherwise -> text post.
    """

    if not account.facebook_page_id:
        raise InputValueError(
            "No Facebook page configured."
        )

    page_token = _get_page_access_token(
        account
    )

    message = "\n".join(
        part
        for part in [title, text]
        if part
    )

    if image_path:

        image_path = Path(
            image_path
        )

        if (
            not image_path.exists()
            or
            not image_path.is_file()
        ):
            raise InputValueError(
                "La imagen no existe."
            )

        return _publish_photo_post(
            account.facebook_page_id,
            page_token,
            image_path,
            message
        )

    return _publish_text_post(
        account.facebook_page_id,
        page_token,
        message
    )