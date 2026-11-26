from urllib.parse import urlsplit


MAX_PUSH_ENDPOINT_LENGTH = 4096


def is_supported_push_endpoint(value):
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_PUSH_ENDPOINT_LENGTH
        or any(character.isspace() or ord(character) < 32 for character in value)
        or "\\" in value
    ):
        return False

    try:
        parsed = urlsplit(value)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except (TypeError, ValueError):
        return False

    supported_host = (
        hostname == "fcm.googleapis.com"
        or hostname == "web.push.apple.com"
        or hostname == "notify.windows.com"
        or hostname.endswith(".notify.windows.com")
        or hostname == "push.services.mozilla.com"
        or hostname.endswith(".push.services.mozilla.com")
    )
    return (
        parsed.scheme == "https"
        and parsed.username is None
        and parsed.password is None
        and port in {None, 443}
        and supported_host
        and not parsed.fragment
    )
