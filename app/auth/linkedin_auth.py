import requests

from datetime import datetime, timedelta

from models.app_errors import InputValueError


AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"


def get_linkedin_auth_url(client_id):
    """
    Generates LinkedIn OAuth URL.
    """

    return (
        f"{AUTH_URL}"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri=urn:ietf:wg:oauth:2.0:oob"
        f"&scope=openid%20profile%20email%20w_member_social"
    )


def create_linkedin_token(
    client_id,
    client_secret,
    code
):
    """
    Creates a fully populated Token object
    after LinkedIn authentication.
    """

    from models.token_manager import Token

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
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
    Gets profile/email information.
    """

    headers = {
        "Authorization":
        f"Bearer {account.access_token}"
    }

    # =========================
    # PROFILE
    # =========================

    profile_response = requests.get(
        "https://api.linkedin.com/v2/me",
        headers=headers
    )

    if profile_response.status_code != 200:
        raise InputValueError(
            "Failed to retrieve LinkedIn profile"
        )

    profile_data = profile_response.json()

    account.provider_user_id = (
        profile_data.get("id")
    )

    first_name = profile_data.get(
        "localizedFirstName",
        ""
    )

    last_name = profile_data.get(
        "localizedLastName",
        ""
    )

    account.username = (
        f"{first_name} {last_name}"
    ).strip()

    # =========================
    # EMAIL
    # =========================

    email_response = requests.get(
        "https://api.linkedin.com/v2/emailAddress"
        "?q=members&projection=(elements*(handle~))",
        headers=headers
    )

    if email_response.status_code == 200:

        email_data = email_response.json()

        elements = email_data.get(
            "elements",
            []
        )

        if elements:

            account.email = (
                elements[0]
                .get("handle~", {})
                .get("emailAddress")
            )