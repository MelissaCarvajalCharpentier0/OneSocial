"""

=============================================================================================

Name: token_manager.py
Description: Module for managing file operations in the project.
Author: Josué Soto, Pamela Fernández, Melissa Carvajal
Date: Abril 2026
Version: 2.0

=============================================================================================

"""

import json
import os
from pathlib import Path
import shutil

from models.token_auth import Token

ENCODING = "utf-8"
INDENT = 2

BASE_DIR = Path(os.path.expanduser("~")) / ".onesocial"
BASE_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_FORMATS = (".png", ".jpg", ".jpeg")
POSTS_FOLDER = BASE_DIR / "posts"
POSTS_FOLDER.mkdir(parents=True, exist_ok=True)

COUNTER_FILE = BASE_DIR / "post_counter.txt"

def write_json(data: list[Token]) -> json:
    """
    - Input: data (list[Token])
    - Output: Data from "data" written to a json object for direct dump with json library
    - Description: Writes the data of the social networks' tokens to a unified json object
    """

    if not isinstance(data, list):
        raise TypeError("Data invalid.")
    for token in data:
        if not isinstance(token, Token):
            raise TypeError("Token invalid.")

    return [token.to_dict() for token in data]

def read_json(json_file:list) -> list[Token]:
    """
    - Input: json_file (dict)
    - Output: tokens (list[Token])
    - Description: Reads the data of the social networks' tokens from a unified json file and returns a list of valid Token objects

    < Note > 
    If an invalid token or value is read it will be ignored  
    """

    if not isinstance(json_file, list):
        raise TypeError("Json_file invalid.")
    
    tokens = []
    for token_data in json_file:
        if isinstance(token_data, dict):
            tokens.append(Token(**token_data))

    return tokens

def get_next_post_id() -> int:
    """
    - Output: next_id (int)
    - Effects: Reads the data of the social networks' tokens from a unified json file and returns a list of valid Token objects
    - Description: Retrieves the next post ID by reading and updating a counter stored in a text file. This ensures that each post has a unique identifier.
    """

    if not COUNTER_FILE.exists():
        COUNTER_FILE.write_text("0")

    current = int(COUNTER_FILE.read_text(encoding=ENCODING).strip())
    next_id = current + 1

    COUNTER_FILE.write_text(str(next_id), encoding=ENCODING)

    return next_id

def get_image(image_path: Path) -> str:
    """
    - Input: image_path (Path)
    - Output: new_name (str)
    - Effects: The image will be copied and stored locally for publication in the folder specified by POSTS_FOLDER
    - Description: Validates the image path and format, then copies the image to a designated folder with a new name based on a unique post ID. Returns the new name of the copied image file.
    """

    if not isinstance(image_path, Path):
        raise TypeError("Image path invalid.")
    
    if image_path.suffix.lower() not in IMAGE_FORMATS:
        raise TypeError(f"Invalid image format (valid formats: {IMAGE_FORMATS})")
    
    POSTS_FOLDER.mkdir(parents=True, exist_ok=True)

    post_id = get_next_post_id()
    new_name = f"post_{post_id}{image_path.suffix.lower()}"
    shutil.copy(image_path, POSTS_FOLDER / new_name)

    print(f"Imagen guardada como: {new_name}")
    return new_name

def account_list(raw_tokens: list[Token]) -> list[list[str]]:
    """
    - Input: raw_tokens (list[Token])
    - Output: accounts (list[str, str])
    - Description: Extracts the social network and username and outputs them in a list with the format ["social", "username"]
    """

    if not isinstance(raw_tokens, list):
        raise TypeError("Tokens got are invalid.")
    for token in raw_tokens:
        if not isinstance(token, Token):
            raise TypeError("Invalid token found in tokens.")

    accounts = []
    for token in raw_tokens:
        if token.provider != "" and token.username not in (None, ""):
            accounts.append({
                "provider": token.provider,
                "username": token.username,
                "display_name": token.account_label,
                "email": token.email,
            })

    return accounts

def filter_tokens_by_account(raw_tokens: list[Token], accounts: list[list[str]]) -> list[Token]:
    """
    - Input: raw_tokens (list[Token]), accounts (list[list[str, str]])
    - Output: filtered_tokens (list[Token])
    - Description: Extracts the tokens that match the accounts in the list (with format ["social", "username"])
    """

    if not isinstance(raw_tokens, list):
        raise TypeError("Tokens got are invalid.")
    for token in raw_tokens:
        if not isinstance(token, Token):
            raise TypeError("Invalid token found in tokens.")
        
    if not isinstance(accounts, list):
        raise TypeError("The accounts should be a list of accounts.")
    for account in accounts:
        if not isinstance(account, list) or len(account) != 2:
            raise TypeError("Invalid account found. Each account must be a list")
        if not isinstance(account[0], str) or not isinstance(account[1], str):
            raise TypeError("Invalid account found. Each account must have a social network provider AND a username as strings")
        
    filtered_tokens = []
    for token in raw_tokens:
        for account in accounts:
            if token.provider == account[0] and token.username == account[1]:
                filtered_tokens.append(token)
                continue

    return filtered_tokens

