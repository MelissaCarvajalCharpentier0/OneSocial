"""

=============================================================================================

Name: wordpress_post.py
Description: Module for handling the creation of posts and their publication on WordPress
Author: Melissa Carvajal
Date: May 2026
Version: 1.1

=============================================================================================

"""

import mimetypes
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

from models.app_errors import ApiError, PublishError

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


####################### WORDPRESSREST #######################


def verify_wordpress_rest(account):
    """
    Verify the REST API credentials by fetching the current user.
    Raises an exception on failure.
    """
    url = f"{account.base_url}/wp-json/wp/v2/users/me"

    headers = {
        "User-Agent": "OneSocial/1.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Disable the Expect header (causes 417/412 on some servers)
    session = requests.Session()
    session.trust_env = False  # avoid system proxy issues

    resp = session.get(
        url,
        auth=HTTPBasicAuth(account.username, account.password),
        headers=headers,
        timeout=15
    )

    if resp.status_code != 200:
        # Add a bit more diagnostic info
        detail = resp.text[:200] if resp.text else "No response body"
        raise Exception(
            f"Verification failed: HTTP {resp.status_code}. "
            f"Reason: {resp.reason}. Detail: {detail}"
        )

    return True


def publish_post_wordpress_rest(account, title, content, image_path=None):
    wp_url = f"{account.base_url}/wp-json/wp/v2"
    headers = {
        "User-Agent": "OneSocial/1.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    session = requests.Session()
    session.trust_env = False

    # 1. Create the post
    post_data = {
        "title": title,
        "content": content,
        "status": "publish"
    }
    r = session.post(
        f"{wp_url}/posts",
        json=post_data,
        auth=HTTPBasicAuth(account.username, account.password),
        headers=headers,
        timeout=30
    )
    if r.status_code not in (200, 201):
        raise Exception(f"Post creation failed: {r.status_code} {r.text}")

    post_id = r.json()["id"]

    # 2. Upload image if provided
    if image_path:
        image_path = Path(image_path)
        if image_path.is_file():
            media_url = f"{wp_url}/media"
            with open(image_path, 'rb') as img:
                mime = f"image/{image_path.suffix[1:]}"
                files = {'file': (image_path.name, img, mime)}
                r_media = session.post(
                    media_url,
                    files=files,
                    auth=HTTPBasicAuth(account.username, account.password),
                    headers={"User-Agent": "OneSocial/1.0"},  # no Content-Type here (multipart sets it)
                    timeout=30
                )
            if r_media.status_code not in (200, 201):
                raise Exception(f"Image upload failed: {r_media.status_code} {r_media.text}")

            media_id = r_media.json()["id"]

            # Set featured image
            featured_data = {"featured_media": media_id}
            session.post(
                f"{wp_url}/posts/{post_id}",
                json=featured_data,
                auth=HTTPBasicAuth(account.username, account.password),
                headers=headers
            )