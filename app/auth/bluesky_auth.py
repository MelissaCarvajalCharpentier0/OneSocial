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
from atproto_client.exceptions import UnauthorizedError, BadRequestError, NetworkError, RequestException, InvokeTimeoutError

from models.app_errors import InputValueError, ApiError



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
    
    except UnauthorizedError:
        raise InputValueError("Access denied.")
    except BadRequestError:
        raise ApiError("Invalid request for bluesky.")
    except InvokeTimeoutError:
        raise ApiError("No response from Bluesky API.")
    except (NetworkError, RequestException):
        raise ApiError("Could not reach Bluesky/ATProto server.")
    except Exception as error:
        raise Exception("Unexpected error at Bluesky login.") from error