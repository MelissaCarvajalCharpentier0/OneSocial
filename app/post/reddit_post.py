"""

=============================================================================================

Name: reddit_post.py
Description: Module for handling the creation of posts and their publication on Reddit
Author: Melissa Carvajal
Date: May 2026
Version: 1.1

=============================================================================================

"""

import requests

from auth.reddit_auth import ensure_reddit_token
from models.app_errors import ApiError, InputValueError, PublishError

REDDIT_SUBMIT_URL = "https://oauth.reddit.com/api/submit"
REDDIT_USER_AGENT = "OneSocial/1.0 (by /u/onesocial)"

def publish_post_reddit_text(title: str, text: str, account):
    """
    - Input:
        - title: str - The title of the Reddit post.
        - text: str - The body content of the Reddit post.
        - account: Account - The account object containing authentication details.
    - Description:
        - Publishes a text-only post to the configured subreddit for the account.
    """

    if not account.subreddit:
        raise InputValueError("Falta el subreddit para Reddit.")

    if not title:
        raise InputValueError("Reddit requiere un titulo.")

    access_token = ensure_reddit_token(account)

    data = {
        "sr": account.subreddit,
        "kind": "self",
        "title": title,
        "text": text or "",
    }

    try:
        response = requests.post(
            REDDIT_SUBMIT_URL,
            headers={
                "Authorization": f"bearer {access_token}",
                "User-Agent": REDDIT_USER_AGENT,
            },
            data=data,
            timeout=30,
        )
    except requests.RequestException as error:
        raise ApiError("No se pudo publicar en Reddit.") from error

    if response.status_code != 200:
        raise PublishError(f"Error publicando en Reddit: {response.text}")

    payload = response.json()
    errors = payload.get("json", {}).get("errors", [])
    if errors:
        raise PublishError(f"Error publicando en Reddit: {errors}")

    return payload