"""

=============================================================================================

Name: mastodon_auth.py
Description: Module for handling Mastodon authentication and token management.  
Author: Pamela Fernández
Date: March 2026 
Version: 1.0

=============================================================================================

"""

from mastodon import Mastodon


def get_mastodon_token(account):

    """
    - Input: 
        - account: Token object for the Mastodon account to authenticate
    - Output: 
        - access_token: str - The access token obtained after authentication
    - Description:
        - Obtain the access token for the given Mastodon account by guiding the 
        user through the authentication process.
    """

    mastodon = Mastodon(
        client_id='clientcred.secret',
        api_base_url='https://mastodon.social'
    )

    url = mastodon.auth_request_url(scopes=['read', 'write'])
    print(f"Autoriza esta cuenta {account.username}:")
    print(url)

    code = input("Pega el código: ")

    mastodon.log_in(
        code=code,
        scopes=['read', 'write']
    )

    return mastodon.access_token




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
    
    account.access_token = get_mastodon_token(account)
    return account.access_token