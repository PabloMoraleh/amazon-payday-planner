"""Data access helpers for the authenticated Supabase client."""

from datetime import datetime, timezone

from supabase import Client


def add_wish(client: Client, name, price_cents, priority=2, url=None, notes=None, asin=None):
    response = (
        client.table("wishes")
        .insert(
            {
                "name": name,
                "price_cents": price_cents,
                "priority": priority,
                "url": url,
                "notes": notes,
                "asin": asin,
            }
        )
        .select("id")
        .execute()
    )
    return response.data[0]["id"]


def list_wishes(client: Client):
    response = (
        client.table("wishes")
        .select("*")
        .eq("status", "wanted")
        .order("priority")
        .order("created_at")
        .execute()
    )
    return response.data


def get_wish(client: Client, wish_id):
    response = (
        client.table("wishes")
        .select("*")
        .eq("id", wish_id)
        .maybe_single()
        .execute()
    )
    return response.data


def update_wish(client: Client, wish_id, name, price_cents, priority, url, notes):
    response = (
        client.table("wishes")
        .update(
            {
                "name": name,
                "price_cents": price_cents,
                "priority": priority,
                "url": url,
                "notes": notes,
            }
        )
        .eq("id", wish_id)
        .select("id")
        .execute()
    )
    return bool(response.data)


def delete_wish(client: Client, wish_id):
    response = (
        client.table("wishes")
        .delete()
        .eq("id", wish_id)
        .select("id")
        .execute()
    )
    return bool(response.data)



def get_notification_preferences(client: Client, user_id):
    response = (
        client.table("notification_preferences")
        .select("*")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    return response.data or {
        "user_id": user_id,
        "enabled": False,
        "reminder_day": 1,
        "timezone": "UTC",
        "locale": "en",
    }


def save_notification_preferences(client: Client, user_id, enabled, reminder_day, timezone_name, locale):
    response = (
        client.table("notification_preferences")
        .upsert(
            {
                "user_id": user_id,
                "enabled": enabled,
                "reminder_day": reminder_day,
                "timezone": timezone_name,
                "locale": locale,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="user_id",
        )
        .execute()
    )
    return response.data[0] if response.data else None


def save_push_subscription(client: Client, user_id, endpoint, p256dh, auth):
    response = (
        client.table("push_subscriptions")
        .upsert(
            {
                "endpoint": endpoint,
                "user_id": user_id,
                "p256dh": p256dh,
                "auth": auth,
            },
            on_conflict="endpoint",
        )
        .execute()
    )
    return bool(response.data)


def delete_push_subscriptions(client: Client, user_id):
    response = (
        client.table("push_subscriptions")
        .delete()
        .eq("user_id", user_id)
        .select("endpoint")
        .execute()
    )
    return len(response.data or [])


def mark_as_bought(client: Client, wish_id):
    marked_at = datetime.now(timezone.utc).isoformat()
    response = (
        client.table("wishes")
        .update(
            {
                "status": "bought",
                "updated_at": marked_at,
                "bought_at": marked_at,
            }
        )
        .eq("id", wish_id)
        .select("id")
        .execute()
    )
    return bool(response.data)
