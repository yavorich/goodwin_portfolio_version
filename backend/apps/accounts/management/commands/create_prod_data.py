import re
from datetime import datetime, date
from decimal import Decimal
from math import ceil

from django.conf import settings
from django.core.management.base import BaseCommand
from sqlite3 import connect

from django.db.models import Q, F
from django.db.models.signals import post_save
from django.utils import timezone

from apps.accounts.models import (
    User,
    Settings,
    Partner,
    Region,
    PersonalVerification,
    VerificationStatus,
    AddressVerification,
)
from apps.finance.models import (
    Program,
    UserProgram,
    UserProgramAccrual,
    OperationHistory,
    WithdrawalRequest,
    UserProgramReplenishment,
    Operation,
)
from apps.finance.signals import handle_operation
from core.utils import DisconnectSignal


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        with connect(settings.BASE_DIR / "goodwinprod.sqlite3") as connection:
            cursor = connection.cursor()

            functions = [
                clean_users,
                create_users,
                create_user_settings,
                update_refer,
                update_wallet_free,
                update_wallet_frozen,
                create_programs,
                create_user_programs,
                create_user_program_accruals,
                create_operation_history_withdraw,
                create_operation_history_partner,
                create_operation_history_program_replenishment,
                create_operation_history_replenishment,
                create_operation_history_extra_fee,
                create_operation_history_start_close_program,
                # imitation_working_app,  no work
            ]

            stages = len(functions)
            for i, func in enumerate(functions):
                func(cursor)
                print(f"[{i+1}/{stages}] {func.__name__}")

        print("Success")


def clean_users(cursor):
    cursor.execute("SELECT email FROM user")
    User.objects.filter(email__in=[email for (email,) in cursor.fetchall()]).delete()


def create_users(cursor):
    cursor.execute(
        "SELECT first_name, last_name, email, user_telegram, user_telegram_id, role, "
        "verified, commentary, registration_at "
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
        commentary,
        registration_at,
    ) in cursor.fetchall():
        update_data = {
            "first_name": first_name.split()[0].capitalize(),
            "last_name": last_name.capitalize(),
            "telegram": user_telegram[1:] if user_telegram is not None else None,
            "telegram_id": user_telegram_id,
            "is_staff": role == 1,
            "agreement_date": timezone.now() if verified == 1 else None,
        }
        if registration_at is not None:
            update_data["date_joined"] = get_datetime_from_iso(registration_at)

        user = User.objects.update_or_create(email=email, defaults=update_data)[0]

        if verified == 1 or commentary not in (None, ""):
            if not hasattr(user, "personal_verification"):
                gender = NAME_TO_GENDER[user.first_name]
                personal_verification = PersonalVerification(
                    user=user,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    gender=gender,
                    date_of_birth=date(year=1990, month=1, day=1),
                    document_type=PersonalVerification.DocumentType.PASSPORT,
                    document_issue_date=date(year=1990, month=1, day=1),
                    document_issue_region="ru",
                    status=VerificationStatus.APPROVED,
                )
                personal_verification.save()

            if not hasattr(user, "address_verification"):
                address_verification = AddressVerification(
                    user=user,
                    country="country",
                    city="city",
                    address="address",
                    postal_code="0",
                    document_type=AddressVerification.DocumentType.OTHER,
                    status=VerificationStatus.APPROVED,
                )
                address_verification.save()


def create_user_settings(cursor):
    Settings.objects.update(
        email_request_code_on_auth=False,
        email_request_code_on_withdrawal=False,
        email_request_code_on_transfer=False,
        telegram_request_code_on_auth=False,
        telegram_request_code_on_withdrawal=False,
        telegram_request_code_on_transfer=False,
    )

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
                "email_request_code_on_transfer": security_withdrawal_email == 1,
                "telegram_request_code_on_auth": security_login_telegram == 1,
                "telegram_request_code_on_withdrawal": security_withdrawal_telegram
                == 1,
                "telegram_request_code_on_transfer": security_withdrawal_telegram == 1,
            },
        )


