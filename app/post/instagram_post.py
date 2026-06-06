"""

=============================================================================================

Name: instagram_post.py
Description: Module for handling the creation of posts and their publication on Instagram
Author: OneSocial Team
Date: May 2026
Version: 1.0

=============================================================================================

"""

import time
from pathlib import Path

import requests

from auth.instagram_auth import ensure_instagram_token
from models.app_errors import ApiError, InputValueError, PublishError

GRAPH_BASE = "https://graph.facebook.com/v23.0"


def _get_page_access_token(account) -> str:
    if account.facebook_page_token:
        return account.facebook_page_token

    if not account.facebook_page_id:
        raise InputValueError("No Facebook Page linked for Instagram.")

    try:
        response = requests.get(
            f"{GRAPH_BASE}/{account.facebook_page_id}",
            params={
                "fields": "access_token",
                "access_token": account.access_token,
            },
            timeout=30,
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo obtener el token de la pagina.") from error

    if response.status_code != 200:
        raise ApiError(f"Error obteniendo token de pagina: {response.text}")

    data = response.json()
    page_token = data.get("access_token")

    if not page_token:
        raise ApiError("No page access token returned from Facebook.")

    return page_token


def _upload_image_to_page(page_id: str, page_token: str, image_path: Path) -> str:
    try:
        with open(image_path, "rb") as image_file:
            response = requests.post(
                f"{GRAPH_BASE}/{page_id}/photos",
                data={
                    "published": "false",
                    "access_token": page_token,
                },
                files={"source": image_file},
                timeout=60,
            )
    except OSError as error:
        raise InputValueError(f"No se pudo leer la imagen: {image_path}") from error
    except requests.RequestException as error:
        raise ApiError("No se pudo subir la imagen a Facebook.") from error

    if response.status_code != 200:
        raise PublishError(f"Error subiendo imagen a Facebook: {response.text}")

    payload = response.json()
    photo_id = payload.get("id")

    if not photo_id:
        raise PublishError("No se obtuvo el id de la foto subida.")

    return photo_id


def _get_photo_source(photo_id: str, page_token: str) -> str:
    try:
        response = requests.get(
            f"{GRAPH_BASE}/{photo_id}",
            params={
                "fields": "images",
                "access_token": page_token,
            },
            timeout=30,
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo obtener la URL de la imagen.") from error

    if response.status_code != 200:
        raise ApiError(f"Error obteniendo URL de imagen: {response.text}")

    payload = response.json()
    images = payload.get("images") or []

    if not images:
        raise PublishError("No se obtuvo la URL de la imagen.")

    source = images[0].get("source")
    if not source:
        raise PublishError("No se obtuvo la URL de la imagen.")

    return source


def _create_instagram_media(account, image_url: str, caption: str) -> str:
    try:
        response = requests.post(
            f"{GRAPH_BASE}/{account.instagram_user_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": account.access_token,
            },
            timeout=60,
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo crear el contenedor de Instagram.") from error

    if response.status_code != 200:
        raise PublishError(f"Error creando media de Instagram: {response.text}")

    payload = response.json()
    creation_id = payload.get("id")

    if not creation_id:
        raise PublishError("No se recibio el creation_id de Instagram.")

    return creation_id


def _wait_for_media_ready(creation_id: str, access_token: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            response = requests.get(
                f"{GRAPH_BASE}/{creation_id}",
                params={
                    "fields": "status_code",
                    "access_token": access_token,
                },
                timeout=20,
            )
        except requests.RequestException as error:
            raise ApiError("No se pudo verificar el estado del media.") from error

        if response.status_code != 200:
            raise PublishError(f"Error verificando media: {response.text}")

        status_code = response.json().get("status_code")

        if status_code == "FINISHED":
            return
        if status_code in ("ERROR", "EXPIRED"):
            raise PublishError("El media de Instagram fallo o expiro.")

        time.sleep(2)

    raise PublishError("Tiempo de espera agotado esperando media de Instagram.")


def _publish_instagram_media(account, creation_id: str) -> dict:
    try:
        response = requests.post(
            f"{GRAPH_BASE}/{account.instagram_user_id}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": account.access_token,
            },
            timeout=60,
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo publicar en Instagram.") from error

    if response.status_code != 200:
        raise PublishError(f"Error publicando en Instagram: {response.text}")

    return response.json()


def publish_post_instagram(account, title, text, image_path):
    """
    - Input:
        - account: Token - The account object containing authentication details.
        - title: str - Optional title for the post.
        - text: str - The body content of the post.
        - image_path: Path - The local image path to publish.
    - Description:
        - Publishes a single-image Instagram post using the Graph API.
    """

    if not account.instagram_user_id:
        raise InputValueError("No Instagram user id configured.")

    if not account.facebook_page_id:
        raise InputValueError("No Facebook Page linked for Instagram.")

    if not image_path:
        raise InputValueError("Instagram requiere una imagen para publicar.")

    image_path = Path(image_path)
    if not image_path.exists() or not image_path.is_file():
        raise InputValueError("La imagen no existe o no es un archivo.")

    ensure_instagram_token(account)

    caption = "\n".join(part for part in [title, text] if part)

    page_token = _get_page_access_token(account)
    photo_id = _upload_image_to_page(account.facebook_page_id, page_token, image_path)
    image_url = _get_photo_source(photo_id, page_token)

    creation_id = _create_instagram_media(account, image_url, caption)
    _wait_for_media_ready(creation_id, account.access_token)

    return _publish_instagram_media(account, creation_id)
