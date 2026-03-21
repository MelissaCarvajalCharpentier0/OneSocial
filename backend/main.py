from mastodon import Mastodon
from models.file_manager import *
from auth.mastodon_auth import *
from auth.wordpress_auth import *


def test_mastodon_auth():
    tokens = read_json_file("data.json")

    for account in tokens:

        if account.provider != "Mastodon":
            continue

        ensure_mastodon_token(account)

        mastodon = Mastodon(
            access_token=account.access_token,
            api_base_url='https://mastodon.social'
        )

        user = mastodon.account_verify_credentials()
        print(user)

    write_json_file(tokens, "data.json")


def test_wordpress_auth():
    tokens = read_json_file("data.json")

    for account in tokens:

        if account.provider != "WordPress":
            continue

        print(f"\nProcesando cuenta: {account.username}")

        # Asegurar token
        ensure_wordpress_token(account)

        # Verificar que funcione
        success = verify_wordpress_access(account)

        print(f"Resultado: {'OK' if success else 'FAIL'}")

    # Guardar JSON actualizado con token
    write_json_file(tokens, "data.json")

test_wordpress_auth()