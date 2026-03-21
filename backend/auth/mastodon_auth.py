# auth/mastodon/register_mastodon.py

from mastodon import Mastodon

def get_mastodon_token(account):

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

    if account.access_token:
        return account.access_token
    
    account.access_token = get_mastodon_token(account)
    return account.access_token