from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from sqlite3 import connect

from apps.accounts.models import User, Settings


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        with connect(settings.BASE_DIR / "goodwinprod.sqlite3") as connection:
            cursor = connection.cursor()

            create_users(cursor)
            create_user_settings(cursor)
            update_refer(cursor)

        print("Success")


def create_users(cursor):
    cursor.execute(
        "SELECT first_name, last_name, email, user_telegram, user_telegram_id, role, verified, registration_at "
        "FROM user"
    )
    for (
        first_name,
        last_name,
        email,
        user_telegram,
        user_telegram_id,
        role,
        verified,
        registration_at,
    ) in cursor.fetchall():
        update_data = {
            "first_name": first_name,
            "last_name": last_name,
            "telegram": user_telegram[1:] if user_telegram is not None else None,
            "telegram_id": user_telegram_id,
            "is_staff": role == 1,
            "agreement_applied": verified != 0,
        }
        if registration_at is not None:
            update_data["date_joined"] = datetime.fromisoformat(registration_at)

        User.objects.update_or_create(
            email=email,
            defaults=update_data,
        )


def create_user_settings(cursor):
    cursor.execute(
        "SELECT email, security_login_telegram, security_withdrawal_telegram, security_login_email, security_withdrawal_email "
        "FROM user_2fa_settings JOIN user "
        "WHERE user_2fa_settings.user_id = user.id"
    )
    for (
        email,
        security_login_telegram,
        security_withdrawal_telegram,
        security_login_email,
        security_withdrawal_email,
    ) in cursor.fetchall():
        user = User.objects.get(email=email)

        Settings.objects.update_or_create(
            user=user,
            defaults={
                "email_request_code_on_auth": security_login_email == 1,
                "email_request_code_on_withdrawal": security_withdrawal_email == 1,
                "telegram_request_code_on_auth": security_login_telegram == 1,
                "telegram_request_code_on_withdrawal": security_withdrawal_telegram
                == 1,
            },
        )


def update_refer(cursor):
    cursor.execute(
        "SELECT parent_user.email AS parent_email, child_user.email as child_email "
        "FROM refer "
        "JOIN user AS parent_user ON refer.inviter_id = parent_user.id "
        "JOIN user AS child_user ON refer.invited_id = child_user.id "
    )
    for parent_email, child_email in cursor.fetchall():
        parent_user = User.objects.get(email=parent_email)
        child_user = User.objects.get(email=child_email)
        child_user.inviter = parent_user
        child_user.save()
