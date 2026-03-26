"""

=============================================================================================

Name: test_crypto_print.py
Description: Manual test script for encrypt.py and decrypt.py using console prints.
Author: Melissa Carvajal
Date: March 2026
Version: 1.0

=============================================================================================

"""

import base64
import json
import os
import sys
import tempfile
from pathlib import Path

# Make project imports work when running this file directly.
PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from backend.crypto.encrypt import process_file as encrypt_process_file
from backend.crypto.decrypt import process_file as decrypt_process_file

COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"


def write_json_file(file_path, data):
    """
    - Input: file_path (str), data (dict or list)
    - Output: JSON file saved in the given path
    - Description: Writes JSON data with utf-8 encoding and readable indentation.
    """
    with open(file_path, "w", encoding="utf-8") as output_file:
        json.dump(data, output_file, indent=2, ensure_ascii=False)


def read_json_file(file_path):
    """
    - Input: file_path (str)
    - Output: Parsed JSON object (dict or list)
    - Description: Reads a JSON file and returns its content as Python object.
    """
    with open(file_path, "r", encoding="utf-8") as input_file:
        return json.load(input_file)


def print_test_result(test_name, was_successful, details):
    """
    - Input: test_name (str), was_successful (bool), details (str)
    - Output: Printed line in console
    - Description: Prints one readable status line for each manual test.
    """
    if was_successful:
        print(f"{COLOR_GREEN}[PASS]{COLOR_RESET} {test_name}: {details}")
    else:
        print(f"{COLOR_RED}[FAIL]{COLOR_RESET} {test_name}: {details}")


def run_simple_list_test(working_folder, password):
    """
    - Input: working_folder (str), password (str)
    - Output: True if the test passes, False otherwise
    - Description: Encrypts and decrypts a simple list in JSON and compares with original.
    """
    test_name = "Simple list JSON"
    original_data = ["facebook", "instagram", "x", "youtube"]

    source_path = os.path.join(working_folder, "simple_list_source.json")
    encrypted_path = os.path.join(working_folder, "simple_list_encrypted.json")
    decrypted_path = os.path.join(working_folder, "simple_list_decrypted.json")

    write_json_file(source_path, original_data)
    encrypt_process_file(source_path, encrypted_path, password)
    decrypt_process_file(encrypted_path, decrypted_path, password)

    decrypted_data = read_json_file(decrypted_path)

    if decrypted_data == original_data:
        print_test_result(test_name, True, "The decrypted list matches the original list.")
        return True

    print_test_result(test_name, False, "The decrypted list does not match the original list.")
    return False


def run_nested_dictionary_test(working_folder, password):
    """
    - Input: working_folder (str), password (str)
    - Output: True if the test passes, False otherwise
    - Description: Encrypts and decrypts a deeply nested dictionary and compares with original.
    """
    test_name = "Deeply nested dictionary JSON"
    original_data = {
        "account_center": {
            "owner": {
                "name": "Melissa",
                "contact": {
                    "email": "meli@example.com",
                    "phone": "+506-8888-0000"
                }
            },
            "social_networks": {
                "facebook": {
                    "username": "meli_fb",
                    "password": "fb-secret-123"
                },
                "instagram": {
                    "username": "meli_ig",
                    "password": "ig-secret-456"
                },
                "x": {
                    "username": "meli_x",
                    "password": "x-secret-789"
                }
            },
            "settings": {
                "notifications": {
                    "email": True,
                    "desktop": True
                },
                "sync": {
                    "frequency": "daily",
                    "last_run": "2026-03-26T10:30:00"
                }
            }
        }
    }

    source_path = os.path.join(working_folder, "nested_dictionary_source.json")
    encrypted_path = os.path.join(working_folder, "nested_dictionary_encrypted.json")
    decrypted_path = os.path.join(working_folder, "nested_dictionary_decrypted.json")

    write_json_file(source_path, original_data)
    encrypt_process_file(source_path, encrypted_path, password)
    decrypt_process_file(encrypted_path, decrypted_path, password)

    decrypted_data = read_json_file(decrypted_path)

    if decrypted_data == original_data:
        print_test_result(test_name, True, "The decrypted dictionary matches the original dictionary.")
        return True

    print_test_result(test_name, False, "The decrypted dictionary does not match the original dictionary.")
    return False


