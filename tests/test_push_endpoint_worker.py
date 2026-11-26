import pytest

from push_endpoints import is_supported_push_endpoint
from scripts import send_monthly_notifications


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
    assert is_supported_push_endpoint(endpoint)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://fcm.googleapis.com/fcm/send/example",
        "https://example.com/push",
        "https://127.0.0.1:443/push",
        "https://fcm.googleapis.com:8443/fcm/send/example",
        "https://user@fcm.googleapis.com/push",
        "https://fcm.googleapis.com.evil.example/push",
        "https://fcm.googleapis.com/push#fragment",
        "https://fcm.googleapis.com/with whitespace",
        "not a url",
        "x" * 4097,
    ],
)
def test_rejects_unsupported_push_endpoints(endpoint):
    assert not is_supported_push_endpoint(endpoint)


class FakeDeleteQuery:
    def __init__(self):
        self.filters = {}

    def delete(self):
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def execute(self):
        return None


class FakeClient:
    def __init__(self):
        self.query = FakeDeleteQuery()

    def table(self, table_name):
        assert table_name == "push_subscriptions"
        return self.query


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://127.0.0.1/internal",
        "https://attacker.example/collect",
        "https://fcm.googleapis.com.evil.example/push",
    ],
)
def test_worker_drops_unsupported_destinations_without_sending(monkeypatch, endpoint):
    client = FakeClient()
    user_id = "user-123"
    attempted_sends = []

    def fake_webpush(**kwargs):
        attempted_sends.append(kwargs)

    monkeypatch.setattr(send_monthly_notifications, "webpush", fake_webpush)

    sent = send_monthly_notifications.send_push_notification(
        client,
        user_id,
        {
            "endpoint": endpoint,
            "p256dh": "public-key",
            "auth": "auth-secret",
        },
        "{}",
        "private-key",
        "mailto:security@example.com",
    )

    assert sent is False
    assert attempted_sends == []
    assert client.query.filters == {"user_id": user_id, "endpoint": endpoint}


def test_worker_sends_to_a_supported_push_service(monkeypatch):
    client = FakeClient()
    attempted_sends = []

    def fake_webpush(**kwargs):
        attempted_sends.append(kwargs)

    monkeypatch.setattr(send_monthly_notifications, "webpush", fake_webpush)

    sent = send_monthly_notifications.send_push_notification(
        client,
        "user-123",
        {
            "endpoint": "https://fcm.googleapis.com/fcm/send/example",
            "p256dh": "public-key",
            "auth": "auth-secret",
        },
        "{}",
        "private-key",
        "mailto:security@example.com",
    )

    assert sent is True
    assert len(attempted_sends) == 1
