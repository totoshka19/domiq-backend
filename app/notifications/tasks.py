import logging

from core.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_new_message_notification(self, recipient_email: str, sender_name: str, text: str) -> None:
    """Уведомить получателя о новом сообщении в чате."""
    try:
        _send_email(
            to=recipient_email,
            subject="Новое сообщение в Domiq",
            body=(
                f"Вам написал {sender_name}:\n\n"
                f"{text[:200]}{'...' if len(text) > 200 else ''}\n\n"
                f"Откройте приложение, чтобы ответить."
            ),
        )
        logger.info("Отправлено уведомление о сообщении на %s", recipient_email)
    except Exception as exc:
        logger.warning("Ошибка отправки уведомления: %s", exc)
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_listing_status_notification(
    self, owner_email: str, listing_title: str, new_status: str
) -> None:
    """Уведомить владельца об изменении статуса объявления."""
    status_labels = {
        "active": "опубликовано",
        "archived": "снято с публикации",
        "sold": "отмечено как проданное",
    }
    label = status_labels.get(new_status, new_status)
    try:
        _send_email(
            to=owner_email,
            subject=f"Статус объявления изменён — Domiq",
            body=f'Ваше объявление "{listing_title}" было {label}.',
        )
        logger.info("Отправлено уведомление о статусе объявления на %s", owner_email)
    except Exception as exc:
        logger.warning("Ошибка отправки уведомления: %s", exc)
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_moderation_notification(self, admin_email: str, listing_title: str) -> None:
    """Уведомить администратора о новом объявлении на модерацию."""
    try:
        _send_email(
            to=admin_email,
            subject="Новое объявление на модерацию — Domiq",
            body=f'Новое объявление "{listing_title}" ожидает модерации.',
        )
        logger.info("Отправлено уведомление о модерации на %s", admin_email)
    except Exception as exc:
        logger.warning("Ошибка отправки уведомления модератору: %s", exc)
        raise self.retry(exc=exc)


def _send_email(to: str, subject: str, body: str) -> None:
    """
    Заглушка для отправки email.
    Заменить на реальную реализацию через SMTP / SendGrid / Mailgun.
    """
    import smtplib
    from email.mime.text import MIMEText
    from core.config import settings

    if not getattr(settings, "SMTP_HOST", None):
        # В dev-режиме просто логируем, не падаем
        logger.info("[EMAIL STUB] To: %s | Subject: %s", to, subject)
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = getattr(settings, "SMTP_FROM", "noreply@domiq.ru")
    msg["To"] = to

    with smtplib.SMTP(settings.SMTP_HOST, getattr(settings, "SMTP_PORT", 587)) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)