def update_refer(cursor):
    cursor.execute(
        "SELECT parent_user.email AS parent_email, child_user.email as child_email, "
        "invited_id "
        "FROM refer "
        "JOIN user AS parent_user ON refer.inviter_id = parent_user.id "
        "JOIN user AS child_user ON refer.invited_id = child_user.id "
    )

    region = Region.objects.get_or_create(name="Russia")[0]
    for parent_email, child_email, invited_id in cursor.fetchall():
        parent_user = User.objects.get(email=parent_email)
        child_user = User.objects.get(email=child_email)

        if hasattr(parent_user, "partner_profile"):
            partner = parent_user.partner_profile
        else:
            partner = Partner.objects.create(
                user=parent_user,
                partner_id=invited_id,
                region=region,
            )

        child_user.partner = partner
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
        raise Exception("has frozen")
        # user = User.objects.get(email=email)
        # wallet = user.wallet
        #
        # user_program_name = get_user_program_name(user_program_name, program_name)
        # user_program = UserProgram.objects.get(wallet=wallet, name=user_program_name)
        #
        # operation_data = {
        #     "type": Operation.Type.WITHDRAWAL,
        #     "wallet": wallet,
        #     "amount_free": 0,
        #     "amount_frozen": amount,
        #     "created_at": timezone.make_aware(datetime.fromisoformat(created)),
        #     "done": True,
        #     "program": user_program.program,
        # }
        # operation = Operation.objects.filter(**operation_data).first()
        # if operation is None:
        #     operation = Operation.objects.create(**operation_data)
        #
        # frozen_item_data = {
        #     "wallet": wallet,
        #     "amount": amount,
        #     # "operation": operation,
        #     "defrost_date": timezone.make_aware(datetime.fromisoformat(expired)),
        # }
        #
        # frozen_item = FrozenItem.objects.filter(**frozen_item_data).first()
        # if frozen_item is None:
        #     frozen_item = FrozenItem.objects.create(**frozen_item_data)
        #     wallet.frozen += amount
        #     wallet.save()
        #
        # if not frozen_item.done and frozen_item.defrost_date <= now:
        #     frozen_item.defrost()


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
            "accrual_type": Program.AccrualType.DAILY,
            "withdrawal_type": Program.WithdrawalType.DAILY
            if p_type == 1
            else Program.WithdrawalType.AFTER_FINISH,
            "max_risk": 0,
            "success_fee": success_fee,
            "management_fee": 0.004,
            "withdrawal_terms": withdrawn_timeout,
        }
        Program.objects.update_or_create(name=name, defaults=update_data)


def create_user_programs(cursor):
    STATUS_NUMBER = {
        1: UserProgram.Status.INITIAL,
        2: UserProgram.Status.RUNNING,
        3: UserProgram.Status.FINISHED,
    }

    cursor.execute(
        "SELECT user_programs.name AS name, user_programs.status AS status, email, "
        "program.name AS program_name, start, finish, days_count, deposit, "
        "user_programs.created_at AS created_at, user_programs.id AS user_program_id "
        "FROM user_programs "
        "JOIN user ON user_programs.user_id = user.id "
        "JOIN program ON user_programs.program_id = program.id "
        "ORDER BY created_at"
    )
    for (
        name,
        status,
        email,
        program_name,
        start,
        finish,
        days_count,
        deposit,
        created_at,
        user_program_id,
    ) in cursor.fetchall():
        program = Program.objects.get(name=program_name)
        user = User.objects.get(email=email)
        wallet = user.wallet

        created_at = (
            get_datetime_from_iso(created_at)
            if created_at
            else get_datetime_from_iso(start) - timezone.timedelta(days=3)
        )
        default_data = {
            "wallet": wallet,
            "program": program,
            "created_at": created_at,
        }

        user_program = UserProgram.objects.filter(**default_data).first()
        if user_program is None:
            user_program = UserProgram(**default_data)

        update_data = {
            "deposit": Decimal(0),
            "profit": Decimal(deposit),
            "start_date": get_datetime_from_iso(start),
            "status": STATUS_NUMBER[status],
        }

        if status == 3:
            if finish:
                update_data["close_date"] = get_datetime_from_iso(finish)
            else:
                close_date = get_close_date(cursor, user_program_id)
                update_data["close_date"] = close_date if close_date else created_at

        for attr, value in update_data.items():
            setattr(user_program, attr, value)

        user_program.save()


