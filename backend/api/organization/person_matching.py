"""Resolve names against every person directory maintained by UAV Center."""

from django.contrib.auth import get_user_model

from .models import PanelResponsible, Person


def _normalized_name(value: str) -> str:
    return " ".join(value.casefold().split())


def registered_person_username_index() -> dict[str, str]:
    """Return unambiguous name/username aliases from all registered person sources.

    Application users, the person-group directory, and panel responsibles form
    the shared candidate pool. If one alias points at different usernames, it is
    intentionally left unresolved rather than assigning work to the wrong person.
    """

    aliases: dict[str, set[str]] = {}

    def add_candidate(name: str, username: str) -> None:
        username = username.strip()
        if not username:
            return
        for alias in (name, username):
            normalized_alias = _normalized_name(alias)
            if normalized_alias:
                aliases.setdefault(normalized_alias, set()).add(username)

    user_model = get_user_model()
    for first_name, last_name, username in user_model.objects.values_list(
        "first_name", "last_name", "username"
    ):
        add_candidate(" ".join(part for part in (first_name, last_name) if part), username)

    group_people = Person.objects.values_list("name", "username")
    for name, username in group_people:
        add_candidate(name, username)

    for name, username in PanelResponsible.objects.values_list("name", "username"):
        add_candidate(name, username)

    return {
        alias: next(iter(usernames)) for alias, usernames in aliases.items() if len(usernames) == 1
    }


def match_registered_person_username(name: str, username_index: dict[str, str]) -> str | None:
    """Resolve one extracted person name through a prebuilt candidate index."""

    return username_index.get(_normalized_name(name))
