"""

=============================================================================================

Name: linkedin_auth.py
Description: Module for handling LinkedIn authentication and token management.  
Author: Pamela Fernández
Date: Mayo 2026 
Version: 2.0

=============================================================================================

"""

import requests
from datetime import datetime, timedelta
from models.app_errors import InputValueError
from urllib.parse import quote


AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
REDIRECT_URI = "http://localhost:8080/linkedin/callback.html"



def get_linkedin_auth_url(client_id):
    """
    - Input:
        - client_id: str - The LinkedIn application's client ID, used to identify the 
        application during the authentication process.
    - Output:
        - auth_url: str - The URL to which the user should be redirected to initiate 
        the LinkedIn authentication process.
    - Description: 
        - Constructs and returns the URL for LinkedIn authentication, which is used to 
        redirect the user to the LinkedIn login page. This URL is relative to the 
        location of this script.   
    """

    encoded_redirect = quote(
        REDIRECT_URI,
        safe=''
    )

    return (
        f"{AUTH_URL}"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={encoded_redirect}"
        f"&scope=openid%20profile%20email%20w_member_social"
    )


def create_linkedin_token(client_id, client_secret, code):
    """
    - Input:
        - client_id: str - The LinkedIn application's client ID, used to identify the 
        application during the authentication process. 
        - client_secret: str - The LinkedIn application's client secret, used to authenticate 
        the application during the token exchange process.
        - code: str - The authorization code received from LinkedIn after the user has authorized 
        the application, used to exchange for an access token.
    - Output:     
        - account: Token object containing the LinkedIn account information and access token.
    - Description: 
        - Exchanges the authorization code for an access token and creates a Token object 
        containing the LinkedIn account information and access token. This function also
        calls the enrich_linkedin_account function to populate additional account information
        such as the provider user ID, username, and email.
    """

    from models.token_manager import Token

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(
        TOKEN_URL,
        data=data
    )

    if response.status_code != 200:
        raise InputValueError(
            f"LinkedIn token error: {response.text}"
        )

    token_data = response.json()

    access_token = token_data.get(
        "access_token"
    )

    expires_in = token_data.get(
        "expires_in",
        0
    )

    now = datetime.utcnow()

    account = Token(
        provider="LinkedIn",
        client_id=client_id,
        client_secret=client_secret,

        access_token=access_token,
        token_type="Bearer",
        scope=token_data.get("scope"),

        issued_at=now.isoformat(),

        access_expires_at=(
            now + timedelta(seconds=expires_in)
        ).isoformat()
    )

    enrich_linkedin_account(account)

    return account


def enrich_linkedin_account(account):
    """
    - Input:
        - account: Token object for the LinkedIn account to enrich with additional information.
    - Description:
        - Retrieves additional information for the LinkedIn account and populates the Token object.
    """
    headers = {
        "Authorization":
        f"Bearer {account.access_token}"
    }

    response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers=headers
    )

    if response.status_code != 200:
        raise InputValueError(
            "Failed to retrieve LinkedIn profile"
        )

    data = response.json()

    account.provider_user_id = data.get("sub")
    account.username = data.get("name")
    account.email = data.get("email")