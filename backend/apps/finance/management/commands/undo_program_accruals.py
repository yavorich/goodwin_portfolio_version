from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.db import transaction
from datetime import datetime
from decimal import Decimal

from apps.finance.models import (
    UserProgramHistory,
    OperationHistory,
    Wallet,
    Program,
    Operation,
    UserProgramAccrual,
)
from apps.finance.models.operation_type import OperationType


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--date", required=True)
        parser.add_argument("--uid", required=False)

    def handle(self, date, uid=None, **kwargs):
        with transaction.atomic():
            try:
                date = datetime.strptime(date, "%Y-%m-%d")
                qs = Wallet.objects.all()
                if uid is not None:
                    qs = qs.filter(user_id=uid)
                self.run(qs, date)
            except Exception as e:
                raise e

    def run(self, qs, date):
        def get_total(queryset, attr):
            return queryset.aggregate(total=Sum(attr))["total"] or Decimal("0.0")

        accruals_to_undo = UserProgramAccrual.objects.filter(
            created_at=date, program__wallet__in=qs.values_list("user_id", flat=True)
        )
        print(f"Accruals to undo: {accruals_to_undo.values_list('amount', flat=True)}")
        total_success_fee = get_total(accruals_to_undo, "success_fee")
        total_management_fee = get_total(accruals_to_undo, "management_fee")
        print(
            f"Total success fee: {total_success_fee}, "
            f"total management fee: {total_management_fee}"
        )
        for wallet in qs:
            print(f"Wallet id: {wallet.user.id}")
            for user_program in wallet.programs.all():
                accrual = user_program.accruals.filter(created_at=date).first()
                if not accrual:
                    print(f"No accrual for date {date.strftime('%Y-%m-%d')}")
                    continue
                amount = accrual.amount
                print(f"Accrual amount: {str(amount)}")
                is_daily = (
                    user_program.program.withdrawal_type == Program.WithdrawalType.DAILY
                )
                print(f"is_daily: {str(is_daily)}")
                if is_daily:

                    # откат баланса
                    print(f"Balance before update: {str(wallet.free)}")
                    wallet.update_balance(free=-amount)
                    print(f"Balance after update: {str(wallet.free)}")

                    # откат истории кошелька
                    for history in wallet.user.wallet_history.filter(
                        created_at__gte=date
                    ):
                        print(
                            f"Wallet history: {history.created_at.strftime('%Y-%m-%d')}"
                            f", {str(history.free)} -> ",
                            end="",
                        )
                        history.free -= amount
                        history.save()
                        print(str(history.free))

                # откат начисления
                accrual.delete()
                print("Accrual has been deleted")
                try:

                    # откат истории программ
                    program_history = UserProgramHistory.objects.get(
                        created_at=date, user_program=user_program
                    )
                    print(
                        f"Program history: "
                        f"{program_history.created_at.strftime('%Y-%m-%d')}, "
                        f"deposit={program_history.deposit}, "
                        f"profit={program_history.profit}, "
                        f"funds={program_history.funds} -> ",
                        end="",
                    )
                    program_history.profit -= amount
                    program_history.funds = (
                        program_history.deposit + program_history.profit
                        if is_daily
                        else program_history.deposit
                    )
                    program_history.save()
                    print(
                        f"deposit={program_history.deposit}, "
                        f"profit={program_history.profit}, "
                        f"funds={program_history.funds}",
                    )
                except UserProgramHistory.DoesNotExist:
                    print("Program history not found")

        # откат комиссий
        commissions_wallet = Wallet.objects.get(user__business_account=True)
        accruals_commissions = commissions_wallet.operations_history.filter(
            created_at__date=date,
            operation_type__in=[
                OperationType.SUCCESS_FEE,
                OperationType.MANAGEMENT_FEE,
            ],
        )
        print(f"Commissions found: {[c.operation_type for c in accruals_commissions]}")
        total_commissions = get_total(accruals_commissions, "amount")
        print(f"Total commissions: {total_commissions}")
        print(f"Commissions balance before update: {str(commissions_wallet.free)}")
        for commission in accruals_commissions:
            if commission.operation_type == OperationType.SUCCESS_FEE:
                decrease_value = total_success_fee
            elif commission.operation_type == OperationType.MANAGEMENT_FEE:
                decrease_value = total_management_fee
            commissions_wallet.update_balance(free=-decrease_value)
            print(
                f"{commission.operation_type} before update: {str(commission.amount)}"
            )
            commission.amount -= decrease_value
            commission.save()
            print(f"{commission.operation_type} after update: {str(commission.amount)}")
        print(f"Commissions balance after update: {str(commissions_wallet.free)}")

        # print(f"Commissions balance before update: {str(commissions_wallet.free)}")
        # commissions_wallet.update_balance(free=-total_commissions)
        # print(f"Commissions balance after update: {str(commissions_wallet.free)}")
        # accruals_commissions.delete()

        # откат истории операций
        OperationHistory.objects.filter(
            operation_type=OperationType.PROGRAM_ACCRUAL,
            created_at__date=date,
        ).delete()

        # откат операций
        Operation.objects.filter(
            type=OperationType.PROGRAM_ACCRUAL, created_at__date=date
        ).delete()
