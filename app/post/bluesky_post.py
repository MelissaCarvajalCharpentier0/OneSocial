"""

=============================================================================================

Name: bluesky_post.py
Description: Module for handling the creation of posts and their publication on Bluesky
Author: Melissa Carvajal
Date: May 2026
Version: 1.1

=============================================================================================

"""

from atproto import Client
from atproto_client.exceptions import (
    BadRequestError,
    InvokeTimeoutError,
    LoginRequiredError,
    NetworkError,
    RequestException,
    UnauthorizedError,
)

from models.app_errors import ApiError, InputValueError

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