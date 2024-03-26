from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.utils.timezone import now

from apps.information.models import (
    Operation,
    UserProgram,
    UserProgramReplenishment,
    FrozenItem,
    Action,
)
from apps.information.services.send_operation_confirm_email import (
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


@receiver(pre_save, sender=UserProgramReplenishment)
def save_user_program_replenishment(
    sender, instance: UserProgramReplenishment, **kwargs
):
    instance._set_apply_date()


@receiver(pre_save, sender=FrozenItem)
def save_frozen_item(sender, instance: FrozenItem, **kwargs):
    instance._set_defrost_date()


@receiver(pre_save, sender=Action)
def handle_action(sender, instance: Action, **kwargs):
    instance.apply()
    if not instance.name:
        instance.name = instance._get_name()
    if not instance.target_name:
        instance.target_name = instance._get_target_name()