def create_user_program_accruals(cursor):
    cursor.execute(
        "SELECT email, user_programs.created_at AS user_program_created_at, "
        "user_programs.start AS user_program_start, "
        "program.name AS program_name, clean_profit, dirty_profit, dirty_percent, "
        "user_program_profit.success_fee AS success_fee, created "
        "FROM user_program_profit "
        "JOIN user_programs ON user_program_id = user_programs.id "
        "JOIN user ON user_programs.user_id = user.id "
        "JOIN program ON user_programs.program_id = program.id "
    )
    for (
        email,
        user_program_created_at,
        user_program_start,
        program_name,
        clean_profit,
        dirty_profit,
        dirty_percent,
        success_fee,
        created,
    ) in cursor.fetchall():
        program = Program.objects.get(name=program_name)
        user = User.objects.get(email=email)
        wallet = user.wallet

        user_program = get_user_program(
            wallet, program, user_program_created_at, user_program_start
        )

        UserProgramAccrual.objects.update_or_create(
            program=user_program,
            created_at=get_datetime_from_iso(created),
            defaults={
                "amount": clean_profit,
                "percent_amount": clean_profit / dirty_profit * dirty_percent
                if dirty_percent
                else 0,
                "success_fee": success_fee,
                "management_fee": 0,
            },
        )
        OperationHistory.objects.update_or_create(
            wallet=wallet,
            type=OperationHistory.Type.SYSTEM_MESSAGE,
            created_at=get_datetime_from_iso(created),
            defaults={
                "description": dict(
                    ru=f"Начисление по программе {user_program.name}",
                    en=f"Accrual under the {user_program.name} program",
                    cn=None,
                ),
                "target_name": wallet.name,
                "amount": clean_profit,
            },
        )


def create_operation_history_withdraw(cursor):
    cursor.execute(
        "SELECT email, withdraw.status AS status, amount, amount_final, address, "
        "created, finished "
        "FROM withdraw "
        "JOIN user ON withdraw.user_id = user.id "
    )
    with DisconnectSignal(post_save, handle_operation, Operation):
        for (
            email,
            status,
            amount,
            amount_final,
            address,
            created,
            finished,
        ) in cursor.fetchall():
            user = User.objects.get(email=email)
            wallet = user.wallet

            created_at = timezone.make_aware(datetime.fromtimestamp(created))
            finished_at = timezone.make_aware(datetime.fromtimestamp(finished))

            if amount_final is None:
                amount_final = amount * 0.97

            operation = Operation.objects.update_or_create(
                created_at=created_at,
                wallet=wallet,
                type=Operation.Type.WITHDRAWAL,
                defaults={
                    "amount": amount,
                    "amount_net": amount_final,
                    "commission": amount - amount_final,
                },
            )[0]
            OperationHistory.objects.update_or_create(
                wallet=wallet,
                type=OperationHistory.Type.WITHDRAWAL,
                created_at=created_at,
                defaults={
                    "description": dict(
                        ru="Заявка на вывод принята",
                        en="Withdrawal request accepted",
                        cn=None,
                    ),
                    "target_name": wallet.name,
                    "amount": -amount,
                },
            )
            withdrawal_request = WithdrawalRequest.objects.update_or_create(
                wallet=wallet,
                created_at=created_at,
                status=WithdrawalRequest.Status.APPROVED
                if status == 3
                else WithdrawalRequest.Status.REJECTED,
                done=True,
                defaults={
                    "address": address,
                    "original_amount": amount,
                    "amount": amount_final,
                    "done_at": finished_at,
                },
            )[0]

            if status == 3:
                OperationHistory.objects.update_or_create(
                    wallet=wallet,
                    type=OperationHistory.Type.SYSTEM_MESSAGE,
                    created_at=finished_at,
                    defaults={
                        "description": dict(
                            ru=f"Заявка на вывод {withdrawal_request.original_amount} USDT исполнена",
                            en=(
                                f"The withdrawal request of {withdrawal_request.original_amount}"
                                "USDT has been processed."
                            ),
                            cn=None,
                        ),
                        "target_name": None,
                        "amount": None,
                    },
                )
                operation.done = True

            else:
                OperationHistory.objects.update_or_create(
                    wallet=wallet,
                    type=OperationHistory.Type.SYSTEM_MESSAGE,
                    created_at=finished_at,
                    defaults={
                        "description": dict(
                            ru=f"Заявка на вывод {withdrawal_request.original_amount} USDT отклонена",
                            en=(
                                f"The withdrawal request of {withdrawal_request.original_amount}"
                                "USDT has been rejected."
                            ),
                            cn=None,
                        ),
                        "target_name": withdrawal_request.wallet.name,
                        "amount": withdrawal_request.original_amount,
                    },
                )
                operation.done = False

            operation.save()


