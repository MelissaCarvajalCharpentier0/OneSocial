"""

=============================================================================================

Name: post_on_socials.py
Description: Module for handling the creation of posts and their publication on social media platforms.
Author: Pamela Fernández, Josue Soto
Date: March 2026
Version: 1.1

=============================================================================================

"""

import mimetypes

from mastodon import Mastodon
from pathlib import Path

import requests

from atproto import Client
from atproto_client.exceptions import UnauthorizedError, BadRequestError, NetworkError, RequestException, InvokeTimeoutError, LoginRequiredError

from models.app_errors import ApiError, InputValueError, PublishError

####################### MASTONDON #######################


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




####################### WORDPRESS #######################

def publish_post_wordpress(account, title, content):
    """
    - Input: 
        - account: Token - The account object containing authentication details.
        - title: str - The title of the post to be published.
        - content: str - The content of the post to be published.
    - Output: 
        - response.json(): dict - The JSON response from the WordPress API after attempting to publish the post, 
        containing details of the created post if successful.
    - Description: 
        - Publishes a post to WordPress using the provided account, title, and content. It constructs the appropriate 
        API endpoint URL using the site ID obtained from the account's access token, sets the necessary headers for 
        authentication, and sends a POST request with the post data. If the request is successful, it returns the JSON 
        response containing details of the created post; otherwise, it prints an error message and returns None.
    """

    url = f"https://public-api.wordpress.com/rest/v1.1/sites/{int(account.site_id)}/posts/new"

    headers = {
        "Authorization": f"Bearer {account.access_token}"
    }

    data = {
        "title": title,
        "content": content,
        "status": "publish"
    }

    try:
        response = requests.post(url, headers=headers, data=data, timeout=30)
    except requests.RequestException as error:
        raise ApiError("No se pudo publicar el post en WordPress.") from error

    if response.status_code != 200:
        raise PublishError(f"Error publicando en WordPress: {response.text}")

    return response.json()


def upload_image_wp(token, site, image_path):
    """
    - Input: 
        - token: str - The access token for authenticating with the WordPress API.
        - site: str - The ID of the WordPress site where the image will be uploaded
        - image_path: Path - The file path to the image to be uploaded.
    - Output: 
        - response.json(): dict - The JSON response from the WordPress API after attempting to upload the image, 
        containing details of the uploaded media if successful.
    - Description: 
        - Uploads an image to WordPress using the provided access token, site ID, and image file path. It constructs the appropriate 
        API endpoint URL for media upload, sets the necessary headers for authentication, and sends a POST request with the image file. 
        The function determines the MIME type of the image based on its file extension and includes it in the request. If the request is successful, 
        it returns the JSON response containing details of the uploaded media; otherwise, it prints an error message and returns None.
    """

    url = f"https://public-api.wordpress.com/rest/v1.1/sites/{site}/media/new"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    mime_type, _ = mimetypes.guess_type(image_path)

    try:
        with open(image_path, "rb") as img:
            response = requests.post(
                url,
                headers=headers,
                files={
                    'media[]': (image_path.name, img, mime_type)
                },
                timeout=30,
            )
    except OSError as error:
        raise PublishError(f"No se pudo leer la imagen para WordPress: {image_path}") from error
    except requests.RequestException as error:
        raise ApiError("No se pudo subir la imagen a WordPress.") from error

    if response.status_code != 200:
        raise PublishError(f"Error subiendo imagen a WordPress: {response.text}")

    return response.json()


def publish_post_wordpress_with_image(account, title, content, image_path):
    """
    - Input: 
        - account: Token - The account object containing authentication details.
        - title: str - The title of the post to be published.   
        - content: str - The content of the post to be published.
        - image_path: Path - The file path to the image to be included in the post
    - Output: 
        - response.json(): dict - The JSON response from the WordPress API after attempting to publish the post with the image, 
        containing details of the created post if successful.
    - Description: 
        - Publishes a post to WordPress with an image using the provided account, title, content, and image file path. 
        The function first uploads the image to WordPress and retrieves its URL. It then constructs the post content by 
        embedding the image URL in an HTML <img> tag followed by the original content. Finally, it calls the publish_post_wordpress
        function to create the post with the combined content. If any step fails, it prints an error message and returns None.
    """

    try:
        media = upload_image_wp(account.access_token, int(account.site_id), image_path)
        image_url = media["media"][0]["URL"]
        content_with_image = f'<img src="{image_url}" /><br>{content}'
        return publish_post_wordpress(account, title, content_with_image)
    except PublishError:
        raise
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise PublishError("La API de WordPress devolvió una respuesta inesperada al subir la imagen.") from error


