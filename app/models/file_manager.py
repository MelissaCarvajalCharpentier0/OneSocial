"""

=============================================================================================

Name: file_manager.py
Description: Module for managing file operations in the project.
Author: Josué Soto, Pamela Fernández
Date: March 2026
Version: 1.4

=============================================================================================

"""

import json
from pathlib import Path
import shutil

from models.token_auth import Token

ENCODING = "utf-8"
INDENT = 2

IMAGE_FORMATS = (".png", ".jpg", ".jpeg")
POSTS_FOLDER = "post/img_posts"
COUNTER_FILE = Path("models/post_counter.txt")


def write_json_file(data: list[Token], filename:str = "data.json"):
    """
    - Input: data (list[Token]), filename (str)
    - Effects: Data from "data" written to a json file specified by filename
    - Description: Writes the data of the social networks' tokens to a unified json file
    """

    if not isinstance(filename, str):
        raise TypeError("Filename invalid.")
    if not isinstance(data, list):
        raise TypeError("Data invalid.")
    for token in data:
        if not isinstance(token, Token):
            raise TypeError("Token invalid.")

    json_data = [token.to_dict() for token in data]


    with open(filename, "w", encoding=ENCODING) as file:
        json.dump(json_data, file, indent=INDENT, ensure_ascii=False)



def write_json(data: list[Token]):
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



def read_json_file(filename:str = "data.json") -> list[Token]:
    """
    - Input: filename (str)
    - Output: tokens (list[Token])
    - Description: Reads the data of the social networks' tokens from a unified json file and returns a list of valid Token objects

    < Note > 
    If an invalid token or value is read it will be ignored  
    """

    if not isinstance(filename, str):
        raise TypeError("Filename invalid.")
    
    with open(filename, "r", encoding=ENCODING) as file:
        json_data = json.load(file)


    if not isinstance(json_data, list):
        raise TypeError("JSON file data invalid.")
    
    tokens = []
    for token_data in json_data:
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

    current = int(COUNTER_FILE.read_text())
    next_id = current + 1

    COUNTER_FILE.write_text(str(next_id))

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
    
    destiny = Path(POSTS_FOLDER)
    destiny.mkdir(parents=True, exist_ok=True)

    post_id = get_next_post_id()
    new_name = f"post_{post_id}{image_path.suffix.lower()}"
    shutil.copy(image_path, destiny / new_name)

    print(f"Imagen guardada como: {new_name}")
    return new_name