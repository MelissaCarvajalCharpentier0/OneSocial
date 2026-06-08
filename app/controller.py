"""

=============================================================================================

Name: controller.py
Description: Main module for testing the functionalities of the project, 
    including authentication and post creation on social media platforms.
Author: Josué Soto, Pamela Fernández, Melissa Carvajal
Date: April 2026
Version: 1.2

=============================================================================================

"""

from pathlib import Path
import base64
import subprocess
import webbrowser

from PIL import Image
import io

from models.token_manager import *
from models.app_errors import InputValueError, PublishError
from models.crypto import encrypt_process_file, decrypt_process_file


from auth.mastodon_auth import *
from auth.wordpress_auth import *
from auth.bluesky_auth import *
from auth.linkedin_auth import *
from auth.reddit_auth import *
from auth.instagram_auth import *
from auth.facebook_auth import (
    build_facebook_account,
    create_facebook_token,
    get_facebook_auth_url,
    get_facebook_pages,
    request_facebook_long_lived_token,
)

from post.mastodon_post import upload_post_mastodon, upload_post_mastodon_text
from post.wordpress_post import publish_post_wordpress, publish_post_wordpress_with_featured_image, publish_post_wordpress_rest
from post.bluesky_post import publish_post_bluesky, publish_post_bluesky_text
from post.linkedin_post import publish_post_linkedin_text, publish_post_linkedin_with_image
from post.reddit_post import publish_post_reddit_text
from post.instagram_post import publish_post_instagram
from post.facebook_post import publish_post_facebook


####################### -<<[]>>-- #######################
#################### GLOBAL VARIABLES ###################
####################### -<<[]>>-- #######################


MASTER_KEY = "#OneSocial_Abrazo"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.expanduser("~"), ".onesocial")
os.makedirs(DATA_DIR, exist_ok=True)
FILE_DIRECTORY = os.path.join(DATA_DIR, "data.dat")


#########################################################


def save(tokens: list[Token]):
    """
    Input: tokens: list[Token] - A list of Token objects representing the account tokens to be saved.
    Output: None
    Description: Takes a list of Token objects, converts it to JSON format, and then encrypts the JSON data before saving it to a file.
    This process overwrites the old tokens so it is advised to load the tokens first and add the new ones to save them.
    """

    json_data = write_json(tokens)
    post_counter = get_post_counter()
    json_data = {
        "tokens": json_data,
        "post_counter": post_counter,
    }
    encrypt_process_file(json_data, FILE_DIRECTORY, MASTER_KEY)


def load():
    """
    Input: None
    Output: tokens: list[Token] - A list of Token objects representing the account tokens that were loaded from the file.
    Description: Reads the encrypted data from the file, decrypts it using the master key, and then converts the decrypted JSON 
                 data back into a list of Token objects. Finally, it prints the loaded tokens to the console.
    """

    tokens = []
    file = Path(FILE_DIRECTORY)

    if file.is_file():
        token_data = decrypt_process_file(FILE_DIRECTORY, MASTER_KEY)
        tokens = read_json(token_data)
    else:
        encrypt_process_file(
            {
                "tokens": [],
                "post_counter": 0
            },
            FILE_DIRECTORY,
            MASTER_KEY
        )
        
    return tokens


def get_accounts() -> list[list[str]]:
    """
    Input: None
    Output: tokens: list[Token] - A list of Token objects representing the account tokens that were loaded from the file.
    Description: Reads the encrypted data from the file, decrypts it using the master key, and then converts the decrypted JSON 
                 data back into a list of Token objects. Finally, it prints the loaded tokens to the console.
    """

    tokens = load()
    return account_list(tokens)


def delete_token(provider, username):
    """
    - Input: provider (str), username (str)
    - Output: bool
    - Description: Deletes the account matching provider and username from the stored tokens.
    """
    tokens = load()
    original_len = len(tokens)
    tokens = [t for t in tokens if not (t.provider == provider and t.username == username)]
    if len(tokens) == original_len:
        return False
    save(tokens)
    return True


def update_account_label(provider, username, new_label):
    """
    - Input: provider (str), username (str), new_label (str)
    - Output: True for success and False for failure
    - Description: Sets the account_label for the matching account.
    """
    tokens = load()
    found = False
    for token in tokens:
        if token.provider == provider and token.username == username:
            token.account_label = new_label.strip() if new_label.strip() else None
            found = True
            break
    if not found:
        return False
    save(tokens)
    return True