def publish_post_wordpress_with_featured_image(account, title, content, image_path):
    """
    - Input: 
        - account: Token - The account object containing authentication details.
        - title: str - The title of the post to be published.   
        - content: str - The content of the post to be published.
        - image_path: Path - The file path to the image to be set as the featured image of the post
    - Output: 
        - response.json(): dict - The JSON response from the WordPress API after attempting to publish 
        the post with the featured image, containing details of the created post if successful.
    - Description: 
        - Publishes a post to WordPress with a featured image using the provided account, title, content, 
        and image file path. The function first uploads the image to WordPress and retrieves its media ID. 
        It then constructs the post data to include the title, content, and the media ID as the featured image. 
        Finally, it sends a POST request to create the post with the specified details.
    """

    try:
        media = upload_image_wp(account.access_token, int(account.site_id), image_path)
        media_id = media["media"][0]["ID"]
        url = f"https://public-api.wordpress.com/rest/v1.1/sites/{int(account.site_id)}/posts/new"

        headers = {
            "Authorization": f"Bearer {account.access_token}"
        }

        data = {
            "title": title,
            "content": content,
            "status": "publish",
            "featured_image": media_id
        }

        response = requests.post(url, headers=headers, data=data, timeout=30)
    except PublishError:
        raise
    except requests.RequestException as error:
        raise ApiError("No se pudo publicar el post con imagen destacada en WordPress.") from error
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise PublishError("La API de WordPress devolvió una respuesta inesperada al subir la imagen destacada.") from error

    if response.status_code != 200:
        raise PublishError(f"Error publicando en WordPress: {response.text}")
    return response.json()






######################## BLUESKY ########################


def publish_post_bluesky(token, title, content, image_path):
    """
    - Input: 
        - token: Token - The account object containing authentication details.
        - title: str - The title of the post to be published.   
        - content: str - The content of the post to be published.
        - image_path: Path - The file path to the image to be set as the featured image of the post
    - Description: 
        - Publishes a post to Bluesky with an image using the provided account, title, content, 
        and image file path.
    """

    if title: # Title not None
        text = f"{title}\n{content}"
    else:
        text = f"{content}"

    try:
        with open(image_path, 'rb') as file:
            data = file.read()

    except Exception as error:
        raise InputValueError("Error loading image.")


    try:
        client = Client()
        client.login(token.username, token.password)
        client.send_image(text=text, image=data, image_alt='')
    
    except UnauthorizedError:
        raise InputValueError("Access denied.")
    except BadRequestError:
        raise ApiError("Invalid request for bluesky. Check post length or content.")
    except InvokeTimeoutError:
        raise ApiError("No response from Bluesky API.")
    except (NetworkError, RequestException):
        raise ApiError("Could not reach Bluesky/ATProto server.")
    except LoginRequiredError:
        raise ApiError("Bluesky login failed or session was not created.")
    except Exception as error:
        raise ApiError("Unexpected error while posting to Bluesky.") from error


def publish_post_bluesky_text(token, title, content):
    """
    - Input: 
        - token: Token - The account object containing authentication details.
        - title: str - The title of the post to be published.   
        - content: str - The content of the post to be published.
    - Description: 
        - Publishes an only text post to Bluesky using the provided account, title and content.
    """

    if title: # Title not None
        text = f"{title}\n{content}"
    else:
        text = f"{content}"

    try:
        client = Client()
        client.login(token.username, token.password)
        client.send_post(text)
    
    except UnauthorizedError:
        raise InputValueError("Access denied.")
    except BadRequestError:
        raise ApiError("Invalid request for bluesky. Check post length or content.")
    except InvokeTimeoutError:
        raise ApiError("No response from Bluesky API.")
    except (NetworkError, RequestException):
        raise ApiError("Could not reach Bluesky/ATProto server.")
    except LoginRequiredError:
        raise ApiError("Bluesky login failed or session was not created.")
    except Exception as error:
        raise ApiError("Unexpected error while posting to Bluesky.") from error