def create_operation_history_partner(cursor):
    if OperationHistory.objects.filter(
        type=OperationHistory.Type.LOYALTY_PROGRAM
    ).exists():
        return

    cursor.execute(
        "SELECT email, bonus, "
        "partner_reward_statistic.created_at AS created_at "
        "FROM partner_reward_statistic "
        "JOIN user ON partner_reward_statistic.to_partner = user.id "
    )
    for email, bonus, created_at in cursor.fetchall():
        user = User.objects.get(email=email)
        wallet = user.wallet

        unique_data = {
            "wallet": wallet,
            "type": OperationHistory.Type.LOYALTY_PROGRAM,
            "created_at": get_datetime_from_iso(created_at),
        }
        OperationHistory.objects.create(
            description="Branch income",
            target_name=wallet.name,
            amount=bonus,
            **unique_data,
        )


def create_operation_history_program_replenishment(cursor):
    cursor.execute(
        "SELECT email, user_programs.created_at AS user_program_created_at, "
        "user_programs.start AS user_program_start, "
        "program.name AS program_name, amount, "
        "user_program_reinvests.created_at AS created_at, execution_at "
        "FROM user_program_reinvests "
        "JOIN user_programs ON user_program_id = user_programs.id "
        "JOIN user ON user_programs.user_id = user.id "
        "JOIN program ON user_programs.program_id = program.id "
    )
    for (
        email,
        user_program_created_at,
        user_program_start,
        program_name,
        amount,
        created_at,
        execution_at,
    ) in cursor.fetchall():
        program = Program.objects.get(name=program_name)
        user = User.objects.get(email=email)
        wallet = user.wallet

        user_program = get_user_program(
            wallet, program, user_program_created_at, user_program_start
        )

        created_at = get_datetime_from_iso(created_at)
        execution_at = get_datetime_from_iso(execution_at)

        OperationHistory.objects.update_or_create(
            wallet=wallet,
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            created_at=created_at,
            defaults={
                "description": dict(
                    ru=f"Перевод в программу {user_program.name}",
                    en=f"Transfer to program {user_program.name}",
                    cn=None,
                ),
                "target_name": wallet.name,
                "amount": -amount,
            },
        )
        user_program_replenishment = UserProgramReplenishment.objects.get_or_create(
            program=user_program,
            amount=amount,
            created_at=created_at,
            apply_date=execution_at,
            status=UserProgramReplenishment.Status.DONE,
            done=True,
        )[0]
        OperationHistory.objects.update_or_create(
            wallet=user_program_replenishment.program.wallet,
            type=OperationHistory.Type.TRANSFER_BETWEEN,
            created_at=execution_at,
            defaults={
                "description": dict(
                    ru=f"Программа {user_program_replenishment.program.name} пополнена",
                    en=f"Program {user_program_replenishment.program.name} has been replenished",
                    cn=None,
                ),
                "target_name": user_program_replenishment.program.name,
                "amount": user_program_replenishment.amount,
            },
        )


def create_operation_history_replenishment(cursor):
    cursor.execute(
        "SELECT email, amount_gc, amount_gc_fee, finished "
        "FROM invoice "
        "JOIN user ON invoice.user_id = user.id "
        "WHERE invoice.status = '2'"
    )
    with DisconnectSignal(post_save, handle_operation, Operation):
        for email, amount_gc, amount_gc_fee, finished in cursor.fetchall():
            user = User.objects.get(email=email)
            wallet = user.wallet
            created_at = get_datetime_from_timestamp(finished)

            Operation.objects.update_or_create(
                created_at=created_at,
                wallet=wallet,
                type=Operation.Type.REPLENISHMENT,
                defaults={
                    "amount": amount_gc,
                    "amount_net": amount_gc_fee,
                    "commission": amount_gc_fee - amount_gc,
                    "done": True,
                },
            )
            OperationHistory.objects.update_or_create(
                wallet=wallet,
                type=OperationHistory.Type.REPLENISHMENT,
                created_at=get_datetime_from_timestamp(finished),
                defaults={
                    "description": dict(
                        ru="Депозит",
                        en="Deposit",
                        cn=None,
                    ),
                    "target_name": wallet.name,
                    "amount": amount_gc,
                },
            )


