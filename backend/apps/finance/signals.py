from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.finance.models import (
    Operation,
    UserProgram,
    UserProgramReplenishment,
    FrozenItem,
    WithdrawalRequest,
    OperationHistory,
    OperationConfirmation,
    DestinationType,
    # Action,
)
from apps.finance.services.send_operation_confirm_email import (
    send_operation_confirm_email,
)
from apps.telegram.utils import send_telegram_message


@receiver(post_save, sender=Operation)
def handle_operation(sender, instance: Operation, created, **kwargs):
    if created:
        is_withdrawal = instance.type in [
            Operation.Type.WITHDRAWAL,
            Operation.Type.PROGRAM_REPLENISHMENT_CANCEL,
            Operation.Type.PROGRAM_CLOSURE,
        ]
        is_transfer = instance.type == Operation.Type.TRANSFER
        for destination in [DestinationType.EMAIL, DestinationType.TELEGRAM]:
            if (
                is_withdrawal
                and getattr(
                    instance.wallet.user.settings,
                    f"{destination}_request_code_on_withdrawal",
                )
                or is_transfer
                and getattr(
                    instance.wallet.user.settings,
                    f"{destination}_request_code_on_transfer",
                )
            ):
                OperationConfirmation.objects.create(
                    operation=instance, destination=destination
                )
        confirmations = instance.confirmations.all()
        if not confirmations:
            instance.apply()
        else:
            for confirmation in confirmations:
                confirmation.generate_code()
                if confirmation.destination == DestinationType.EMAIL:
                    send_operation_confirm_email(confirmation)
                elif confirmation.destination == DestinationType.TELEGRAM:
                    send_telegram_message(
                        telegram_id=confirmation.operation.wallet.user.telegram_id,
                        text=_(
                            "Подтверждение операции\nВаш код для подтверждения операции"
                        )
                        + f": {confirmation.code}",
                    )


@receiver(pre_save, sender=UserProgram)
def save_user_program(sender, instance: UserProgram, **kwargs):
    instance._set_name()
    instance._set_start_date()
    instance._set_end_date()
    instance._update_funds()
    try:
        previous = UserProgram.objects.get(pk=instance.pk)
        running = UserProgram.Status.RUNNING
        if previous.status != instance.status == running:
            instance.start_date = now().date()
    except UserProgram.DoesNotExist:
        pass


@receiver(post_save, sender=UserProgramReplenishment)
def save_user_program_replenishment(
    sender, instance: UserProgramReplenishment, created: bool, **kwargs
):
    if created:
        instance._set_apply_date()
        instance.save()
    elif not instance.done and instance.status == UserProgramReplenishment.Status.DONE:
        instance.apply()


@receiver(pre_save, sender=FrozenItem)
def save_frozen_item(sender, instance: FrozenItem, **kwargs):
    instance._set_defrost_date()


@receiver(post_save, sender=WithdrawalRequest)
def handle_withdrawal_request(sender, instance: WithdrawalRequest, **kwargs):
    if not instance.done:
        if instance.status == WithdrawalRequest.Status.PENDING:
            return
        if instance.status == WithdrawalRequest.Status.APPROVED:
            OperationHistory.objects.create(
                wallet=instance.wallet,
                type=OperationHistory.Type.SYSTEM_MESSAGE,
                description=dict(
                    ru=f"Заявка на вывод {instance.original_amount} USDT исполнена",
                    en=(
                        f"The withdrawal request of {instance.original_amount}"
                        "USDT has been processed."
                    ),
                    cn=None,
                ),
                target_name=None,
                amount=None,
            )
            instance.done_at = now().date()
        if instance.status == WithdrawalRequest.Status.REJECTED:
            if instance.reject_message == "":
                raise ValidationError("Reject message is required for REJECTED status.")
            instance.wallet.update_balance(free=instance.original_amount)
            OperationHistory.objects.create(
                wallet=instance.wallet,
                type=OperationHistory.Type.SYSTEM_MESSAGE,
                description=dict(
                    ru=f"Заявка на вывод {instance.original_amount} USDT отклонена",
                    en=(
                        f"The withdrawal request of {instance.original_amount}"
                        "USDT has been rejected."
                    ),
                    cn=None,
                ),
                target_name=instance.wallet.name,
                amount=instance.original_amount,
            )
        instance.done = True
        instance.save()
