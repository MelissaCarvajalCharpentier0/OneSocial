"""

=============================================================================================

Name: linkedin_post.py
Description: Module for handling the creation of posts and their publication on LinkedIn
Author: Melissa Carvajal
Date: May 2026
Version: 1.1

=============================================================================================

"""

from post.post_on_socials import *


LINKEDIN_POST_URL = ("https://api.linkedin.com/v2/ugcPosts")


def publish_post_linkedin_text(account, text):
    """
    - Input:
        - account: Token - The account object containing authentication details.
        - text: str - The text content of the post to be published.
    - Output:
        - dict: A dictionary containing the success status, message, and post ID if the post was published successfully.
    - Description:
        - Publishes a text-only post to LinkedIn using the provided account and text. 
    """

    headers = {
        "Authorization":
            f"Bearer {account.access_token}",

        "X-Restli-Protocol-Version":
            "2.0.0",

        "Content-Type":
            "application/json"
    }

    payload = {
        "author":
            f"urn:li:person:{account.provider_user_id}",

        "lifecycleState":
            "PUBLISHED",

        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory":
                    "NONE"
            }
        },

        "visibility": {

            "com.linkedin.ugc.MemberNetworkVisibility":
                "PUBLIC"
        }
    }

    response = requests.post(
        LINKEDIN_POST_URL,
        headers=headers,
        json=payload
    )

    if response.status_code != 201:
        raise PublishError(
            "Failed to publish LinkedIn post:\n"
            f"{response.text}"
        )

    return {
        "success": True,
        "message": "LinkedIn post published",
        "post_id":
            response.headers.get(
                "x-restli-id"
            )
    }


def publish_post_linkedin_with_image(account, text, image_path):
    """
    - Input:
        - account: Token - The account object containing authentication details.
        - text: str - The text content of the post to be published.
        - image_path: Path - The file path to the image to be included in the post.
    - Output:
        - dict: A dictionary containing the success status and post ID if the post was published successfully.
    - Description:
        - Publishes a post with an image to LinkedIn using the provided account, text, and image file path. 
    """

    headers = {
        "Authorization":
            f"Bearer {account.access_token}",

        "X-Restli-Protocol-Version":
            "2.0.0",

        "Content-Type":
            "application/json"
    }

    register_payload = {
        "registerUploadRequest": {
            "recipes": [
                "urn:li:digitalmediaRecipe:feedshare-image"
            ],
            "owner":
                f"urn:li:person:{account.provider_user_id}",
            "serviceRelationships": [
                {
                    "relationshipType":
                        "OWNER",

                    "identifier":
                        "urn:li:userGeneratedContent"
                }
            ]
        }
    }

    register_response = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers=headers,
        json=register_payload
    )

    if register_response.status_code != 200:
        raise PublishError(
            "Failed to register "
            "LinkedIn image upload:\n"
            f"{register_response.text}"
        )

    register_data = register_response.json()

    upload_info = (
        register_data["value"]
        ["uploadMechanism"]
        ["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]
    )

    upload_url = upload_info["uploadUrl"]
    asset = register_data["value"]["asset"]

    with open(image_path, "rb") as image_file:
        upload_response = requests.put(
            upload_url,
            data=image_file,
            headers={
                "Authorization":
                    f"Bearer {account.access_token}"
            }
        )

    if upload_response.status_code not in [200, 201]:
        raise PublishError(
            "Failed to upload "
            "LinkedIn image:\n"
            f"{upload_response.text}"
        )

    post_payload = {
        "author":
            f"urn:li:person:{account.provider_user_id}",

        "lifecycleState":
            "PUBLISHED",

        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory":
                    "IMAGE",
                "media": [
                    {
                        "status":
                            "READY",
                        "description": {
                            "text": text
                        },
                        "media":
                            asset,
                        "title": {
                            "text": "OneSocial"
                        }
                    }
                ]
            }
        },

        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility":
                "PUBLIC"
        }
    }

    post_response = requests.post(
        LINKEDIN_POST_URL,
        headers=headers,
        json=post_payload
    )

    if post_response.status_code != 201:
        raise PublishError(
            "Failed to publish "
            "LinkedIn image post:\n"
            f"{post_response.text}"
        )

    return {
        "success": True,
        "post_id":
            post_response.headers.get(
                "x-restli-id"
            )
    }