def create_operation_history_extra_fee(cursor):
    cursor.execute(
        "SELECT email, fee, extra_fee_statistic.created_at AS created_at "
        "FROM extra_fee_statistic "
        "JOIN user ON extra_fee_statistic.user_id = user.id "
    )
    for email, fee, created_at in cursor.fetchall():
        user = User.objects.get(email=email)
        wallet = user.wallet

        OperationHistory.objects.update_or_create(
            wallet=wallet,
            type=OperationHistory.Type.SYSTEM_MESSAGE,
            created_at=get_datetime_from_iso(created_at),
            defaults={
                "description": dict(
                    ru="Списание комиссии Extra Fee",
                    en="Extra Fee commission write-off",
                    cn=None,
                ),
                "target_name": wallet.name,
                "amount": -fee,
            },
        )


def create_operation_history_start_close_program(cursor):
    cursor.execute("SELECT email FROM user")
    emails = [email for (email,) in cursor.fetchall()]

    for user in User.objects.filter(email__in=emails):
        user_programs = UserProgram.objects.filter(wallet__user=user)
        if not user_programs.exists():
            continue

        for program_id in (
            user_programs.values("program_id")
            .distinct()
            .values_list("program_id", flat=True)
        ):
            program = Program.objects.get(pk=program_id)

            cursor.execute(
                "SELECT email, deposit, "
                "program_deposit_statistic.created_at AS created_at, "
                "program.name AS program_name "
                "FROM program_deposit_statistic "
                "JOIN user ON program_deposit_statistic.user_id = user.id "
                "JOIN program ON program_deposit_statistic.program_id = program.id "
                f"WHERE email = '{user.email}' AND program.name = '{program.name}'"
                "ORDER BY program_deposit_statistic.created_at"
            )

            result = cursor.fetchall()

            c_ups = user_programs.filter(program_id=program_id)

            user_program_start = [
                (get_datetime_from_iso(created_at).date(), Decimal(round(deposit, 2)))
                for email, deposit, created_at, program_name in result
                if deposit > 0
            ]
            for user_program in c_ups:
                c_dates = filter(
                    lambda t: t[0]
                    >= user_program.created_at.date() - timezone.timedelta(days=1),
                    user_program_start,
                )

                c_dates = list(
                    map(
                        lambda x: (
                            abs((x[0] - user_program.created_at.date()).days),
                            # abs((x[1] - ))
                            x[0],
                            x[1],
                        ),
                        c_dates,
                    )
                )
                c_dates.sort(key=lambda x: x[0])

                if len(c_dates) == 0:
                    continue

                choice = c_dates[0]
                deposit = user_program_start.pop(
                    user_program_start.index((choice[1], choice[2]))
                )[1]

                funds = Decimal(get_upe_deposit(cursor, user_program))
                user_program.deposit = deposit
                user_program.profit = funds - deposit
                user_program.save()

                up = UserProgram.objects.get(pk=user_program.pk)

                start_date = get_datetime_from_iso(
                    get_upe_start_date(cursor, user_program)
                )
                create_operation_history_start_program(
                    user_program, deposit, start_date
                )

            user_program_end = [
                (get_datetime_from_iso(created_at), Decimal(round(deposit, 2)))
                for email, deposit, created_at, program_name in result
                if deposit < 0
            ]
            for user_program in c_ups.filter(status=UserProgram.Status.FINISHED):
                c_dates = filter(
                    lambda t: t[0].date()
                    >= user_program.created_at.date() - timezone.timedelta(days=1),
                    user_program_end,
                )

                funds = Decimal(get_upe_deposit(cursor, user_program))

                c_dates = list(
                    map(
                        lambda x: (
                            x[0],
                            x[1],
                            abs((x[0].date() - user_program.close_date).days),
                            abs(
                                -(
                                    user_program_end[
                                        user_program_end.index((x[0], x[1]))
                                    ]
                                )[1]
                                - funds
                            ),
                        ),
                        c_dates,
                    )
                )
                c_dates.sort(key=lambda x: (x[2], x[3]))

                if len(c_dates) == 0:
                    continue

                choice = c_dates[0]
                date_, deposit = user_program_end.pop(
                    user_program_end.index((choice[0], choice[1]))
                )

                user_program.close_date = date_
                amount = -deposit
                user_program.save()
                create_operation_history_close_program(user_program, amount, date_)


