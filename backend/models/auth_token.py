# auth_token.py
# Token structure for social networks' credentials


# Author: Josue Daniel Soto Gonzalez
# Created on: 20/03/2026
# Updated by: ---
# Updated on: ---




from dataclasses import dataclass
from typing import Optional





@dataclass
class Token:

    provider: str
    provider_user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    account_label: Optional[str] = None

    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None

    issued_at: Optional[str] = None
    access_expires_at: Optional[str] = None
    refresh_expires_at: Optional[str] = None

    base_url: Optional[str] = None



    def to_dict(self):
        return {
            "provider": self.provider,
            "provider_user_id": self.provider_user_id,
            "username": self.username,
            "email": self.email,
            "account_label": self.account_label,

            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "scope": self.scope,

            "issued_at": self.issued_at,
            "access_expires_at": self.access_expires_at,
            "refresh_expires_at": self.refresh_expires_at,

            "base_url": self.base_url
        }



# Implementacion base de tokens
@dataclass
class Token_ejemplo(Token):

    campo_ejemplo: str = ""


    def to_dict(self):
        data = super().to_dict()
        data["campo_ejemplo"] = self.campo_ejemplo

        raise NotImplementedError("Token no implementado")
        #return data


