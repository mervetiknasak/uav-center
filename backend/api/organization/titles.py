ORGANIZATION_TITLES = ("CVE", "AS", "PSK", "Şef", "IPT")


def normalize_organization_titles(values):
    """Return known titles once and in their catalog order."""

    selected = set(values)
    return [title for title in ORGANIZATION_TITLES if title in selected]


def parse_organization_title(value):
    """Read the legacy comma-separated title field without exposing unknown values."""

    if not value:
        return []
    values = [part.strip() for part in value.split(",") if part.strip()]
    if any(value not in ORGANIZATION_TITLES for value in values):
        return []
    return normalize_organization_titles(values)


def format_organization_titles(values):
    return ", ".join(normalize_organization_titles(values))