def general_upload_post(tokens, text, title, image_path=None):
    """
    - Input: 
        - account: Token - The account object containing authentication details and provider information.
        - text: str - The text content of the post to be published.
        - title: str - The title of the post.
        - image_path: Path (optional) - The file path to the image to be included in the post, if applicable.
    - Description:
        - If the provider is recognized the corresponding post function is called.
        - If the provider is not recognized, it prints a message indicating that the provider is not supported.
    """
    results = []

    for account in tokens:
        try:
            content = "\n".join(
                part for part in [title, text] if part
            )
            if account.provider == "Mastodon":
                if image_path:
                    upload_post_mastodon(title + "\n" + text, image_path, account)
                else:
                    upload_post_mastodon_text(title + "\n" + text, account)
            elif account.provider == "WordPress":
                if image_path: 
                    publish_post_wordpress_with_featured_image(account, title, text, image_path)
                else:
                    publish_post_wordpress(account, title, text)
            elif account.provider == "WordPressREST":
                publish_post_wordpress_rest(account, title, text, image_path)
            elif account.provider == "Bluesky":
                if image_path: 
                    publish_post_bluesky(account, title, text, image_path)
                else:
                    publish_post_bluesky_text(account, title, text)
            elif account.provider == "LinkedIn":
                if image_path: 
                    publish_post_linkedin_with_image(account, title + "\n" + text, image_path)
                else:
                    publish_post_linkedin_text(account, title + "\n" + text)
            elif account.provider == "Reddit":
                if image_path:
                    raise InputValueError("Reddit no soporta imagenes en esta version.")
                publish_post_reddit_text(title, text, account)
            elif account.provider == "Instagram":
                publish_post_instagram(account, title, text, image_path)
            elif account.provider == "Facebook":
                publish_post_facebook(account, title, text, image_path)
            elif account.provider == "Discord":
                from post.discord_post import send_discord_message, send_discord_message_with_image
                webhook_url = account.access_token
                if not webhook_url:
                    raise PublishError("Discord webhook URL missing")
    
                if image_path:
                    success = send_discord_message_with_image(webhook_url, content, str(image_path))
                else:
                    success = send_discord_message(webhook_url, content)
    
                if not success:
                    raise PublishError("Discord webhook failed")
            else:
                raise InputValueError(f"Proveedor {account.provider} no soportado.")

            results.append({
                'provider': account.provider,
                'success': True,
                'message': 'Publicado correctamente'
            })
            
        except Exception as e:

            results.append({
                'provider': account.provider,
                'success': False,
                'message': str(e)
            })

    return results



def save_new_account(username, client_id, client_secret, provider, tokens):
    """
    - Input: Account info, current tokens 
    - Output:Data.json updated
    - Description: This function allows for adding a new account to the existing list of accounts stored in "data.json". 
        It reads the current accounts, appends the new account, and then writes the updated list back to the file, 
        ensuring that all accounts are preserved.
    """

    new_account = Token(
        provider = provider,
        username = username,
        client_id = client_id,
        client_secret = client_secret
    )
    if username not in [token.username for token in tokens]:
        tokens.append(new_account)
    save(tokens)


def save_or_update_reddit_account(username, client_id, client_secret, subreddit, provider, tokens):
    """
    - Input: Reddit account info, current tokens
    - Description: Saves a new Reddit account or updates an existing one.
    """

    for token in tokens:
        if token.provider == provider and token.username == username:
            token.client_id = client_id
            token.client_secret = client_secret
            token.subreddit = subreddit
            save(tokens)
            return

    new_account = Token(
        provider=provider,
        username=username,
        client_id=client_id,
        client_secret=client_secret,
        subreddit=subreddit,
    )
    tokens.append(new_account)
    save(tokens)


def _copy_meta_account_fields(existing, new_token):
    existing.access_token = new_token.access_token
    existing.token_type = new_token.token_type
    existing.scope = new_token.scope
    existing.issued_at = new_token.issued_at
    existing.access_expires_at = new_token.access_expires_at
    existing.client_id = new_token.client_id
    existing.client_secret = new_token.client_secret
    existing.facebook_page_id = new_token.facebook_page_id
    existing.facebook_page_token = new_token.facebook_page_token
    existing.instagram_user_id = new_token.instagram_user_id
    existing.username = new_token.username
    existing.account_label = new_token.account_label
    existing.provider_user_id = new_token.provider_user_id
    existing.email = new_token.email


