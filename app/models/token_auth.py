"""

=============================================================================================

Name: token_auth.py
Description: Module for general Token structure for authentification
Author: Josué Soto
Date: March 2026
Version: 1.1

=============================================================================================

"""

from dataclasses import dataclass
from typing import Optional





@dataclass
class Token:

    provider: str
    provider_user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    account_label: Optional[str] = None

    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None

    issued_at: Optional[str] = None
    access_expires_at: Optional[str] = None
    refresh_expires_at: Optional[str] = None

    base_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    site_id: Optional[str] = None



    def to_dict(self):
        """
    - Input: 
        - data: list[Token] - List of Token objects for the credentials of each social network
        - filename: str - The name of the JSON file to write the data to
    - Effects: 
        - Data from "data" written to a json file specified by filename
    - Description: 
        - Writes the data of the social networks' tokens to a unified json file 
    """


        return {
            "provider": self.provider,
            "provider_user_id": self.provider_user_id,
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "account_label": self.account_label,

            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "scope": self.scope,

            "issued_at": self.issued_at,
            "access_expires_at": self.access_expires_at,
            "refresh_expires_at": self.refresh_expires_at,

            "base_url": self.base_url,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "site_id": self.site_id
        }


"""
# Ejemplo de Implementacion base de tokens (heredan de Token)
@dataclass
class Token_ejemplo(Token):

    campo_ejemplo: str = ""


    def to_dict(self):
        data = super().to_dict()
        data["campo_ejemplo"] = self.campo_ejemplo

        return data
"""
