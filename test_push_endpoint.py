import pytest

from app import _is_supported_push_endpoint


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://fcm.googleapis.com/fcm/send/example",
        "https://updates.push.services.mozilla.com/wpush/v2/example",
        "https://web.push.apple.com/abc/example",
        "https://wns2.example.notify.windows.com/w/",
    ],
)
def test_accepts_browser_push_service_endpoints(endpoint):
    assert _is_supported_push_endpoint(endpoint)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://fcm.googleapis.com/fcm/send/example",
        "https://example.com/push",
        "https://127.0.0.1:443/push",
        "https://fcm.googleapis.com:8443/fcm/send/example",
        "https://user@fcm.googleapis.com/fcm/send/example",
        "https://fcm.googleapis.com.evil.example/push",
        "not a url",
    ],
)
def test_rejects_unsupported_push_endpoints(endpoint):
    assert not _is_supported_push_endpoint(endpoint)
