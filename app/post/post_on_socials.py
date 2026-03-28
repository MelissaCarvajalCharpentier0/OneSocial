"""

=============================================================================================

Name: post_on_socials.py
Description: Module for handling the creation of posts and their publication on social media platforms.
Author: Pamela Fernández
Date: March 2026
Version: 1.0

=============================================================================================

"""

import mimetypes

from mastodon import Mastodon
from pathlib import Path

import requests
from auth.mastodon_auth import ensure_mastodon_token



####################### MASTONDON #######################


def upload_post_mastodon(text: str, image_path: Path, account):
    """
    - Input: 
        - text: str - The text content of the post.
        - image_path: Path - The file path to the image to be uploaded.
        - account: Account - The account object containing authentication details.
    - Description: 
        - Uploads a post to Mastodon with the given text and image. It first ensures that the account 
        has a valid access token, then it uploads the image and creates a new status with the text and the media ID of the uploaded image.
    """

    mastodon = Mastodon(
        access_token=ensure_mastodon_token(account),
        api_base_url='https://mastodon.social'
    )

    media = mastodon.media_post(image_path)
    mastodon.status_post(text, media_ids=[media])


def upload_post_mastodon_text(text: str, account):
    """
    - Input: 
        - text: str - The text content of the post.
        - account: Account - The account object containing authentication details.
    - Description: 
        - Uploads a text-only post to Mastodon. It ensures that the account has a valid access token and then creates a new status with the provided text.
    """
    mastodon = Mastodon(
        access_token=ensure_mastodon_token(account),
        api_base_url='https://mastodon.social'
    )

    mastodon.status_post(text)




####################### WORDPRESS #######################

def get_sites(token):
    """
    - Input: 
        - token: str - The access token for authenticating with the WordPress API.
    - Output: 
        - site_id: str - The ID of the first site associated with the authenticated account.
    - Description: 
        - Makes a GET request to the WordPress API to retrieve the list of sites associated with the authenticated account.
        - Parses the response to extract and return the ID of the first site found. If no sites are found, it prints a message and returns None.    
    """

    url = "https://public-api.wordpress.com/rest/v1.1/me/sites"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    sites = data.get("sites", [])

    if not sites:
        print("No se encontraron sitios")
        return None

    site_id = sites[0]["ID"] 
    return site_id


def publish_post_wordpress(account, title, content):
    """
    - Input: 
        - account: Account - The account object containing authentication details.
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

    url = f"https://public-api.wordpress.com/rest/v1.1/sites/{get_sites(account.access_token)}/posts/new"

    headers = {
        "Authorization": f"Bearer {account.access_token}"
    }

    data = {
        "title": title,
        "content": content,
        "status": "publish"
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        print("Error:", response.text)
        return None

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

    with open(image_path, "rb") as img:
        response = requests.post(
            url,
            headers=headers,
            files={
                'media[]': (image_path.name, img, mime_type)
            }
        )

    if response.status_code != 200:
        return None

    return response.json()


def publish_post_wordpress_with_image(account, title, content, image_path):
    """
    - Input: 
        - account: Account - The account object containing authentication details.
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

    media = upload_image_wp(account.access_token, get_sites(account.access_token), image_path)

    if not media:
        print("Falló subida de imagen")
        return None

    image_url = media["media"][0]["URL"]

    content_with_image = f'<img src="{image_url}" /><br>{content}'

    return publish_post_wordpress(account.access_token, get_sites(account.access_token), title, content_with_image)


def publish_post_wordpress_with_featured_image(account, title, content, image_path):
    """
    - Input: 
        - account: Account - The account object containing authentication details.
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

    site_id = get_sites(account.access_token)
    media = upload_image_wp(account.access_token, site_id, image_path)

    if not media:
        print("Falló subida de imagen")
        return None

    media_id = media["media"][0]["ID"]
    url = f"https://public-api.wordpress.com/rest/v1.1/sites/{site_id}/posts/new"

    headers = {
        "Authorization": f"Bearer {account.access_token}"
    }

    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "featured_image": media_id
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        print("Error:", response.text)
        return None
    return response.json()