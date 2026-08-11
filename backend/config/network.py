"""Validation policy for operator-configured HTTP service URLs and browser origins."""

from ipaddress import ip_address
from urllib.parse import urlsplit


class InvalidServiceUrl(ValueError):
    """Raised when an outbound integration URL is unsafe or malformed."""


def _is_local_hostname(hostname: str) -> bool:
    normalized = hostname.rstrip(".").casefold()
    if normalized == "localhost" or normalized.endswith(".localhost"):
        return True
    try:
        address = ip_address(normalized)
    except ValueError:
        return False
    return address.is_loopback or address.is_private or address.is_link_local


def validated_http_url(
    value: str,
    *,
    setting_name: str = "service URL",
    require_local: bool = False,
    require_https: bool = False,
    require_https_for_remote: bool = False,
) -> str:
    """Return a normalized HTTP(S) URL that satisfies the requested trust policy."""

    candidate = str(value or "").strip()
    try:
        parsed = urlsplit(candidate)
        _ = parsed.port
    except ValueError as exc:
        raise InvalidServiceUrl(f"{setting_name} geçerli bir URL olmalıdır.") from exc

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise InvalidServiceUrl(f"{setting_name} yalnızca http veya https kullanmalıdır.")
    if parsed.username is not None or parsed.password is not None:
        raise InvalidServiceUrl(f"{setting_name} kullanıcı bilgisi içermemelidir.")
    if parsed.fragment:
        raise InvalidServiceUrl(f"{setting_name} URL fragment içermemelidir.")

    is_local = _is_local_hostname(parsed.hostname)
    if require_local and not is_local:
        raise InvalidServiceUrl(
            f"{setting_name} varsayılan olarak yalnız loopback/private host kullanabilir."
        )
    if require_https and parsed.scheme != "https":
        raise InvalidServiceUrl(f"{setting_name} HTTPS kullanmalıdır.")
    if require_https_for_remote and not is_local and parsed.scheme != "https":
        raise InvalidServiceUrl(f"Uzak {setting_name} HTTPS kullanmalıdır.")
    return candidate


def validated_browser_origin(
    value: str,
    *,
    setting_name: str,
    require_https: bool = False,
) -> str:
    """Validate a scheme+authority browser origin without path, query, or credentials."""

    candidate = validated_http_url(
        value,
        setting_name=setting_name,
        require_https=require_https,
    )
    parsed = urlsplit(candidate)
    if parsed.path not in {"", "/"} or parsed.query:
        raise InvalidServiceUrl(f"{setting_name} yalnızca origin içermelidir; path/query içeremez.")
    return f"{parsed.scheme}://{parsed.netloc}"
