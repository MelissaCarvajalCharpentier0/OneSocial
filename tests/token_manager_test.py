"""

=============================================================================================

Name: token_manager_test.py
Description: Automated tests for token_manager.py using pytest assertions.
Author: Josué Soto
Date: March 2026
Version: 1.1

=============================================================================================

"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app"

if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

from models.token_auth import Token
from models.token_manager import read_json, write_json


def build_tokens() -> list[Token]:
    """
    - Input:
        - None
    - Output:
        - list[Token] - Sample token list for test scenarios.
    - Description:
        - Builds deterministic sample token objects to validate serialization and deserialization.
    """

    return [
        Token(
            provider="github",
            provider_user_id="123",
            username="alice",
            email="alice@example.com",
            access_token="abc123",
        ),
        Token(
            provider="google",
            provider_user_id="456",
            username="bob",
            email="bob@example.com",
            refresh_token="refresh456",
        ),
    ]


def test_write_json_returns_serializable_list() -> None:
    """
    - Input:
        - None
    - Output:
        - None
    - Description:
        - Verifies that write_json returns a list of dictionaries ready for JSON serialization.
    """

    tokens = build_tokens()
    result = write_json(tokens)

    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert result[0]["provider"] == "github"
    assert result[1]["email"] == "bob@example.com"


def test_read_json_restores_token_instances() -> None:
    """
    - Input:
        - None
    - Output:
        - None
    - Description:
        - Verifies that read_json reconstructs Token instances and preserves key values.
    """

    serialized = write_json(build_tokens())
    restored = read_json(serialized)

    assert isinstance(restored, list)
    assert isinstance(restored[0], Token)
    assert restored[0].provider == "github"
    assert restored[1].email == "bob@example.com"


def test_write_json_raises_type_error_for_non_list_input() -> None:
    """
    - Input:
        - None
    - Output:
        - None
    - Description:
        - Ensures write_json validates input type and raises TypeError for invalid payloads.
    """

    with pytest.raises(TypeError):
        write_json("invalid")


def test_read_json_raises_type_error_for_non_list_input() -> None:
    """
    - Input:
        - None
    - Output:
        - None
    - Description:
        - Ensures read_json validates input type and raises TypeError for invalid payloads.
    """

    with pytest.raises(TypeError):
        read_json({"not": "a list"})
