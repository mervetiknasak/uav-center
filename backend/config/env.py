import os

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def load_env_file(path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError(
        f"{name} geçerli bir boolean olmalı: {', '.join(sorted(TRUE_VALUES | FALSE_VALUES))}"
    )


def env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} geçerli bir tam sayı olmalı.") from exc


def env_list(name, default=None):
    value = os.getenv(name)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def env_choice(name, *, choices, default):
    value = os.getenv(name, default).strip().lower()
    if value not in choices:
        allowed = ", ".join(sorted(choices))
        raise ValueError(f"{name} şu değerlerden biri olmalı: {allowed}")
    return value
