from typing import Any

from django.contrib.auth import get_user_model

from d20.models import Character, User

REGISTRATION_DATA = {
    "username": "new_player",
    "password1": "user12test",
    "password2": "user12test",
    "first_name": "Test first",
    "last_name": "Test last",
    "email": "new_player@example.com",
}


def create_user(username: str, **extra_fields: Any) -> User:
    return get_user_model().objects.create_user(username=username, **extra_fields)


def create_character(owner: User, name: str = "Gimli") -> Character:
    return Character.objects.create(
        name=name,
        character_class=Character.CharacterClass.FIGHTER,
        ancestry=Character.Ancestry.DWARF,
        owner=owner,
    )
