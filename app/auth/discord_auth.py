"""

=============================================================================================

Name: discord_auth.py
Description: Module for handling Discord authentication and url webhook management.
Author: Pamela Fernández
Date: June 2026
Version: 1.0

=============================================================================================

"""

import requests


def validate_discord_webhook(webhook_url: str) -> tuple[bool, str]:
    try:
        response = requests.get(webhook_url, timeout=10)

        if response.status_code == 200:
            return True, "Discord webhook verified successfully."

        if response.status_code == 404:
            return False, "Discord webhook was not found."

        return False, f"Discord returned status code {response.status_code}."

    except requests.RequestException as e:
        return False, f"Could not verify Discord webhook: {e}"