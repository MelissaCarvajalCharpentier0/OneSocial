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


def ensure_mastodon_app():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(BASE_DIR, "clientcred.secret")

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
    mastodon = Mastodon(
        client_id='clientcred.secret',
        api_base_url='https://mastodon.social'
    )

    url = mastodon.auth_request_url(
        scopes=['read', 'write'],
        redirect_uris="http://localhost:8000/callback"
    )

    return url


def save_mastodon_token(account, code):
    mastodon = Mastodon(
        client_id='clientcred.secret',
        api_base_url='https://mastodon.social'
    )

    mastodon.log_in(
        code=code,
        scopes=['read', 'write'],
        redirect_uri="http://localhost:8000/callback"
    )

    account.access_token = mastodon.access_token