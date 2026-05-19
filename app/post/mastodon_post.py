"""

=============================================================================================

Name: mastodon_post.py
Description: Module for handling the creation of posts and their publication on Mastodon
Author: Melissa Carvajal
Date: May 2026
Version: 1.1

=============================================================================================

"""

from post.post_on_socials import *

def upload_post_mastodon(text: str, image_path: Path, account):
    """
    - Input: 
        - text: str - The text content of the post.
        - image_path: Path - The file path to the image to be uploaded.
        - account: Token - The account object containing authentication details.
    - Description: 
        - Uploads a post to Mastodon with the given text and image. It first ensures that the account 
        has a valid access token, then it uploads the image and creates a new status with the text and the media ID of the uploaded image.
    """

    try:
        mastodon = Mastodon(
            access_token=account.access_token,
            api_base_url=f"https://{account.server}"
        )

        media = mastodon.media_post(image_path)
        mastodon.status_post(text, media_ids=[media])
    except Exception as error:
        raise PublishError("No se pudo publicar en Mastodon.") from error


def upload_post_mastodon_text(text: str, account):
    """
    - Input: 
        - text: str - The text content of the post.
        - account: Token - The account object containing authentication details.
    - Description: 
        - Uploads a text-only post to Mastodon. It ensures that the account has a valid access token and then creates a new status with the provided text.
    """
    if not account.access_token:
        raise InputValueError("No hay access_token. Debes autenticar primero.")
    
    try:
        mastodon = Mastodon(
            access_token=account.access_token,
            api_base_url=f"https://{account.server}"
        )

        mastodon.status_post(text)
    except Exception as error:
        raise PublishError("No se pudo publicar el texto en Mastodon.") from error
