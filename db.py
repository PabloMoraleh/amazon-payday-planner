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


def mark_as_bought(client: Client, wish_id, bought_price_cents):
    response = (
        client.table("wishes")
        .update(
            {
                "status": "bought",
                "bought_price_cents": bought_price_cents,
                "bought_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", wish_id)
        .select("id")
        .execute()
    )
    return bool(response.data)