def create_operation_history_start_program(user_program, deposit, start_date):
    OperationHistory.objects.update_or_create(
        wallet=user_program.wallet,
        type=OperationHistory.Type.TRANSFER_BETWEEN,
        created_at=start_date,
        defaults={
            "description": dict(
                ru=f"Запуск программы {user_program.name}",
                en=f"Starting the {user_program.name} program",
                cn=None,
            ),
            "target_name": user_program.wallet.name,
            "amount": -deposit,
        },
    )
    OperationHistory.objects.update_or_create(
        wallet=user_program.wallet,
        type=OperationHistory.Type.TRANSFER_BETWEEN,
        created_at=start_date,
        defaults={
            "description": dict(
                ru=f"Программа {user_program.name} пополнена",
                en=f"Program {user_program.name} has been replenished",
                cn=None,
            ),
            "target_name": user_program.name,
            "amount": deposit,
        },
    )


def create_operation_history_close_program(user_program, amount, close_date):
    if user_program.end_date != close_date.date():
        description = dict(
            ru=f"Программа {user_program.name} закрыта досрочно",
            en=f"The {user_program.name} program is closed early",
            cn=None,
        )
    else:
        description = dict(
            ru=f"Программа {user_program.name} закрыта",
            en=f"{user_program.name} program is closed",
            cn=None,
        )

    OperationHistory.objects.update_or_create(
        wallet=user_program.wallet,
        type=OperationHistory.Type.SYSTEM_MESSAGE,
        created_at=close_date,
        defaults={
            "description": description,
            "target_name": user_program.name,
            "amount": -amount,
        },
    )
    OperationHistory.objects.update_or_create(
        wallet=user_program.wallet,
        type=OperationHistory.Type.TRANSFER_FROZEN,
        created_at=close_date,
        defaults={
            "description": dict(
                ru=f"Перевод депозита {user_program.name}",
                en=f"Transfer of deposit {user_program.name}",
                cn=None,
            ),
            "target_name": user_program.wallet.name,
            "amount": amount,
        },
    )


def imitation_working_app(cursor):
    for user in User.objects.all():
        # if user.email != "1111katya83@gmail.com":
        #     continue

        user_programs = UserProgram.objects.filter(wallet__user=user)
        if not user_programs.exists():
            continue

        for user_program in user_programs:
            print(
                user_program.name,
                user_program.deposit,
                user_program.funds,
                get_upe_deposit(cursor, user_program),
                user_program.status,
            )

        continue

        start_date = user_programs.order_by("created_at").first().created_at.date()
        end_date = user_programs.order_by("-close_date").first().close_date
        if end_date is None:
            end_date = timezone.now().date()

        total_days = (end_date - start_date).days

        user_programs_data = {
            user_program.pk: [
                user_program,
                user_program.deposit,
                {
                    accrual.created_at: accrual
                    for accrual in user_program.accruals.iterator()
                },
                {
                    replenishment.created_at: replenishment
                    for replenishment in user_program.replenishments.iterator()
                },
            ]
            for user_program in user_programs.iterator()
        }

        for i in range(total_days + 1):
            current_date = start_date + timezone.timedelta(days=i)

            cur_ups = []
            for _id, user_program_data in user_programs_data.items():
                user_program = user_program_data[0]

                up_start_date = user_program.created_at.date()
                up_end_date = (
                    user_program.close_date
                    if user_program.close_date
                    else timezone.now().date()
                )

                if up_start_date <= current_date <= up_end_date:
                    cur_ups.append(user_program)

            if len(cur_ups) == 0:
                continue

            programs = {user_program.program_id for user_program in cur_ups}

            for program_id in programs:
                p_cur_ups = list(
                    filter(lambda up: up.program_id == program_id, cur_ups)
                )
                if len(p_cur_ups) == 0:
                    continue

                for user_program in p_cur_ups:
                    user_program_data = user_programs_data[user_program.pk]

                    if current_date in user_program_data[2].keys():
                        user_program_data[1] += user_program_data[2][
                            current_date
                        ].amount
                        # print(
                        #     user_program_data[1], user_program_data[2][current_date][1]
                        # )

                    if current_date in user_program_data[3].keys():
                        user_program_data[1] += user_program_data[3][
                            current_date
                        ].amount

        print(
            [
                (upd[1], get_upe_deposit(cursor, upd[0]), upd[0].funds)
                for upd in user_programs_data.values()
            ]
        )

        # accruals = user_program.accruals
        # replenishments = user_program.replenishments

        # UserProgramAccrual  # начисления по проценту
        # UserProgramReplenishment  # начисления пользователей


