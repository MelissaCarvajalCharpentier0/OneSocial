"""

=============================================================================================

Name: main.py
Description: Main module for testing the functionalities of the project, including authentication and post creation on social media platforms.
Author: Josué Soto, Pamela Fernández
Date: March 2026
Version: 1.0

=============================================================================================

"""

from mastodon import Mastodon
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from models.file_manager import *
from auth.mastodon_auth import *
from auth.wordpress_auth import *

from post.functions_post import *
from post.post_on_socials import *


def test_mastodon_auth():
    """
    - Output: 
        - write_json_file(tokens, "data.json"): json - Writes the updated tokens with access tokens to the "data.json" file.
    - Description: 
        - Reads the tokens from "data.json" and iterates through each account.
        - For each Mastodon account, it ensures that a valid access token is obtained and then verifies the credentials by making an API call to Mastodon.
        - Finally, it saves the updated tokens back to "data.json".
    """

    tokens = read_json_file("data.json")

    for account in tokens:

        if account.provider != "Mastodon":
            continue

        ensure_mastodon_token(account)

        mastodon = Mastodon(
            access_token=account.access_token,
            api_base_url='https://mastodon.social'
        )

        user = mastodon.account_verify_credentials()
        print(user)

    write_json_file(tokens, "data.json")


def test_wordpress_auth():
    """
    - Output: 
        - write_json_file(tokens, "data.json"): json - Writes the updated tokens with access tokens to the "data.json" file.
    - Description: 
        - Reads the tokens from "data.json" and iterates through each account.
        - For each WordPress account, it ensures that a valid access token is obtained and then verifies the access by making an API call to WordPress.
        - Finally, it saves the updated tokens back to "data.json".
    """

    tokens = read_json_file("data.json")

    for account in tokens:

        if account.provider != "WordPress":
            continue

        print(f"\nProcesando cuenta: {account.username}")

        # Asegurar token
        ensure_wordpress_token(account)

        # Verificar que funcione
        success = verify_wordpress_access(account)

        print(f"Resultado: {'OK' if success else 'FAIL'}")

    # Guardar JSON actualizado con token
    write_json_file(tokens, "data.json")


def test_image():
    """
    - Effects: 
        - Opens a file dialog for the user to select an image file.
        - Prints the selected file path to the console.
    - Description: 
        - Uses the tkinter library to create a file dialog that allows the user to select an image file from their system.
        - The selected file path is then printed to the console. If no file is selected, it prints a message indicating that no file was chosen.
    """

    root = tk.Tk()
    root.withdraw()

    ruta_str = filedialog.askopenfilename(
        title="Selecciona un archivo",
        filetypes=[
            ("Imágenes", "*.png *.jpg *.jpeg *.JPG *.JPEG *.PNG"),
        ]
    )

    print("Ruta seleccionada:", ruta_str)

    if not ruta_str:
        print("No se seleccionó ningún archivo.")
        return

    ruta = Path(ruta_str)
    get_image(ruta)


def test_post_mastodon_with_image():
    """
    - Effects:
        - Uploads a post to Mastodon with the given text and image for each Mastodon account found in "data.json". 
    - Description: 
        - Reads the post information (text and image) and the account tokens from "data.json". For each Mastodon account, 
        it calls the function to upload a post with the specified text and image. The function ensures that the account 
        has a valid access token before uploading the media and creating the status.
    """

    info_post = create_post_content_image()
    tokens = read_json_file("data.json")

    for account in tokens:

        if account.provider != "Mastodon":
            continue
        upload_post_mastodon(info_post["text"], Path(POSTS_FOLDER) / info_post["image"], account)


def test_post_wordpress_with_image():
    """
    - Effects: 
        - Publishes a post to WordPress with the given title, content, and image for each WordPress account found in "data.json".
    - Description: 
        - Reads the post information (title, content, and image) and the account tokens from "data.json". For each WordPress account, 
        it calls the function to publish a post with the specified title, content, and image. The function ensures that the account 
        has a valid access token before uploading the media and creating the post.
    """

    info_post = create_post_title_content_image()
    tokens = read_json_file("data.json")

    for account in tokens:

        if account.provider != "WordPress":
            continue

        publish_post_wordpress_with_image(
            account,
            title=info_post["title"],
            content=info_post["content"],
            image_path=Path(POSTS_FOLDER) / info_post["image"]
        )


def test_post_mastodon_text():
    """
    - Effects:
        - Uploads a text-only post to Mastodon for each Mastodon account found in "data.json". 
    - Description: 
        - Reads the post information (text) and the account tokens from "data.json". For each Mastodon account, 
        it calls the function to upload a text-only post with the specified text. The function ensures that the account 
        has a valid access token before creating the status.
    """

    info_post = create_post_content()
    tokens = read_json_file("data.json")

    for account in tokens:

        if account.provider != "Mastodon":
            continue
        upload_post_mastodon_text(info_post["content"], account)


def test_post_wordpress_text():
    """
    - Effects: 
        - Publishes a text-only post to WordPress for each WordPress account found in "data.json".
    - Description: 
        - Reads the post information (title and content) and the account tokens from "data.json". For each WordPress account, 
        it calls the function to publish a text-only post with the specified title and content. The function ensures that the account 
        has a valid access token before creating the post.
    """

    info_post = create_post_title_content()
    tokens = read_json_file("data.json")

    for account in tokens:

        if account.provider != "WordPress":
            continue

        publish_post_wordpress(
            account,
            title=info_post["title"],
            content=info_post["content"]
        )


def test_post_wordpress_with_featured_image():
    """
    - Effects: 
        - Publishes a post to WordPress with the given title, content, and featured image for 
        each WordPress account found in "data.json".
    - Description: 
        - Reads the post information (title, content, and image) and the account tokens from "data.json". 
        For each WordPress account, it calls the function to publish a post with the specified title, content, 
        and featured image. The function ensures that the account has a valid access token before uploading the 
        media and creating the post. This function specifically tests the ability to set a featured image for the 
        post on WordPress.         
    """

    info_post = create_post_title_content_image()
    tokens = read_json_file("data.json")

    for account in tokens:

        if account.provider != "WordPress":
            continue

        publish_post_wordpress_with_featured_image(
            account,
            title=info_post["title"],
            content=info_post["content"],
            image_path=Path(POSTS_FOLDER) / info_post["image"]
        )


test_post_wordpress_with_featured_image()