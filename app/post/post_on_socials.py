"""

=============================================================================================

Name: post_on_socials.py
Description: Module for handling the creation of posts and their publication on social media platforms.
Author: Pamela Fernández, Josue Soto
Date: March 2026
Version: 1.1

=============================================================================================

"""

import mimetypes

from mastodon import Mastodon
from pathlib import Path

import requests

from atproto import Client
from atproto_client.exceptions import UnauthorizedError, BadRequestError, NetworkError, RequestException, InvokeTimeoutError, LoginRequiredError

from models.app_errors import ApiError, InputValueError, PublishError
from auth.reddit_auth import ensure_reddit_token

from requests.auth import HTTPBasicAuth


