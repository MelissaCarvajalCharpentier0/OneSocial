"""

=============================================================================================

Name: controller.py
Description: Main module for testing the functionalities of the project, including authentication and post creation on social media platforms.
Author: Josué Soto, Pamela Fernández, Melissa Carvajal
Date: April 2026
Version: 1.2

=============================================================================================

"""

from pathlib import Path
import base64
import binascii
import subprocess

from models.token_manager import *
from auth.mastodon_auth import *
from auth.wordpress_auth import *
from auth.bluesky_auth import *
from models.app_errors import InputValueError

from post.post_on_socials import *

from models.crypto import encrypt_process_file, decrypt_process_file



MASTER_KEY = "#OneSocial_Abrazo"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.expanduser("~"), ".onesocial")
os.makedirs(DATA_DIR, exist_ok=True)
FILE_DIRECTORY = os.path.join(DATA_DIR, "data.dat")







def save(tokens: list[Token]):
    """
    Input: tokens: list[Token] - A list of Token objects representing the account tokens to be saved.
    Output: None
    Description: Takes a list of Token objects, converts it to JSON format, and then encrypts the JSON data before saving it to a file.
    """

    json_data = write_json(tokens)
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

    return tokens


def get_accounts() -> list[str, str]:
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
    - Output: dict with success and message
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
        - Determines the social media platform based on the account's provider and calls the appropriate function to upload the post.
        - If the provider is "Mastodon", it calls the upload_post_mastodon function with the text and image path.
        - If the provider is "WordPress", it calls the publish_post_wordpress_with_image function with the account, text as title, text as content, and image path.
        - If the provider is not recognized, it prints a message indicating that the provider is not supported.
    """

    for account in tokens:
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
        elif account.provider == "Bluesky":
            if image_path: 
                publish_post_bluesky(account, title, text, image_path)
            else:
                publish_post_bluesky_text(account, title, text)
        else:
            raise InputValueError(f"Proveedor {account.provider} no soportado.")   


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
    full_path = Path(POSTS_FOLDER) / new_name

    print(f"Ruta completa de imagen: {full_path}")

    return full_path


def save_image_from_base64(image_data: str, image_name: str) -> Path:
    """
    - Input:
        - image_data: str - A string containing the base64 encoded image data, typically in the format 
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
        - image_name: str - The original name of the image file, used to determine the file extension.  
    - Output:
        - full_path: Path - The file path where the decoded image has been saved locally.
    - Description:
        - This function takes a base64 encoded image string and the original image name, decodes the image data, 
        and saves it to a local file. It first validates the image format based on the file extension, then creates
        a new file name using a unique post ID. The decoded image data is written to a new file in the designated
        posts folder, and the full path to the saved image is returned.
    """

    if not image_data:
        raise InputValueError("No image data provided")

    try:
        header, encoded = image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
    except (ValueError, binascii.Error) as error:
        raise InputValueError("Invalid base64 image payload") from error

    suffix = Path(image_name).suffix.lower()
    if suffix not in IMAGE_FORMATS:
        raise InputValueError(f"Formato inválido: {suffix}")

    destiny = Path(POSTS_FOLDER)
    destiny.mkdir(parents=True, exist_ok=True)

    post_id = get_next_post_id()
    new_name = f"post_{post_id}{suffix}"

    full_path = destiny / new_name

    with open(full_path, "wb") as f:
        f.write(image_bytes)

    return full_path