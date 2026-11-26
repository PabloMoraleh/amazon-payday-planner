import os
import re
import secrets
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from decimal import Decimal, InvalidOperation
from functools import wraps
from urllib.parse import urlsplit

from flask_babel import Babel, format_currency, get_locale, gettext as _
from flask import (
    Flask,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from cachelib.file import FileSystemCache
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from redis import Redis
from supabase import Client, create_client

from push_endpoints import is_supported_push_endpoint as _is_supported_push_endpoint

from db import (
    add_wish,
    delete_push_subscriptions,
    delete_wish,
    get_notification_preferences,
    get_wish,
    list_wishes,
    mark_as_bought,
    save_notification_preferences,
    save_push_subscription,
)


csrf = CSRFProtect()
babel = Babel()
SUPPORTED_LOCALES = ("en", "es", "fr", "de")


def select_locale():
    selected_locale = session.get("locale")
    if selected_locale in SUPPORTED_LOCALES:
        return selected_locale
    return request.accept_languages.best_match(SUPPORTED_LOCALES) or "en"


def create_app(test_config=None):
    app = Flask(__name__)
    app_env = os.environ.get("APP_ENV", "development").lower()
    redis_url = os.environ.get("SESSION_REDIS_URL")

    app.config.from_mapping(
        APP_ENV=app_env,
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32),
        SUPABASE_URL=os.environ.get("SUPABASE_URL"),
        SUPABASE_PUBLISHABLE_KEY=os.environ.get("SUPABASE_PUBLISHABLE_KEY"),
        VAPID_PUBLIC_KEY=os.environ.get("VAPID_PUBLIC_KEY"),
        SESSION_TYPE="redis" if redis_url else "cachelib",
        SESSION_FILE_DIR=os.path.join(app.instance_path, "sessions"),
        SESSION_PERMANENT=False,
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=app_env == "production",
        SESSION_COOKIE_SAMESITE="Lax",
        WTF_CSRF_ENABLED=True,
        BABEL_DEFAULT_LOCALE="en",
        BABEL_SUPPORTED_LOCALES=SUPPORTED_LOCALES,
    )
    if test_config:
        app.config.update(test_config)

    if app.config["APP_ENV"] == "production":
        if not os.environ.get("SECRET_KEY") and "SECRET_KEY" not in (test_config or {}):
            raise RuntimeError("SECRET_KEY must be configured in production.")
        if len(app.config["SECRET_KEY"]) < 32:
            raise RuntimeError("SECRET_KEY must contain at least 32 characters in production.")
        if not app.config["SUPABASE_URL"] or not app.config["SUPABASE_PUBLISHABLE_KEY"]:
            raise RuntimeError("SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY must be configured in production.")
        if not redis_url and "SESSION_REDIS" not in (test_config or {}):
            raise RuntimeError("SESSION_REDIS_URL must be configured in production.")
        if "SESSION_REDIS" in (test_config or {}):
            app.config["SESSION_TYPE"] = "redis"

    if app.config["SESSION_TYPE"] == "redis" and "SESSION_REDIS" not in app.config:
        configured_redis_url = os.environ.get("SESSION_REDIS_URL")
        if configured_redis_url:
            app.config["SESSION_REDIS"] = Redis.from_url(configured_redis_url)
    elif app.config["SESSION_TYPE"] == "cachelib" and "SESSION_CACHELIB" not in app.config:
        app.config["SESSION_CACHELIB"] = FileSystemCache(
            app.config["SESSION_FILE_DIR"], threshold=500, mode=0o600
        )

    Session(app)
    csrf.init_app(app)
    babel.init_app(app, locale_selector=select_locale)
    app.jinja_env.globals.update(
        format_currency=format_currency,
        get_locale=get_locale,
    )

    @app.get("/")
    def home():
        if session.get("user_id"):
            return redirect(url_for("wishes"))
        return redirect(url_for("login"))

    @app.post("/language")
    def set_language():
        requested_locale = request.form.get("locale", "")
        if requested_locale in SUPPORTED_LOCALES:
            session["locale"] = requested_locale
        destination = request.form.get("next", "/")
        if not destination.startswith("/") or destination.startswith("//") or "\\" in destination:
            destination = "/"
        parsed_destination = urlsplit(destination)
        if parsed_destination.scheme or parsed_destination.netloc:
            destination = "/"
        return redirect(destination)

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            password_confirmation = request.form.get("password_confirmation", "")

            if not email or not password:
                flash(_("Enter your email and password."), "error")
            elif len(password) < 8:
                flash(_("Your password must contain at least 8 characters."), "error")
            elif password != password_confirmation:
                flash(_("The passwords do not match."), "error")
            else:
                client = _new_supabase_client()
                try:
                    response = client.auth.sign_up(
                        {"email": email, "password": password}
                    )
                except Exception:
                    current_app.logger.info("Supabase signup request failed", exc_info=True)
                    flash(_("We could not create the account. Check the details and try again."), "error")
                else:
                    if response.session:
                        _save_session(response.session, response.user)
                        return redirect(url_for("wishes"))
                    flash(_("Check your email to confirm your account, then sign in."), "success")
                    return redirect(url_for("login"))

        return render_template("auth.html", mode="signup")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id"):
            return redirect(url_for("wishes"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not email or not password:
                flash(_("Enter your email and password."), "error")
            else:
                client = _new_supabase_client()
                try:
                    response = client.auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )
                except Exception:
                    current_app.logger.info("Supabase sign-in failed", exc_info=True)
                    flash(_("Email or password is incorrect."), "error")
                else:
                    if not response.session:
                        flash(_("Check your email to confirm your account, then sign in."), "success")
                        return redirect(url_for("login"))
                    _save_session(response.session, response.user)
                    return redirect(url_for("wishes"))

        return render_template("auth.html", mode="login")

    @app.post("/logout")
    @login_required
    def logout():
        try:
            g.supabase.auth.sign_out({"scope": "local"})
        except Exception:
            current_app.logger.info("Supabase sign-out request failed", exc_info=True)
        session.clear()
        flash(_("You have signed out."), "success")
        return redirect(url_for("login"))

    @app.get("/wishes")
    @login_required
    def wishes():
        try:
            wishes = list_wishes(g.supabase)
        except Exception:
            current_app.logger.exception("Could not load the current user's wishes")
            abort(503)
        try:
            notification_preferences = get_notification_preferences(
                g.supabase, g.current_user_id
            )
        except Exception:
            current_app.logger.exception("Could not load notification preferences")
            notification_preferences = {
                "enabled": False,
                "reminder_day": 1,
                "timezone": "UTC",
                "locale": get_locale().language,
            }
        return render_template(
            "wishes.html",
            wishes=wishes,
            user_email=session.get("user_email", ""),
            notification_preferences=notification_preferences,
            vapid_public_key=current_app.config.get("VAPID_PUBLIC_KEY", ""),
        )

    @app.get("/notifications/public-key")
    @login_required
    def notification_public_key():
        public_key = current_app.config.get("VAPID_PUBLIC_KEY")
        if not public_key:
            return jsonify({"error": "Notifications are not configured."}), 503
        return jsonify({"publicKey": public_key})


    @app.post("/notifications/subscribe")
    @login_required
    def notification_subscribe():
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return jsonify({"error": _("Could not enable notifications. Please try again.")}), 400
        subscription = data.get("subscription") or {}
        if not isinstance(subscription, dict):
            return jsonify({"error": _("Could not enable notifications. Please try again.")}), 400
        keys = subscription.get("keys") or {}
        if not isinstance(keys, dict):
            return jsonify({"error": _("Could not enable notifications. Please try again.")}), 400
        endpoint = subscription.get("endpoint", "")
        if not isinstance(endpoint, str) or len(endpoint) > 4096:
            return jsonify({"error": _("Could not enable notifications. Please try again.")}), 400
        if (
            not _is_supported_push_endpoint(endpoint)
            or not keys.get("p256dh")
            or not keys.get("auth")
        ):
            return jsonify({"error": _("Could not enable notifications. Please try again.")}), 400

        try:
            reminder_day = int(data.get("reminder_day", 1))
        except (TypeError, ValueError):
            reminder_day = 0
        if reminder_day not in {1, 2, 3, 4, 5}:
            return jsonify({"error": _("Choose a day from 1 to 5.")}), 400

        timezone_name = data.get("timezone", "UTC")
        try:
            ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, TypeError, ValueError):
            timezone_name = "UTC"
        locale = data.get("locale", "en")
        if locale not in SUPPORTED_LOCALES:
            locale = "en"

        try:
            save_push_subscription(
                g.supabase,
                g.current_user_id,
                endpoint,
                keys["p256dh"],
                keys["auth"],
            )
            save_notification_preferences(
                g.supabase,
                g.current_user_id,
                True,
                reminder_day,
                timezone_name,
                locale,
            )
        except Exception:
            current_app.logger.exception("Could not save browser notification subscription")
            return jsonify({"error": _("Could not enable notifications. Please try again.")}), 503

        return jsonify({"ok": True})


    @app.post("/notifications/preferences")
    @login_required
    def notification_preferences_update():
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return jsonify({"error": _("Could not save the reminder day. Please try again.")}), 400
        try:
            reminder_day = int(data.get("reminder_day", 1))
        except (TypeError, ValueError):
            reminder_day = 0
        if reminder_day not in {1, 2, 3, 4, 5}:
            return jsonify({"error": _("Choose a day from 1 to 5.")}), 400

        timezone_name = data.get("timezone", "UTC")
        try:
            ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, TypeError, ValueError):
            timezone_name = "UTC"
        locale = data.get("locale", "en")
        if locale not in SUPPORTED_LOCALES:
            locale = "en"

        try:
            current_preferences = get_notification_preferences(g.supabase, g.current_user_id)
            save_notification_preferences(
                g.supabase,
                g.current_user_id,
                bool(current_preferences.get("enabled")),
                reminder_day,
                timezone_name,
                locale,
            )
        except Exception:
            current_app.logger.exception("Could not update notification preferences")
            return jsonify({"error": _("Could not save the reminder day. Please try again.")}), 503

        return jsonify({"ok": True})


    @app.post("/notifications/unsubscribe")
    @login_required
    def notification_unsubscribe():
        try:
            delete_push_subscriptions(g.supabase, g.current_user_id)
            current_preferences = get_notification_preferences(g.supabase, g.current_user_id)
            save_notification_preferences(
                g.supabase,
                g.current_user_id,
                False,
                int(current_preferences.get("reminder_day", 1)),
                current_preferences.get("timezone", "UTC"),
                current_preferences.get("locale", get_locale().language),
            )
        except Exception:
            current_app.logger.exception("Could not disable browser notifications")
            return jsonify({"error": _("Could not disable notifications. Please try again.")}), 503
        return jsonify({"ok": True})


    @app.post("/wishes")
    @login_required
    def create_wish():
        name = request.form.get("name", "").strip()
        price_text = request.form.get("price", "").strip().replace(",", ".")
        priority_text = request.form.get("priority", "2")
        product_url = request.form.get("url", "").strip()

        if not name or len(name) > 200:
            flash(_("Enter a product name up to 200 characters long."), "error")
            return redirect(url_for("wishes"))

        try:
            price = Decimal(price_text)
            price_cents = int(price * 100)
        except (InvalidOperation, ValueError, OverflowError):
            flash(_("Enter a valid price."), "error")
            return redirect(url_for("wishes"))

        if not price.is_finite() or price < 0 or price * 100 != price_cents:
            flash(_("Enter a price with up to two decimal places."), "error")
            return redirect(url_for("wishes"))

        try:
            priority = int(priority_text)
        except ValueError:
            priority = 0

        if priority not in {1, 2, 3}:
            flash(_("Choose a priority from 1 to 3."), "error")
            return redirect(url_for("wishes"))

        if product_url and not _is_amazon_es_url(product_url):
            flash(_("Enter a valid Amazon Spain product link."), "error")
            return redirect(url_for("wishes"))

        try:
            add_wish(
                g.supabase,
                name=name,
                price_cents=price_cents,
                priority=priority,
                url=product_url or None,
                asin=_extract_asin(product_url),
            )
        except Exception:
            current_app.logger.exception("Could not create wish")
            abort(503)

        flash(_("Product added to your wishlist."), "success")
        return redirect(url_for("wishes"))

    @app.post("/wishes/<int:wish_id>/bought")
    @login_required
    def wish_bought(wish_id):
        try:
            wish = get_wish(g.supabase, wish_id)
        except Exception:
            current_app.logger.exception("Could not load wish")
            abort(503)
        if wish is None:
            abort(404)

        try:
            updated = mark_as_bought(g.supabase, wish_id)
        except Exception:
            current_app.logger.exception("Could not mark wish as bought")
            abort(503)
        if not updated:
            abort(404)

        flash(_("Product marked as bought."), "success")
        return redirect(url_for("wishes"))

    @app.post("/wishes/<int:wish_id>/delete")
    @login_required
    def wish_delete(wish_id):
        try:
            deleted = delete_wish(g.supabase, wish_id)
        except Exception:
            current_app.logger.exception("Could not delete wish")
            abort(503)
        if not deleted:
            abort(404)

        flash(_("Product removed from your wishlist."), "success")
        return redirect(url_for("wishes"))

    return app


