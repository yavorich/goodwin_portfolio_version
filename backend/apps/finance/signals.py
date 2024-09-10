from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.utils.timezone import now, timedelta
from django.utils import translation
from rest_framework.exceptions import ValidationError

from config.celery import celery_app
from apps.finance.models import (
    Operation,
    UserProgram,
    UserProgramReplenishment,
    FrozenItem,
    WithdrawalRequest,
    OperationHistory,
    OperationConfirmation,
    DestinationType,
    ProgramResult,
)
from apps.finance.models.operation_type import MessageType, OperationType
from apps.finance.services.send_operation_confirm_email import (
    send_operation_confirm_email,
)
from apps.finance.services.commissions import add_commission_to_history
from apps.finance.tasks import make_daily_programs_accruals
from apps.telegram.tasks import send_template_telegram_message_task
from apps.telegram.models import MessageType as TelegramMessageType


@receiver(post_save, sender=Operation)
def handle_operation(sender, instance: Operation, created, **kwargs):
    if created and instance.created_at > now() - timedelta(hours=1):
        if instance.need_confirm:
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
                    send_template_telegram_message_task.delay(
                        telegram_id=confirmation.operation.wallet.user.telegram_id,
                        message_type=TelegramMessageType.OPERATION_CONFIRM,
                        insertion_data={"code": confirmation.code},
                        language=translation.get_language(),
                    )


@receiver(pre_save, sender=UserProgram)
def save_user_program(sender, instance: UserProgram, **kwargs):
    instance._set_name()
    instance._set_start_date()
    instance._set_end_date()
    try:
        previous = UserProgram.objects.get(pk=instance.pk)
        running = UserProgram.Status.RUNNING
        if previous.status != instance.status == running:
            instance.start_date = now().date()
            if telegram_id := instance.wallet.user.telegram_id:
                send_template_telegram_message_task.delay(
                    telegram_id,
                    message_type=TelegramMessageType.PROGRAM_STARTED,
                    insertion_data={
                        "program_name": instance.name,
                        "underlying_asset": instance.deposit,
                        "email": instance.wallet.user.email,
                    },
                    language=translation.get_language(),
                )
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
        if telegram_id := instance.program.wallet.user.telegram_id:
            send_template_telegram_message_task.delay(
                telegram_id,
                message_type=TelegramMessageType.START_WITH_REPLENISHMENT,
                insertion_data={
                    "program_name": instance.program.name,
                },
                language=translation.get_language(),
            )


@receiver(pre_save, sender=FrozenItem)
def save_frozen_item(sender, instance: FrozenItem, **kwargs):
    instance._set_defrost_date()


@receiver(pre_save, sender=WithdrawalRequest)
def reset_status_if_done(sender, instance: WithdrawalRequest, **kwargs):
    if instance.done:
        previous = WithdrawalRequest.objects.get(pk=instance.pk)
        instance.status = previous.status


@receiver(post_save, sender=WithdrawalRequest)
def handle_withdrawal_request(sender, instance: WithdrawalRequest, **kwargs):
    if not instance.done:
        if instance.status == WithdrawalRequest.Status.PENDING:
            return

        insertion_data = {"amount": float(instance.original_amount)}

        if instance.status == WithdrawalRequest.Status.APPROVED:
            instance.operation.add_history(
                type=OperationHistory.Type.SYSTEM_MESSAGE,
                message_type=MessageType.WITHDRAWAL_REQUEST_APPROVED,
                target_name=None,
                amount=None,
                insertion_data=insertion_data,
            )
            telegram_message_type = TelegramMessageType.SUCCESSFUL_TRANSFER
            instance.done_at = now().date()
            add_commission_to_history(
                commission_type=OperationType.WITHDRAWAL_FEE, amount=instance.commission
            )

        elif instance.status == WithdrawalRequest.Status.REJECTED:
            if instance.reject_message == "":
                raise ValidationError(
                    f"При постановке статуса {WithdrawalRequest.Status.REJECTED.label}"
                    f" необходимо указать причину отказа.",
                )

            instance.wallet.update_balance(free=instance.original_amount)
            instance.operation.add_history(
                type=OperationHistory.Type.SYSTEM_MESSAGE,
                message_type=MessageType.WITHDRAWAL_REQUEST_REJECTED,
                target_name=None,
                amount=None,
                insertion_data=insertion_data,
            )
            telegram_message_type = TelegramMessageType.TRANSFER_REJECTED

        if telegram_id := instance.wallet.user.telegram_id:
            send_template_telegram_message_task.delay(
                telegram_id,
                message_type=telegram_message_type,
                insertion_data={
                    "amount": instance.original_amount,
                    "commission_amount": instance.commission,
                    "amount_with_commission": instance.amount,
                    "transfer address": instance.address,
                    "email": instance.wallet.user.email,
                },
                language=translation.get_language(),
            )
        instance.done = True
        instance.save()
        if instance.operation:
            instance.operation.done = True
            instance.operation.save()


@receiver(pre_save, sender=ProgramResult)
def update_program_result_settings(sender, instance: ProgramResult, **kwargs):
    if instance.task_id:
        celery_app.control.revoke(instance.task_id)

    apply_datetime = instance.get_apply_datetime()
    print(apply_datetime, apply_datetime.tzinfo)
    if apply_datetime.date() <= instance.until:
        task_id = make_daily_programs_accruals.apply_async(eta=apply_datetime)
        instance.task_id = task_id
