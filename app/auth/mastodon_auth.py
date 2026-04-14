"""

=============================================================================================

Name: mastodon_auth.py
Description: Module for handling Mastodon authentication and token management.  
Author: Pamela Fernández
Date: March 2026 
Version: 1.0

=============================================================================================

"""
import os
from mastodon import Mastodon

def get_cred_path():
    """
    - Output:
        - cred_path: str - The file path to the Mastodon client credentials file.
    - Description: 
        - Constructs and returns the file path to the Mastodon client credentials file, 
        which is used for authentication with the Mastodon API. This path is relative to the 
        location of this script.   
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(BASE_DIR, "clientcred.secret")


def ensure_mastodon_app():
    """
    - Description: 
        - Ensures that the Mastodon application credentials file exists. If it does not exist, it 
        creates a new Mastodon application and saves the credentials to the specified file path. 
        This is necessary for authenticating with the Mastodon API and obtaining access tokens for 
        user accounts.    
    """
    cred_path = get_cred_path()

    if not os.path.exists(cred_path):
        print("Creando app de Mastodon...")

        Mastodon.create_app(
            'onesocial',
            api_base_url='https://mastodon.social',
            to_file=cred_path
        )


def ensure_mastodon_token(account):
    """
    - Input: 
        - account: Token object for the Mastodon account to ensure authentication
    - Output: 
        - access_token: str - The access token for the Mastodon account, either existing or newly obtained.
    - Description: 
        - If the account already has an access token, it is returned. Otherwise, the 
        authentication process is initiated to obtain a new access token, which is then returned.  
    """

    if account.access_token:
        return account.access_token
    else:
        return None



def get_mastodon_auth_url(account):
    """
    - Input: 
        - account: Token object for the Mastodon account to get the authentication URL for.
    - Output: 
        - url: str - The authentication URL for the Mastodon account.
    - Description: 
        - Generates the authentication URL for the Mastodon account, which can be used to initiate the 
        authentication process.
    """
    cred_path = get_cred_path()

    mastodon = Mastodon(
        client_id=cred_path,
        api_base_url='https://mastodon.social'
    )

    url = mastodon.auth_request_url(
        scopes=['read', 'write'],
        redirect_uris="urn:ietf:wg:oauth:2.0:oob"
    )

    return url


def save_mastodon_token(account, code):
    """
    - Input: 
        - account: Token object for the Mastodon account to save the access token for.
        - code: str - The authentication code received from the Mastodon authentication process.
    - Output: 
        - access_token: str - The access token obtained from the Mastodon authentication process, which
        is saved to the account object.
    - Description: 
        - Takes the authentication code received from the Mastodon authentication process, uses it to obtain an
        access token, and saves that token to the provided account object for future authenticated interactions with Mastodon.  
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(BASE_DIR, "clientcred.secret")

    mastodon = Mastodon(
        client_id=cred_path,
        api_base_url='https://mastodon.social'
    )

    mastodon.log_in(
        code=code,
        scopes=['read', 'write'],
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )

    account.access_token = mastodon.access_token