from file_manager import *

tokens_to_save = [
    Token(
        provider="github",
        provider_user_id="123",
        username="alice",
        email="alice@example.com",
        access_token="abc123"
    ),
    Token(
        provider="google",
        provider_user_id="456",
        username="bob",
        email="bob@example.com",
        refresh_token="refresh456"
    )
]

write_json_file(tokens_to_save, "test.json")

loaded_tokens = read_json_file("test.json")

print(loaded_tokens)
print(type(loaded_tokens))
print(type(loaded_tokens[0]))
print(loaded_tokens[0].provider)
print(loaded_tokens[1].email)
