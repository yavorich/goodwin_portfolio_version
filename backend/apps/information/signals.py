from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from apps.information.models import (
    Operation,
    UserProgram,
    UserProgramReplenishment,
    FrozenItem,
    Action,
)
from apps.information.services import send_operation_confirm_email


@receiver(pre_save, sender=Operation)
def save_operation(sender, instance: Operation, **kwargs):
    if instance.type not in [
        Operation.Type.WITHDRAWAL,
        Operation.Type.PROGRAM_CLOSURE,
        Operation.Type.PROGRAM_REPLENISHMENT_CANCEL,
    ]:
        instance.confirmed = True
    if not instance.confirmed:
        instance.set_code()


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
