def format_user_display_name(user):
    """Format an actor for UI audit records, falling back to the username."""

    if user is None:
        return None

    username = str(getattr(user, "username", "") or "").strip()
    first_name = str(getattr(user, "first_name", "") or "").strip()
    last_name = str(getattr(user, "last_name", "") or "").strip()
    if first_name and last_name:
        full_name = f"{first_name} {last_name}"
        return f"{full_name} ({username})" if username else full_name
    return username or None
