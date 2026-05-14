from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from loguru import logger

@shared_task
def send_email_task(subject, plain_email, from_email, recipient_list, html_email=None):
    """
    Celery task to send emails asynchronously.
    """
    try:
        email = EmailMultiAlternatives(subject, plain_email, from_email, recipient_list)
        if html_email:
            email.attach_alternative(html_email, "text/html")
        email.send()
        logger.info(f"Email sent successfully to: {recipient_list}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: Error: {str(e)}")
        raise e
