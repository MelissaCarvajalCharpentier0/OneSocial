"""

=============================================================================================

Name: test_crypto_print.py
Description: Automated tests for crypto.py using pytest assertions.
Author: Melissa Carvajal
Date: March 2026
Version: 1.1

=============================================================================================

"""

import base64
import json
import os
import sys
from pathlib import Path

import pytest

# Make project imports work when running tests directly.
PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from app.crypto import decrypt_process_file, encrypt_process_file


def write_json_file(file_path: Path, data: dict | list) -> None:
    """
    - Input:
        - file_path: Path - Output JSON file path.
        - data: dict | list - JSON-compatible data to write.
    - Output:
        - None
    - Description:
        - Writes JSON data with utf-8 encoding and indentation to the given path.
    """

    with open(file_path, "w", encoding="utf-8") as output_file:
        json.dump(data, output_file, indent=2, ensure_ascii=False)


def read_json_file(file_path: Path) -> dict | list:
    """
    - Input:
        - file_path: Path - JSON file path to read.
    - Output:
        - dict | list - Parsed JSON payload.
    - Description:
        - Reads a JSON file from disk and returns the parsed Python structure.
    """

    with open(file_path, "r", encoding="utf-8") as input_file:
        return json.load(input_file)


def test_encrypt_decrypt_simple_list(tmp_path: Path) -> None:
    """
    - Input:
        - tmp_path: Path - Temporary test directory from pytest fixture.
    - Output:
        - None
    - Description:
        - Encrypts and decrypts a simple list payload and verifies content integrity.
    """

    password = "master-pass-for-tests"
    original_data = ["facebook", "instagram", "x", "youtube"]

    encrypted_path = tmp_path / "simple_list_encrypted.json"
    encrypt_process_file(original_data, encrypted_path, password)
    decrypted_data = decrypt_process_file(encrypted_path, password)

    assert decrypted_data == original_data


def test_encrypt_decrypt_nested_dictionary(tmp_path: Path) -> None:
    """
    - Input:
        - tmp_path: Path - Temporary test directory from pytest fixture.
    - Output:
        - None
    - Description:
        - Encrypts and decrypts a deeply nested dictionary and verifies exact equality.
    """

    password = "master-pass-for-tests"
    original_data = {
        "account_center": {
            "owner": {
                "name": "Melissa",
                "contact": {
                    "email": "meli@example.com",
                    "phone": "+506-8888-0000",
                },
            },
            "social_networks": {
                "facebook": {
                    "username": "meli_fb",
                    "password": "fb-secret-123",
                },
                "instagram": {
                    "username": "meli_ig",
                    "password": "ig-secret-456",
                },
                "x": {
                    "username": "meli_x",
                    "password": "x-secret-789",
                },
            },
            "settings": {
                "notifications": {
                    "email": True,
                    "desktop": True,
                },
                "sync": {
                    "frequency": "daily",
                    "last_run": "2026-03-26T10:30:00",
                },
            },
        }
    }

    encrypted_path = tmp_path / "nested_dictionary_encrypted.json"
    encrypt_process_file(original_data, encrypted_path, password)
    decrypted_data = decrypt_process_file(encrypted_path, password)

    assert decrypted_data == original_data


def test_mismatched_salt_raises_error(tmp_path: Path) -> None:
    """
    - Input:
        - tmp_path: Path - Temporary test directory from pytest fixture.
    - Output:
        - None
    - Description:
        - Replaces stored salt after encryption and verifies decryption fails with ValueError.
    """

    password = "master-pass-for-tests"
    original_data = {
        "platform": "instagram",
        "username": "meli_ig",
        "password": "ig-secret-456",
    }

    encrypted_path = tmp_path / "mismatched_salt_encrypted.json"
    encrypt_process_file(original_data, encrypted_path, password)

    encrypted_payload = read_json_file(encrypted_path)
    different_salt_bytes = os.urandom(16)
    encrypted_payload["salt"] = base64.b64encode(different_salt_bytes).decode("utf-8")
    write_json_file(encrypted_path, encrypted_payload)

    with pytest.raises(ValueError):
        decrypt_process_file(encrypted_path, password)


def test_encrypt_decrypt_special_characters(tmp_path: Path) -> None:
    """
    - Input:
        - tmp_path: Path - Temporary test directory from pytest fixture.
    - Output:
        - None
    - Description:
        - Encrypts and decrypts payload containing symbols, accents, and emoji.
    """

    password = "master-pass-for-tests"
    original_data = {
        "owner": "Melissa",
        "note": "Contrasena con simbolos: !@#$%^&*()_+-=[]{}|;:',.<>/?",
        "unicode": "Café, nandé, canción, emoji 😀",
        "path": "C:/Users/meli/Documents/OneSocial/accounts.json",
        "json_like": "{\"key\": \"value\"}",
    }

    encrypted_path = tmp_path / "special_characters_encrypted.json"
    encrypt_process_file(original_data, encrypted_path, password)
    decrypted_data = decrypt_process_file(encrypted_path, password)

    assert decrypted_data == original_data
