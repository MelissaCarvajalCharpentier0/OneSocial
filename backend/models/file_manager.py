# file_manager.py
# File manager for the project to write json files and read json files


# Author: Josue Daniel Soto Gonzalez
# Created on: 20/03/2026
# Updated by: Josue Daniel Soto Gonzalez
# Updated on: 21/03/2026



import shutil
import json
from pathlib import Path

from models.auth_token import Token



ENCODING = "utf-8"
INDENT = 2

IMAGE_FORMATS = (".png", ".jpg", ".jpeg")
POSTS_FOLDER = "posts"










def write_json_file(data: list[Token], filename:str = "data.json"):

    # Writes the data of the social networks' tokens to a unified json file

    # Inputs
    # filename: String of the filename
    # data: List of Token objects for the credentials of each social network
    # Effects
    # Data from "data" written to a json file specified by filename


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



def read_json_file(filename:str = "data.json") -> list[Token]:

    # Writes the data of the social networks' tokens to a unified json file

    # Inputs
    # filename: String of the filename
    # Outputs
    # list[Token]: List of valid tokens read in json file
    # [!] Note: If an invalid token is read it will be ignored


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
            


def get_image(image_path: Path):

    # Copies an image for publication into a temporary file

    # Inputs
    # image_path: String of the path for the image file
    # Effects
    # Image will be copied and stored locally for publication in the folder specified by POSTS_FOLDER


    if not isinstance(image_path, Path):
        raise TypeError("Image path invalid.")
    
    if image_path.suffix.lower() not in IMAGE_FORMATS:
        raise TypeError(f"Invalid image format (valid formats: {IMAGE_FORMATS})")
    
    destiny = Path(POSTS_FOLDER)
    destiny.mkdir(parents=True, exist_ok=True)
    shutil.copy(image_path, destiny / image_path.name)


