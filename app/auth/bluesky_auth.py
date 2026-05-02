"""

=============================================================================================

Name: bluesky_auth.py
Description: Module for handling Bluesky authentication and token management.  
Author: Josué Soto
Date: April 2026 
Version: 1.0

=============================================================================================

"""

from atproto import Client
from atproto_client.exceptions import (
    UnauthorizedError,
    BadRequestError,
    NetworkError,
    RequestException,
    InvokeTimeoutError,
    ModelError,
    AtProtocolError,
)

from models.app_errors import InputValueError, ApiError, TokenStorageError

"""
client = Client()
client.login('onesocial.bsky.social', 'kzu7-nq4a-awd4-7dt2')

post = client.send_post('Hello world! I posted this via the Python SDK with an app password c:.')

print(post)




with open('my_cat.jpg', 'rb') as f:
    img_data = f.read()

client.send_image(text='I love my cat', image=img_data, image_alt='My cat mittens')
"""


def verify_bluesky_login(token):
    """
    - Description: Verifies that a Bluesky/ATProto login token works.
    """

    username = token.username
    app_password = token.password

    if not username or not app_password:
        raise InputValueError("Missing credentials necesary for login")

    try:
        client = Client()
        client.login(username, app_password)
    
    except UnauthorizedError as error:
        raise InputValueError("Access denied.")

    except BadRequestError as error:
        raise ApiError("Invalid request for bluesky.")

    except InvokeTimeoutError as error:
        raise ApiError ("No response from Bluesky API.")

    except (NetworkError, RequestException) as error:
        raise ApiError ("Could not reach Bluesky/ATProto server.")

    except Exception as error:
        raise Exception ("Unexpected error at Bluesky login.")