def _upsert_meta_account(tokens, new_token, provider):
    existing = None

    for token in tokens:
        if token.provider != provider:
            continue

        if token.provider_user_id and token.provider_user_id == new_token.provider_user_id:
            existing = token
            break

        if provider == "Instagram" and token.instagram_user_id and token.instagram_user_id == new_token.instagram_user_id:
            existing = token
            break

        if provider == "Facebook" and token.facebook_page_id and token.facebook_page_id == new_token.facebook_page_id:
            existing = token
            break

    if existing:
        _copy_meta_account_fields(existing, new_token)
    else:
        tokens.append(new_token)

    return tokens


def register_and_auth_wordpress(provider, username, client_id, client_secret):
    """
    Effects:
        - Initiates the authentication process for WordPress accounts by ensuring that a valid access token is  
        obtained for each WordPress account found in "data.json". It also prints the result of the authentication 
        process for each account.
    Description:
        - Reads the tokens from "data.json" and iterates through each account. For each WordPress account, it 
        calls the function to ensure that a valid access token is obtained. It then verifies the access by making 
        an API call to WordPress and prints the result of the authentication process for each account. Finally, it 
        saves the updated tokens back to "data.json".
    """
    tokens = load()
    save_new_account(username, client_id, client_secret, provider, tokens)
    tokens = load() 

    for account in tokens: 
        if account.provider != "WordPress":
            continue
        
        if account.username != username:
            continue

        print(f"\nProcesando cuenta: {account.username}")

        # Ensure token 
        ensure_wordpress_token(account)

        # Verify that the token works
        success = verify_wordpress_access(account)

        print(f"Resultado: {'OK' if success else 'FAIL'}")

    # Guardar JSON actualizado con token
    save(tokens)


def register_and_auth_reddit(provider, username, client_id, client_secret, subreddit):
    """
    Effects:
        - Initiates the authentication process for Reddit accounts and stores tokens.
    """

    tokens = load()
    save_or_update_reddit_account(username, client_id, client_secret, subreddit, provider, tokens)
    tokens = load()

    for account in tokens:
        if account.provider != "Reddit":
            continue

        if account.username != username:
            continue

        ensure_reddit_token(account)
        verify_reddit_access(account)

    save(tokens)


def setup_mastodon_account(provider, username):
    """
    Effects:
        - Initiates the authentication process for Mastodon accounts by ensuring that a valid access token is  
        obtained for each Mastodon account found in "data.json". It also prints the result of the authentication 
        process for each account.
    Description:
        - Reads the tokens from "data.json" and iterates through each account. For each Mastodon account, it 
        calls the function to ensure that a valid access token is obtained. It then verifies the credentials by making 
        an API call to Mastodon and prints the user information if successful. Finally, it saves the updated tokens 
        back to "data.json".
    Return codes:
        0: Success
        1: Get code navigator opened
        2: Not found
    """
    tokens = load()
    new_token = Token(
            provider=provider,
            username=username
        )
    
    tokens.append(new_token)
    
    for account in tokens: 
        if account.provider != "Mastodon":
            continue
        
        if account.username != username:
            continue

        # Ensure token
        token = ensure_mastodon_token(account)

        if token:
            return 0
        
        save(tokens)
        ensure_mastodon_app(account)
        auth_url = get_mastodon_auth_url(account)
        subprocess.run(f'start "" "{auth_url}"', shell=True)
        return 1

    return 2


def setup_mastodon_account_auth(code, username):
    """
    Effects:
        - Completes the authentication process for a Mastodon account by saving the obtained access token 
        after the user has authorized the app.
    Description:
        - Reads the tokens from "data.json" and iterates through each account. For each Mastodon account, 
        it checks if the access token is already present. If not, it calls the function to save the access 
        token using the provided authorization code. Finally, it saves the updated tokens back to "data.json".
    """

    tokens = load()

    for account in tokens: 
        if account.provider != "Mastodon":
            continue

        if account.username != username:
            continue

        save_mastodon_token(account, code)

    save(tokens) 


def setup_bluesky_account_auth(username, password):
    """
    - Input: username (str), password (str) 
    - Description: Completes the authentication process for a Bluesky account by saving the token.
    """

    tokens = load()
    bluesky_token = Token(
            provider="Bluesky",
            username=username,
            password=password
        )
    
    verify_bluesky_login(bluesky_token)
    
    tokens.append(bluesky_token)
    save(tokens) 


