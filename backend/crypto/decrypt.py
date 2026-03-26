"""

=============================================================================================

Name: decrypt.py
Description: Module for decrypting JSON files using the Fernet symmetric encryption method.
Author: Melissa Carvajal
Date: MArch 2026
Version: 1.0


Docuemntation:
- https://cryptography.io/en/latest/fernet/#fernet-symmetric-encryption 
- https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#cryptography.hazmat.primitives.kdf.hkdf.HKDF.extract
- https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#scrypt

Concepts:
- Fernet guarantees that a message encrypted using it cannot be manipulated or read without the 
  key. Fernet is an implementation of symmetric (also known as “secret key”) authenticated cryptography. 
  Fernet also has support for implementing key rotation via MultiFernet.
- A salt. Randomizes the KDF’s output. Optional, but highly recommended. Ideally as many bits of entropy 
  as the security level of the hash: often that means cryptographically random and as long as the hash output.
- A Key Derivation Function (KDF) is a cryptographic algorithm that generates secure keys from a primary secret 
 like a password or master key
- Scrypt is a KDF designed for password storage by Colin Percival to be resistant against hardware-assisted 
  attackers by having a tunable memory cost. 

=============================================================================================

"""


import json
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


def derive_key(password: bytes, salt: bytes) -> bytes:
    """
    - Input: password (bytes), salt (bytes)
    - Output: derived key (bytes)
    - Description: Derives a key from the given password and salt using the Scrypt key
    """
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
    )
    return base64.urlsafe_b64encode(kdf.derive(password))


def decrypt_value(value, fernet):
    """
    - Input: value (str or other), fernet (Fernet object)
    - Output: decrypted value (str or original value)
    - Description: Decrypts the value if it's a string, otherwise returns it unchanged.
    """
    if isinstance(value, str):
        return fernet.decrypt(value.encode()).decode()
    return value  


def decrypt_json(data, fernet):
    """
    - Input: data (dict or other), fernet (Fernet object)
    - Output: decrypted data (dict or original value)
    - Description: Recursively decrypts all string values in the JSON data using the provided Fernet
    """
    if isinstance(data, dict):
        decrypted_dict = {}
        for key, value in data.items():
            decrypted_dict[key] = decrypt_json(value, fernet)
        return decrypted_dict

    if isinstance(data, list):
        return [decrypt_json(item, fernet) for item in data]

    return decrypt_value(data, fernet)


def process_file(input_path, output_path, password):
    """
    - Input: input_path (str), output_path (str), password (str)
    - Output: Decrypted JSON file saved to output_path
    - Description: Reads a JSON file, decrypts its contents using the provided password, and
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)

    if not isinstance(payload, dict) or 'salt' not in payload or 'data' not in payload:
        raise ValueError("Invalid encrypted file format. Expected keys: 'salt' and 'data'.")

    salt = base64.b64decode(payload['salt'])
    key = derive_key(password.encode('utf-8'), salt)
    fernet = Fernet(key)

    try:
        decrypted_data = decrypt_json(payload['data'], fernet)
    except InvalidToken:
        raise ValueError("Incorrect password or corrupted encrypted data.") 

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(decrypted_data, f, indent=4)