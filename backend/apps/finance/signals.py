from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from apps.finance.models import (
    Operation,
    UserProgram,
    UserProgramReplenishment,
    FrozenItem,
    WithdrawalRequest,
    OperationHistory,
    # Action,
)
from apps.finance.services.send_operation_confirm_email import (
    send_operation_confirm_email,
)


@receiver(pre_save, sender=Operation)
def save_operation(sender, instance: Operation, **kwargs):
    if (
        instance.type
        in [
            Operation.Type.WITHDRAWAL,
            Operation.Type.PROGRAM_REPLENISHMENT_CANCEL,
            Operation.Type.PROGRAM_CLOSURE,
        ]
        and instance.wallet.user.settings.email_request_code_on_withdrawal
        or instance.type == Operation.Type.TRANSFER
        and instance.wallet.user.settings.email_request_code_on_transfer
    ):
        instance.set_code()
    else:
        instance.confirmed = True


@receiver(post_save, sender=Operation)
def handle_operation(sender, instance: Operation, created, **kwargs):
    if created:
        if not instance.confirmed:
            send_operation_confirm_email(instance)
        else:
            instance.apply()


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