def process_image(image_path: Path) -> Path:
    """
    - Input: image_path (Path)
    - Output: full_path (Path)
    - Description:
        Calls get_image to store the image and returns the full path
        where the image was saved.
    """

    new_name = get_image(image_path)  # "post_1.jpg"
    full_path = Path(IMAGES_FOLDER) / new_name

    print(f"Ruta completa de imagen: {full_path}")

    return full_path


def save_image_from_base64(image_data: str, image_name: str) -> Path:
    """
    - Input:
        - image_data: str - base64 encoded image (with data URL prefix)
        - image_name: str - original filename (only used for logging)
    - Output: full_path (Path) to the saved JPEG file
    - Description:
        Decodes base64, verifies & converts to JPEG using Pillow,
        saves into POSTS_FOLDER with a unique post ID and .jpg extension.
    """
    if not image_data:
        raise ValueError("No image data provided")

    # 1. Decode base64 (skip the data URL header)
    if ',' in image_data:
        header, encoded = image_data.split(",", 1)
    else:
        encoded = image_data
    image_bytes = base64.b64decode(encoded)

    # 2. Open with Pillow – this handles ANY format Pillow knows
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Cannot open image: {e}")

    # 3. Convert to RGB (JPEG doesn't support transparency)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # 4. Prepare destination
    POSTS_FOLDER.mkdir(parents=True, exist_ok=True)
    post_id = get_next_post_id()
    new_name = f"post_{post_id}.jpg"
    full_path = POSTS_FOLDER / new_name

    # 5. Save as JPEG (quality 90)
    img.save(full_path, "JPEG", quality=90)

    return full_path


def setup_linkedin_account(client_id):
    """
    - Input: 
        - client_id (str): The LinkedIn application's client ID, used to 
        identify the application during the authentication process.
    - Output:
        - int: A status code indicating the result of the operation. 
        0 for success, 1 for navigator opened, 2 for error.
    - Description:
        - Initiates the authentication process for LinkedIn accounts by opening the 
        authorization URL in the user's web browser. The function constructs the 
        authorization URL using the provided client ID and a predefined redirect URI, 
        then opens this URL in the default web browser to allow the user to authorize 
        the application. The function returns a status code indicating whether the operation 
        was successful or if there was an error.
    """

    auth_url = get_linkedin_auth_url(client_id)

    subprocess.run(
        f'start "" "{auth_url}"',
        shell=True
    )

    return 1


def setup_instagram_account(client_id):
    """
    - Input:
        - client_id (str): The Instagram application's client ID, used to
        identify the application during the authentication process.
    - Output:
        - int: A status code indicating the result of the operation.
    - Description:
        - Initiates the authentication process for Instagram by opening the
        authorization URL in the user's web browser.
    """

    auth_url = get_instagram_auth_url(client_id)

    if not webbrowser.open(auth_url, new=1, autoraise=True):
        subprocess.run(
            f'start "" "{auth_url}"',
            shell=True
        )

    return 1


def setup_linkedin_account_auth(username, client_id, client_secret, code):
    """
    - Input:
        - username (str): The username of the LinkedIn account being authenticated.
        - client_id (str): The LinkedIn application's client ID, used to identify 
        the application during the authentication process.
        - client_secret (str): The LinkedIn application's client secret, used to 
        authenticate the application during the token exchange process.
        - code (str): The authorization code received from LinkedIn after the user 
        has authorized the application, used to exchange for an access token.
    - Output:
        - int: A status code indicating the result of the operation. 
        0 for success, 1 for error.
    - Description:
        - Completes the authentication process for a LinkedIn account by exchanging 
        the authorization code for an access token and saving the account information. 
        The function creates a new Token object for the LinkedIn account, populates it 
        with the obtained access token and other relevant information, and then saves 
        this information to the data file. The function returns a status code indicating 
        whether the operation was successful or if there was an error.
    """

    tokens = load()

    new_token = create_linkedin_token(client_id, client_secret, code)
    new_token.account_label = username

    exists = any(
        token.provider == "LinkedIn"
        and token.provider_user_id
        == new_token.provider_user_id
        for token in tokens
    )

    if not exists:
        tokens.append(new_token)

    save(tokens)

def save_discord_account(label: str, webhook_url: str):
    """
    Save a Discord webhook as a Token (provider="Discord").
    """
    tokens = load()
    # Remove any existing account with same label (optional)
    tokens = [t for t in tokens if not (t.provider == "Discord" and t.username == label)]
    new_token = Token(
        provider="Discord",
        username=label,                     # display label
        access_token=webhook_url,           # store the webhook URL
        account_label=label
    )
    tokens.append(new_token)
    save(tokens)

