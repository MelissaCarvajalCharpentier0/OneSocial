"""
=============================================================================================

Name: app_errors.py
Description: Errors for the app
Author: Melissa Carvajal
Date: April 2026
Version: 1.0


Note:
If you want to add new errors, just need to add a new class and the type of exception you are 
referencing (e.g Type error)
=============================================================================================
"""

from enum import Enum


class ErrorCategory(str, Enum):
    USER_INPUT = "user_input"
    API = "api"
    TOKEN_STORAGE = "token_storage"
    PUBLISH = "publish"
    CRYPTOGRAPHY = "cryptography"
    UNKNOWN = "unknown"


class InputValueError(TypeError):
    category = ErrorCategory.USER_INPUT


class ApiError(RuntimeError):
    category = ErrorCategory.API


class TokenStorageError(OSError):
    category = ErrorCategory.TOKEN_STORAGE


class PublishError(RuntimeError):
    category = ErrorCategory.PUBLISH

class CryptographyError(RuntimeError):
    category = ErrorCategory.CRYPTOGRAPHY