def _is_amazon_es_url(value):
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.hostname is not None
        and (parsed.hostname == "amazon.es" or parsed.hostname.endswith(".amazon.es"))
        and parsed.username is None
        and parsed.password is None
    )


def _extract_asin(value):
    match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:/|$)", urlsplit(value).path, re.IGNORECASE)
    return match.group(1).upper() if match else None


def _new_supabase_client() -> Client:
    url = current_app.config.get("SUPABASE_URL")
    key = current_app.config.get("SUPABASE_PUBLISHABLE_KEY")
    if not url or not key:
        abort(503, description="Supabase is not configured for this environment.")

    client_factory = current_app.config.get("SUPABASE_CLIENT_FACTORY", create_client)
    return client_factory(url, key)


def _save_session(auth_session, user):
    if not auth_session or not user:
        session.clear()
        flash(_("Check your email to confirm your account, then sign in."), "success")
        return

    session.clear()
    current_app.session_interface.regenerate(session)
    session["user_id"] = str(user.id)
    session["user_email"] = user.email
    session["access_token"] = auth_session.access_token
    session["refresh_token"] = auth_session.refresh_token
    session.permanent = True


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        access_token = session.get("access_token")
        refresh_token = session.get("refresh_token")
        if not session.get("user_id") or not access_token or not refresh_token:
            session.clear()
            return redirect(url_for("login"))

        client = _new_supabase_client()
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception as error:
            if getattr(error, "status", None) in {400, 401, 403}:
                session.clear()
                flash(_("Your session has expired. Please sign in again."), "error")
                return redirect(url_for("login"))
            raise

        refreshed_session = client.auth.get_session()
        if refreshed_session:
            session["access_token"] = refreshed_session.access_token
            session["refresh_token"] = refreshed_session.refresh_token

        g.supabase = client
        g.current_user_id = session["user_id"]
        return current_app.ensure_sync(view)(**kwargs)

    return wrapped_view


app = create_app()