def setup_instagram_account_auth(username, client_id, client_secret, code, selected_page_id=None):
    """
    - Input:
        - username (str): Display name for the Instagram account.
        - client_id (str): Instagram application client ID.
        - client_secret (str): Instagram application client secret.
        - code (str): Authorization code returned by Instagram.
    - Description:
        - Exchanges the authorization code for tokens, enriches the account
        info, and stores it in the local token store.
    """

    tokens = load()

    new_token = create_instagram_token(
        client_id,
        client_secret,
        code,
        selected_page_id
    )
    if username:
        new_token.account_label = username

    tokens = _upsert_meta_account(tokens, new_token, "Instagram")
    save(tokens)


def setup_instagram_account_from_token(
    username,
    client_id,
    client_secret,
    access_token,
    expires_in=None,
    selected_page_id=None
):
    """
    - Input:
        - username (str): Display name for the Instagram account.
        - client_id (str): Instagram application client ID.
        - client_secret (str): Instagram application client secret.
        - access_token (str): Long-lived access token.
        - expires_in (int | str | None): Token lifetime in seconds.
        - selected_page_id (str | None): Facebook Page ID to link.
    - Description:
        - Creates or updates an Instagram account from an existing long-lived token.
    """

    tokens = load()

    new_token = build_instagram_account(
        access_token,
        client_id=client_id,
        client_secret=client_secret,
        expires_in=expires_in,
        selected_page_id=selected_page_id
    )

    if username:
        new_token.account_label = username

    tokens = _upsert_meta_account(tokens, new_token, "Instagram")
    save(tokens)


def setup_facebook_account(client_id):
    """
    Opens the Facebook OAuth URL in the browser.
    """

    auth_url = get_facebook_auth_url(client_id)

    if not webbrowser.open(auth_url, new=1, autoraise=True):
        subprocess.run(
            f'start "" "{auth_url}"',
            shell=True
        )

    return 1


def setup_facebook_account_auth(username, client_id, client_secret, code, selected_page_id=None):
    """
    Completes Facebook OAuth and persists the selected page account.
    """

    tokens = load()

    new_token = create_facebook_token(
        client_id,
        client_secret,
        code,
        selected_page_id
    )

    if username:
        new_token.account_label = username

    tokens = _upsert_meta_account(tokens, new_token, "Facebook")
    save(tokens)


def setup_facebook_account_from_token(
    username,
    client_id,
    client_secret,
    access_token,
    expires_in=None,
    selected_page_id=None
):
    """
    Creates or updates a Facebook account from an existing long-lived token.
    """

    tokens = load()

    new_token = build_facebook_account(
        access_token,
        client_id=client_id,
        client_secret=client_secret,
        expires_in=expires_in,
        selected_page_id=selected_page_id
    )

    if username:
        new_token.account_label = username

    tokens = _upsert_meta_account(tokens, new_token, "Facebook")
    save(tokens)


def list_facebook_pages(client_id, client_secret, code):
    """
    Returns available Facebook Pages for page selection.
    """

    token_data = request_facebook_long_lived_token(
        client_id,
        client_secret,
        code
    )

    access_token = token_data.get("access_token")
    if not access_token:
        raise InputValueError("No access token received.")

    accounts = get_facebook_pages(access_token)
    token_payload = {
        "access_token": access_token,
        "expires_in": token_data.get("expires_in")
    }

    return accounts, token_payload


def list_instagram_pages(client_id, client_secret, code):
    """
    - Input:
        - client_id (str): Instagram application client ID.
        - client_secret (str): Instagram application client secret.
        - code (str): Authorization code returned by Instagram.
    - Output:
        - list of available Instagram accounts with page metadata.
    - Description:
        - Exchanges the authorization code for a long-lived token and
        returns the available Instagram accounts for selection.
    """

    token_data = request_instagram_long_lived_token(
        client_id,
        client_secret,
        code
    )

    access_token = token_data.get("access_token")
    if not access_token:
        raise InputValueError("No access token received.")

    accounts = get_instagram_accounts(access_token)
    token_payload = {
        "access_token": access_token,
        "expires_in": token_data.get("expires_in")
    }

    return accounts, token_payload


def get_discord_accounts():
    """Return list of Discord accounts (label, webhook_url) for UI."""
    tokens = load()
    return [(t.username, t.access_token) for t in tokens if t.provider == "Discord"]