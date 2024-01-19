from celery import shared_task
from django.core.mail import send_mail
from django.utils.html import strip_tags
from config.settings import EMAIL_HOST_USER


@shared_task
def send_email_msg(email, subject, msg, from_email=None, html=False):
    if from_email is None:
        from_email = EMAIL_HOST_USER
    else:
        from_email = f"{from_email} <{EMAIL_HOST_USER}>"

    msg_data = {
        "subject": subject,
        "from_email": from_email,
        "recipient_list": [email],
    }
    if html:
        msg_data["message"] = strip_tags(msg)
        msg_data["html_message"] = msg
    else:
        msg_data["message"] = msg

    return send_mail(**msg_data)
