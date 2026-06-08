import requests
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_discord_message(webhook_url: str, content: str) -> bool:
    """
    Sends a simple text message to a Discord channel via a webhook.

    Args:
        webhook_url (str): The Discord webhook URL.
        content (str): The text content to send.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    data = {"content": content}
    return _send_discord_webhook(webhook_url, data)

def send_discord_embed(webhook_url: str, embed: Dict[str, Any]) -> bool:
    """
    Sends a rich embed message to a Discord channel via a webhook.

    Args:
        webhook_url (str): The Discord webhook URL.
        embed (dict): The embed data structure.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    data = {"embeds": [embed]}
    return _send_discord_webhook(webhook_url, data)

def _send_discord_webhook(webhook_url: str, payload: Dict[str, Any]) -> bool:
    """
    Internal function to handle the actual HTTP request to Discord's webhook.
    """
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

        if response.status_code == 204:  # 204 No Content is the success code for webhooks
            logger.info("Discord webhook message sent successfully.")
            return True
        else:
            # If Discord returns a 200, it usually includes the message data
            logger.info(f"Discord webhook message sent successfully. Response: {response.status_code}")
            return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord webhook: {e}")
        if e.response:
            logger.error(f"Response content: {e.response.text}")
        return False

def send_discord_message_with_image(webhook_url: str, content: str, image_path: str) -> bool:
    """
    Sends a text message with an image attachment to a Discord channel via webhook.

    Args:
        webhook_url (str): The Discord webhook URL.
        content (str): The text content to send.
        image_path (str): Path to the image file (JPEG/PNG supported).

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    try:
        with open(image_path, 'rb') as img_file:
            files = {
                'file': (image_path.split('/')[-1], img_file, 'image/png')  # or 'image/jpeg'
            }
            data = {'content': content}
            response = requests.post(webhook_url, data=data, files=files)
            response.raise_for_status()
            logger.info("Discord message with image sent successfully.")
            return True
    except Exception as e:
        logger.error(f"Failed to send Discord message with image: {e}")
        return False