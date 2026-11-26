import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pywebpush import WebPushException, webpush
from supabase import create_client


MESSAGES = {
    "en": ("Your wishlist reminder", "You still have items on your wishlist to plan for this month."),
    "es": ("Recordatorio de tu lista", "Tienes artículos pendientes para planificar este mes."),
    "fr": ("Rappel de votre liste", "Des articles de votre liste restent à prévoir ce mois-ci."),
    "de": ("Erinnerung an deine Wunschliste", "Für diesen Monat stehen noch Artikel auf deiner Wunschliste."),
}


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    supabase_url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY")
    vapid_subject = os.environ.get("VAPID_SUBJECT")

    if not all((supabase_url, service_role_key, vapid_private_key, vapid_subject)):
        raise RuntimeError("Monthly notification environment variables are not configured.")

    client = create_client(supabase_url, service_role_key)
    preferences = (
        client.table("notification_preferences")
        .select("*")
        .eq("enabled", True)
        .execute()
        .data
    )
    sent_count = 0

    for preference in preferences:
        try:
            user_timezone = ZoneInfo(preference["timezone"])
        except (ZoneInfoNotFoundError, KeyError, TypeError):
            user_timezone = ZoneInfo("UTC")

        local_now = datetime.now(user_timezone)
        reminder_day = int(preference.get("reminder_day", 1))
        month_key = local_now.strftime("%Y-%m-01")

        if local_now.day < reminder_day or preference.get("last_sent_month") == month_key:
            continue

        user_id = preference["user_id"]
        wishes = (
            client.table("wishes")
            .select("id")
            .eq("user_id", user_id)
            .eq("status", "wanted")
            .execute()
            .data
        )
        if not wishes:
            continue

        subscriptions = (
            client.table("push_subscriptions")
            .select("endpoint,p256dh,auth")
            .eq("user_id", user_id)
            .execute()
            .data
        )
        if not subscriptions:
            continue

        locale = preference.get("locale", "en")
        title, body = MESSAGES.get(locale, MESSAGES["en"])
        payload = json.dumps({"title": title, "body": body, "url": "/wishes"})
        user_sent = False

        for subscription in subscriptions:
            subscription_info = {
                "endpoint": subscription["endpoint"],
                "keys": {
                    "p256dh": subscription["p256dh"],
                    "auth": subscription["auth"],
                },
            }
            try:
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=vapid_private_key,
                    vapid_claims={"sub": vapid_subject},
                )
                user_sent = True
                sent_count += 1
            except WebPushException as error:
                status_code = getattr(getattr(error, "response", None), "status_code", None)
                if status_code in {404, 410}:
                    client.table("push_subscriptions").delete().eq(
                        "endpoint", subscription["endpoint"]
                    ).execute()
                else:
                    logging.warning("Push delivery failed with status %s", status_code)

        if user_sent:
            (
                client.table("notification_preferences")
                .update(
                    {
                        "last_sent_month": month_key,
                        "updated_at": local_now.isoformat(),
                    }
                )
                .eq("user_id", user_id)
                .execute()
            )

    logging.info("Delivered %s monthly reminder notifications.", sent_count)


if __name__ == "__main__":
    main()