def get_user_program_name(_name, program_name):
    match = re.search("[(]\d+[)]", _name)
    if match:
        return program_name + f"/{_name[match.start()+1:match.end()-1]}"
    else:
        return program_name


def get_datetime_from_iso(_datetime_iso):
    return timezone.make_aware(datetime.fromisoformat(_datetime_iso))


def get_datetime_from_timestamp(_datetime_timestamp):
    return timezone.make_aware(datetime.fromtimestamp(_datetime_timestamp))


def get_date_time_from_iso_or_null(_datetime):
    return timezone.make_aware(datetime.fromisoformat(_datetime)) if _datetime else None


def get_upe_deposit(cursor, user_program):
    cursor.execute(
        "SELECT deposit, user_programs.created_at AS created_at, "
        "user_programs.start start "
        "FROM user_programs "
        "JOIN user ON user_programs.user_id = user.id "
        "JOIN program ON user_programs.program_id = program.id "
        f"WHERE email = '{user_program.wallet.user.email}' "
        f"AND program.name = '{user_program.program.name}'"
    )
    return next(
        map(
            lambda x: x[0],
            filter(
                lambda x: (
                    get_datetime_from_iso(x[1])
                    if x[1]
                    else get_datetime_from_iso(x[2]) - timezone.timedelta(days=3)
                )
                == user_program.created_at,
                cursor.fetchall(),
            ),
        )
    )


def get_upe_start_date(cursor, user_program):
    cursor.execute(
        "SELECT user_programs.created_at AS created_at, "
        "user_programs.start start "
        "FROM user_programs "
        "JOIN user ON user_programs.user_id = user.id "
        "JOIN program ON user_programs.program_id = program.id "
        f"WHERE email = '{user_program.wallet.user.email}' "
        f"AND program.name = '{user_program.program.name}'"
    )
    return next(
        map(
            lambda x: x[1],
            filter(
                lambda x: (
                    get_datetime_from_iso(x[0])
                    if x[0]
                    else get_datetime_from_iso(x[1]) - timezone.timedelta(days=3)
                )
                == user_program.created_at,
                cursor.fetchall(),
            ),
        )
    )


def get_close_date(cursor, user_program_external_id):
    cursor.execute(
        "SELECT created "
        "FROM user_program_profit "
        f"WHERE user_program_id = '{user_program_external_id}' "
        "ORDER BY created DESC"
    )
    result = cursor.fetchone()
    if result:
        return get_datetime_from_iso(result[0])


def get_user_program(wallet, program, created_at_iso, start_iso):
    up_created_at = (
        get_datetime_from_iso(created_at_iso)
        if created_at_iso
        else get_datetime_from_iso(start_iso) - timezone.timedelta(days=3)
    )
    return UserProgram.objects.get(
        wallet=wallet,
        program=program,
        created_at=up_created_at,
    )