def run_mismatched_salt_test(working_folder, password):
    """
    - Input: working_folder (str), password (str)
    - Output: True if the test passes, False otherwise
    - Description: Encrypts a file, replaces salt with a different one, then confirms decryption fails.
    """
    test_name = "Mismatched salt JSON"
    original_data = {
        "platform": "instagram",
        "username": "meli_ig",
        "password": "ig-secret-456"
    }

    source_path = os.path.join(working_folder, "mismatched_salt_source.json")
    encrypted_path = os.path.join(working_folder, "mismatched_salt_encrypted.json")
    decrypted_path = os.path.join(working_folder, "mismatched_salt_decrypted.json")

    write_json_file(source_path, original_data)
    encrypt_process_file(source_path, encrypted_path, password)

    encrypted_payload = read_json_file(encrypted_path)
    different_salt_bytes = os.urandom(16)
    encrypted_payload["salt"] = base64.b64encode(different_salt_bytes).decode("utf-8")
    write_json_file(encrypted_path, encrypted_payload)

    try:
        decrypt_process_file(encrypted_path, decrypted_path, password)
    except Exception:
        print_test_result(test_name, True, "Decryption failed as expected because salt does not match.")
        return True

    print_test_result(test_name, False, "Decryption unexpectedly succeeded with mismatched salt.")
    return False


def run_special_characters_test(working_folder, password):
    """
    - Input: working_folder (str), password (str)
    - Output: True if the test passes, False otherwise
    - Description: Encrypts and decrypts JSON with special characters and compares with original.
    """
    test_name = "Special characters JSON"
    original_data = {
        "owner": "Melissa",
        "note": "Contrasena con simbolos: !@#$%^&*()_+-=[]{}|;:',.<>/?",
        "unicode": "Café, nandé, canción, emoji 😀",
        "path": "C:/Users/meli/Documents/OneSocial/accounts.json",
        "json_like": "{\"key\": \"value\"}"
    }

    source_path = os.path.join(working_folder, "special_characters_source.json")
    encrypted_path = os.path.join(working_folder, "special_characters_encrypted.json")
    decrypted_path = os.path.join(working_folder, "special_characters_decrypted.json")

    write_json_file(source_path, original_data)
    encrypt_process_file(source_path, encrypted_path, password)
    decrypt_process_file(encrypted_path, decrypted_path, password)

    decrypted_data = read_json_file(decrypted_path)

    if decrypted_data == original_data:
        print_test_result(test_name, True, "The decrypted data with special characters matches the original.")
        return True

    print_test_result(test_name, False, "The decrypted data with special characters does not match the original.")
    return False


def main():
    """
    - Input: None
    - Output: Exit code 0 if all tests pass, 1 otherwise
    - Description: Runs all manual crypto tests and prints a readable final summary.
    """
    print("\nStarting manual crypto tests...\n")
    password = "master-pass-for-manual-tests"

    with tempfile.TemporaryDirectory() as temporary_folder:
        test_1_result = run_simple_list_test(temporary_folder, password)
        test_2_result = run_nested_dictionary_test(temporary_folder, password)
        test_3_result = run_mismatched_salt_test(temporary_folder, password)
        test_4_result = run_special_characters_test(temporary_folder, password)

    all_tests_passed = test_1_result and test_2_result and test_3_result and test_4_result

    print("\nFinal summary:")
    print(f"- Simple list JSON: {test_1_result}")
    print(f"- Deeply nested dictionary JSON: {test_2_result}")
    print(f"- Mismatched salt JSON: {test_3_result}")
    print(f"- Special characters JSON: {test_4_result}")

    if all_tests_passed:
        print("\nAll manual crypto tests passed.")
        raise SystemExit(0)

    print("\nSome manual crypto tests failed.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
