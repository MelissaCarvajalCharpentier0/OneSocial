"""

=============================================================================================

Name: main.py
Description: Main module for testing the functionalities of the project, including authentication and post creation on social media platforms.
Author: Josué Soto, Pamela Fernández, Melissa Carvajal
Date: March 2026
Version: 1.1

=============================================================================================

"""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from mastodon import Mastodon
import webbrowser

from models.file_manager import *
from auth.mastodon_auth import *
from auth.wordpress_auth import *

from post.functions_post import *
from post.post_on_socials import *

from crypto.encrypt import process_file as encrypt_process_file
from crypto.decrypt import process_file as decrypt_process_file



MASTER_KEY = "ASDFADFASFASDASFADFFASD"
FILE_DIRECTORY = "data/data.dat"


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


def general_upload_post(tokens, text, title=None, image_path=None):
    """
    - Input: 
        - account: Account - The account object containing authentication details and provider information.
        - text: str - The text content of the post to be published.
        - title: str (optional) - The title of the post, if applicable.
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
                upload_post_mastodon(text, image_path, account)
            else:
                upload_post_mastodon_text(text, account)
        elif account.provider == "WordPress":
            if image_path: 
                publish_post_wordpress_with_featured_image(account, title, text, image_path)
            else:
                publish_post_wordpress(account, title, text)
    else:
        print(f"Proveedor {account.provider} no soportado.")    


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
    save_new_account(provider, username, client_id, client_secret)
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


def setup_mastodon_account(provider, username, password):
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
    """

    save_new_account(provider, username, password)
    tokens = load()

    for account in tokens: 
        if account.provider != "Mastodon":
            continue
        
        if account.username != username:
            continue

        # Ensure app
        ensure_mastodon_app()

        # Ensure token
        token = ensure_mastodon_token(account)

        if token:
            save(tokens)
            return True

        auth_url = get_mastodon_auth_url(account)
        webbrowser.open(auth_url)

    save(tokens)
    return False


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