NAME_TO_GENDER = {
    "Admin": PersonalVerification.Gender.MALE,
    "Екатерина": PersonalVerification.Gender.FEMALE,
    "Start": PersonalVerification.Gender.MALE,
    "Евгений": PersonalVerification.Gender.MALE,
    "Good": PersonalVerification.Gender.MALE,
    "Марат": PersonalVerification.Gender.MALE,
    "Роберт": PersonalVerification.Gender.MALE,
    "Ильдар": PersonalVerification.Gender.MALE,
    "Александр": PersonalVerification.Gender.MALE,
    "Михаил": PersonalVerification.Gender.MALE,
    "Людмила": PersonalVerification.Gender.FEMALE,
    "Ильнар": PersonalVerification.Gender.MALE,
    "Виктор": PersonalVerification.Gender.MALE,
    "Рустем": PersonalVerification.Gender.MALE,
    "Юлия": PersonalVerification.Gender.FEMALE,
    "Оксана": PersonalVerification.Gender.FEMALE,
    "Вадим": PersonalVerification.Gender.MALE,
    "Татьяна": PersonalVerification.Gender.FEMALE,
    "Рамиль": PersonalVerification.Gender.MALE,
    "Aleksei": PersonalVerification.Gender.MALE,
    "Руслан": PersonalVerification.Gender.MALE,
    "Наталья": PersonalVerification.Gender.FEMALE,
    "Денис": PersonalVerification.Gender.MALE,
    "Владимир": PersonalVerification.Gender.MALE,
    "Алмаз": PersonalVerification.Gender.MALE,
    "Дмитрий": PersonalVerification.Gender.MALE,
    "Алексей": PersonalVerification.Gender.MALE,
    "Сергей": PersonalVerification.Gender.MALE,
    "Андрей": PersonalVerification.Gender.MALE,
    "Имя": PersonalVerification.Gender.MALE,
    "Наиль": PersonalVerification.Gender.MALE,
    "Резеда": PersonalVerification.Gender.FEMALE,
    "Айрат": PersonalVerification.Gender.MALE,
    "Раис": PersonalVerification.Gender.MALE,
    "Валерий": PersonalVerification.Gender.MALE,
    "Георгий": PersonalVerification.Gender.MALE,
    "Лейла": PersonalVerification.Gender.FEMALE,
    "Елена": PersonalVerification.Gender.FEMALE,
    "Гульнур": PersonalVerification.Gender.MALE,
    "Test": PersonalVerification.Gender.MALE,
    "Ярослав": PersonalVerification.Gender.MALE,
    "Арсен": PersonalVerification.Gender.MALE,
    "Тесак": PersonalVerification.Gender.MALE,
    "Салават": PersonalVerification.Gender.MALE,
    "Назар": PersonalVerification.Gender.MALE,
    "Артур": PersonalVerification.Gender.MALE,
    "Aleks": PersonalVerification.Gender.MALE,
    "Antoniv": PersonalVerification.Gender.MALE,
    "Jonah": PersonalVerification.Gender.MALE,
    "Антон": PersonalVerification.Gender.MALE,
    "Alexksa": PersonalVerification.Gender.FEMALE,
    "Сашко": PersonalVerification.Gender.MALE,
    "Геннадий": PersonalVerification.Gender.MALE,
    "Инна": PersonalVerification.Gender.FEMALE,
    "Павел": PersonalVerification.Gender.MALE,
    "Valeriia": PersonalVerification.Gender.FEMALE,
    "Никита": PersonalVerification.Gender.MALE,
    "Анвар": PersonalVerification.Gender.MALE,
    "Булат": PersonalVerification.Gender.MALE,
    "Ангелина": PersonalVerification.Gender.FEMALE,
    "Эльвира": PersonalVerification.Gender.FEMALE,
    "Евгения": PersonalVerification.Gender.FEMALE,
    "Artem": PersonalVerification.Gender.MALE,
    "Вадя": PersonalVerification.Gender.MALE,
    "Bytyh": PersonalVerification.Gender.MALE,
    "Ahmadishin": PersonalVerification.Gender.MALE,
    "Валентин": PersonalVerification.Gender.MALE,
    "Кирилл": PersonalVerification.Gender.MALE,
    "Леонид": PersonalVerification.Gender.MALE,
    "Alfred": PersonalVerification.Gender.MALE,
    "Diana": PersonalVerification.Gender.FEMALE,
    "Сервиса": PersonalVerification.Gender.FEMALE,
    "Владислав": PersonalVerification.Gender.MALE,
    "Альберт": PersonalVerification.Gender.MALE,
    "Pupkin": PersonalVerification.Gender.MALE,
    "Ростислав": PersonalVerification.Gender.MALE,
    "Светлана": PersonalVerification.Gender.FEMALE,
    "Vvv": PersonalVerification.Gender.MALE,
}
