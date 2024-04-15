import re
from datetime import datetime
from math import ceil

from django.conf import settings
from django.core.management.base import BaseCommand
from sqlite3 import connect

from django.utils import timezone

from apps.accounts.models import User, Settings
from apps.finance.models import Program, UserProgram, Operation, FrozenItem


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        with connect(settings.BASE_DIR / "goodwinprod.sqlite3") as connection:
            cursor = connection.cursor()

            create_users(cursor)
            create_user_settings(cursor)
            update_refer(cursor)
            update_wallet_free(cursor)
            create_programs(cursor)
            create_user_programs(cursor)
            update_wallet_frozen(cursor)

        print("Success")


def create_users(cursor):
    cursor.execute(
        "SELECT first_name, last_name, email, user_telegram, user_telegram_id, role, "
        "verified, registration_at "
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
            "agreement_date": timezone.now() if verified != 0 else None,
        }
        if registration_at is not None:
            update_data["date_joined"] = timezone.make_aware(
                datetime.fromisoformat(registration_at)
            )

        User.objects.update_or_create(email=email, defaults=update_data)


def create_user_settings(cursor):
    cursor.execute(
        "SELECT email, security_login_telegram, security_withdrawal_telegram, "
        "security_login_email, security_withdrawal_email "
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


def update_wallet_free(cursor):
    cursor.execute("SELECT email, white_wallet, green_wallet FROM user")
    for email, white_wallet, green_wallet in cursor.fetchall():
        user = User.objects.get(email=email)
        wallet = user.wallet

        wallet.free = white_wallet + green_wallet
        wallet.save()


def update_wallet_frozen(cursor):
    cursor.execute(
        "SELECT email, user_programs.name AS user_program_name, "
        "program.name AS program_name, amount, created, expired "
        "FROM green_wallet_freeze "
        "JOIN user ON green_wallet_freeze.user_id = user.id "
        "JOIN user_programs ON green_wallet_freeze.program_id = user_programs.id "
        "JOIN program ON user_programs.program_id = program.id"
    )
    now = timezone.now()
    for (
        email,
        user_program_name,
        program_name,
        amount,
        created,
        expired,
    ) in cursor.fetchall():
        user = User.objects.get(email=email)
        wallet = user.wallet

        # match = re.search("[(]\d+[)]", user_program_name)
        # if match:
        #     user_program_name = (
        #         program_name + f"{user_program_name[match.start()+1:match.end()-1]}"
        #     )
        # else:
        #     user_program_name = program_name
        #
        # user_program = UserProgram.objects.get(wallet=wallet, name=user_program_name)
        #
        # operation_data = {
        #     "type": Operation.Type.WITHDRAWAL,
        #     "wallet": wallet,
        #     "amount_free": 0,
        #     "amount_frozen": amount,
        #     "created_at": created,
        #     "done": True,
        #     "program": user_program.program,
        # }
        # operation = Operation.objects.filter(**operation_data).first()
        # if operation is None:
        #     operation = Operation.objects.create(**operation_data)

        frozen_item_data = {
            "wallet": wallet,
            "amount": amount,
            # "operation": operation,
            "defrost_date": timezone.make_aware(datetime.fromisoformat(expired)),
        }

        frozen_item = FrozenItem.objects.filter(**frozen_item_data).first()
        if frozen_item is None:
            frozen_item = FrozenItem.objects.create(**frozen_item_data)
            wallet.frozen += amount
            wallet.save()

        if not frozen_item.done and frozen_item.defrost_date <= now:
            frozen_item.defrost()


def create_programs(cursor):
    cursor.execute(
        "SELECT type, name, min_deposit, expected_profit, success_fee, "
        "withdrawn_timeout, reinvesting, min_reinvesting, calendar_days "
        "FROM program "
        "ORDER BY name"
    )
    for (
        p_type,
        name,
        min_deposit,
        expected_profit,
        success_fee,
        withdrawn_timeout,
        reinvesting,
        min_reinvesting,
        calendar_days,
    ) in cursor.fetchall():
        update_data = {
            "duration": ceil(calendar_days / 20) if calendar_days is not None else None,
            "exp_profit": expected_profit,
            "min_deposit": min_deposit,
            "accrual_type": Program.AccrualType.DAILY
            if p_type == 1
            else Program.AccrualType.AFTER_FINISH,
            "withdrawal_type": Program.WithdrawalType.DAILY
            if p_type == 1
            else Program.WithdrawalType.AFTER_FINISH,
            "max_risk": 0,
            "success_fee": success_fee,
            "management_fee": 0.004,  # TODO get from admin
            "withdrawal_terms": withdrawn_timeout,
        }
        Program.objects.update_or_create(name=name, defaults=update_data)


def create_user_programs(cursor):
    cursor.execute(
        "SELECT user_programs.name AS name, user_programs.status AS status, email, "
        "program.name AS program_name, start, finish, days_count, "
        "user_programs.created_at AS created_at "
        "FROM user_programs "
        "JOIN user ON user_programs.user_id = user.id "
        "JOIN program ON user_programs.program_id = program.id "
    )
    now = timezone.now()
    for (
        name,
        status,
        email,
        program_name,
        start,
        finish,
        days_count,
        created_at,
    ) in cursor.fetchall():
        program = Program.objects.get(name=program_name)
        user = User.objects.get(email=email)
        wallet = user.wallet

        match = re.search("[(]\d+[)]", name)
        if match:
            name = program.name + f"{name[match.start()+1:match.end()-1]}"
        else:
            name = program.name

        data = {
            "name": name,
            "wallet": wallet,
            "program": program,
            "start_date": timezone.make_aware(datetime.fromisoformat(start)),
        }

        if UserProgram.objects.filter(**data).exists():
            continue

        end_date = (
            timezone.make_aware(datetime.fromisoformat(finish)) if finish else None
        )
        if end_date and end_date < now:
            data["status"] = UserProgram.Status.FINISHED
            data["end_date"] = end_date

        elif data["start_date"] <= now:
            data["status"] = UserProgram.Status.RUNNING

        else:
            data["status"] = UserProgram.Status.INITIAL

        UserProgram.objects.create(**data)
